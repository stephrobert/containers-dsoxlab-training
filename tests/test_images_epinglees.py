"""Méta-test du dépôt : ce que les setups TIRENT est épinglé par digest.

`LABS-A-ECRIRE.md` l'exige : « Toute image porte la forme `image:tag@sha256:…`.
Jamais `:latest`, jamais un tag seul. » Rien ne le contrôlait, et la mesure du
2026-10-29 a montré où cela mène : sur le seul lab écrit, sept références nues,
et `gitlab-ci` à 22 % d'épinglage. Une règle écrite que rien ne vérifie finit
toujours par décrire une intention et non le dépôt.

CE QUI EST DANS LE PÉRIMÈTRE, ET POURQUOI PAS LE RESTE
------------------------------------------------------

On contrôle `setup.yaml` et `cleanup.yaml` : ce que **le dépôt exécute
lui-même** pour poser l'état de départ. Une image non épinglée y rend le lab
non reproductible, ce qui est le défaut que la règle vise.

On ne contrôle PAS les `fixtures/`, et ce n'est pas un oubli : la frontière est
déjà tracée par `scripts/hooks/hadolint-cible.sh`, qui l'explique mieux que ce
fichier ne le ferait. Un `fixtures/` peut livrer un Dockerfile volontairement
fautif, et ce hook nomme « image de base en tag flottant » parmi les sujets
d'exercice légitimes. Le refuser ici retirerait du lab ce qui fait le lab.

On ne contrôle pas non plus les énoncés (`scenario.md`, `challenge/README.md`) :
un énoncé CITE une commande que l'apprenant tapera, il ne l'exécute pas.

LE MARQUEUR, ET POURQUOI SA PORTÉE EST LA TÂCHE
-----------------------------------------------

Un lab peut avoir besoin d'une référence nue dans son propre setup. Le cas
existe déjà et il est instructif : `images-identifier-image` demande à
l'apprenant le digest de `debian:13` « telle qu'elle est sur cette machine ».
Épingler ce `docker pull` écrirait la réponse attendue dans le setup, et le lab
ne mesurerait plus rien.

Le marqueur s'écrit dans la **tâche** qui porte la référence, jamais en tête de
fichier : une exemption posée en haut couvrirait les références ajoutées plus
tard sans que personne ne le décide, et c'est exactement ainsi qu'une exception
devient la règle. La portée est donc le bloc délimité par la ligne vide
précédente, ce qui est la façon dont un playbook sépare ses tâches.

Une portée en nombre de lignes fixe a été essayée d'abord, et elle ne tient
pas : dans un bloc `content: |`, le `FROM` est à cinq lignes du commentaire de
sa tâche, et un marqueur posé plus près serait **écrit dans le Dockerfile** que
le setup génère, donc livré à l'apprenant.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
LABS = REPO / "labs"

#: Ce que le dépôt exécute lui-même, par opposition à ce qu'il donne à lire.
JOUES_PAR_LE_DEPOT = ("setup.yaml", "cleanup.yaml")

#: Le marqueur d'une référence nue délibérée. Il porte une raison après les
#: deux-points : un marqueur sans motif est un contournement, pas une décision.
MARQUEUR = "dsoxlab:tag-nu-volontaire"

#: Au-delà, on arrête de remonter. Un setup écrit sans aucune ligne vide ferait
#: sinon porter une exemption sur tout le fichier, ce qui est précisément ce
#: qu'on refuse. Douze lignes couvrent une tâche Ansible commentée, pas deux.
PORTEE_MAXIMALE = 12

#: Les trois formes par lesquelles une image est TIRÉE D'UN REGISTRE, et dans
#: lesquelles sa position ne dépend d'aucune option : le seul argument de
#: `docker pull`, celui de `FROM`, celui de `image:`.
#:
#: `docker run`, `docker build -t` et `docker tag` en sont absents, et ce n'est
#: pas un renoncement, c'est le périmètre juste. Deux raisons, la seconde étant
#: la vraie :
#:
#: 1. la position de l'image y dépend des options, et aucun motif ne distingue
#:    `--name vitrine` suivi d'une image de `-d` suivi du nom `vitrine`. Mesuré
#:    en écrivant `docker-premier-conteneur` : le détecteur refusait le setup en
#:    prenant un nom de CONTENEUR pour une image ;
#: 2. ce qu'on y trouve est le plus souvent un tag LOCAL, créé sur la machine à
#:    partir d'un digest déjà tiré. Un tel tag n'a pas de digest propre, et
#:    exiger qu'il soit épinglé n'aurait aucun sens. La règle porte sur ce qui
#:    ENTRE depuis un registre, parce que c'est là que le flottement se produit.
RE_CONSOMMATION = re.compile(
    r"""(?:
          docker\s+pull\s+
        | ^\s*FROM\s+
        | ^\s*image:\s+
        )
        (?P<ref>[a-z0-9][a-z0-9._/-]*(?::[\w.-]+)?(?:@sha256:[0-9a-f]{64})?)
    """,
    re.IGNORECASE | re.VERBOSE | re.MULTILINE,
)

#: Une référence sans tag ni digest : `debian`, `alpine`. Elle vaut `:latest`
#: en pratique, donc elle est refusée comme un tag nu, et le message le dit.
RE_SANS_TAG = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")


#: Les deux formes par lesquelles un setup FABRIQUE un tag sur la machine :
#: `docker build -t <tag>` et `docker tag <reference> <tag>`. Un tag fabriqué
#: ici n'a pas de digest propre, et un `FROM` qui le désigne ne tire rien d'un
#: registre.
#:
#: C'est le même raisonnement que celui qui exclut `build` et `tag` du périmètre
#: de consommation, poussé d'un cran : il ne suffisait pas de ne pas accuser la
#: ligne qui fabrique, il faut aussi ne pas accuser celle qui s'en sert. Mesuré
#: le 2026-10-30 : six setups construisaient un socle d'atelier puis déposaient
#: un Dockerfile qui en partait, et le détecteur réclamait un digest pour une
#: image qui n'existait pas encore.
#: La référence SOURCE d'un `docker tag` peut être une expression Jinja, qui
#: porte des espaces : `docker tag {{ image_epinglee }} {{ socle }}`. Un `\S+`
#: ne la couvre pas, et trois setups du dépôt l'écrivent ainsi. Mesuré le
#: 2026-10-30, leur fabrication passait inaperçue et le `FROM` correspondant
#: était refusé.
RE_FABRICATION = re.compile(
    r"""(?:
          docker\s+build\s+(?:[^\n]*?\s)?-t\s+
        | docker\s+tag\s+(?:\{\{[^}]*\}\}|\S+)\s+
        )
        (?P<tag>
            \{\{\s*[\w.]+\s*\}\}
          | [a-z0-9][a-z0-9._/-]*(?::[\w.-]+)?
        )
    """,
    re.IGNORECASE | re.VERBOSE,
)

#: Une expression Jinja réduite à un nom de variable, telle qu'elle apparaît en
#: cible d'un `docker tag` ou d'un `-t`. Le point couvre `item.nom`, la forme
#: qu'une boucle donne à ses valeurs.
RE_JINJA = re.compile(r"^\{\{\s*([\w.]+)\s*\}\}$")


def _tags_fabriques(source: str) -> set[str]:
    """Les tags que CE fichier construit ou étiquette lui-même.

    UNE CIBLE PEUT ÊTRE UNE VARIABLE, et elle l'est presque toujours : un setup
    écrit `-t {{ socle }}` et déclare `socle: lab-x:1.0` plus haut, ou pose ses
    tags dans une boucle dont les valeurs portent une clé `nom`. On résout donc
    la cible par les littéraux du fichier.

    LA RÉSOLUTION EST VOLONTAIREMENT ÉTROITE : seules les valeurs qui ont la
    forme d'un tag (`nom:version`, sans digest) sont retenues. Une variable qui
    porterait un digest est déjà épinglée et ne concerne pas ce contrôle ; une
    variable qui porterait autre chose n'est pas un tag.
    """
    # UNE CLÉ PEUT PORTER PLUSIEURS VALEURS, et c'est le cas dès qu'une boucle
    # nomme plusieurs socles : la clé `nom` apparaît une fois par élément. Un
    # dictionnaire ne garderait que la dernière, et le détecteur accuserait
    # l'autre socle du même fichier. Mesuré le 2026-10-30 sur le setup qui
    # nomme un socle lourd et un socle léger dans la même boucle.
    variables: dict[str, list[str]] = {}
    for cle, valeur in RE_VARIABLE.findall(source):
        variables.setdefault(cle, []).append(valeur)

    tags = set()
    for brut in RE_FABRICATION.findall(source):
        jinja = RE_JINJA.match(brut)
        if not jinja:
            tags.add(brut)
            continue
        nom = jinja.group(1)
        # `item.nom` dans une boucle : la clé seule suffit à retrouver les
        # valeurs déclarées dans la liste.
        court = nom.rsplit(".", 1)[-1]
        for cle, valeurs in variables.items():
            if cle in (nom, court):
                tags.update(valeurs)
    return tags


#: Une variable Ansible dont la valeur est un tag littéral, sur une seule ligne.
#: Les valeurs repliées (`>-`) portent des digests et sont déjà épinglées, donc
#: elles ne concernent pas ce contrôle.
#: Les deux formes sous lesquelles un tag littéral est déclaré : en bloc
#: (`socle: lab-x:1.0`) et EN LIGNE dans une liste de boucle
#: (`- { digest: ..., nom: "lab-x:1.0" }`). La seconde manquait au premier jet,
#: et le setup qui pose ses deux socles par une boucle restait refusé.
#:
#: Les valeurs repliées (`>-`) portent des digests et sont déjà épinglées, donc
#: elles ne concernent pas ce contrôle.
RE_VARIABLE = re.compile(
    r"""([a-z_][a-z0-9_]*)\s*:\s*
        ["']?(?P<tag>[a-z0-9][a-z0-9._/-]*:[\w.-]+)["']?
        (?=\s*[,}\n])
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _fichiers_joues() -> list[Path]:
    return sorted(
        chemin
        for nom in JOUES_PAR_LE_DEPOT
        for chemin in LABS.glob(f"*/{nom}")
    )


