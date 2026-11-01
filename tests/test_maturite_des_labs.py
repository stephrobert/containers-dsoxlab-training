"""Un squelette ne doit jamais passer pour un lab qui prouve quelque chose.

POURQUOI CE CONTRÔLE EXISTE

Le défaut qu'il ferme rend une suite de tests trompeuse : **pytest compte un
lab entièrement skippé comme une exécution réussie.** Un catalogue dont la
moitié des labs porte

    pytestmark = pytest.mark.skip(reason="Lab squelette : tests à écrire")

annonce « tous les labs passent » alors que la moitié ne mesure rien. Le
message est vrai au sens de pytest, et faux au sens de ce que le catalogue
promet.

CE CATALOGUE A FAIT LE BON CHOIX, ET C'EST CE QU'ON VÉRIFIE ICI

`dsoxlab new lab` pose ici une suite qui **lève** au lieu de skipper :

    def test_a_ecrire() -> None:
        raise AssertionError("Les tests de ce lab restent à écrire. ...")

Un squelette est donc ROUGE, jamais vert, et c'est exactement ce qu'il faut :
`dsoxlab check` rend un échec plutôt qu'un succès qui ne prouve rien. Ce module
tient ce choix en place. Mesuré le 2026-10-30 : 71 labs, dont 42 squelettes, et
les 42 lèvent bien. Aucune suite du catalogue ne porte de `pytestmark`.

POURQUOI UNE MATURITÉ DÉRIVÉE, ET SANS LISTE À TENIR

La première idée est de déclarer l'état dans `lab.yaml`. Deux raisons de ne pas
le faire, et la seconde est la vraie :

1. `dsoxlab validate-structure` REFUSE un champ inconnu du contrat ;
2. surtout, **un statut déclaré peut mentir.** Rien n'empêche d'écrire
   « vérifié » sans avoir rien vérifié, et l'on retombe sur le problème qu'on
   voulait résoudre.

La maturité se LIT donc dans le dépôt. Et contrairement au catalogue DevSecOps
jumeau, qui énumère ses squelettes dans une liste `COQUILLES`, ce module n'en
tient aucune : avec 42 squelettes en cours d'écriture, une liste de noms serait
réécrite à chaque lab livré, et un diff de 42 lignes ne se relit pas. Ce qui
est contrôlé ici est une **implication**, qui ne dépend d'aucun chiffre :

    tests écrits  <=>  solution de référence présente

Les deux moitiés comptent. Un lab écrit sans solution n'a jamais été éprouvé
dans le sens « 100 » : ses tests peuvent exiger l'impossible, et seul un
apprenant s'en apercevrait. Un squelette AVEC solution est l'inverse, et il est
tout aussi faux : la solution a été écrite pour des tests qui n'existent pas,
donc rien ne l'a jamais jouée.

    uv run pytest tests/test_maturite_des_labs.py -v
"""

from __future__ import annotations

import io
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import lab_target_roles

RACINE = Path(__file__).resolve().parent.parent
LABS = RACINE / "labs"
SOLUTIONS = RACINE / "solution"

#: Ce que `dsoxlab new lab` laisse dans la suite d'un lab non écrit.
MARQUEUR_SQUELETTE = "def test_a_ecrire"

#: Ce qu'un squelette doit faire : refuser. Le vérifier est le coeur de ce
#: module, parce que remplacer ce `raise` par un skip rendrait les 42
#: squelettes verts d'un coup, sans qu'aucun autre contrôle ne bouge.
MARQUEUR_DE_REFUS = "raise AssertionError"


def tous_les_labs() -> list[str]:
    return sorted(str(c.parent.relative_to(LABS)) for c in LABS.rglob("lab.yaml"))


def suite_du_lab(rel: str) -> Path:
    return LABS / rel / "challenge" / "tests" / "test_functional.py"


def est_un_squelette(rel: str) -> bool:
    suite = suite_du_lab(rel)
    if not suite.is_file():
        return True
    return MARQUEUR_SQUELETTE in suite.read_text(encoding="utf-8")


def a_une_solution(rel: str) -> bool:
    dossier = SOLUTIONS / rel
    return dossier.is_dir() and any(f.is_file() for f in dossier.rglob("*"))


TOUS = tous_les_labs()
SQUELETTES = [rel for rel in TOUS if est_un_squelette(rel)]
ECRITS = [rel for rel in TOUS if not est_un_squelette(rel)]


@pytest.fixture
def validateur(monkeypatch):
    monkeypatch.syspath_prepend(str(RACINE / "scripts"))
    return runpy.run_path(str(RACINE / "scripts/valider-labs.py"))


