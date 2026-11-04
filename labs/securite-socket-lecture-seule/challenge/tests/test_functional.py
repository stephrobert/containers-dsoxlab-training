"""Le conteneur applicatif n'atteint plus le socket du démon, par aucun chemin.

Pourquoi deux contrôles, et pourquoi ils ne comparent pas des noms
------------------------------------------------------------------

La version précédente de ce fichier portait un seul contrôle, qui cherchait un
montage dont la source **ou** la destination valait exactement
``/var/run/docker.sock``. Il laissait passer la moitié des formes dangereuses,
et c'est mesuré, pas supposé. Sur la VM du lab, ``/var/run`` est un lien vers
``/run``, ce que la leçon affiche d'ailleurs elle-même dans sa sortie ``mount`` :

===================================================  ==================  ====================
montage                                              ancien contrôle     pouvoir réel
===================================================  ==================  ====================
``src=/var/run/docker.sock dst=/var/run/docker.sock``  signalé             204, témoin ``exited``
``src=/run/docker.sock dst=/var/run/docker.sock``      signalé, par la dst  204, témoin ``exited``
``src=/run/docker.sock dst=/tmp/sock``                 **aveugle**         204, témoin ``exited``
``src=/run dst=/hostrun``                              **aveugle**         204, témoin ``exited``
===================================================  ==================  ====================

Deux formes sur quatre déclaraient la mission accomplie sur un conteneur qui
gardait le pouvoir d'arrêter n'importe quoi sur l'hôte : exactement ce que le
lab prétend interdire. Le dernier cas est le pire des quatre, puisque monter
``/run`` en entier expose **quarante-sept** sockets, dont celui de containerd,
le bus système, l'agent SSH et les sockets gnupg de l'utilisateur.

La leçon à en tirer gouverne les deux contrôles de ce fichier : **un chemin est
ce que l'apprenant a tapé, l'inode est ce que le noyau désigne**. On ne compare
donc plus des noms.

- Le premier contrôle lit la **vue du démon** : pour chaque montage, la source
  est résolue sur l'hôte, puis comparée au socket résolu, qu'elle le soit
  elle-même ou qu'elle le contienne comme répertoire.
- Le second lit la **vue du conteneur** : tout socket unix visible à
  l'intérieur est relevé avec son couple (device, inode), et aucun ne doit être
  celui du démon. Ce contrôle ne dépend d'aucun nom de montage et attrape donc
  ce que le premier ne saurait pas nommer.

Les deux échouent sur l'état de départ et passent une fois la capacité retirée.
Aucun ne vérifie que l'apprenant a *constaté* que ``:ro`` ne protège rien : un
arrêt déclenché par l'API ne laisse aucune trace qui le distingue d'un
``docker stop`` tapé sur l'hôte, et un contrôle qui prétendrait l'exiger
mesurerait la docilité, pas la compréhension. Le scénario fait faire le constat,
les contrôles mesurent la capacité.
"""

from __future__ import annotations

import json
import shlex

import pytest

from conftest import lab_host, message

CONTENEUR = "dsoxlab-socket-readonly"
LAB = "securite-socket-lecture-seule"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _conteneur(host) -> dict:
    """L'inspection du conteneur applicatif, ou un échec qui dit quoi faire.

    Ces deux vérifications sont des **garde-fous de mesure** et non des
    exigences de plus : sans un conteneur étiqueté et actif, aucun des deux
    contrôles ne peut regarder quoi que ce soit, et un contrôle qui n'a pas pu
    regarder ne doit jamais conclure au vert.
    """
    inspecte = host.run(shlex.join(["docker", "inspect", CONTENEUR]))
    assert inspecte.rc == 0, message(
        en=(
            f"The {CONTENEUR} container does not exist. Recreate it without the"
            " socket mount, keeping its name and its label."
        ),
        fr=(
            f"Le conteneur {CONTENEUR} n'existe pas. Recréez-le sans le montage"
            " du socket, en conservant son nom et son label."
        ),
    )
    conteneur = json.loads(inspecte.stdout)[0]

    assert conteneur["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=(
            f"The {CONTENEUR} container lost its dsoxlab.lab={LAB} label. Keep"
            " it: the cleanup removes only what carries it."
        ),
        fr=(
            f"Le conteneur {CONTENEUR} a perdu son label dsoxlab.lab={LAB}."
            " Conservez-le : le nettoyage ne retire que ce qui le porte."
        ),
    )
    assert conteneur["State"]["Running"], message(
        en=(
            f"The {CONTENEUR} container is stopped. Leave it running: a stopped"
            " container cannot be inspected from the inside."
        ),
        fr=(
            f"Le conteneur {CONTENEUR} est arrêté. Laissez-le actif : un"
            " conteneur arrêté ne peut pas être inspecté de l'intérieur."
        ),
    )
    return conteneur


