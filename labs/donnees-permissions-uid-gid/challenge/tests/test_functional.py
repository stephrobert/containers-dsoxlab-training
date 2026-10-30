"""Tests fonctionnels du lab donnees-permissions-uid-gid : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un volume monté appartient à root, qu'un conteneur
non-root n'y écrit donc pas, et que la réponse n'est NI de passer le conteneur
en root, NI d'ouvrir le volume à tout le monde. C'est le groupe qu'on aligne.

POURQUOI LE GROUPE ET PAS LE PROPRIÉTAIRE. Deux conteneurs doivent écrire dans
le même volume, sous deux UID différents. Aucun propriétaire ne peut convenir
aux deux ; un groupe partagé, oui. C'est la situation réelle dès qu'une
application et son outil de sauvegarde partagent des données, et c'est pour
cela que le lab porte DEUX conteneurs.

MESURÉ SUR docker.lab LE 2026-10-30, et ces chiffres sont le lab :

| État | propriétaire du volume | uid 1000 écrit | uid 1001 écrit |
| volume frais | `0:0`, mode `755` | non | non |
| après `chown root:2000` + `chmod 2775` | `0:2000`, mode `2775` | oui | oui |

Et le détail qui fait la différence entre une solution qui tient et une qui
marche une fois : avec le bit setgid, les fichiers créés portent le groupe
`2000`. Sans lui, chacun porterait le groupe primaire de son auteur, et le
voisin ne pourrait pas les modifier.

LE QUATRIÈME CONTRÔLE ÉCARTE LA FAUSSE SOLUTION. `chmod 777` ferait passer les
trois premiers : les deux conteneurs écriraient, et les fichiers seraient bien
à eux. Il refuse donc explicitement un volume ouvert en écriture aux autres,
parce que c'est la réponse qu'on trouve partout et qu'elle donne à n'importe
quel processus du conteneur le droit de tout réécrire.

LES CONTRÔLES ÉCRIVENT POUR MESURER, et ils nettoient derrière eux. Lire les
permissions ne suffit pas : c'est la capacité d'écrire qui est le sujet, et une
permission se déclare sans toujours produire l'effet attendu.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true`,
ce qui donne accès au moteur. Mais les écritures d'épreuve passent par
`docker exec` SANS `--user`, donc sous l'utilisateur que le conteneur déclare :
c'est bien lui qu'on mesure, et non root.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

PRODUCTEUR = "rapport"
RELECTEUR = "verificateur"
CHEMIN = "/rapports"
GID_EQUIPE = 2000
UID_RELECTEUR = 1001

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui
    les lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier.
    """
    return lab_host(TARGET_HOST)