def _lab_de(chemin: Path) -> str:
    return chemin.parent.name


def _sans_commentaires(source: str) -> str:
    """La source dont les commentaires sont blanchis, positions préservées.

    Un commentaire n'exécute rien, et il cite volontiers une commande pour
    l'expliquer. Mesuré en écrivant `docker-verifier-son-moteur` : le détecteur
    refusait le setup à cause de la phrase « `docker run hello-world` ne
    trouverait rien », qui est justement l'explication de la tâche voisine.

    On remplace par des espaces au lieu de supprimer, pour que les numéros de
    ligne et de colonne restent ceux du fichier : un message qui envoie à la
    mauvaise ligne fait chercher au mauvais endroit.

    Limite assumée : un `#` à l'intérieur d'une chaîne fait blanchir la fin de
    la ligne. Cela peut masquer une référence écrite après lui, jamais en
    inventer une, et aucune des deux formes n'existe dans le dépôt.
    """
    propres = []
    for ligne in source.splitlines():
        i = ligne.find("#")
        propres.append(ligne if i < 0 else ligne[:i] + " " * (len(ligne) - i))
    return "\n".join(propres)


def _bloc_de_la_tache(lignes: list[str], no: int) -> str:
    """Le texte de la tâche qui porte la ligne `no`, commentaire compris.

    On remonte jusqu'à la ligne vide précédente, parce que c'est ainsi qu'un
    playbook sépare ses tâches et que le commentaire d'une tâche vit AU-DESSUS
    de son `- name:`. Une portée en nombre de lignes fixe ne marcherait pas :
    dans un bloc `content: |`, la référence est à cinq lignes de son
    commentaire, et le marqueur ne peut pas être posé plus près sans être écrit
    dans le fichier que le setup génère.
    """
    debut = max(0, no - 1 - PORTEE_MAXIMALE)
    for i in range(no - 2, debut - 1, -1):
        if not lignes[i].strip():
            debut = i + 1
            break
    return "\n".join(lignes[debut:no])


