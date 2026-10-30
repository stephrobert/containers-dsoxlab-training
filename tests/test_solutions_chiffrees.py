"""Aucune solution de référence ne part en clair.

POURQUOI CE CONTRÔLE EXISTE

Une solution lisible dans le dépôt que l'apprenant clone ne gâche pas un lab
une fois : elle le gâche pour toujours, parce que git garde l'historique. Le
chiffrement par `ansible-vault` est donc la seule protection, et il ne vaut que
si quelque chose vérifie qu'il a bien été appliqué. Oublier un `ansible-vault
encrypt` ne lève nulle part : le fichier reste parfaitement valide, le cycle de
validation le joue sans broncher, et le défaut ne se voit qu'en relisant le
dépôt à la main.

CE QU'IL LIT, ET POURQUOI IL N'A PAS BESOIN DU MOT DE PASSE

L'en-tête que `ansible-vault` écrit en première ligne, et rien d'autre. Ce
contrôle tourne donc **sans `.vault-pass`** : c'est ce qui le rend jouable en
CI et par n'importe qui, alors que le secret ne voyage avec aucun catalogue de
la collection.

CE QU'IL NE PEUT PAS FAIRE

Il ne dit pas qu'une solution est JUSTE : c'est le travail de
`scripts/valider-labs.py`, qui la rejoue et exige 0 avant puis 100 après. Il ne
dit pas non plus qu'une solution oubliée dans l'historique a disparu : un
fichier retiré reste dans les objets git, d'où la règle de changer le mot de
passe plutôt que de se contenter d'un `git rm`.

    uv run pytest tests/test_solutions_chiffrees.py -v
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SOLUTIONS = RACINE / "solution"

#: L'en-tête qu'ansible-vault écrit en première ligne d'un fichier chiffré.
ENTETE_VAULT = b"$ANSIBLE_VAULT"

#: Fichiers de service, non chiffrés par nature : ils ne portent aucun contenu
#: de solution. `verified-with.json` est un index de versions d'outils, un
#: éventuel `README.md` explique où regarder.
EXEMPTS = {"verified-with.json", "README.md"}

#: Ce que ce répertoire peut porter sans que ce soit une solution : les caches
#: que Python et les outils y déposent.
PARTS_IGNOREES = {"__pycache__", ".pytest_cache", ".ruff_cache"}


def fichiers_de_solution() -> list[Path]:
    if not SOLUTIONS.is_dir():
        return []
    return sorted(
        f
        for f in SOLUTIONS.rglob("*")
        if f.is_file()
        and f.name not in EXEMPTS
        and not PARTS_IGNOREES.intersection(f.parts)
    )


def test_le_depot_porte_ses_solutions() -> None:
    """Garde-fou : sans lui, un `solution/` disparu rendrait la suite verte.

    Un contrôle qui ne trouve plus rien à contrôler passe, et c'est la forme la
    plus discrète de faux vert.
    """
    assert SOLUTIONS.is_dir(), (
        "Le répertoire solution/ est absent : aucune solution de référence ne "
        "peut être rejouée, et `scripts/valider-labs.py` ne prouverait plus "
        "rien sur le catalogue."
    )
    assert fichiers_de_solution(), (
        "solution/ existe mais ne porte aucun fichier : le balayage mesurerait "
        "le vide."
    )


@pytest.mark.parametrize(
    "fichier",
    fichiers_de_solution(),
    ids=lambda p: str(p.relative_to(SOLUTIONS)),
)
def test_la_solution_est_chiffree(fichier: Path) -> None:
    """Chaque fichier de solution porte l'en-tête d'ansible-vault."""
    debut = fichier.read_bytes()[: len(ENTETE_VAULT)]

    assert debut == ENTETE_VAULT, (
        f"{fichier.relative_to(RACINE)} n'est pas chiffré.\n\n"
        "Chiffrez-le avant de committer :\n"
        "    ansible-vault encrypt --vault-password-file .vault-pass "
        f"{fichier.relative_to(RACINE)}\n\n"
        "Si le fichier est déjà parti en clair dans un commit, le chiffrer "
        "maintenant ne suffit pas : la version lisible reste dans "
        "l'historique, et le mot de passe du vault doit changer."
    )


def test_le_mot_de_passe_du_vault_n_est_pas_suivi() -> None:
    """Un mot de passe commité avec ce qu'il ouvre annule le chiffrement.

    Il voyage avec le dépôt : l'apprenant qui clone reçoit la serrure et la clé
    dans le même paquet.
    """
    issue = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".vault-pass"],
        cwd=RACINE,
        capture_output=True,
        text=True,
        check=False,
    )

    assert issue.returncode != 0, (
        ".vault-pass est suivi par git. Retirez-le de l'index "
        "(`git rm --cached .vault-pass`), puis CHANGEZ le mot de passe et "
        "rechiffrez les solutions : la valeur publiée reste dans l'historique."
    )
