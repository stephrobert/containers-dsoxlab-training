"""Méta-test du dépôt : aucune assertion ne refuse sans dire pourquoi.

Ce contrôle est le pendant de `test_assertions_bilingues.py`, et il est séparé
à dessein. Celui-là vérifie que le texte lu par l'apprenant existe dans les
deux langues ; celui-ci vérifie qu'il existe. Son voisin l'énonçait déjà :
« une assertion **sans** message n'est pas refusée ici : c'est un autre défaut,
que le style des tests du dépôt traite ailleurs. On ne mélange pas les deux, un
contrôle qui refuse deux choses à la fois ne dit plus laquelle. »

**Ailleurs n'existait pas**, et c'est ce que ce fichier répare.

POURQUOI IL EXISTE, ET CE QU'IL A TROUVÉ
----------------------------------------

Mesuré le 2026-11-05 en parsant l'AST des 90 labs : **1313 assertions, dont 10
sans aucun message**, toutes dans `reseau-pare-feu-cible/challenge/tests/
probe.py`. Le contrôle bilingue les voyait et les laissait passer, par
construction.

Ce que l'apprenant lisait quand l'une refusait, mesuré avec un interpréteur :

    File "<string>", line 5, in <module>
    File "<string>", line 4, in assess
    AssertionError

Une trace et un mot. Deux causes s'additionnaient : l'assertion ne portait pas
de message, et l'extracteur du test ne retenait que les lignes commençant par
« AssertionError: ». Or **Python n'écrit les deux-points que s'il y a un
message**, si bien que le cas nu tombait dans le repli qui rend la trace brute.
La docstring de cet extracteur affirmait pourtant que « la sonde lève ses
assertions avec des messages écrits pour être lus ».

LES SONDES COMPTENT AUTANT QUE LES TESTS
----------------------------------------

Le périmètre est le même que celui du contrôle bilingue, `labs/*/challenge/
tests/*.py`, et il inclut les `probe.py`. C'est nécessaire : une sonde est
jouée sur la machine du lab, et son `AssertionError` remonte dans le message du
test qui la lance. L'apprenant la lit donc tout autant, et c'est précisément là
que les dix se trouvaient.

CE QU'IL NE JUGE PAS
--------------------

Ni la qualité du message, ni sa pertinence : une phrase creuse passerait. Il
mesure l'existence, rien de plus, et c'est déjà ce qui manquait.
"""

from __future__ import annotations

import ast
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
LABS = RACINE / "labs"


def _fichiers_de_test() -> list[Path]:
    """Les mêmes fichiers que le contrôle bilingue, sondes comprises."""
    return sorted(
        f for f in LABS.glob("*/challenge/tests/*.py")
        if "__pycache__" not in f.parts
    )


def _lab_de(fichier: Path) -> str:
    return fichier.parent.parent.parent.name


def test_le_glob_regarde_quelque_chose() -> None:
    """Garde-fou : un glob cassé rendrait ce fichier vert sans rien mesurer.

    C'est la règle du dépôt, et elle a déjà servi : un contrôle qui n'a pas pu
    regarder ne conclut jamais au vert.
    """
    fichiers = _fichiers_de_test()
    assert len(fichiers) >= 80, (
        f"{len(fichiers)} fichier(s) de test trouvé(s) sous labs/*/challenge/"
        "tests/*.py, alors que le catalogue en porte au moins un par lab. Le "
        "glob ne regarde plus au bon endroit, et ce contrôle ne mesure rien."
    )


def test_aucune_assertion_ne_refuse_sans_message() -> None:
    """Chaque `assert` porte un second argument, quel qu'il soit."""
    nues: list[str] = []
    for fichier in _fichiers_de_test():
        arbre = ast.parse(fichier.read_text(encoding="utf-8"))
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Assert) and noeud.msg is None:
                nues.append(f"{_lab_de(fichier)} : {fichier.name}:{noeud.lineno}")

    assert not nues, (
        f"{len(nues)} assertion(s) refuseraient sans dire pourquoi, et "
        "l'apprenant ne lirait qu'une trace Python et le mot « AssertionError » :\n"
        + "\n".join(f"  {n}" for n in nues)
        + "\n\nChaque assertion porte un message, par `message(en=…, fr=…)` du "
        "conftest. Une sonde compte autant qu'un test : son AssertionError "
        "remonte dans le message du test qui la lance."
    )
