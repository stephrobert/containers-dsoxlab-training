"""test_functional.py : conteneur-limiter-a-la-main

Un conteneur limité se reconnaît à l'état du noyau : un cgroup quai qui porte
les plafonds demandés, un processus dont la racine est /srv/quai qui vit dans
ce cgroup et dans son propre namespace pid, des masques de capabilities sans
CAP_SYS_ADMIN, et un compteur oom_kill qui prouve que le plafond mémoire a
déjà tué. Les tests lisent /sys/fs/cgroup et /proc, jamais l'historique.

Aucun n'est vrai avant le travail : au départ, le cgroup quai n'existe pas, et
aucun processus n'a /srv/quai pour racine.

Pourquoi lire les masques plutôt que tenter un `hostname` : `nsenter`, lancé
en root depuis l'hôte, garde toutes ses capabilities (mesuré le 2026-11-24,
CapEff 000001ffffffffff). Un essai par nsenter réussirait donc toujours. Le
masque est ce que le noyau consulte pour refuser.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

RACINE = "/srv/quai"
CGROUP = "/sys/fs/cgroup/quai"
MEMOIRE = "50331648"  # 48M
PROCESSUS = "32"
CPU = "30000 100000"
#: Rang de CAP_SYS_ADMIN dans les masques de /proc/<pid>/status
#: (`setpriv --list-caps`, 22e ligne, comptée à partir de 0).
BIT_SYS_ADMIN = 21


@pytest.fixture(scope="module")
def host():
    return lab_host(lab_target_host("oci.lab"))


def _lire(host, fichier: str) -> str:
    return host.run(f"sudo cat {fichier} 2>/dev/null").stdout.strip()


def _processus(host) -> list[str]:
    """Les PID de l'hôte dont la racine est /srv/quai."""
    res = host.run(
        "sudo sh -c 'for p in $(ls /proc | grep -E \"^[0-9]+$\"); do "
        f"[ \"$(readlink /proc/$p/root 2>/dev/null)\" = {RACINE} ] && echo $p; done; true'"
    )
    return res.stdout.split()


def _champ(host, pid: str, nom: str) -> str:
    return host.run(f"sudo awk '/^{nom}:/ {{$1=\"\"; print}}' /proc/{pid}/status").stdout.strip()


def test_le_cgroup_quai_plafonne_la_memoire_sans_swap(host):
    memoire = _lire(host, f"{CGROUP}/memory.max")
    swap = _lire(host, f"{CGROUP}/memory.swap.max")
    assert memoire == MEMOIRE and swap == "0", message(
        en=f"In {CGROUP}, memory.max reads \"{memoire or 'nothing'}\" and "
        f"memory.swap.max \"{swap or 'nothing'}\". Expected 48M ({MEMOIRE} "
        "bytes) and 0: without swap, the container cannot spill over its cap.",
        fr=f"Dans {CGROUP}, memory.max vaut « {memoire or 'rien'} » et "
        f"memory.swap.max « {swap or 'rien'} ». Attendu : 48M ({MEMOIRE} "
        "octets) et 0. Sans swap, le conteneur ne peut pas déborder de son "
        "plafond.",
    )


def test_le_cgroup_quai_plafonne_processus_et_cpu(host):
    pids = _lire(host, f"{CGROUP}/pids.max")
    cpu = _lire(host, f"{CGROUP}/cpu.max")
    assert pids == PROCESSUS and cpu == CPU, message(
        en=f"In {CGROUP}, pids.max reads \"{pids or 'nothing'}\" and cpu.max "
        f"\"{cpu or 'nothing'}\". Expected {PROCESSUS} tasks, and \"{CPU}\": "
        "30 ms of CPU per period of 100 ms, that is 30 % of one core.",
        fr=f"Dans {CGROUP}, pids.max vaut « {pids or 'rien'} » et cpu.max "
        f"« {cpu or 'rien'} ». Attendu : {PROCESSUS} tâches, et « {CPU} » : "
        "30 ms de CPU par période de 100 ms, soit 30 % d'un cœur.",
    )


