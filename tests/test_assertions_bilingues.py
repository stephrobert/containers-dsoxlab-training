"""Méta-test du dépôt : ce que l'apprenant lit quand un test échoue existe dans les deux langues.

Quand `dsoxlab check` refuse, il affiche le **message écrit par l'auteur du
test**. C'est la seule consigne que l'apprenant reçoit à cet instant, et c'est
donc de l'interface, exactement comme un `README`. Tout le reste du catalogue
existe en anglais et en français ; ce texte-là ne peut pas l'être par
duplication, parce que le contrat dsoxlab impose un nom de fichier unique,
`challenge/tests/test_functional.py`. D'où le helper `message(en=…, fr=…)` du
`conftest.py`, qui choisit à l'exécution sur `DSOXLAB_LANG`.

POURQUOI CE TEST EXISTE, ET POURQUOI MAINTENANT
-----------------------------------------------

Le `conftest.py` documente cet usage sur quarante lignes, et **rien ne le
contrôlait**. Mesuré le 2026-10-29, en parsant l'AST des tests livrés :

    publier-service    735 assert dont 732 via message()   (99,6 %)
    gitlab-ci          393 assert dont 393 via message()   (100 %)
    containers          10 assert dont   0 via message()   (0 %)

Les deux catalogues livrés tiennent la convention par discipline d'écriture.
Celui-ci, qui n'avait encore qu'un seul lab écrit, l'avait déjà perdue. Le
poser avant d'écrire les soixante-dix labs restants coûte ce fichier ; le poser
après coûte soixante-dix relectures, et l'expérience du dépôt est qu'elles
n'ont pas lieu.

CE QU'IL MESURE, ET CE QU'IL NE MESURE PAS
------------------------------------------

Il parse l'AST, il ne cherche pas un motif dans le texte. Un `grep` sur
`message(` dirait qu'un fichier « parle de » message sans dire si **chaque**
assertion y passe, et c'est précisément l'écart qui compte. Trois porteurs de
texte sont contrôlés, ceux que la mesure ci-dessus a trouvés dans les
catalogues livrés : `assert …, msg`, `pytest.fail(msg)` et `pytest.skip(msg)`.

Il ne juge pas la **qualité** de la traduction : un `fr=` recopié de l'anglais
passerait. Ce contrôle-là n'existe pas et relève d'une relecture humaine.

Une assertion **sans** message n'est pas refusée ici : c'est un autre défaut,
que le style des tests du dépôt traite ailleurs. On ne mélange pas les deux, un
contrôle qui refuse deux choses à la fois ne dit plus laquelle.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
LABS = REPO / "labs"

#: Les appels dont le premier argument est un texte lu par l'apprenant.
APPELS_PORTEURS = frozenset({"fail", "skip"})

#: Labs dont les messages ne sont pas encore bilingues. Elle n'est PAS une
#: exemption commode : comme la `DETTE` de `test_hints_ecrits.py`, le test
#: refuse aussi qu'un lab y reste alors qu'il est devenu conforme. Sans cette
#: seconde moitié, la liste ne décroîtrait jamais et plus personne ne la
#: regarderait.
DETTE: set[str] = set()


def _fichiers_de_test() -> list[Path]:
    return sorted(LABS.glob("*/challenge/tests/*.py"))


def _lab_de(fichier: Path) -> str:
    """L'identifiant du lab, remonté depuis challenge/tests/<fichier>."""
    return fichier.parent.parent.parent.name


def _est_appel_message(noeud: ast.expr | None) -> bool:
    """Le texte passe-t-il par `message(…)` ?

    On accepte l'appel nu et l'appel qualifié (`conftest.message(…)`) : les
    deux formes sont reconnues par dsoxlab, qui ne regarde que la forme de
    l'appel, et refuser la seconde serait une règle de notre invention.
    """
    if not isinstance(noeud, ast.Call):
        return False
    f = noeud.func
    if isinstance(f, ast.Name):
        return f.id == "message"
    return isinstance(f, ast.Attribute) and f.attr == "message"


def _porteurs_monolingues(source: str) -> list[tuple[str, int]]:
    """Les textes lus par l'apprenant qui ne passent pas par le helper.

    Rend `(genre, ligne)` pour chacun, afin que l'échec nomme l'endroit exact
    plutôt que le fichier : un message qui dit « quelque part dans ce fichier »
    fait relire deux cents lignes.
    """
    fautifs: list[tuple[str, int]] = []
    for noeud in ast.walk(ast.parse(source)):
        if isinstance(noeud, ast.Assert):
            if noeud.msg is not None and not _est_appel_message(noeud.msg):
                fautifs.append(("assert", noeud.lineno))
        elif isinstance(noeud, ast.Call):
            f = noeud.func
            if isinstance(f, ast.Attribute) and f.attr in APPELS_PORTEURS:
                premier = noeud.args[0] if noeud.args else None
                if premier is not None and not _est_appel_message(premier):
                    fautifs.append((f"pytest.{f.attr}", noeud.lineno))
    return sorted(fautifs, key=lambda p: p[1])


def test_il_y_a_des_tests_a_mesurer() -> None:
    """Garde-fou : un glob cassé rendrait ce fichier vert sans rien mesurer."""
    fichiers = _fichiers_de_test()
    assert fichiers, (
        "Aucun `labs/*/challenge/tests/*.py` : le glob ne regarde plus au bon "
        "endroit, ou le catalogue est vide."
    )
    assert any("assert" in f.read_text(encoding="utf-8") for f in fichiers), (
        "Aucun fichier de test ne porte d'assertion : il n'y a rien à mesurer, "
        "et un test vert ici ne voudrait rien dire."
    )


@pytest.mark.parametrize("fichier", _fichiers_de_test(), ids=_lab_de)
def test_chaque_message_lu_par_l_apprenant_est_bilingue(fichier: Path) -> None:
    lab = _lab_de(fichier)
    fautifs = _porteurs_monolingues(fichier.read_text(encoding="utf-8"))
    if lab in DETTE:
        pytest.skip(f"{lab} est dans la dette des messages monolingues")
    assert not fautifs, (
        f"{lab} : {len(fautifs)} message(s) lus par l'apprenant ne sont pas "
        "bilingues.\n\n"
        + "\n".join(f"    {fichier.name}:{ligne}  ({genre})" for genre, ligne in fautifs)
        + "\n\nIls s'écrivent avec le helper du conftest, qui choisit la langue "
        "à l'exécution :\n\n"
        "    from conftest import lab_host, message\n\n"
        "    assert f.exists, message(\n"
        '        en="/etc/myapp is missing. Create it with ansible.builtin.file.",\n'
        '        fr="/etc/myapp est absent. Cree-le avec ansible.builtin.file.",\n'
        "    )\n"
    )


@pytest.mark.parametrize("lab", sorted(DETTE))
def test_la_dette_ne_retient_aucun_lab_devenu_conforme(lab: str) -> None:
    """Un lab repris doit sortir de la dette, et c'est ce test qui l'exige."""
    fichiers = [f for f in _fichiers_de_test() if _lab_de(f) == lab]
    assert fichiers, (
        f"{lab} est dans la dette mais n'a aucun fichier de test : la liste "
        "nomme un lab qui n'existe plus."
    )
    restants = [p for f in fichiers for p in _porteurs_monolingues(f.read_text(encoding="utf-8"))]
    assert restants, (
        f"{lab} n'a plus aucun message monolingue : retire-le de `DETTE`, "
        "sinon la liste ne décroît jamais."
    )
