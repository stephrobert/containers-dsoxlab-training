"""Prove allowed service paths and denied direct access, including by IP."""

from __future__ import annotations

import json
import secrets
import shlex

import pytest

from conftest import lab_host, message

PROJECT = "dsoxlab-isolation-reseau"
COMPOSE = "/opt/lab-compose-net/compose.yaml"
URL = "http://127.0.0.1:18088/cgi-bin/value"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _services(host):
    found = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={PROJECT}")
    assert found.rc == 0 and len(found.stdout.split()) == 3, message(
        en="Start exactly three Compose services in project dsoxlab-isolation-reseau.",
        fr="Démarrez exactement trois services Compose dans le projet dsoxlab-isolation-reseau.",
    )
    result = host.run(shlex.join(["docker", "inspect", *found.stdout.split()]))
    assert result.rc == 0, message(
        en="Cannot inspect the project's containers.",
        fr="Impossible d'inspecter les conteneurs du projet.",
    )
    services = {c["Config"]["Labels"].get("com.docker.compose.service"): c for c in json.loads(result.stdout)}
    assert set(services) == {"front", "api", "data"} and all(c["State"]["Running"] for c in services.values()), message(
        en="The front, api and data services must all be running.",
        fr="Les services front, api et data doivent tous être démarrés.",
    )
    for name, container in services.items():
        image = host.run("docker image inspect %s", f"dsoxlab-compose-net:{name}")
        assert image.rc == 0, message(
            en=f"The supplied image for {name} must exist.",
            fr=f"L'image fournie pour {name} doit exister.",
        )
        original = json.loads(image.stdout)[0]
        assert container["Image"] == original["Id"] and not container["Mounts"] and all(
            container["Config"][key] == original["Config"][key] for key in ("Cmd", "Entrypoint")
        ) and not container["HostConfig"]["Privileged"] and not container["HostConfig"]["CapAdd"], message(
            en=f"Keep {name}'s supplied image and command without mounts, extra capabilities or privileged mode.",
            fr=f"Gardez l'image et la commande de {name} sans montages, capacités supplémentaires ni mode privilégié.",
        )
    return services


def _topology(host):
    services = _services(host)
    networks = {name: set(c["NetworkSettings"]["Networks"]) for name, c in services.items()}
    assert len(networks["front"]) == len(networks["data"]) == 1 and len(networks["api"]) == 2 and not (
        networks["front"] & networks["data"]
    ) and networks["api"] == networks["front"] | networks["data"], message(
        en="Use two separate networks: front+api on one, api+data on the other, with no extra attachments.",
        fr="Utilisez deux réseaux séparés : front+api sur l'un, api+data sur l'autre, sans raccordements supplémentaires.",
    )
    inspected = host.run(shlex.join(["docker", "network", "inspect", *sorted(networks["api"])]))
    assert inspected.rc == 0, message(
        en="Cannot inspect the two application networks.",
        fr="Impossible d'inspecter les deux réseaux applicatifs.",
    )
    details = {n["Name"]: n for n in json.loads(inspected.stdout)}
    assert all(n["Driver"] == "bridge" and n["Labels"].get("com.docker.compose.project") == PROJECT for n in details.values()), message(
        en="Both networks must be Compose-managed bridge networks.",
        fr="Les deux réseaux doivent être des bridges gérés par Compose.",
    )
    assert details[next(iter(networks["data"]))]["Internal"] and not details[next(iter(networks["front"]))]["Internal"], message(
        en="Make the data network internal and keep the frontend network non-internal.",
        fr="Rendez le réseau de données interne et gardez le réseau de façade non interne.",
    )
    assert services["front"]["HostConfig"]["PortBindings"] == {
        "8080/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18088"}],
    } and all(not services[name]["HostConfig"]["PortBindings"] for name in ("api", "data")), message(
        en="Publish only front on 127.0.0.1:18088; keep api and data unpublished.",
        fr="Publiez uniquement front sur 127.0.0.1:18088 ; ne publiez ni api ni data.",
    )
    return services


def _response(host, expected):
    result = host.run(
        "curl --noproxy '*' -fsS --retry 10 --retry-connrefused --retry-delay 1 --max-time 3 %s", URL,
    )
    assert result.rc == 0 and result.stdout.strip() == expected, message(
        en=f"The frontend must relay live data through the API: {result.stderr[-400:]}",
        fr=f"La façade doit relayer les données actuelles via l'API : {result.stderr[-400:]}",
    )


def _isolation(host, services):
    expected = json.loads(host.file("/root/.lab-compose-net.json").content_string)["value"]
    positive = host.run("docker exec %s wget -T 3 -qO- %s", services["api"]["Id"], "http://data:8080/value.txt")
    assert positive.rc == 0 and positive.stdout.strip() == expected, message(
        en="The data server must be reachable from api before testing denied access.",
        fr="Le serveur de données doit être accessible depuis api avant l'essai de refus.",
    )
    data_ip = next(iter(services["data"]["NetworkSettings"]["Networks"].values()))["IPAddress"]
    assert data_ip, message(
        en="The data container must have a bridge IP address.",
        fr="Le conteneur de données doit avoir une adresse IP de bridge.",
    )
    for url in ("http://data:8080/value.txt", f"http://{data_ip}:8080/value.txt"):
        denied = host.run("docker exec %s wget -T 2 -qO- %s", services["front"]["Id"], url)
        assert denied.rc == 1, message(
            en="Direct data access from front must fail by name and by IP, not just lose DNS.",
            fr="L'accès direct de front aux données doit échouer par nom et par IP, pas seulement perdre le DNS.",
        )


def test_network_membership_internal_boundary_and_port_publication(host):
    _topology(host)
    _response(host, json.loads(host.file("/root/.lab-compose-net.json").content_string)["value"])


def test_frontend_relays_changed_data_through_api(host):
    services = _topology(host)
    original = json.loads(host.file("/root/.lab-compose-net.json").content_string)["value"]
    alternate = secrets.token_hex(24)
    try:
        written = host.run("docker exec %s sh -c %s", services["data"]["Id"], f"printf '%s\\n' {alternate} > /www/value.txt")
        assert written.rc == 0, message(
            en="Cannot change the live data for the communication trial.",
            fr="Impossible de changer les données pour l'essai de communication.",
        )
        _response(host, alternate)
    finally:
        restored = host.run("docker exec %s sh -c %s", services["data"]["Id"], f"printf '%s\\n' {shlex.quote(original)} > /www/value.txt")
        assert restored.rc == 0, message(
            en="Cannot restore the data after the trial.",
            fr="Impossible de restaurer les données après l'essai.",
        )


def test_direct_access_is_denied_before_and_after_recreation(host):
    before = _topology(host)
    _isolation(host, before)
    assert host.file(COMPOSE).is_file, message(
        en=f"Write the reusable declaration at {COMPOSE}.",
        fr=f"Écrivez la déclaration réutilisable dans {COMPOSE}.",
    )
    recreated = host.run("docker compose -p %s -f %s up -d --force-recreate --no-build --pull never", PROJECT, COMPOSE)
    assert recreated.rc == 0, message(
        en=f"Compose recreation must succeed: {recreated.stderr[-600:]}",
        fr=f"La recréation Compose doit réussir : {recreated.stderr[-600:]}",
    )
    after = _topology(host)
    assert all(before[name]["Id"] != after[name]["Id"] for name in before), message(
        en="Recreate all three services from the declaration.",
        fr="Recréez les trois services depuis la déclaration.",
    )
    _response(host, json.loads(host.file("/root/.lab-compose-net.json").content_string)["value"])
    _isolation(host, after)
