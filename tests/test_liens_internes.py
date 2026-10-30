"""Tout lien relatif d'un Markdown pointe vers un fichier qui existe.

POURQUOI CE CONTRÔLE EXISTE

Un lien interne cassé ne fait échouer aucun test fonctionnel : il ne casse que
la navigation de l'apprenant, en silence. C'est exactement ce qu'un contrôle
attrape mieux qu'une relecture, et le catalogue Ansible jumeau en a relevé 150
d'un coup le jour où il y a été écrit, dont 112 qui pointaient un niveau trop
haut.

Ce catalogue a deux raisons de plus d'en avoir besoin :

1. **la table des README est générée** par `scripts/gen_catalog.py`, et elle
   renvoie vers les répertoires de labs. Un lab renommé y laisserait un renvoi
   mort sans que rien ne le dise ;
2. **le nombre de `../` n'est pas le même partout.** Depuis
   `labs/<lab>/README.md`, la racine est à deux niveaux ; depuis
   `labs/<lab>/challenge/README.md`, elle est à trois. C'est une source
   d'erreur mécanique, et le genre de détail qu'une relecture ne voit pas.

CE QU'IL NE CONTRÔLE PAS

Les URL absolues. Elles ne sont pas du ressort de ce module : le moteur les
joint avec `dsoxlab validate-structure --check-urls`, et les ancres des
`doc_url` ont leur propre contrôle, `scripts/verifier-ancres.py`. Les deux font
du réseau, celui-ci non : il reste donc rapide et jouable hors connexion, dans
un hook.

Il ne contrôle pas non plus l'ancre d'un lien relatif (`../README.md#section`) :
elle est résolue par le lecteur Markdown, pas par le système de fichiers. Elle
est retirée avant de tester le chemin.

    uv run pytest tests/test_liens_internes.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
LABS = RACINE / "labs"

#: `[libellé](cible)` où la cible est relative, donc commence par `./` ou `../`.
#: Un lien `(image.png)` sans préfixe n'est pas retenu : la forme employée dans
#: ce catalogue est toujours explicite.
LIEN_RELATIF = re.compile(r"\[[^\]]*\]\((\.\.?/[^)]+)\)")

#: Chaque lab porte au moins quatre Markdown (README et scénario, en anglais et
#: en français), les labs écrits en portent six avec leurs briefs. Le seuil suit
#: donc la taille du catalogue au lieu d'être une constante, qui deviendrait
#: fausse au lab suivant. Mesuré le 2026-10-30 : 358 fichiers pour 71 labs.
MARKDOWN_MINIMUM_PAR_LAB = 4


def _fichiers_markdown() -> list[Path]:
    """Les Markdown des labs, et ceux de la racine du dépôt."""
    return sorted(LABS.rglob("*.md")) + sorted(RACINE.glob("*.md"))


def _nombre_de_labs() -> int:
    return len(list(LABS.rglob("lab.yaml")))


def _liens_casses(fichier: Path) -> list[str]:
    contenu = fichier.read_text(encoding="utf-8", errors="ignore")
    casses = []
    for cible in LIEN_RELATIF.findall(contenu):
        chemin = (fichier.parent / cible.split("#")[0]).resolve()
        if not chemin.exists():
            casses.append(cible)
    return casses


def test_il_y_a_des_markdown_a_verifier() -> None:
    """Garde-fou : sans lui, un glob cassé rendrait la suite verte à vide."""
    trouves = _fichiers_markdown()
    labs = _nombre_de_labs()

    assert labs, "aucun lab.yaml trouvé : le glob est cassé."
    assert len(trouves) >= MARKDOWN_MINIMUM_PAR_LAB * labs, (
        f"Seulement {len(trouves)} fichier(s) .md trouvé(s) pour {labs} labs : "
        "le glob est probablement cassé, et la suite deviendrait verte sans "
        "rien mesurer."
    )


def test_l_extracteur_voit_bien_un_lien_relatif() -> None:
    """Le contrôle doit VOIR ce qu'il prétend voir.

    Une expression régulière cassée rend tout le module vert : plus aucun lien
    n'est extrait, donc aucun n'est déclaré mort. Les cas sont construits ici
    plutôt que cherchés dans le dépôt, pour que ce test ne dépende pas du
    contenu du jour.
    """
    assert LIEN_RELATIF.findall("voir [le brief](./challenge/README.md)") == [
        "./challenge/README.md"
    ]
    assert LIEN_RELATIF.findall("voir [la racine](../../README.md#titre)") == [
        "../../README.md#titre"
    ]
    assert LIEN_RELATIF.findall("[le blog](https://www.stephane-robert.info)") == [], (
        "Une URL absolue ne doit pas être prise pour un lien relatif : elle est "
        "contrôlée par le moteur, qui la joint."
    )


@pytest.mark.parametrize(
    "fichier",
    _fichiers_markdown(),
    ids=lambda p: str(p.relative_to(RACINE)),
)
def test_les_liens_relatifs_pointent_vers_un_fichier_existant(fichier: Path) -> None:
    casses = _liens_casses(fichier)

    assert not casses, (
        f"{fichier.relative_to(RACINE)} contient {len(casses)} lien(s) mort(s) :\n"
        + "\n".join(f"  - {c}" for c in casses)
        + "\n\nComptez les niveaux depuis le fichier qui PORTE le lien : depuis "
        "`labs/<lab>/README.md`, la racine du dépôt est à deux `../` ; depuis "
        "`labs/<lab>/challenge/README.md`, elle est à trois."
    )
