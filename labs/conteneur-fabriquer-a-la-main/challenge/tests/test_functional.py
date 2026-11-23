"""test_functional.py : conteneur-fabriquer-a-la-main

Un conteneur fabriqué à la main, sans moteur, se reconnaît à l'état du noyau :
un processus dont la racine est /srv/atelier, qui a ses propres namespaces,
porte le nom de machine demandé et se croit PID 1. Les tests interrogent
/proc et nsenter, jamais l'historique de l'apprenant.

Aucun n'est vrai avant le travail : au départ, /srv/atelier n'existe pas, et
aucun processus n'y a sa racine.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

RACINE = "/srv/atelier"
NOM = "atelier-isole"
VERSION = "3.24.2"
#: L'empreinte du busybox de l'archive officielle, relevée le 2026-11-23 sur
#: oci.lab après `sha256sum -c` de l'archive contre la somme d'Alpine. La copie
#: altérée du dépôt porte un octet de plus dans ce fichier.
BUSYBOX_OFFICIEL = "01a989eb4d1d04b0d146c790ac536abd88f374ec74a2e110c58910b840d42045"
ISOLES = ("pid", "uts", "mnt", "net", "ipc")


@pytest.fixture(scope="module")
def host():
    return lab_host(lab_target_host("oci.lab"))


def _processus(host) -> list[str]:
    """Les PID de l'hôte dont la racine est /srv/atelier."""
    res = host.run(
        "sudo sh -c 'for p in $(ls /proc | grep -E \"^[0-9]+$\"); do "
        f"[ \"$(readlink /proc/$p/root 2>/dev/null)\" = {RACINE} ] && echo $p; done; true'"
    )
    return res.stdout.split()


def _pid_1(host) -> str | None:
    """Le processus du conteneur qui est PID 1 dans son namespace, s'il existe."""
    for pid in _processus(host):
        nspid = host.run(f"sudo awk '/^NSpid:/ {{print $NF}}' /proc/{pid}/status").stdout.strip()
        if nspid == "1":
            return pid
    return None


def test_le_rootfs_vient_de_l_archive_verifiee(host):
    version = host.run(f"sudo cat {RACINE}/etc/alpine-release").stdout.strip()
    assert version == VERSION, message(
        en=f"{RACINE} does not hold the Alpine {VERSION} root filesystem "
        f"(etc/alpine-release reads \"{version or 'nothing'}\"). Extract the "
        "archive of the depot into it.",
        fr=f"{RACINE} ne contient pas le système de fichiers Alpine {VERSION} "
        f"(etc/alpine-release vaut « {version or 'rien'} »). Extrayez-y "
        "l'archive du dépôt.",
    )
    empreinte = host.run(f"sudo sha256sum {RACINE}/bin/busybox").stdout.split()[:1]
    assert empreinte == [BUSYBOX_OFFICIEL], message(
        en="The root filesystem comes from the ALTERED archive: its bin/busybox "
        "is not the official one. Only one of the two copies of the depot "
        "matches the SHA-256 published by Alpine (/srv/depot/SHA256SUMS). "
        "Check before extracting.",
        fr="Le système de fichiers vient de l'archive ALTÉRÉE : son bin/busybox "
        "n'est pas celui d'Alpine. Une seule des deux copies du dépôt "
        "correspond à la somme SHA-256 publiée par Alpine "
        "(/srv/depot/SHA256SUMS). Vérifiez avant d'extraire.",
    )


def test_un_processus_tourne_avec_ses_propres_namespaces(host):
    pid = _pid_1(host) or next(iter(_processus(host)), None)
    assert pid, message(
        en=f"No process has {RACINE} as its root. The container must keep "
        "running after you log out: launch it detached (setsid, or & then "
        "disown).",
        fr=f"Aucun processus n'a {RACINE} pour racine. Le conteneur doit "
        "continuer de tourner après votre déconnexion : lancez-le détaché "
        "(setsid, ou & puis disown).",
    )
    communs = [
        ns for ns in ISOLES
        if host.run(f"sudo readlink /proc/{pid}/ns/{ns}").stdout.strip()
        == host.run(f"sudo readlink /proc/1/ns/{ns}").stdout.strip()
    ]
    assert not communs, message(
        en=f"The container process shares these namespaces with the host: "
        f"{communs}. Each of pid, uts, mnt, net and ipc must be its own.",
        fr=f"Le processus du conteneur partage ces namespaces avec l'hôte : "
        f"{communs}. pid, uts, mnt, net et ipc doivent tous être les siens.",
    )


def test_le_conteneur_porte_le_nom_demande_sans_toucher_l_hote(host):
    pid = _pid_1(host) or next(iter(_processus(host)), None)
    assert pid, message(
        en=f"No process has {RACINE} as its root, so there is no host name to read.",
        fr=f"Aucun processus n'a {RACINE} pour racine : il n'y a pas de nom de machine à lire.",
    )
    nom = host.run(f"sudo nsenter --target {pid} --uts hostname").stdout.strip()
    hote = host.run("hostname").stdout.strip()
    assert nom == NOM and hote != NOM, message(
        en=f"Inside the container the host name is \"{nom}\", on the host "
        f"\"{hote}\". The container must be called {NOM}, and the host must "
        "keep its own name: that is what a separate uts namespace allows.",
        fr=f"Dans le conteneur, le nom de machine vaut « {nom} », sur l'hôte "
        f"« {hote} ». Le conteneur doit s'appeler {NOM}, et l'hôte garder son "
        "nom : c'est ce que permet un namespace uts à part.",
    )


def test_le_processus_est_le_pid_1_de_son_conteneur(host):
    assert _pid_1(host), message(
        en="No process of the container is PID 1 in its own namespace. A new "
        "pid namespace only applies to the CHILDREN of the process that "
        "creates it: unshare needs --fork for the program to become PID 1.",
        fr="Aucun processus du conteneur n'est le PID 1 de son namespace. Un "
        "nouveau namespace pid ne s'applique qu'aux ENFANTS du processus qui le "
        "crée : unshare a besoin de --fork pour que le programme devienne le "
        "PID 1.",
    )


def test_dev_null_est_un_vrai_peripherique(host):
    etat = host.run(f"sudo stat -c '%F %t,%T' {RACINE}/dev/null").stdout.strip()
    assert etat == "character special file 1,3", message(
        en=f"{RACINE}/dev/null is \"{etat or 'absent'}\", not the character "
        "device 1,3. Without it, a redirection to /dev/null creates an ordinary "
        "file, which can fill the disk. Create it with mknod.",
        fr=f"{RACINE}/dev/null vaut « {etat or 'absent'} », pas le périphérique "
        "caractère 1,3. Sans lui, une redirection vers /dev/null crée un "
        "fichier ordinaire, qui peut remplir le disque. Créez-le avec mknod.",
    )