def test_la_photographie_vm_interroge_la_cible_pas_le_poste(validateur, tmp_path, monkeypatch):
    lab = tmp_path / "lab"
    lab.mkdir()
    (lab / "lab.yaml").write_text(
        "runtime:\n  type: vm\n  default: second\n  targets:\n"
        "    - {name: first, host: first.lab}\n"
        "    - {name: second, host: second.lab}\n"
    )
    monkeypatch.delenv("DSOXLAB_TARGET_HOST", raising=False)
    state = {
        "images": ["image:tag|sha256:abc"], "conteneurs": [], "volumes": [],
        "reseaux": ["bridge"], "docker": "26.1.5", "store": "classic",
    }
    called = []

    def command(args, journal, timeout):
        called.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps(state), "")

    def local_docker(_args):
        pytest.fail("Une photographie VM ne doit pas interroger le Docker du poste.")

    globals_ = validateur["photographier"].__globals__
    monkeypatch.setitem(globals_, "commande", command)
    monkeypatch.setitem(globals_, "docker", local_docker)
    photo = validateur["photographier"](lab, io.StringIO())
    assert called[0][-1] == "second.lab"
    assert photo["images"] == state["images"]
    assert photo["docker"] == "26.1.5"


@pytest.mark.parametrize("code,output", [
    (1, ""), (0, "not json"), (0, "{}"),
    (0, '{"images":[null],"conteneurs":[],"volumes":[],"reseaux":[],"docker":"26","store":"classic"}'),
])
def test_une_photographie_vm_impossible_ne_devient_pas_un_etat_vide(
    validateur, tmp_path, monkeypatch, code, output,
):
    (tmp_path / "lab.yaml").write_text(
        "runtime:\n  type: vm\n  targets:\n    - {name: cible, host: docker.lab}\n"
    )
    monkeypatch.setitem(
        validateur["photographier"].__globals__, "commande",
        lambda args, journal, timeout: subprocess.CompletedProcess(args, code, output, "SSH failed"),
    )
    with pytest.raises(validateur["Echec"], match="photographie"):
        validateur["photographier"](tmp_path, io.StringIO())


def test_la_photographie_distingue_les_images_orphelines(validateur):
    baseline = {
        "images": ["<none>:<none>|sha256:old"], "conteneurs": [],
        "volumes": [], "reseaux": [], "workdir_present": False,
    }
    after = dict(baseline, images=baseline["images"] + ["<none>:<none>|sha256:new"])
    assert validateur["ecarts"](baseline, after) == [
        "image laissé : <none>:<none>|sha256:new",
    ]


def test_la_photographie_couvre_les_roles_pas_les_cibles_alternatives(
    validateur, tmp_path, monkeypatch,
):
    (tmp_path / "lab.yaml").write_text(
        "runtime:\n  type: vm\n  default: principal\n  targets:\n"
        "    - name: principal\n      host: docker.lab\n"
        "      roles: {client: docker-client.lab, restore: docker-client.lab}\n"
        "    - {name: autre_distribution, host: autre.lab}\n"
    )
    monkeypatch.delenv("DSOXLAB_TARGET_HOST", raising=False)
    state = {
        "images": [], "conteneurs": [], "volumes": [], "reseaux": [],
        "docker": "26.1.5", "store": "classic",
    }
    called = []

    def command(args, journal, timeout):
        called.append(args[-1])
        return subprocess.CompletedProcess(args, 0, json.dumps(state), "")

    monkeypatch.setitem(validateur["photographier"].__globals__, "commande", command)
    photo = validateur["photographier"](tmp_path, io.StringIO())
    assert called == ["docker.lab", "docker-client.lab"]
    assert set(photo["autres_hotes"]) == {"docker-client.lab"}


def test_un_objet_laisse_sur_le_client_rend_le_lab_rouge(validateur):
    state = {
        "images": [], "conteneurs": [], "volumes": [], "reseaux": [],
        "workdir_present": False,
    }
    before = dict(state, autres_hotes={"docker-client.lab": dict(state)})
    after = dict(state, autres_hotes={
        "docker-client.lab": dict(state, volumes=["dsoxlab-restauration-data"]),
    })
    assert validateur["ecarts"](before, after) == [
        "docker-client.lab : volume laissé : dsoxlab-restauration-data",
    ]


def test_une_photographie_client_absente_rend_le_lab_rouge(validateur):
    state = {
        "images": [], "conteneurs": [], "volumes": [], "reseaux": [],
        "workdir_present": False,
    }
    before = dict(state, autres_hotes={"docker-client.lab": dict(state)})
    assert validateur["ecarts"](before, state) == [
        "docker-client.lab : photographie manquante avant ou après",
    ]


