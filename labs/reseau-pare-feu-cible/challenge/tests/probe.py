"""Diagnostic multi-sauts dans le namespace du routeur, une étape à la fois.

Ce fichier portait un `main()` qui jouait tout et un unique `def test_` qui
agrégeait le verdict. Pour deux exigences distinctes, l'apprenant recevait un
seul refus et neuf cents caractères de trace.

`assess()` était déjà autonome : il vérifie la topologie, les trois sauts, les
refus et les compteurs nftables. Deux étapes l'exposent donc, appelées par leur
nom en argument :

    etat         un seul `assess()`
    recreation   recrée la stack, puis `assess()`

La topologie et les refus restent DANS `assess()` comme garde-fous, et non comme
étapes : ils tiennent déjà sur l'état initial, où le pare-feu bloque tout. Ce qui
est vrai avant tout travail ne peut pas noter.
"""

import json
import os
import subprocess
import sys
import time

LAB = "reseau-pare-feu-cible"
PROJECT = "dsoxlab-" + LAB + "-stack"
WORK = "/opt/dsoxlab-" + LAB


def message(en: str, fr: str) -> str:
    return fr if os.environ.get("DSOXLAB_LANG", "en").lower().startswith("fr") else en


def docker(*args, timeout=25):
    result = subprocess.run(
        ["docker", *args], check=False, text=True, capture_output=True, timeout=timeout
    )
    assert result.returncode == 0, message(
        en=f"Namespace operation failed: {args[0]}",
        fr=f"L'operation dans le namespace echoue : {args[0]}",
    )
    return result.stdout.strip()