def _references_nues(source: str) -> list[tuple[int, str]]:
    """Les références consommées sans digest, hors celles marquées.

    Rend `(ligne, reference)`, pour que l'échec envoie à l'endroit exact.

    Noter l'asymétrie, qui est voulue : on CHERCHE les références dans la
    source blanchie de ses commentaires, mais on cherche le MARQUEUR dans la
    source d'origine. Le marqueur est précisément un commentaire : le blanchir
    aussi le rendrait introuvable, et aucune exemption ne fonctionnerait plus.
    """
    lignes = source.splitlines()
    fautives: list[tuple[int, str]] = []
    for trouve in RE_CONSOMMATION.finditer(_sans_commentaires(source)):
        ref = trouve.group("ref")
        if "@sha256:" in ref:
            continue
        no = source.count("\n", 0, trouve.start()) + 1
        if MARQUEUR in _bloc_de_la_tache(lignes, no):
            continue
        fautives.append((no, ref))
    fabriques = _tags_fabriques(source)
    return [(no, ref) for no, ref in fautives if ref not in fabriques]


def test_il_y_a_des_setups_a_mesurer() -> None:
    """Garde-fou : un glob cassé rendrait ce fichier vert sans rien mesurer."""
    fichiers = _fichiers_joues()
    assert fichiers, (
        "Aucun `labs/*/setup.yaml` ni `cleanup.yaml` : le glob ne regarde plus "
        "au bon endroit, ou le catalogue est vide."
    )