def test_la_solution_vm_rejoue_les_roles_de_la_cible(tmp_path, monkeypatch):
    (tmp_path / "lab.yaml").write_text(
        "runtime:\n  default: source\n  targets:\n"
        "    - {name: source, host: docker.lab, roles: {restore: docker-client.lab}}\n"
        "    - {name: alternative, host: autre.lab, roles: {restore: autre-client.lab}}\n"
    )
    monkeypatch.delenv("DSOXLAB_TARGET", raising=False)
    assert lab_target_roles(tmp_path, "docker.lab") == {"restore": "docker-client.lab"}
    assert lab_target_roles(tmp_path, "autre.lab") == {"restore": "autre-client.lab"}
    with pytest.raises(RuntimeError, match="non déclarée"):
        lab_target_roles(tmp_path, "inconnu.lab")


def resultat_mesure(passed, total=1):
    return {
        "passed": passed, "total": total, "recorded": True, "skipped": 0,
        "status": "passed" if passed == total else "failed", "echecs": [],
    }


@pytest.mark.parametrize("second_score,expected", [(1, "VALIDE"), (0, "ROUGE")])
def test_le_double_passage_exige_un_second_succes(
    validateur, tmp_path, monkeypatch, second_score, expected,
):
    globals_ = validateur["valider"].__globals__
    monkeypatch.setenv("HOME", str(tmp_path))
    scores = iter([0, 1, 0, second_score])
    solutions = []
    state = {
        "images": [], "conteneurs": [], "volumes": [], "reseaux": [],
        "workdir_present": False, "docker": "26", "store": "classic", "host": "docker.lab",
    }
    monkeypatch.setitem(globals_, "CACHE", tmp_path)
    monkeypatch.setitem(globals_, "photographier", lambda *_: state)
    monkeypatch.setitem(globals_, "dsoxlab", lambda *_: subprocess.CompletedProcess([], 0, "", ""))
    monkeypatch.setitem(globals_, "check", lambda *_: resultat_mesure(next(scores)))
    monkeypatch.setitem(globals_, "poser_solution", lambda *_: solutions.append(True))
    result = validateur["valider"](tmp_path / "lab", double_passage=True)
    assert len(solutions) == 2
    assert result["protocole"] == "double-passage"
    assert result["apres_rejeu"]["passed"] == second_score
    assert result["verdict"] == expected


def test_un_second_passage_absent_ne_devient_pas_une_preuve(validateur):
    result = {
        "avant": resultat_mesure(0), "apres": resultat_mesure(1),
        "rejeu": resultat_mesure(0), "protocole": "double-passage", "ecarts": [],
    }
    assert validateur["verdict"](result, True) == "ROUGE"
    with pytest.raises(ValueError, match="exige le rejeu"):
        validateur["valider"](Path("unused"), rejeu=False, double_passage=True)


def test_un_second_passage_sans_mesure_reste_a_remesurer(validateur):
    result = {
        "avant": resultat_mesure(0), "apres": resultat_mesure(1),
        "rejeu": resultat_mesure(0), "protocole": "double-passage", "ecarts": [],
        "apres_rejeu": {"passed": 0, "total": 0, "recorded": True, "status": "not_measured"},
    }
    assert validateur["verdict"](result, True) == "SKIP"


def test_la_relecture_cli_respecte_le_lab_selectionne(validateur, tmp_path, monkeypatch):
    labs = tmp_path / "labs"
    for name in ("selected", "unmeasured"):
        folder = labs / name
        folder.mkdir(parents=True)
        (folder / "lab.yaml").write_text(f"id: {name}\n")
    results = tmp_path / "validation.json"
    results.write_text(json.dumps({
        "selected": {
            "verdict": "VALIDE", "protocole": "double-passage",
            "apres_rejeu": resultat_mesure(1),
        },
    }))
    globals_ = validateur["main"].__globals__
    monkeypatch.setitem(globals_, "LABS", labs)
    monkeypatch.setitem(globals_, "RESULTATS", results)
    monkeypatch.setattr(sys, "argv", [
        "valider-labs.py", "--check", "--lab", "selected", "--double-passage",
    ])
    assert validateur["main"]() == 0
    monkeypatch.setattr(sys, "argv", ["valider-labs.py", "--check"])
    assert validateur["main"]() == 1


def test_un_nettoyage_ne_peut_pas_supprimer_les_objets_preexistants(validateur):
    baseline = {
        "images": [], "conteneurs": [], "volumes": ["travail-apprenant"],
        "reseaux": [], "workdir_present": False,
    }
    after = dict(baseline, volumes=[])
    assert validateur["ecarts"](baseline, after) == [
        "volume préexistant supprimé : travail-apprenant",
    ]