def _tourne(host, nom: str) -> None:
    """Le préalable de chaque contrôle.

    Ce lab fait RECRÉER les conteneurs, puisque l'utilisateur d'un conteneur se
    fixe à sa création : un nom manquant veut presque toujours dire qu'un
    conteneur a été détruit et pas relancé.
    """
    res = host.run(
        "docker container inspect %s --format %s", nom, "{{.State.Status}}"
    )
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{nom}` does not exist. This lab requires recreating "
               "the containers, because a container's user is fixed at "
               "creation: it has to be relaunched under the SAME name.",
            fr=f"le conteneur `{nom}` n'existe pas. Ce lab demande de recréer "
               "les conteneurs, puisque l'utilisateur d'un conteneur se fixe à "
               "sa création : il faut le relancer sous le MÊME nom.",
        ))
    etat = res.stdout.strip()
    if etat != "running":
        pytest.fail(message(
            en=f"container `{nom}` is in state `{etat}`, not `running`. Its "
               "rights cannot be tested while it is not running.",
            fr=f"le conteneur `{nom}` est dans l'état `{etat}`, pas `running`. "
               "Ses droits ne peuvent pas être éprouvés tant qu'il ne tourne "
               "pas.",
        ))


def _identite(host, nom: str) -> tuple[int, int]:
    """L'UID et le GID effectifs d'un conteneur, vus de l'intérieur.

    De l'intérieur, et non `.Config.User` : un `--user` peut désigner un compte
    que l'image ne connaît pas, et c'est l'identité réelle des processus qui
    décide des droits, pas ce qui a été demandé.
    """
    uid = host.run("docker exec %s id -u", nom)
    gid = host.run("docker exec %s id -g", nom)
    try:
        return int(uid.stdout.strip()), int(gid.stdout.strip())
    except ValueError:
        return -1, -1


def _ecrit(host, nom: str, fichier: str) -> tuple[bool, str]:
    """Le conteneur peut-il écrire ce fichier, et à qui appartient-il ?

    L'écriture est faite par le conteneur lui-même, sans `--user` : c'est son
    identité déclarée qui agit. Le fichier est retiré ensuite, pour qu'un
    contrôle ne laisse pas de trace dans le volume d'un rejeu.
    """
    chemin = f"{CHEMIN}/{fichier}"
    essai = host.run("docker exec %s sh -c %s", nom, f"echo epreuve > {chemin}")
    if essai.rc != 0:
        return False, ""
    proprietaire = host.run("docker exec %s stat -c %s %s", nom, "%u:%g", chemin)
    host.run("docker exec %s rm -f %s", nom, chemin)
    return True, proprietaire.stdout.strip()


def test_le_producteur_ne_tourne_plus_en_root(host) -> None:
    """La première mauvaise réponse, et la plus répandue.

    Passer un conteneur en root parce qu'« il n'écrivait pas » règle le
    symptôme et ouvre tout le reste : ses processus peuvent alors écrire partout
    où le conteneur a accès, y compris sur l'hôte à travers un bind mount.

    L'identité est lue DANS le conteneur, et non dans ce qui a été demandé à la
    création : c'est elle qui décide des droits.
    """
    _tourne(host, PRODUCTEUR)
    uid, gid = _identite(host, PRODUCTEUR)
    assert uid > 0, message(
        en=f"`{PRODUCTEUR}` runs as uid {uid}, that is root.\n"
           "Switching a container to root because it could not write fixes the "
           "symptom and opens everything else: its processes can then write "
           "anywhere the container reaches.",
        fr=f"`{PRODUCTEUR}` tourne sous l'uid {uid}, c'est-à-dire root.\n"
           "Passer un conteneur en root parce qu'il n'écrivait pas règle le "
           "symptôme et ouvre tout le reste : ses processus peuvent alors "
           "écrire partout où le conteneur a accès.",
    )
    assert gid == GID_EQUIPE, message(
        en=f"`{PRODUCTEUR}` runs as gid {gid}, not {GID_EQUIPE}.\n"
           "The shared group is what lets two different uids write into the "
           "same volume: a container outside that group is alone.",
        fr=f"`{PRODUCTEUR}` tourne sous le gid {gid}, pas {GID_EQUIPE}.\n"
           "Le groupe partagé est ce qui permet à deux uid différents d'écrire "
           "dans le même volume : un conteneur hors de ce groupe est seul.",
    )


def test_ce_que_le_producteur_ecrit_lui_appartient(host) -> None:
    """Il écrit, et ses fichiers sont à lui et au groupe.

    Deux faits en un contrôle, parce qu'ils ne se séparent pas : pouvoir écrire
    sans que le fichier porte le bon groupe donnerait un volume où chacun
    produit des fichiers que les autres ne peuvent pas reprendre, ce qui est la
    panne suivante.

    C'est aussi ce qui distingue une solution qui tient d'une qui marche une
    fois : le groupe se propage aux fichiers créés quand le répertoire porte le
    bit setgid.
    """
    _tourne(host, PRODUCTEUR)
    uid, _ = _identite(host, PRODUCTEUR)
    peut, proprietaire = _ecrit(host, PRODUCTEUR, ".epreuve-producteur")
    assert peut, message(
        en=f"`{PRODUCTEUR}` cannot write into {CHEMIN}.\n"
           "A freshly created volume belongs to root and is not writable by a "
           "group: that is the starting point, and root is not the answer.",
        fr=f"`{PRODUCTEUR}` n'écrit pas dans {CHEMIN}.\n"
           "Un volume fraîchement créé appartient à root et n'est pas "
           "accessible en écriture à un groupe : c'est le point de départ, et "
           "root n'est pas la réponse.",
    )
    assert proprietaire == f"{uid}:{GID_EQUIPE}", message(
        en=f"the file written by `{PRODUCTEUR}` belongs to `{proprietaire}`, "
           f"expected `{uid}:{GID_EQUIPE}`.\n"
           "A file whose group is not the shared one cannot be taken over by "
           "the other container: the group has to propagate to created files, "
           "which the directory decides.",
        fr=f"le fichier écrit par `{PRODUCTEUR}` appartient à "
           f"`{proprietaire}`, attendu `{uid}:{GID_EQUIPE}`.\n"
           "Un fichier dont le groupe n'est pas le groupe partagé ne peut pas "
           "être repris par l'autre conteneur : le groupe doit se propager aux "
           "fichiers créés, et c'est le répertoire qui en décide.",
    )


def test_le_repertoire_appartient_au_groupe_partage(host) -> None:
    """La correction elle-même, lue sur le répertoire du volume.

    Le propriétaire peut rester root : ce n'est pas lui qui donne le droit
    d'écrire ici. C'est le groupe, et c'est ce qui permet à deux UID différents
    de travailler côte à côte sans qu'aucun ne soit propriétaire.
    """
    _tourne(host, PRODUCTEUR)
    res = host.run(
        "docker exec %s stat -c %s %s", PRODUCTEUR, "%g %A", CHEMIN
    )
    assert res.rc == 0, message(
        en=f"cannot read {CHEMIN}'s rights: {res.stderr.strip()}",
        fr=f"impossible de lire les droits de {CHEMIN} : {res.stderr.strip()}",
    )
    morceaux = res.stdout.split()
    gid = morceaux[0] if morceaux else ""
    droits = morceaux[1] if len(morceaux) > 1 else ""
    assert gid == str(GID_EQUIPE), message(
        en=f"{CHEMIN} belongs to group {gid}, not {GID_EQUIPE}.\n"
           "The owner may well stay root: it is not the owner that grants the "
           "right to write here, it is the group.",
        fr=f"{CHEMIN} appartient au groupe {gid}, pas {GID_EQUIPE}.\n"
           "Le propriétaire peut très bien rester root : ce n'est pas lui qui "
           "donne le droit d'écrire ici, c'est le groupe.",
    )
    # `%A` rend les droits en lettres, par exemple `drwxrwsr-x`. La lettre
    # d'écriture du groupe est à l'index 5, et un `s` à l'index 6 marquerait le
    # setgid, qui propage le groupe aux fichiers créés.
    ecriture_groupe = len(droits) > 5 and droits[5] == "w"
    assert ecriture_groupe, message(
        en=f"{CHEMIN} does not grant write access to its group ({droits}).\n"
           "Belonging to the group is not enough: the group must be able to "
           "write.",
        fr=f"{CHEMIN} ne donne pas l'écriture à son groupe ({droits}).\n"
           "Appartenir au groupe ne suffit pas : il faut que le groupe puisse "
           "écrire.",
    )


def test_l_autre_uid_ecrit_sans_que_tout_soit_ouvert(host) -> None:
    """Le contrôle qui écarte la fausse solution, et il faut les deux moitiés.

    Un `chmod 777` ferait passer les trois contrôles précédents : les deux
    conteneurs écriraient, et leurs fichiers seraient bien à eux. C'est la
    réponse qu'on trouve partout, et elle donne à n'importe quel processus du
    conteneur le droit de tout réécrire.

    Les deux moitiés sont donc indissociables : l'autre UID doit écrire, ET le
    répertoire ne doit pas être ouvert en écriture aux autres.
    """
    _tourne(host, RELECTEUR)
    uid, gid = _identite(host, RELECTEUR)
    assert uid == UID_RELECTEUR, message(
        en=f"`{RELECTEUR}` runs as uid {uid}, not {UID_RELECTEUR}.\n"
           "It is the witness of the shared group: giving it the same uid as "
           f"`{PRODUCTEUR}` would prove nothing, since the whole point is that "
           "two different uids work side by side.",
        fr=f"`{RELECTEUR}` tourne sous l'uid {uid}, pas {UID_RELECTEUR}.\n"
           "C'est le témoin du groupe partagé : lui donner le même uid que "
           f"`{PRODUCTEUR}` ne prouverait rien, puisque tout l'intérêt est que "
           "deux uid différents travaillent côte à côte.",
    )
    assert gid == GID_EQUIPE, message(
        en=f"`{RELECTEUR}` runs as gid {gid}, not {GID_EQUIPE}.",
        fr=f"`{RELECTEUR}` tourne sous le gid {gid}, pas {GID_EQUIPE}.",
    )

    peut, proprietaire = _ecrit(host, RELECTEUR, ".epreuve-relecteur")
    assert peut, message(
        en=f"`{RELECTEUR}` cannot write into {CHEMIN}, although its uid differs "
           f"from `{PRODUCTEUR}`'s and it shares its group.\n"
           "That is exactly the symptom the scenario reports: a second "
           "container, well behaved and non-root, which writes nothing.",
        fr=f"`{RELECTEUR}` n'écrit pas dans {CHEMIN}, alors que son uid diffère "
           f"de celui de `{PRODUCTEUR}` et qu'il partage son groupe.\n"
           "C'est exactement le symptôme que raconte le scénario : un second "
           "conteneur, bien élevé et non-root, qui n'écrit rien.",
    )
    assert proprietaire.endswith(f":{GID_EQUIPE}"), message(
        en=f"the file written by `{RELECTEUR}` belongs to `{proprietaire}`, "
           f"whose group is not {GID_EQUIPE}.",
        fr=f"le fichier écrit par `{RELECTEUR}` appartient à `{proprietaire}`, "
           f"dont le groupe n'est pas {GID_EQUIPE}.",
    )

    res = host.run("docker exec %s stat -c %s %s", RELECTEUR, "%A", CHEMIN)
    droits = res.stdout.strip()
    # L'écriture des autres est la huitième lettre de `drwxrwsr-x`.
    ouvert_a_tous = len(droits) > 8 and droits[8] == "w"
    assert not ouvert_a_tous, message(
        en=f"{CHEMIN} is open for writing to everyone ({droits}).\n"
           "That is the answer found everywhere, and it works: it also gives "
           "any process of the container the right to rewrite everything. The "
           "shared group is enough, and it names who may write.",
        fr=f"{CHEMIN} est ouvert en écriture à tout le monde ({droits}).\n"
           "C'est la réponse qu'on trouve partout, et elle marche : elle donne "
           "aussi à n'importe quel processus du conteneur le droit de tout "
           "réécrire. Le groupe partagé suffit, et il nomme qui peut écrire.",
    )
