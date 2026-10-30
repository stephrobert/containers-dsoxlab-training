"""Un lab ÉCRIT ne doit pas se présenter comme un lab non écrit.

POURQUOI CE CONTRÔLE EXISTE

Le défaut qu'il ferme a échappé à tous les autres, et il est du même genre que
ceux qu'ils attrapent : **le lab était bon, sa présentation mentait.** Mesuré
dans le catalogue DevSecOps jumeau le 2026-09-24 : vingt-huit labs sur soixante-
dix, livrés et validés dans les deux sens, portaient toujours « ce lab n'est pas
encore écrit » en tête de leur README. L'apprenant qui ouvre un tel lab lit
qu'il n'existe pas, et c'est cela qu'il croit, pas la suite de tests.

Rien ne l'avait vu parce que les deux descriptions d'un lab, celle qui
s'exécute et celle qui se lit, n'étaient comparées par rien.
`test_maturite_des_labs.py` dérive la maturité du test fonctionnel, ce qui est
le bon critère pour savoir si un lab PROUVE quelque chose, mais un apprenant
lit d'abord un README.

COMMENT UN SQUELETTE EST RECONNU, ET POURQUOI CE CRITÈRE

`dsoxlab new lab` produit une suite qui lève volontairement :

    def test_a_ecrire() -> None:
        raise AssertionError("Les tests de ce lab restent à écrire. ...")

C'est la présence de `def test_a_ecrire` dans
`challenge/tests/test_functional.py` qui fait d'un lab un squelette, et c'est
le bon marqueur plutôt que le contenu du README : il porte sur ce qui
s'exécute, donc il ne peut pas être « corrigé » sans écrire le lab. Mesuré le
2026-10-30 : 42 squelettes sur 71 labs, et les 42 lèvent bien, aucun ne se
contente de skipper.

**Ce module ne juge que les 29 labs ÉCRITS.** Un squelette porte « À remplir »
et « TO FILL IN » dans tous ses textes, c'est son état normal, et crier dessus
bloquerait chaque commit du catalogue en cours d'écriture.

LA LANGUE OFFICIELLE EST L'ANGLAIS

Le fichier **sans suffixe** porte l'anglais, le `.fr.` la traduction. Un lab
écrit doit avoir les deux : livrer le français seul laisse la version
officielle annoncer que le lab n'existe pas.

CE QUE LA LISTE `DETTE` EST, ET POURQUOI ELLE N'EST CONTRÔLÉE QUE DANS UN SENS

Elle porte les labs dont les tests sont écrits mais dont la rédaction reste à
faire : un lab en cours d'écriture, à l'instant précis où sa suite existe et
pas encore ses textes.

Le catalogue DevSecOps jumeau contrôle sa liste équivalente dans les DEUX sens,
et refuse qu'un lab y reste une fois rédigé : sans cela, une liste d'exemptions
ne se vide jamais. **Ce catalogue ne le fait pas, et c'est mesuré.** Il compte
42 squelettes en cours d'écriture, et un lab franchit l'état « tests écrits,
textes au gabarit » pendant le temps qu'il faut pour rédiger six Markdown et
deux `lab.yaml`. Le 2026-10-30, deux labs l'ont franchi en vingt minutes. Une
liste qui doit égaler la réalité au lab près devient alors rouge **au moment où
l'on réussit**, plusieurs fois par jour, et un garde-fou qui rougit sur un
succès apprend une seule chose : à être édité sans être lu.

Le sens qui reste est celui qui attrape le défaut : un lab dont les tests sont
écrits et qui annonce « À remplir » sans que personne ne l'ait reconnu. Une
entrée périmée ne coûte qu'une exemption pour un lab déjà rédigé, et le
contrôle ci-dessous refuse au moins qu'elle désigne un lab inexistant.

Le jour où le catalogue sera écrit, la seconde moitié vaudra d'être remise :
elle est utile dans un dépôt stable, et nuisible dans un dépôt en écriture.

    uv run pytest tests/test_langue_officielle.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
LABS = RACINE / "labs"

#: Ce que `dsoxlab new lab` laisse dans la suite d'un lab non écrit.
MARQUEUR_SQUELETTE = "def test_a_ecrire"

#: Les tournures que le générateur laisse dans les textes, dans les deux
#: langues. Un fichier qui en porte une n'a pas été relu par un humain.
#: Mesuré le 2026-10-30 : 417 occurrences de « À remplir » et 166 de
#: « TO FILL IN », toutes dans des squelettes.
MARQUEURS_DE_GABARIT = (
    "À remplir",
    "A remplir",
    "TO FILL IN",
    "is not written yet",
    "n'est pas encore écrit",
    "(skeleton)",
    "(squelette)",
)

#: Ce qu'un lab écrit doit porter, dans les deux langues. Un squelette n'a pas
#: de `challenge/README*` du tout : c'est pourquoi un fichier absent compte ici
#: comme une rédaction non faite, et non comme une erreur de structure, dont
#: `dsoxlab validate-structure` s'occupe.
FICHIERS_DE_LECTURE = (
    "README.md",
    "README.fr.md",
    "scenario.md",
    "scenario.fr.md",
    "challenge/README.md",
    "challenge/README.fr.md",
    "lab.yaml",
    "lab.fr.yaml",
)

#: Labs dont les tests sont écrits mais dont la rédaction reste à faire.
#:
#: Mesuré le 2026-10-30, en cours de rédaction au moment où ce module est
#: écrit : `images-non-root` a sa suite fonctionnelle, et ses six Markdown plus
#: ses deux `lab.yaml` annoncent encore « À remplir ». Son titre est celui que
#: `dsoxlab list-labs` affiche, donc la seule chose qu'un apprenant voit avant
#: d'ouvrir le lab.
#:
#: Une entrée se retire quand la rédaction est faite. Rien ici ne l'y force,
#: pour la raison expliquée en tête de module.
DETTE: set[str] = {"images-non-root"}


def tous_les_labs() -> list[str]:
    return sorted(str(c.parent.relative_to(LABS)) for c in LABS.rglob("lab.yaml"))


def est_un_squelette(rel: str) -> bool:
    """Un lab dont la suite lève volontairement, telle que le générateur l'a posée."""
    suite = LABS / rel / "challenge" / "tests" / "test_functional.py"
    if not suite.is_file():
        return True
    return MARQUEUR_SQUELETTE in suite.read_text(encoding="utf-8")


