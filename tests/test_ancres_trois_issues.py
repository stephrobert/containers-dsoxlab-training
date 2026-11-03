"""Le controle d'ancres a TROIS issues, et une liste d'attente qui doit se vider.

POURQUOI CE TEST EXISTE

`scripts/verifier-ancres.py` interroge la PRODUCTION du site et sortait en 1 des
qu'une ancre etait fausse OU une page injoignable. Mesure du 2026-11-03, sur les
91 `doc_url` des labs, croisee lien par lien avec la source de `origin/main` du
site :

    41 verts en production
    50 rouges, dont 44 JUSTES a la source et 6 visant des pages en brouillon

Soit **zero dette reelle du catalogue sur 50 rouges**. Ce controle ne mesurait
pas le catalogue, il mesurait l'ecart de deploiement du site. Il etait rouge sur
`main` en permanence, et les PR etaient fusionnees par-dessus : un controle
qu'on fusionne par-dessus ne controle plus rien.

DEUX CHANGEMENTS, ET LEUR GARDE-FOU

1. Une page injoignable devient `unknown` au sens de `dsoxlab doctor` : elle
   s'affiche, elle ne peint pas en rouge, et `--strict` lui rend son propre code
   (`10`), distinct de l'echec reel (`1`).
2. Une ancre juste a la source mais pas encore deployee se declare dans
   `scripts/ancres-en-attente.yml`, nommee, datee et motivee, plutot que
   toleree en silence.

Le garde-fou du second est ce qui empeche ce fichier de devenir un depotoir :
le controle **echoue** sur une entree qui n'a plus d'objet, soit parce que
l'ancre resout desormais, soit parce qu'aucun `doc_url` ne la porte plus.

CE QUE CE TEST MESURE, ET POURQUOI IL NE PASSE PAS PAR LE RESEAU

Un test qui laisserait la sonde appeler le site mesurerait le deploiement du
jour, pas le code : il serait vert ou rouge selon l'heure. `ancres()` et
`attentes()` sont donc remplacees par des tables, et chaque cas est CHOISI.
C'est aussi ce qui evite le banc en panne, celui dont tous les cas rendent la
meme chose parce que la sonde ne repond a aucun : ici les codes attendus
divergent (0, 1, 10).

ET SURTOUT, IL PROVOQUE LES REFUS. Jouer « tout va bien -> code 0 » ne mesure
rien : un controle incapable de refuser passerait ce cycle sans broncher.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "scripts" / "verifier-ancres.py"

# La production, telle que CE TEST la decide. `None` = la page ne repond pas.
SERVIES: dict[str, set[str] | None] = {
    "https://exemple/servie/": {"section-qui-existe"},
    "https://exemple/injoignable/": None,
}

JUSTE = ("lab a", "https://exemple/servie/#section-qui-existe")
FAUSSE = ("lab b", "https://exemple/servie/#section-inventee")
INJOIGNABLE = ("lab c", "https://exemple/injoignable/#peu-importe")
SANS_ANCRE = ("lab d", "https://exemple/servie/")

# Une attente qui a encore son objet : l'ancre de `lab b` ne resout pas.
ATTENTE_UTILE = {("b", "section-inventee"): {"depuis": "2026-11-03"}}
# Une attente qui n'a plus d'objet : l'ancre de `lab a` resout.
ATTENTE_RESOLUE = {("a", "section-qui-existe"): {"depuis": "2026-11-03"}}
# Une attente qui ne correspond a aucun doc_url controle.
ATTENTE_MORTE = {("lab-disparu", "peu-importe"): {"depuis": "2026-11-03"}}


def _charger(monkeypatch: pytest.MonkeyPatch, listees: dict):
    spec = importlib.util.spec_from_file_location("verifier_ancres", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ancres", lambda page: SERVIES.get(page, set()))
    monkeypatch.setattr(module, "attentes", lambda: dict(listees))
    return module


@pytest.fixture
def controle(monkeypatch: pytest.MonkeyPatch):
    """Joue le controle sur des cibles choisies, sans reseau ni fichier."""

    def jouer(cibles: list[tuple[str, str]], *, strict: bool = False,
              listees: dict | None = None) -> tuple[int, str]:
        module = _charger(monkeypatch, listees or {})
        flux = io.StringIO()
        with contextlib.redirect_stdout(flux):
            code = module.controler(list(cibles), strict=strict)
        return code, flux.getvalue()

    return jouer


@pytest.mark.parametrize(
    ("libelle", "cibles", "strict", "attendu"),
    [
        ("une ancre juste ne refuse rien", [JUSTE], False, 0),
        ("une ancre juste ne refuse rien, meme en strict", [JUSTE], True, 0),
        ("une ancre FAUSSE est refusee", [FAUSSE], False, 1),
        ("une ancre FAUSSE est refusee en strict aussi", [FAUSSE], True, 1),
        ("une page injoignable ne refuse pas", [INJOIGNABLE], False, 0),
        ("une page injoignable refuse en strict, code 10", [INJOIGNABLE], True, 10),
        ("une faute l'emporte sur une ignorance", [FAUSSE, INJOIGNABLE], True, 1),
        ("un doc_url sans ancre ne juge rien", [SANS_ANCRE], True, 0),
    ],
)
def test_les_trois_issues(controle, libelle: str,
                          cibles: list[tuple[str, str]],
                          strict: bool, attendu: int) -> None:
    code, _ = controle(cibles, strict=strict)
    assert code == attendu, libelle


def test_une_ancre_declaree_en_attente_ne_refuse_plus(controle) -> None:
    """Declaree, elle est toleree : c'est tout l'objet du fichier."""
    code, sortie = controle([FAUSSE], listees=ATTENTE_UTILE)
    assert code == 0
    assert "EN ATTENTE" in sortie
    assert "2026-11-03" in sortie, "la sortie doit dire DEPUIS QUAND elle est tolérée"
    assert "FAUSSE" not in sortie


def test_une_attente_resolue_est_refusee(controle) -> None:
    """LE GARDE-FOU. L'ancre resout : la tolerance n'a plus d'objet.

    Sans ce refus, le fichier deviendrait un depotoir dont personne ne sait plus
    pourquoi une entree est la, et une vraie ancre fausse pourrait s'y cacher.
    """
    code, sortie = controle([JUSTE], listees=ATTENTE_RESOLUE)
    assert code == 1
    assert "ancres-en-attente.yml" in sortie
    assert "résolvent désormais" in sortie


def test_une_attente_morte_est_refusee(controle) -> None:
    """Une entree qui ne correspond a aucun doc_url controle."""
    code, sortie = controle([JUSTE], listees=ATTENTE_MORTE)
    assert code == 1
    assert "lab-disparu" in sortie
    assert "ne correspondent plus" in sortie


def test_une_page_injoignable_est_dite_et_non_tue(controle) -> None:
    """Un controle qui TAIT ce qu'il ignore est pire qu'absent.

    Ne plus refuser n'est pas ne plus dire : c'est la difference entre tolerer
    et dissimuler. Le cas doit rester lisible, avec le geste qui le tranche.
    """
    code, sortie = controle([INJOIGNABLE])
    assert code == 0
    assert "INJOIGNABLE" in sortie
    assert "injoignable/" in sortie
    assert "--strict" in sortie, "la sortie doit nommer le geste qui rend le cas bloquant"


def test_le_fichier_du_depot_est_lisible_et_motive() -> None:
    """La liste reellement commitee : chaque entree porte sa date et sa raison.

    Une tolerance sans date ne peut pas se perimer, et une tolerance sans raison
    ne se relit pas. Ce test porte sur le FICHIER du depot, pas sur une table de
    test : c'est lui qui sera lu dans six mois.
    """
    import yaml

    chemin = RACINE / "scripts" / "ancres-en-attente.yml"
    if not chemin.is_file():
        pytest.skip("aucune ancre en attente : toutes les leçons sont déployées")
    donnees = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    entrees = donnees.get("ancres") or []
    assert entrees, "un fichier présent mais vide se supprime"
    for entree in entrees:
        for champ in ("lab", "ancre", "page", "depuis", "pourquoi"):
            assert entree.get(champ), f"entrée sans {champ} : {entree}"
