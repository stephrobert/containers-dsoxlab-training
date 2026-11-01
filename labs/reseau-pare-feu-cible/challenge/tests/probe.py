"""Namespace-scoped multi-hop diagnostics and denied-path counter evidence."""

import json
import os
import subprocess
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
        assert service["State"]["Running"] and service["Image"] == image
        assert service["Config"]["Labels"].get("dsoxlab.lab") == LAB
        assert (
            not host["Privileged"]
            and host["CapAdd"] == ["NET_ADMIN"]
            and host["CapDrop"] == ["ALL"]
        )
        assert host["NetworkMode"] != "host" and not host["PortBindings"]
        assert host["PidMode"] != "host" and host["IpcMode"] != "host"
        assert all(m["Destination"] == "/rules.nft" for m in service["Mounts"]), message(
            en="Do not mount host APIs or namespaces",
            fr="Ne montez ni API ni namespaces de l'hote",
        )
    router, server = services["router"], services["server"]
    network_names = set(router["NetworkSettings"]["Networks"])
    assert len(network_names) == 2
    for net in json.loads(docker("network", "inspect", *network_names)):
        assert net["Driver"] == "bridge" and net["Labels"].get("dsoxlab.lab") == LAB
        assert set(net["Containers"]) <= {
            service["Id"] for service in services.values()
        }, message(
            en="Keep the dedicated bridges exclusive to this lab",
            fr="Reservez les bridges dedies a ce lab",
        )
    assert docker("exec", router["Id"], "cat", "/proc/sys/net/ipv4/ip_forward") == "1"
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
    assert after["business"] > before["business"]
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


def main():
    first = assess()
    docker(
        "compose",
        "-p",
        PROJECT,
        "-f",
        WORK + "/compose.yaml",
        "up",
        "-d",
        "--force-recreate",
        "--pull",
        "never",
        timeout=35,
    )
    second = assess()
    print(
        json.dumps(
            {
                "hops": ["client-router", "router-server", "client-server"],
                "counters": [first, second],
                "recreation": "protected",
            }
        )
    )


if __name__ == "__main__":
    main()