def test_le_detecteur_reconnait_ce_qu_il_doit_reconnaitre() -> None:
    """Le contrôle se contrôle lui-même, sinon il peut être vert par panne.

    Les quatre premiers cas DOIVENT être vus, les trois derniers ne doivent pas
    l'être. Sans cette seconde moitié, un détecteur qui refuse tout passerait
    pour rigoureux.
    """
    vus = _references_nues(
        "cmd: docker pull debian:13\n"
        "    FROM python:3.12-slim\n"
        "    image: nginx\n"
    )
    assert [r for _, r in vus] == ["debian:13", "python:3.12-slim", "nginx"], vus

    ignores = _references_nues(
        f"    # {MARQUEUR} : le lab demande ce digest, l'épingler écrirait la réponse\n"
        "    - name: Tirer l'image dont le lab demande le digest\n"
        "      ansible.builtin.copy:\n"
        '        dest: /opt/lab-images/Dockerfile.v1\n'
        '        mode: "0644"\n'
        "        content: |\n"
        "          FROM debian:13\n"
        "\n"
        "    - name: Une image epinglee\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker pull debian:13@sha256:"
        "0000000000000000000000000000000000000000000000000000000000000000\n"
        "\n"
        "    - name: Un tag PRODUIT par un build, pas consomme\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker build -q -t inventaire:1.0 /opt/lab-images\n"
    )
    assert ignores == [], (
        "le détecteur refuse un cas légitime : une tâche marquée, un digest, ou "
        f"le tag PRODUIT par un build.\n  vus : {ignores}"
    )

    # Un commentaire n'exécute rien, et il cite volontiers une commande pour
    # l'expliquer. Ce cas a été mesuré, pas imaginé : il refusait un setup réel.
    commentaires = _references_nues(
        "    # Le digest ne porte pas de nom : `docker run hello-world` ne\n"
        "    # trouverait rien, d'ou le tag pose juste apres.\n"
        "    - name: Une tache sans aucune reference nue\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker tag a@sha256:"
        "0000000000000000000000000000000000000000000000000000000000000000 b:1.0\n"
    )
    assert commentaires == [], (
        "le détecteur lit les commentaires, qui n'exécutent rien.\n"
        f"  vus : {commentaires}"
    )

    # Un nom de CONTENEUR n'est pas une image, et aucun motif ne les distingue
    # dans un `docker run` : ce cas a fait refuser un setup réel, d'où le
    # périmètre limité aux trois formes où la position de l'image est fixe.
    hors_perimetre = _references_nues(
        "    - name: Lancer le conteneur de la mise en situation\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker run -d --name vitrine lab-base:1.0 sh -c 'sleep infinity'\n"
        "\n"
        "    - name: Creer un conteneur arrete\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker create --name rebut lab-base:1.0\n"
        "\n"
        "    - name: Nommer une image deja tiree par son digest\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker tag a@sha256:"
        "0000000000000000000000000000000000000000000000000000000000000000 lab-base:1.0\n"
    )
    assert hors_perimetre == [], (
        "le détecteur sort de son périmètre : `docker run`, `create` et `tag` "
        "portent des noms de conteneur et des tags locaux, pas des références "
        f"tirées d'un registre.\n  vus : {hors_perimetre}"
    )

    # Et le marqueur ne doit PAS franchir la ligne vide : sans ce contrôle, une
    # exemption couvrirait la tâche suivante en silence.
    deborde = _references_nues(
        f"    # {MARQUEUR} : raison\n"
        "    - name: La tache marquee\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker pull debian:13\n"
        "\n"
        "    - name: La tache SUIVANTE, qui n'est pas marquee\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker pull alpine:3.20\n"
    )
    assert [r for _, r in deborde] == ["alpine:3.20"], (
        "le marqueur franchit la ligne vide et exempte la tâche suivante.\n"
        f"  vus : {deborde}"
    )