def test_un_conteneur_tourne_dans_le_cgroup_quai(host):
    pids = _processus(host)
    assert pids, message(
        en=f"No process has {RACINE} as its root. The container must keep "
        "running after you log out: launch it detached, with a command that "
        "lasts.",
        fr=f"Aucun processus n'a {RACINE} pour racine. Le conteneur doit "
        "continuer de tourner après votre déconnexion : lancez-le détaché, "
        "avec une commande qui dure.",
    )
    dehors = [p for p in pids if _lire(host, f"/proc/{p}/cgroup") != "0::/quai"]
    assert not dehors, message(
        en=f"These container processes are not in the quai cgroup: {dehors}. "
        "A cap only applies to the processes of its group: put the process in "
        "cgroup.procs BEFORE it starts the container, so that all it starts "
        "inherits the group.",
        fr=f"Ces processus du conteneur ne sont pas dans le cgroup quai : "
        f"{dehors}. Un plafond ne s'applique qu'aux processus de son groupe : "
        "écrivez le processus dans cgroup.procs AVANT qu'il lance le "
        "conteneur, pour que tout ce qu'il lance en hérite.",
    )
    seuls = [p for p in pids if len(_champ(host, p, "NSpid").split()) < 2]
    assert not seuls, message(
        en=f"These processes have {RACINE} as their root but share the pid "
        f"namespace of the host: {seuls}. A chroot alone is not a container: "
        "start it with unshare, as in the previous lab.",
        fr=f"Ces processus ont {RACINE} pour racine mais partagent le "
        f"namespace pid de l'hôte : {seuls}. Un chroot seul ne fait pas un "
        "conteneur : lancez-le avec unshare, comme au lab précédent.",
    )


def test_le_root_du_conteneur_n_a_plus_cap_sys_admin(host):
    pids = _processus(host)
    assert pids, message(
        en=f"No process has {RACINE} as its root, so there are no capabilities to read.",
        fr=f"Aucun processus n'a {RACINE} pour racine : il n'y a pas de capabilities à lire.",
    )
    garde = []
    for p in pids:
        for ensemble in ("CapBnd", "CapEff"):
            masque = _champ(host, p, ensemble)
            if not masque or (int(masque, 16) >> BIT_SYS_ADMIN) & 1:
                garde.append(f"{p} {ensemble}={masque or '?'}")
    assert not garde, message(
        en=f"CAP_SYS_ADMIN (bit {BIT_SYS_ADMIN}) is still there: {garde}. Remove "
        "it from the bounding set with setpriv, AFTER unshare has created the "
        "namespaces and BEFORE entering the root filesystem. The root of the "
        "container then can no longer change the host name.",
        fr=f"CAP_SYS_ADMIN (bit {BIT_SYS_ADMIN}) est toujours là : {garde}. "
        "Retirez-la du bounding set avec setpriv, APRÈS qu'unshare a créé les "
        "namespaces et AVANT d'entrer dans le système de fichiers. Le root du "
        "conteneur ne peut alors plus changer le nom de machine.",
    )


def test_le_plafond_memoire_a_deja_tue_un_processus(host):
    evenements = _lire(host, f"{CGROUP}/memory.events")
    tues = next(
        (int(ligne.split()[1]) for ligne in evenements.splitlines() if ligne.startswith("oom_kill ")),
        0,
    )
    assert tues >= 1, message(
        en=f"The oom_kill counter of {CGROUP}/memory.events reads {tues}: the "
        "memory cap has never killed anything. Run, in the quai cgroup, a "
        "program that grows in memory (tail /dev/zero), and watch the kernel "
        "kill it.",
        fr=f"Le compteur oom_kill de {CGROUP}/memory.events vaut {tues} : le "
        "plafond mémoire n'a encore rien tué. Lancez, dans le cgroup quai, un "
        "programme qui grossit en mémoire (tail /dev/zero), et regardez le "
        "noyau le tuer.",
    )