def _socket_du_demon(host) -> str:
    """Le chemin réel du socket, lien symbolique résolu."""
    resolu = host.run(shlex.join(["readlink", "-f", "/var/run/docker.sock"]))
    assert resolu.rc == 0 and resolu.stdout.strip(), message(
        en=(
            "The Docker socket cannot be resolved on the host. This is not your"
            " fault: the check cannot measure anything, report it."
        ),
        fr=(
            "Le socket Docker ne peut pas être résolu sur l'hôte. Ce n'est pas"
            " votre faute : le contrôle ne peut rien mesurer, signalez-le."
        ),
    )
    return resolu.stdout.strip()


def test_aucun_montage_ne_donne_acces_au_socket_du_demon(host):
    """Vue du démon : aucune source ne mène au socket, directement ou non."""
    conteneur = _conteneur(host)
    socket_reel = _socket_du_demon(host)

    coupables: list[str] = []
    for montage in conteneur["Mounts"]:
        source = montage.get("Source") or ""
        if not source:
            continue
        resolue = host.run(shlex.join(["readlink", "-f", source]))
        chemin = resolue.stdout.strip() if resolue.rc == 0 else source

        # Deux façons d'atteindre le socket : être ce fichier, ou être un
        # répertoire qui le contient. La seconde est celle que le contrôle
        # précédent ne voyait pas, et c'est la plus large des deux.
        if chemin == socket_reel:
            coupables.append(
                f"{source} -> {chemin} (le socket lui-même),"
                f" monté sur {montage.get('Destination')}"
            )
        elif socket_reel.startswith(chemin.rstrip("/") + "/"):
            coupables.append(
                f"{source} -> {chemin} (répertoire qui contient {socket_reel}),"
                f" monté sur {montage.get('Destination')}"
            )

    assert not coupables, message(
        en=(
            "The host Docker socket still reaches this container through:"
            f" {'; '.join(coupables)}. Read-only does not make its API"
            " read-only: remove the mount instead of restricting it."
        ),
        fr=(
            "Le socket Docker de l'hôte atteint encore ce conteneur par :"
            f" {'; '.join(coupables)}. La lecture seule ne rend pas son API"
            " en lecture seule : retirez le montage au lieu de le restreindre."
        ),
    )


def test_le_socket_du_demon_est_injoignable_depuis_le_conteneur(host):
    """Vue du conteneur : aucun socket visible n'est celui du démon.

    L'identité se lit sur le couple (device, inode) et non sur un nom : une
    destination renommée, un répertoire parent monté en entier, ou un chemin
    qu'aucune liste n'aurait prévu donnent tous le même couple que le socket de
    l'hôte, parce que c'est le même fichier.
    """
    _conteneur(host)
    socket_reel = _socket_du_demon(host)

    reference = host.run(shlex.join(["stat", "-c", "%d:%i", socket_reel]))
    assert reference.rc == 0 and reference.stdout.strip(), message(
        en=(
            "The Docker socket inode cannot be read on the host. This is not"
            " your fault: the check cannot measure anything, report it."
        ),
        fr=(
            "L'inode du socket Docker est illisible sur l'hôte. Ce n'est pas"
            " votre faute : le contrôle ne peut rien mesurer, signalez-le."
        ),
    )
    attendu = reference.stdout.strip()

    # `find / -type s` liste les sockets unix visibles dans le conteneur, et
    # `stat` donne l'identité de chacun. Mesuré sur l'image alpine du lab : la
    # liste est vide quand rien n'est monté.
    releve = host.run(
        shlex.join(
            [
                "docker",
                "exec",
                CONTENEUR,
                "sh",
                "-c",
                'for s in $(find / -type s 2>/dev/null); do'
                ' stat -c "%d:%i $s" "$s" 2>/dev/null; done; true',
            ]
        )
    )
    assert releve.rc == 0, message(
        en=(
            f"Cannot list the unix sockets inside {CONTENEUR}:"
            f" {releve.stderr.strip()}. This is not your fault if the container"
            " is running, report it."
        ),
        fr=(
            f"Impossible de lister les sockets unix dans {CONTENEUR} :"
            f" {releve.stderr.strip()}. Ce n'est pas votre faute si le"
            " conteneur est actif, signalez-le."
        ),
    )

    joignables = [
        ligne.split(" ", 1)[1]
        for ligne in releve.stdout.splitlines()
        if ligne.startswith(attendu + " ")
    ]

    assert not joignables, message(
        en=(
            "Inside the container, the host daemon socket is still reachable as"
            f" {', '.join(joignables)}. Same inode means the same file,"
            " whatever name it was given."
        ),
        fr=(
            "Dans le conteneur, le socket du démon de l'hôte est encore"
            f" joignable sous {', '.join(joignables)}. Même inode veut dire même"
            " fichier, quel que soit le nom qu'on lui a donné."
        ),
    )
