"""test_functional.py : runtime-qui-appelle-qui

Savoir qui appelle qui se reconnaît à quatre choses : un conteneur Podman
`vigie` lancé par runc et non par crun ; une tâche containerd `releve` en
marche dans le namespace `equipe` ; et deux PID notés, celui du shim de
`gardien` et celui du conmon de `vigie`, qui doivent être les VRAIS parents
des processus de ces conteneurs. Les tests lisent Podman, containerd et /proc,
jamais l'historique.

Aucun n'est vrai avant le travail : au départ, vigie et releve n'existent pas,
et /srv/reponses est vide.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_target_host, message

REPONSES = "/srv/reponses"


@pytest.fixture(scope="module")
def host():
    return lab_host(lab_target_host("oci.lab"))


def _vigie(host) -> dict:
    res = host.run("sudo podman inspect vigie 2>/dev/null")
    if res.rc != 0 or not res.stdout.strip():
        return {}
    return (json.loads(res.stdout) or [{}])[0]


def _taches(host, ns: str) -> dict[str, tuple[str, str]]:
    """Les tâches d'un namespace containerd : nom vers (PID, état)."""
    res = host.run(f"sudo ctr -n {ns} task ls 2>/dev/null")
    taches = {}
    for ligne in res.stdout.splitlines()[1:]:
        champs = ligne.split()
        if len(champs) >= 3:
            taches[champs[0]] = (champs[1], champs[2])
    return taches


def _parent(host, pid: str) -> str:
    return host.run(f"sudo awk '{{print $4}}' /proc/{pid}/stat 2>/dev/null").stdout.strip()


def _reponse(host, nom: str) -> str:
    return host.run(f"sudo cat {REPONSES}/{nom} 2>/dev/null").stdout.strip()


def test_vigie_tourne_avec_runc(host):
    vigie = _vigie(host)
    etat = vigie.get("State", {})
    assert etat.get("Running") is True, message(
        en="No Podman container vigie is running "
        f"(state: {etat.get('Status', 'absent')}). Start it detached, on busybox, "
        "with a command that lasts.",
        fr="Aucun conteneur Podman vigie ne tourne "
        f"(état : {etat.get('Status', 'absent')}). Lancez-le détaché, sur busybox, "
        "avec une commande qui dure.",
    )
    assert vigie.get("OCIRuntime") == "runc", message(
        en=f"vigie runs with the runtime \"{vigie.get('OCIRuntime')}\". Podman picks "
        "crun by default: the --runtime runc option makes it hand the bundle to "
        "runc. A running container keeps its runtime: remove it and start it again.",
        fr=f"vigie tourne avec le runtime « {vigie.get('OCIRuntime')} ». Podman "
        "choisit crun par défaut : l'option --runtime runc lui fait confier le "
        "bundle à runc. Un conteneur qui tourne garde son runtime : supprimez-le "
        "et relancez-le.",
    )
    assert "busybox" in vigie.get("ImageName", ""), message(
        en=f"vigie runs the image {vigie.get('ImageName')}, not busybox.",
        fr=f"vigie tourne sur l'image {vigie.get('ImageName')}, pas sur busybox.",
    )


def test_releve_tourne_dans_le_namespace_equipe(host):
    taches = _taches(host, "equipe")
    _, etat = taches.get("releve", ("", "absente"))
    assert etat == "RUNNING", message(
        en=f"The task releve of the containerd namespace equipe is {etat}. ctr "
        "reads the default namespace unless told otherwise: the -n option names "
        "another one, for the pull as for the run.",
        fr=f"La tâche releve du namespace containerd equipe est {etat}. ctr lit "
        "le namespace default sauf indication contraire : l'option -n en désigne "
        "un autre, pour le pull comme pour le run.",
    )
    info = host.run("sudo ctr -n equipe container info releve 2>/dev/null").stdout
    image = json.loads(info or "{}").get("Image", "")
    assert "busybox" in image, message(
        en=f"releve runs the image {image or 'unknown'}, not busybox.",
        fr=f"releve tourne sur l'image {image or 'inconnue'}, pas sur busybox.",
    )


def test_le_shim_de_gardien_est_note(host):
    pid, etat = _taches(host, "nuit").get("gardien", ("", "absente"))
    assert etat == "RUNNING" and pid, message(
        en=f"The task gardien of the namespace nuit is {etat}: it had to be "
        "found, not stopped. Replay the lab with dsoxlab reset.",
        fr=f"La tâche gardien du namespace nuit est {etat} : il fallait la "
        "trouver, pas l'arrêter. Rejouez le lab avec dsoxlab reset.",
    )
    shim = _parent(host, pid)
    reponse = _reponse(host, "shim-gardien")
    assert reponse == shim, message(
        en=f"{REPONSES}/shim-gardien reads \"{reponse or 'nothing'}\", which is not "
        "the parent of the gardien process. ctr task ls does not show gardien: it "
        "lives in another namespace (ctr namespaces ls). Its PID is in the task "
        "list of that namespace, and its parent is the shim.",
        fr=f"{REPONSES}/shim-gardien contient « {reponse or 'rien'} », qui n'est "
        "pas le parent du processus de gardien. ctr task ls ne montre pas "
        "gardien : il vit dans un autre namespace (ctr namespaces ls). Son PID est "
        "dans la liste des tâches de ce namespace, et son parent est le shim.",
    )


def test_le_conmon_de_vigie_est_note(host):
    pid = str(_vigie(host).get("State", {}).get("Pid") or "")
    assert pid and pid != "0", message(
        en="vigie has no running process: there is no parent to read.",
        fr="vigie n'a pas de processus en marche : il n'y a pas de parent à lire.",
    )
    conmon = _parent(host, pid)
    reponse = _reponse(host, "conmon-vigie")
    assert reponse == conmon, message(
        en=f"{REPONSES}/conmon-vigie reads \"{reponse or 'nothing'}\", which is not "
        f"the parent of the vigie process (PID {pid} on the host). Read the "
        "process tree: the parent of the container is conmon, not podman.",
        fr=f"{REPONSES}/conmon-vigie contient « {reponse or 'rien'} », qui n'est "
        f"pas le parent du processus de vigie (PID {pid} sur l'hôte). Lisez "
        "l'arbre des processus : le parent du conteneur est conmon, pas podman.",
    )