def test_la_photographie_shell_reste_locale(validateur, tmp_path, monkeypatch):
    (tmp_path / "lab.yaml").write_text("runtime:\n  type: shell\n")
    called = []

    def docker(args):
        called.append(args)
        return []

    def remote(*_args):
        pytest.fail("Une photographie shell ne doit pas lancer un relevé SSH.")

    globals_ = validateur["photographier"].__globals__
    monkeypatch.setitem(globals_, "docker", docker)
    monkeypatch.setitem(globals_, "commande", remote)
    photo = validateur["photographier"](tmp_path, io.StringIO())
    assert len(called) == 4
    assert photo["images"] == []
    assert "host" not in photo


def test_le_catalogue_se_lit_dans_les_deux_etats() -> None:
    """Garde-fou : un marqueur qui dériverait classerait tout du même côté.

    Si `dsoxlab new lab` change sa tournure, tous les labs passent pour écrits
    et les contrôles ci-dessous ne jugent plus rien, en silence.
    """
    assert TOUS, "aucun lab.yaml trouvé : le glob est cassé."
    assert ECRITS, (
        f"Aucun lab écrit : `{MARQUEUR_SQUELETTE}` n'est probablement plus le "
        "marqueur que pose le générateur."
    )
    if not SQUELETTES:
        # SANS SQUELETTE, CE GARDE-FOU NE MESURE PLUS RIEN, et il ne prouve pas
        # pour autant que le marqueur a dérivé : les deux situations se
        # ressemblent et n'appellent pas le même geste. Il saute donc, au lieu
        # de refuser une livraison saine ou de conclure au vert sans avoir
        # regardé.
        #
        # Rencontré en livrant sur `main` : la branche de travail porte 39
        # squelettes, et la livraison n'emporte que les labs attestés. Le
        # contrôle y accusait un catalogue dont tous les labs sont écrits.
        pytest.skip(
            "aucun squelette dans ce catalogue : la dérive du marqueur ne peut "
            "pas être mesurée ici. C'est le cas d'une livraison qui n'emporte "
            "que des labs attestés, et ce n'est pas un défaut."
        )


@pytest.mark.parametrize("rel", SQUELETTES)
def test_un_squelette_refuse_au_lieu_de_skipper(rel: str) -> None:
    """Un lab non écrit doit être ROUGE, pas vert et muet.

    C'est le point de tout ce module : pytest compte un skip comme un succès,
    et un catalogue de squelettes skippés annonce alors que tout passe.
    """
    texte = suite_du_lab(rel).read_text(encoding="utf-8")

    assert MARQUEUR_DE_REFUS in texte, (
        f"{rel} est un squelette dont la suite ne lève pas : elle ne porte pas "
        f"`{MARQUEUR_DE_REFUS}`.\n\nUn squelette qui skippe fait passer "
        "`dsoxlab check` et le rejeu du catalogue au vert sans rien prouver. "
        "Tant que les tests ne sont pas écrits, la suite doit refuser."
    )
    assert "pytestmark" not in texte, (
        f"{rel} porte un `pytestmark` : s'il désactive la suite, le lab devient "
        "vert sans mesurer quoi que ce soit. Aucune suite du catalogue n'en "
        "emploie, et c'est ce qui rend le rejeu lisible."
    )


@pytest.mark.parametrize("rel", ECRITS)
def test_un_lab_ecrit_porte_une_solution_de_reference(rel: str) -> None:
    """Un test sans solution ne peut pas être validé.

    C'est l'implication que le catalogue doit tenir :

        lab publié  =>  solution existe  =>  solution rejouable

    Sans solution, `scripts/valider-labs.py` ne peut rien rejouer, et le lab n'a
    jamais été éprouvé dans le sens « 100 ».
    """
    assert a_une_solution(rel), (
        f"{rel} a des tests fonctionnels écrits, mais AUCUNE solution sous "
        f"solution/{rel}/.\n\nRien ne prouve alors que ses tests sont "
        "satisfaisables : ils peuvent exiger l'impossible, et seul un apprenant "
        "s'en apercevrait."
    )


@pytest.mark.parametrize("rel", SQUELETTES)
def test_un_squelette_ne_porte_pas_de_solution(rel: str) -> None:
    """L'autre moitié de l'implication, et elle attrape une incohérence réelle.

    Une solution écrite pour des tests qui n'existent pas n'a jamais été jouée
    par quoi que ce soit : le cycle de validation a besoin des deux. Si la
    solution est juste, ce sont les tests qui manquent ; si les tests ont été
    effacés, c'est une régression qu'il faut voir.
    """
    assert not a_une_solution(rel), (
        f"{rel} porte une solution sous solution/{rel}/, mais sa suite est "
        "encore le squelette du générateur.\n\nRien n'a donc jamais joué cette "
        "solution : le cycle « 0 avant, 100 après » a besoin de tests écrits. "
        "Soit les tests restent à écrire et la solution est prématurée, soit "
        "ils ont disparu."
    )
