"""test_functional.py : runtime-lancer-un-bundle

Un bundle lancé par runc se reconnaît à quatre choses : un config.json qui
décrit la commande, le nom de machine et la racine en lecture seule demandés ;
un conteneur `veilleur` à l'état running, dont le bundle est /srv/veilleur ;
un conteneur qui, vu de l'intérieur, porte ce nom et refuse l'écriture à la
racine ; et plus aucun essai arrêté. Les tests lisent le disque et l'état que
runc tient dans /run/runc, jamais l'historique.

Aucun n'est vrai avant le travail : au départ, /srv/veilleur n'existe pas, et
l'identifiant veilleur est pris par un essai arrêté dont le bundle est
/srv/ancien.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_target_host, message

BUNDLE = "/srv/veilleur"
ID = "veilleur"
COMMANDES = (["sleep", "infinity"], ["/bin/sleep", "infinity"])


@pytest.fixture(scope="module")
def host():
    return lab_host(lab_target_host("oci.lab"))


def _etat(host) -> dict:
    res = host.run(f"sudo runc state {ID} 2>/dev/null")
    return json.loads(res.stdout) if res.rc == 0 and res.stdout.strip() else {}


def _conteneurs(host) -> list[dict]:
    res = host.run("sudo runc list -f json 2>/dev/null")
    return json.loads(res.stdout or "null") or []


def test_le_bundle_decrit_ce_qui_est_demande(host):
    res = host.run(f"sudo cat {BUNDLE}/config.json 2>/dev/null")
    assert res.rc == 0 and res.stdout.strip(), message(
        en=f"No config.json in {BUNDLE}. A bundle is a folder with a rootfs and a "
        "config.json next to it: umoci unpack writes both from the image.",
        fr=f"Aucun config.json dans {BUNDLE}. Un bundle est un dossier avec un "
        "rootfs et un config.json à côté : umoci unpack écrit les deux depuis "
        "l'image.",
    )
    try:
        config = json.loads(res.stdout)
    except json.JSONDecodeError as erreur:
        pytest.fail(message(
            en=f"{BUNDLE}/config.json is not valid JSON ({erreur}). Edit it with "
            "jq rather than by hand: jq rewrites a valid document.",
            fr=f"{BUNDLE}/config.json n'est pas un JSON valide ({erreur}). "
            "Modifiez-le avec jq plutôt qu'à la main : jq réécrit un document "
            "valide.",
        ))
    ecarts = []
    if config.get("process", {}).get("args") not in COMMANDES:
        ecarts.append(("process.args", str(config.get("process", {}).get("args"))))
    if config.get("hostname") != ID:
        ecarts.append(("hostname", str(config.get("hostname"))))
    if (config.get("root") or {}).get("readonly") is not True:
        ecarts.append(("root.readonly", str((config.get("root") or {}).get("readonly"))))
    assert not ecarts, message(
        en="config.json does not describe what is asked: "
        + ", ".join(f"{champ} reads {valeur}" for champ, valeur in ecarts)
        + ". Expected: args [\"sleep\", \"infinity\"], hostname veilleur, and a "
        "read-only root (umoci leaves it writable).",
        fr="Le config.json ne décrit pas ce qui est demandé : "
        + ", ".join(f"{champ} vaut {valeur}" for champ, valeur in ecarts)
        + ". Attendu : args [\"sleep\", \"infinity\"], hostname veilleur, et une "
        "racine en lecture seule (umoci la laisse modifiable).",
    )
    rootfs = host.run(f"sudo test -x {BUNDLE}/rootfs/bin/busybox")
    assert rootfs.rc == 0, message(
        en=f"{BUNDLE}/rootfs does not hold busybox: the root filesystem comes "
        "from the image of /srv/oci-busybox.",
        fr=f"{BUNDLE}/rootfs ne porte pas busybox : le système de fichiers "
        "racine vient de l'image de /srv/oci-busybox.",
    )


def test_veilleur_tourne_depuis_ce_bundle(host):
    etat = _etat(host)
    assert etat.get("status") == "running" and etat.get("bundle") == BUNDLE, message(
        en=f"runc sees the container {ID} as \"{etat.get('status', 'absent')}\", "
        f"with the bundle \"{etat.get('bundle', 'none')}\". Expected: running, "
        f"from {BUNDLE}. A stopped container keeps its identifier until runc "
        "delete; runc run -d then starts it detached.",
        fr=f"runc voit le conteneur {ID} « {etat.get('status', 'absent')} », avec "
        f"le bundle « {etat.get('bundle', 'aucun')} ». Attendu : running, depuis "
        f"{BUNDLE}. Un conteneur arrêté garde son identifiant jusqu'à runc "
        "delete ; runc run -d le lance ensuite détaché.",
    )


def test_le_conteneur_porte_son_nom_et_refuse_l_ecriture(host):
    nom = host.run(f"sudo runc exec {ID} hostname 2>&1")
    assert nom.rc == 0 and nom.stdout.strip() == ID, message(
        en=f"Inside the container, hostname answers \"{nom.stdout.strip()}\". "
        f"Expected {ID}: the hostname field of config.json sets it.",
        fr=f"Dans le conteneur, hostname répond « {nom.stdout.strip()} ». Attendu : "
        f"{ID}. C'est le champ hostname du config.json qui le pose.",
    )
    ecriture = host.run(f"sudo runc exec {ID} touch /preuve-dsoxlab 2>&1")
    assert ecriture.rc != 0 and "Read-only" in ecriture.stdout, message(
        en="Inside the container, writing at the root succeeded: the root is "
        "not read-only. Set root.readonly to true in config.json, then delete "
        "and start the container again: a running container keeps its config.",
        fr="Dans le conteneur, l'écriture à la racine a réussi : la racine n'est "
        "pas en lecture seule. Mettez root.readonly à true dans le config.json, "
        "puis supprimez et relancez le conteneur : un conteneur qui tourne garde "
        "sa configuration.",
    )


def test_plus_aucun_essai_arrete(host):
    restes = [
        f"{c.get('id')} ({c.get('status')}, {c.get('bundle')})"
        for c in _conteneurs(host)
        if c.get("status") == "stopped" or c.get("bundle") == "/srv/ancien"
    ]
    assert not restes, message(
        en=f"runc still lists: {restes}. A stopped container keeps its "
        "identifier and its state in /run/runc until runc delete.",
        fr=f"runc liste encore : {restes}. Un conteneur arrêté garde son "
        "identifiant et son état dans /run/runc jusqu'à runc delete.",
    )