def request(container, address, port):
    script = (
        "import json,urllib.request,sys;"
        f"u='http://{address}:{port}/record';"
        "\ntry:\n with urllib.request.urlopen(u,timeout=1.2) as r: print(r.read().decode())"
        "\nexcept OSError: sys.exit(7)"
    )
    result = subprocess.run(
        ["docker", "exec", container["Id"], "python", "-c", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=4,
    )
    if result.returncode:
        assert result.returncode == 7, message(
            en="The negative probe failed to execute, rather than being refused",
            fr="La sonde negative ne s'execute pas, au lieu de subir un refus",
        )
        return None
    return json.loads(result.stdout)


def protections(router):
    rules = json.loads(docker("exec", router["Id"], "nft", "-j", "list", "ruleset"))[
        "nftables"
    ]
    chains = {r["chain"]["name"]: r["chain"] for r in rules if "chain" in r}
    assert chains["input"]["policy"] == chains["forward"]["policy"] == "drop", message(
        en="Keep namespace default-deny policies",
        fr="Conservez les politiques de refus par defaut du namespace",
    )
    comments = {r["rule"].get("comment"): r["rule"] for r in rules if "rule" in r}
    assert {
        "deny-untrusted",
        "deny-debug",
        "deny-rest",
        "business",
    } <= comments.keys(), message(
        en="Keep unrelated namespace protections",
        fr="Conservez les protections du namespace sans rapport avec la panne",
    )
    return {
        key: sum(e["counter"]["packets"] for e in value["expr"] if "counter" in e)
        for key, value in comments.items()
    }


def canonique(noms):
    """Les capabilities sous leur nom CANONIQUE, prefixe `CAP_` compris.

    MESURE du 2026-11-02 sur Docker 29.9.2 : `--cap-add NET_ADMIN` ressort en
    `CapAdd=[CAP_NET_ADMIN]`, la ou 26 rendait le nom nu. Comparer la forme nue
    refusait donc une solution juste. On compare des noms canoniques : les deux
    ecritures sont acceptees cote apprenant, et une capability de trop reste un
    ecart. `ALL` reste `ALL`, qui n'est pas une capability mais le mot qui les
    designe toutes.
    """
    return sorted(
        n if n == "ALL" else "CAP_" + n.removeprefix("CAP_")
        for n in (noms or [])
    )


def assess():
    ids = docker(
        "ps", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}"
    ).split()
    assert len(ids) == 4, message(
        en="Start the four isolated topology components",
        fr="Demarrez les quatre composants isoles de la topologie",
    )
    services = {
        c["Config"]["Labels"]["com.docker.compose.service"]: c
        for c in json.loads(docker("inspect", *ids))
    }
    image = docker(
        "image", "inspect", "dsoxlab-" + LAB + "-image", "--format", "{{.Id}}"
    )
    for service in services.values():
        host = service["HostConfig"]
        assert service["State"]["Running"] and service["Image"] == image, message(
            en="Each component must run the image this lab builds",
            fr="Chaque composant doit tourner l'image que ce lab construit",
        )
        assert service["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
            en="Keep the dsoxlab.lab label: cleanup removes only what carries it",
            fr="Conservez le label dsoxlab.lab : le nettoyage ne retire que ce qui le porte",
        )
        assert (
            not host["Privileged"]
            and canonique(host["CapAdd"]) == ["CAP_NET_ADMIN"]
            and canonique(host["CapDrop"]) == ["ALL"]
        ), message(
            en="Each component keeps CAP_NET_ADMIN only, drops the rest, and stays "
               "unprivileged: a privileged container escapes the very routing this "
               "lab measures",
            fr="Chaque composant garde CAP_NET_ADMIN seul, abandonne le reste et "
               "reste non privilegie : un conteneur privilegie echappe au routage "
               "meme que ce lab mesure",
        )
        assert host["NetworkMode"] != "host" and not host["PortBindings"], message(
            en="No component uses the host network or publishes a port: the three "
               "hops must cross the router, not the host stack",
            fr="Aucun composant n'utilise le reseau de l'hote ni ne publie de port : "
               "les trois sauts doivent traverser le routeur, pas la pile de l'hote",
        )
        assert host["PidMode"] != "host" and host["IpcMode"] != "host", message(
            en="No component shares the host PID or IPC namespace",
            fr="Aucun composant ne partage le namespace PID ou IPC de l'hote",
        )
        assert all(m["Destination"] == "/rules.nft" for m in service["Mounts"]), message(
            en="Do not mount host APIs or namespaces",
            fr="Ne montez ni API ni namespaces de l'hote",
        )
    router, server = services["router"], services["server"]
    network_names = set(router["NetworkSettings"]["Networks"])
    assert len(network_names) == 2, message(
        en=f"The router must sit on exactly two networks, found "
           f"{len(network_names)}: it is what makes it a router rather than a peer",
        fr=f"Le routeur doit etre sur exactement deux reseaux, {len(network_names)} "
           f"trouve(s) : c'est ce qui en fait un routeur et non un voisin",
    )
    for net in json.loads(docker("network", "inspect", *network_names)):
        assert net["Driver"] == "bridge" and net["Labels"].get("dsoxlab.lab") == LAB, message(
            en="Both networks are dedicated bridges labelled for this lab",
            fr="Les deux reseaux sont des bridges dedies, etiquetes pour ce lab",
        )
        assert set(net["Containers"]) <= {
            service["Id"] for service in services.values()
        }, message(
            en="Keep the dedicated bridges exclusive to this lab",
            fr="Reservez les bridges dedies a ce lab",
        )
    assert docker(
        "exec", router["Id"], "cat", "/proc/sys/net/ipv4/ip_forward"
    ) == "1", message(
        en="The router does not forward: net.ipv4.ip_forward is 0 in its namespace, "
           "so no packet can cross it whatever the rules say",
        fr="Le routeur ne relaie pas : net.ipv4.ip_forward vaut 0 dans son namespace, "
           "donc aucun paquet ne peut le traverser quoi que disent les regles",
    )
    for role in ("allowed", "denied"):
        route = docker(
            "exec", services[role]["Id"], "ip", "route", "get", "172.30.202.10"
        )
        assert "via 172.30.201.254" in route, message(
            en="The client must traverse the router, not a Docker gateway",
            fr="Le client doit traverser le routeur, pas une passerelle Docker",
        )
    assert "via 172.30.202.254" in docker(
        "exec", server["Id"], "ip", "route", "get", "172.30.201.10"
    ), message(
        en="The server must answer through the router: without that return route "
           "the reply never comes back, and the hop looks blocked when it is not",
        fr="Le serveur doit repondre par le routeur : sans cette route retour la "
           "reponse ne revient jamais, et le saut parait bloque sans l'etre",
    )
    deadline = time.monotonic() + 8
    while request(server, "127.0.0.1", 8080) is None:
        assert time.monotonic() < deadline, message(
            en="Server readiness deadline exceeded",
            fr="Le delai de disponibilite du serveur est depasse",
        )
        time.sleep(0.05)
    assert request(server, "127.0.0.1", 9090)["component"] == "server", message(
        en="Debug service must really be listening",
        fr="Le service de debug doit reellement ecouter",
    )
    assert (
        request(services["allowed"], "172.30.201.254", 8081)["component"] == "router"
    ), message(
        en="The first hop is unavailable", fr="Le premier saut est indisponible",
    )
    assert request(router, "172.30.202.10", 8080) == {
        "component": "server",
        "value": "inventory-ready",
    }, message(
        en="Router-to-server hop is unavailable", fr="Le saut routeur-serveur est indisponible",
    )
    before = protections(router)
    assert request(services["allowed"], "172.30.202.10", 8080) == {
        "component": "server",
        "value": "inventory-ready",
    }, message(
        en="The business firewall rule still blocks the allowed client",
        fr="La regle metier du pare-feu bloque encore le client autorise",
    )
    assert request(services["denied"], "172.30.202.10", 8080) is None, message(
        en="Untrusted client bypassed filtering",
        fr="Le client non autorise contourne le filtrage",
    )
    assert request(services["allowed"], "172.30.202.10", 9090) is None, message(
        en="Debug port bypassed filtering", fr="Le port de debug contourne le filtrage",
    )
    assert request(services["allowed"], "172.30.202.10", 8089) is None, message(
        en="The mistaken destination must not be opened",
        fr="La destination erronee ne doit pas etre ouverte",
    )
    after = protections(router)
    assert after["business"] > before["business"], message(
        en="The accepted traffic did not increment the business rule counter: it "
           "reached its destination without traversing the rule that allows it",
        fr="Le trafic accepte n'a pas incremente le compteur de la regle metier : il "
           "a atteint sa destination sans traverser la regle qui l'autorise",
    )
    assert (
        after["deny-untrusted"] > before["deny-untrusted"]
        and after["deny-debug"] > before["deny-debug"]
    ), message(
        en="Denied probes must actually traverse the protective rules",
        fr="Les sondes refusees doivent reellement traverser les regles de protection",
    )
    return {
        key: after[key] - before[key]
        for key in ("business", "deny-untrusted", "deny-debug")
    }


def etape_etat():
    """Le flux métier passe-t-il, et les exclusions tiennent-elles ?"""
    return {
        "hops": ["client-router", "router-server", "client-server"],
        "counters": assess(),
    }


def etape_recreation():
    """Tout tient-il encore après une recréation de la stack ?

    Le scénario l'exige implicitement : une règle corrigée à la main dans le
    namespace du routeur disparaîtrait au redémarrage, et le lab serait réussi
    sur un état qui ne survit pas.

    L'étape joue `assess()` AVANT et APRÈS, parce qu'une recréation qui partirait
    d'un état déjà faux ne dirait rien de la persistance.
    """
    avant = assess()
    docker(
        "compose", "-p", PROJECT, "-f", WORK + "/compose.yaml",
        "up", "-d", "--force-recreate", "--pull", "never", timeout=35,
    )
    apres = assess()
    return {"counters": [avant, apres], "recreation": "protected"}


ETAPES = {
    "etat": etape_etat,
    "recreation": etape_recreation,
}


def main(argv):
    if len(argv) != 2 or argv[1] not in ETAPES:
        print(f"usage: probe.py <{', '.join(sorted(ETAPES))}>", file=sys.stderr)
        return 2
    print(json.dumps(ETAPES[argv[1]]()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