def test_un_socle_fabrique_sur_place_n_est_pas_accuse() -> None:
    """Les quatre formes sous lesquelles un setup fabrique son propre socle.

    MESURÉ LE 2026-10-30 : six setups construisent un socle local puis déposent
    un Dockerfile qui en part. Le détecteur réclamait un digest pour une image
    qui n'existe que sur la machine, et dont le digest n'existe pas avant la
    construction. C'est le même raisonnement qui exclut déjà `docker build -t`
    et `docker tag` du périmètre de consommation, poussé d'un cran : il ne
    suffit pas de ne pas accuser la ligne qui fabrique, il faut aussi ne pas
    accuser celle qui s'en sert.

    LES TROIS DERNIÈRES FORMES ONT CHACUNE COÛTÉ UN JET. La cible d'un
    `docker tag` est presque toujours une variable ; la référence source peut
    être une expression Jinja, que `\\S+` ne couvre pas ; et une boucle déclare
    plusieurs valeurs sous la MÊME clé, qu'un dictionnaire réduisait à la
    dernière, de sorte que le détecteur accusait le premier socle d'un lab dont
    le second passait.

    ET LE DERNIER CAS EST LE PLUS IMPORTANT : un `FROM` dont le tag n'est
    fabriqué nulle part doit toujours être refusé. Sans lui, cette correction
    aurait pu désarmer le contrôle entier sans que rien ne le dise.
    """
    sur_place = _references_nues(
        "    - name: Construire le socle\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker build -t lab-atelier:1.0 /opt/x/socle\n"
        "\n"
        "    - name: Deposer le Dockerfile\n"
        "      ansible.builtin.copy:\n"
        "        content: |\n"
        "          FROM lab-atelier:1.0\n"
    )
    assert sur_place == [], (
        "un socle construit par le setup lui-même est accusé.\n"
        f"  vus : {sur_place}"
    )

    par_variable = _references_nues(
        "  vars:\n"
        "    socle: lab-taille:1.0\n"
        "  tasks:\n"
        "    - name: Construire le socle\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker build -t {{ socle }} /opt/x/socle\n"
        "\n"
        "    - name: Deposer le Dockerfile\n"
        "      ansible.builtin.copy:\n"
        "        content: |\n"
        "          FROM lab-taille:1.0\n"
    )
    assert par_variable == [], (
        "un socle fabriqué via une variable est accusé.\n"
        f"  vus : {par_variable}"
    )

    par_boucle = _references_nues(
        "  tasks:\n"
        "    - name: Nommer les deux socles\n"
        "      ansible.builtin.command:\n"
        "        cmd: docker tag {{ item.digest }} {{ item.nom }}\n"
        "      loop:\n"
        '        - { digest: "{{ a }}", nom: "lab-socle-lourd:1.0" }\n'
        '        - { digest: "{{ b }}", nom: "lab-socle-leger:1.0" }\n'
        "\n"
        "    - name: Deposer le Dockerfile\n"
        "      ansible.builtin.copy:\n"
        "        content: |\n"
        "          FROM lab-socle-lourd:1.0\n"
    )
    assert par_boucle == [], (
        "le premier socle d'une boucle est accusé : une clé répétée ne doit "
        "pas être réduite à sa dernière valeur.\n"
        f"  vus : {par_boucle}"
    )

    jamais_fabrique = _references_nues(
        "    - name: Deposer le Dockerfile\n"
        "      ansible.builtin.copy:\n"
        "        content: |\n"
        "          FROM debian:13\n"
    )
    assert [r for _, r in jamais_fabrique] == ["debian:13"], (
        "un tag flottant venu d'un registre n'est plus refusé : la "
        "reconnaissance des socles locaux a désarmé le contrôle.\n"
        f"  vus : {jamais_fabrique}"
    )


@pytest.mark.parametrize("fichier", _fichiers_joues(), ids=_lab_de)
def test_les_images_tirees_par_le_setup_sont_epinglees(fichier: Path) -> None:
    fautives = _references_nues(fichier.read_text(encoding="utf-8"))
    sans_tag = [(no, ref) for no, ref in fautives if RE_SANS_TAG.match(ref)]
    assert not fautives, (
        f"{_lab_de(fichier)} : {len(fautives)} image(s) consommées sans digest "
        f"dans {fichier.name}.\n\n"
        + "\n".join(f"    {fichier.name}:{no}  {ref}" for no, ref in fautives)
        + "\n\nElles s'écrivent `image:tag@sha256:…` : un tag désigne, il ne "
        "garantit rien, et un lab qui part d'un tag flottant ne se rejoue pas "
        "à l'identique."
        + (
            "\n\nUne référence sans tag du tout vaut `:latest`, c'est-à-dire la "
            "plus mouvante : " + ", ".join(ref for _, ref in sans_tag)
            if sans_tag
            else ""
        )
        + f"\n\nSi la référence nue est le SUJET du lab, marque SA TÂCHE, avec la "
        f"raison. Le marqueur vaut jusqu'à la ligne vide qui précède, donc un "
        f"commentaire posé au-dessus du `- name:` suffit :\n"
        f"    # {MARQUEUR} : <pourquoi l'épingler casserait ce lab>\n"
    )
