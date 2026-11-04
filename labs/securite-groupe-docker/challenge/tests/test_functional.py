"""Un accès équivalent à root retiré, et réellement perdu.

Pourquoi deux contrôles là où il n'y en avait qu'un
--------------------------------------------------

Le fichier précédent portait **un** `def test_` et **deux** assertions : le
compte existe, et il n'est plus dans le groupe `docker`. C'était le lab le plus
maigre du catalogue, et son défaut n'était pas la maigreur.

IL NE MESURAIT QUE L'APPARTENANCE AU GROUPE, c'est-à-dire une **déclaration**.
Rien ne vérifiait que l'accès au démon soit réellement perdu. C'est le même
défaut que la rotation des journaux, qui lisait `HostConfig.LogConfig` sans
jamais regarder si la rotation avait lieu : une ligne de `/etc/group` dit ce
qu'on a écrit, pas ce que le compte peut encore faire.

Le pouvoir est pourtant éprouvable, et il discrimine. Mesuré sur `docker.lab` :

    dans le groupe docker     docker ps -> rc 0, il liste les conteneurs
    retiré du groupe          docker ps -> rc 1, « permission denied while
                              trying to connect to the docker API at
                              unix:///var/run/docker.sock »

Les deux contrôles mesurent donc deux choses indépendantes :

1. le compte **n'appartient plus** au groupe privilégié ;
2. il **ne peut plus** joindre le démon, éprouvé par un appel réel.

Le second n'est pas une redite du premier. L'appartenance au groupe est une des
voies d'accès au socket, pas la seule : des droits posés directement sur le
fichier, ou une appartenance par un groupe intermédiaire, laisseraient le premier
contrôle satisfait et le pouvoir intact.

DEUX GARDE-FOUS, ET CE SONT DES INTERDICTIONS DU SCÉNARIO, non des objectifs :
le compte doit **survivre** au retrait, et l'accès de l'opérateur ne doit pas être
touché. Supprimer le compte retire bien son accès, en supprimant ce que
l'exercice demandait de conserver ; vider le groupe `docker` de tous ses membres
casserait l'environnement de travail. Les deux sont vérifiés avant les mesures,
avec des messages qui nomment l'interdiction franchie.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

COMPTE = "dsoxlab-auditor"
GROUPE = "docker"
OPERATEUR = "ansible"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _garde_fous(host) -> None:
    """Le compte survit, et l'accès de l'opérateur n'a pas été touché.

    Ce ne sont pas des exigences à atteindre : les deux sont déjà vraies au
    départ. Ce sont les deux interdictions du scénario, et les franchir est une
    faute qui doit se dire.
    """
    compte = host.run("getent passwd %s", COMPTE)
    assert compte.rc == 0, message(
        en=(
            f"The {COMPTE} account no longer exists. Deleting it does remove its "
            "access, by removing what the exercise asked you to keep: the audit "
            "account stays, only its privilege goes."
        ),
        fr=(
            f"Le compte {COMPTE} n'existe plus. Le supprimer retire bien son "
            "accès, en supprimant ce que l'exercice demandait de conserver : le "
            "compte d'audit reste, seul son privilège part."
        ),
    )

    # L ACCES DE L OPERATEUR, qui est l'autre interdiction : « ne modifiez pas
    # vos propres accès ». Vider le groupe de tous ses membres retirerait bien
    # celui du compte d'audit, en cassant l'environnement de travail.
    operateur = host.run("id -Gn %s", OPERATEUR)
    assert operateur.rc == 0, message(
        en=f"Cannot read the groups of {OPERATEUR}. Not your fault: the check cannot measure anything, report it.",
        fr=f"Les groupes de {OPERATEUR} sont illisibles. Ce n'est pas votre faute : le contrôle ne peut rien mesurer, signalez-le.",
    )
    assert GROUPE in operateur.stdout.split(), message(
        en=(
            f"{OPERATEUR} is no longer in the {GROUPE} group. Emptying the group "
            "does remove the audit account's access, along with the access the "
            "work itself needs, and the scenario forbids touching your own."
        ),
        fr=(
            f"{OPERATEUR} n'est plus dans le groupe {GROUPE}. Vider le groupe "
            "retire bien l'accès du compte d'audit, et avec lui celui dont le "
            "travail a besoin ; le scénario interdit de toucher au vôtre."
        ),
    )


def test_le_compte_n_appartient_plus_au_groupe_privilegie(host):
    """Ce qui a été écrit dans la configuration des groupes."""
    _garde_fous(host)

    groupes = host.run("id -Gn %s", COMPTE)
    assert groupes.rc == 0, message(
        en=f"Cannot read the groups of {COMPTE}. Not your fault if the account exists, report it.",
        fr=f"Les groupes de {COMPTE} sont illisibles. Ce n'est pas votre faute si le compte existe, signalez-le.",
    )
    appartenances = groupes.stdout.split()
    assert GROUPE not in appartenances, message(
        en=(
            f"{COMPTE} still belongs to the {GROUPE} group.\n"
            f"  groups: {' '.join(appartenances)}\n"
            "Membership of that group is equivalent to root on this host, since "
            "it grants write access to the daemon socket."
        ),
        fr=(
            f"{COMPTE} appartient encore au groupe {GROUPE}.\n"
            f"  groupes : {' '.join(appartenances)}\n"
            "L'appartenance à ce groupe équivaut à root sur cet hôte, puisqu'elle "
            "donne l'écriture sur le socket du démon."
        ),
    )


def test_le_compte_ne_peut_plus_joindre_le_demon(host):
    """Ce que le compte ne peut plus faire, éprouvé par un appel réel.

    Le contrôle précédent lit une ligne de configuration ; celui-ci essaie. Le
    groupe n'est qu'une des voies d'accès au socket : des droits posés
    directement sur le fichier, ou une appartenance par un groupe intermédiaire,
    laisseraient le premier contrôle satisfait et le pouvoir intact.

    `docker ps` est choisi parce qu'il ne modifie rien : il ouvre le socket et
    lit. Un refus d'accès y suffit à prouver la perte.
    """
    _garde_fous(host)

    essai = host.run("sudo -n -u %s docker ps", COMPTE)
    assert essai.rc != 0, message(
        en=(
            f"{COMPTE} can still reach the daemon: `docker ps` succeeded.\n"
            "Reaching the socket is the privilege itself, and the group is only "
            "one of the ways to it. Check the socket's own permissions and any "
            "intermediate group."
        ),
        fr=(
            f"{COMPTE} joint encore le démon : `docker ps` a réussi.\n"
            "Atteindre le socket EST le privilège, et le groupe n'est qu'une des "
            "voies qui y mènent. Vérifiez les droits du socket lui-même et tout "
            "groupe intermédiaire."
        ),
    )
    refus = (essai.stderr + essai.stdout).lower()
    assert "permission denied" in refus or "permission refus" in refus, message(
        en=(
            f"`docker ps` failed for {COMPTE}, but not on a permission refusal:\n"
            f"  {(essai.stderr or essai.stdout).strip()[:200]}\n"
            "A daemon that is down, or a missing binary, would fail the same way "
            "while leaving the privilege in place. Only a refusal on the socket "
            "proves it was lost."
        ),
        fr=(
            f"`docker ps` a échoué pour {COMPTE}, mais pas sur un refus de "
            f"permission :\n  {(essai.stderr or essai.stdout).strip()[:200]}\n"
            "Un démon arrêté, ou un binaire absent, échoueraient de la même "
            "façon en laissant le privilège en place. Seul un refus sur le socket "
            "prouve qu'il a été perdu."
        ),
    )
