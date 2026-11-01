"""Prove service discovery and recreation of the declared Compose project."""

from __future__ import annotations

import json
import secrets
import shlex

import pytest

from conftest import lab_host, message

PROJECT = "dsoxlab-premiere-stack"
COMPOSE = "/opt/lab-compose-first/compose.yaml"
URL = "http://127.0.0.1:18086/cgi-bin/release"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _services(host):
    result = host.run(
        "docker container ls -aq --filter %s", f"label=com.docker.compose.project={PROJECT}"
    )
    assert result.rc == 0 and len(result.stdout.split()) == 2, message(
        en="Start exactly two services in the dsoxlab-premiere-stack Compose project.",
        fr="Démarrez exactement deux services dans le projet Compose dsoxlab-premiere-stack.",
    )
    inspected = host.run(shlex.join(["docker", "inspect", *result.stdout.split()]))
    assert inspected.rc == 0, message(
        en="Cannot inspect the Compose project's containers.",
        fr="Impossible d'inspecter les conteneurs du projet Compose.",
    )
    containers = json.loads(inspected.stdout)
    services = {c["Config"]["Labels"].get("com.docker.compose.service"): c for c in containers}
    assert set(services) == {"api", "web"} and all(c["State"]["Running"] for c in containers), message(
        en="The Compose project must contain running api and web services.",
        fr="Le projet Compose doit contenir les services api et web démarrés.",
    )
    for name, container in services.items():
        image = host.run("docker image inspect %s", f"dsoxlab-compose-first:{name}")
        assert image.rc == 0, message(
            en=f"Cannot inspect the supplied image for {name}.",
            fr=f"Impossible d'inspecter l'image fournie pour {name}.",
        )
        original = json.loads(image.stdout)[0]
        assert container["Image"] == original["Id"] and not container["Mounts"] and all(
            container["Config"][key] == original["Config"][key] for key in ("Cmd", "Entrypoint")
        ), message(
            en=f"Service {name} must run its supplied image without overriding the product.",
            fr=f"Le service {name} doit exécuter son image fournie sans remplacer le produit.",
        )
    return services


def _release(host):
    return json.loads(host.file("/root/.lab-compose-first.json").content_string)["release"]


def _response(host, expected):
    result = host.run(
        "curl --noproxy '*' --fail --silent --show-error --retry 10 --retry-connrefused --retry-delay 1 --max-time 3 %s",
        URL,
    )
    assert result.rc == 0 and result.stdout.strip() == expected, message(
        en=f"The web endpoint must relay the live API release: {result.stdout[-200:]} {result.stderr[-400:]}",
        fr=f"Le point d'accès web doit relayer la release actuelle de l'API : {result.stdout[-200:]} {result.stderr[-400:]}",
    )


def test_two_compose_services_share_a_network_and_only_web_is_published(host):
    services = _services(host)
    common = set(services["api"]["NetworkSettings"]["Networks"]) & set(services["web"]["NetworkSettings"]["Networks"])
    assert common - {"host", "none", "bridge"}, message(
        en="The services must share a user-defined network with service DNS.",
        fr="Les services doivent partager un réseau dédié avec DNS de services.",
    )
    bindings = services["web"]["HostConfig"]["PortBindings"].get("8080/tcp", [])
    assert bindings == [{"HostIp": "127.0.0.1", "HostPort": "18086"}], message(
        en="Publish only web's port 8080 on 127.0.0.1:18086.",
        fr="Publiez seulement le port 8080 de web sur 127.0.0.1:18086.",
    )
    assert not services["api"]["HostConfig"]["PortBindings"], message(
        en="Keep the API internal; it must not publish host ports.",
        fr="Gardez l'API interne ; elle ne doit publier aucun port hôte.",
    )
    _response(host, _release(host))


def test_web_relays_live_api_content_through_service_discovery(host):
    services = _services(host)
    original = _release(host)
    _response(host, original)
    nonce = secrets.token_hex(24)
    try:
        written = host.run(
            "docker exec %s sh -c %s", services["api"]["Id"],
            f"printf '%s\\n' {shlex.quote(nonce)} > /www/release.txt",
        )
        assert written.rc == 0, message(
            en="Cannot change the live API release for the service-discovery trial.",
            fr="Impossible de changer la release de l'API active pour l'essai DNS.",
        )
        _response(host, nonce)
    finally:
        restored = host.run(
            "docker exec %s sh -c %s", services["api"]["Id"],
            f"printf '%s\\n' {shlex.quote(original)} > /www/release.txt",
        )
        assert restored.rc == 0, message(
            en="Cannot restore the API release after the trial.",
            fr="Impossible de restaurer la release de l'API après l'essai.",
        )


def test_the_declaration_recreates_both_services_without_manual_steps(host):
    before = _services(host)
    assert host.file(COMPOSE).is_file, message(
        en=f"Write the reusable declaration at {COMPOSE}.",
        fr=f"Écrivez la déclaration réutilisable dans {COMPOSE}.",
    )
    recreated = host.run(
        "docker compose -p %s -f %s up -d --force-recreate --no-build --pull never", PROJECT, COMPOSE,
    )
    assert recreated.rc == 0, message(
        en=f"Compose must recreate the application from the declaration: {recreated.stderr[-600:]}",
        fr=f"Compose doit recréer l'application depuis sa déclaration : {recreated.stderr[-600:]}",
    )
    after = _services(host)
    assert all(before[name]["Id"] != after[name]["Id"] for name in before), message(
        en="Both services must be recreated by Compose, not just left running.",
        fr="Les deux services doivent être recréés par Compose, pas seulement laissés démarrés.",
    )
    _response(host, _release(host))