def fichiers_au_gabarit(rel: str) -> list[str]:
    """Les fichiers de lecture absents, ou qui portent encore une tournure du générateur."""
    restes = []
    for nom in FICHIERS_DE_LECTURE:
        chemin = LABS / rel / nom
        if not chemin.is_file():
            restes.append(f"{nom} (absent)")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if any(marqueur in texte for marqueur in MARQUEURS_DE_GABARIT):
            restes.append(nom)
    return restes


LABS_ECRITS = [rel for rel in tous_les_labs() if not est_un_squelette(rel)]


def test_le_catalogue_porte_des_labs_ecrits() -> None:
    """Garde-fou : un marqueur de squelette qui dériverait classerait tout en squelette.

    La suite serait alors verte sans juger un seul lab, et c'est la forme la
    plus discrète de faux vert.
    """
    assert LABS_ECRITS, (
        "Aucun lab écrit trouvé : soit le catalogue est vide, soit "
        f"`{MARQUEUR_SQUELETTE}` n'est plus le marqueur que pose "
        "`dsoxlab new lab`, et ce module ne juge plus rien."
    )


@pytest.mark.parametrize("rel", LABS_ECRITS)
def test_un_lab_ecrit_ne_se_declare_pas_non_ecrit(rel: str) -> None:
    """Les deux descriptions d'un lab doivent dire la même chose.

    Celle qui s'exécute, c'est `test_functional.py`. Celle qui se lit, c'est le
    README. Quand la première prouve huit choses et que la seconde annonce
    « À remplir », c'est la seconde que l'apprenant croit.
    """
    restes = fichiers_au_gabarit(rel)

    assert not restes or rel in DETTE, (
        f"{rel} a des tests fonctionnels écrits, mais ces fichiers portent "
        f"encore le gabarit du générateur ou manquent : {restes}.\n\n"
        "Un apprenant qui ouvre ce lab lit qu'il n'existe pas. Soit la "
        "rédaction est à faire, et le lab s'inscrit dans DETTE (dans ce "
        "fichier) ; soit elle est faite, et les tournures du générateur "
        "doivent disparaître.\n\n"
        "Rappel : le fichier SANS suffixe porte l'anglais, langue officielle du "
        "dépôt ; le `.fr.` porte la traduction."
    )


def test_la_dette_ne_designe_que_des_labs_existants() -> None:
    """Un lab renommé ou supprimé ne doit pas laisser une entrée fantôme."""
    fantomes = DETTE - set(tous_les_labs())

    assert not fantomes, (
        f"DETTE désigne des labs qui n'existent pas : {sorted(fantomes)}."
    )


def test_la_dette_reelle_ne_depasse_pas_ce_qui_est_reconnu() -> None:
    """Rend visible un chiffre qui, sinon, ne se lit nulle part.

    C'est la forme que prend ici le « compte attendu » du catalogue DevSecOps :
    une INÉGALITÉ et non une égalité. Elle refuse qu'un lab non rédigé
    apparaisse sans être reconnu, et reste verte quand un lab de la liste est
    terminé. Une égalité rougirait sur ce succès, et la raison est en tête de
    module.
    """
    reste = {rel: fichiers_au_gabarit(rel) for rel in LABS_ECRITS}
    reste = {rel: fichiers for rel, fichiers in reste.items() if fichiers}
    non_reconnus = sorted(set(reste) - DETTE)

    assert not non_reconnus, (
        f"Labs écrits dont la rédaction reste à faire : {sorted(reste)}.\n"
        f"DETTE en déclare : {sorted(DETTE)}.\n\n"
        f"Non reconnus : {non_reconnus}"
    )
