"""Measure a service-scoped file secret without exposing its content."""

from __future__ import annotations

import hashlib
import json
import secrets
import shlex
import time

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-compose-secret"
PROJECT = "dsoxlab-compose-secrets"
TOKEN = f"{ROOT}/credentials/token.txt"
BASE = "alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _compose(host, *args):
    return host.run(shlex.join(["docker", "compose", "-p", PROJECT, "-f", f"{ROOT}/compose.yaml", *args]))


def _services(host):
    found = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={PROJECT}")
    assert found.rc == 0 and len(found.stdout.split()) == 2, message(
        en="Start exactly app and observer in project dsoxlab-compose-secrets.",
        fr="Démarrez exactement app et observer dans le projet dsoxlab-compose-secrets.",
    )
    result = host.run(shlex.join(["docker", "inspect", *found.stdout.split()]))
    assert result.rc == 0, message(
        en="Cannot inspect the secret consumers.",
        fr="Impossible d'inspecter les consommateurs du secret.",
    )
    services = {c["Config"]["Labels"].get("com.docker.compose.service"): c for c in json.loads(result.stdout)}
    assert set(services) == {"app", "observer"} and all(c["State"]["Running"] for c in services.values()), message(
        en="Both app and observer must run.",
        fr="App et observer doivent être démarrés.",
    )
    for name, reference in (("app", "dsoxlab-compose-secret:app"), ("observer", BASE)):
        image = host.run("docker image inspect %s", reference)
        assert image.rc == 0, message(
            en=f"Keep the supplied image for {name}.",
            fr=f"Gardez l'image fournie pour {name}.",
        )
        original = json.loads(image.stdout)[0]
        assert services[name]["Image"] == original["Id"] and not services[name]["Config"]["Entrypoint"], message(
            en=f"Use the supplied {name} image without replacing its entrypoint.",
            fr=f"Utilisez l'image {name} fournie sans remplacer son entrypoint.",
        )
        if name == "app":
            assert services[name]["Config"]["Cmd"] == original["Config"]["Cmd"], message(
                en="Keep the supplied secret consumer command.",
                fr="Gardez la commande fournie de consommation du secret.",
            )
    return services, result.stdout


def _fingerprint(host, app, expected):
    for _ in range(20):
        result = host.run("docker exec %s cat /tmp/fingerprint", app["Id"])
        if result.rc == 0:
            break
        time.sleep(0.1)
    assert result.rc == 0 and result.stdout.strip() == expected, message(
        en="The app must consume the current mounted secret at startup.",
        fr="L'application doit consommer le secret actuellement monté au démarrage.",
    )


def test_compose_grants_the_file_secret_only_to_app(host):
    services, _ = _services(host)
    config = _compose(host, "config", "--format", "json")
    assert config.rc == 0, message(
        en="The Compose declaration must resolve.",
        fr="La déclaration Compose doit être résolue.",
    )
    resolved = json.loads(config.stdout)
    assert resolved.get("secrets", {}).get("api_token", {}).get("file") == TOKEN and [
        s["source"] for s in resolved["services"]["app"].get("secrets", [])
    ] == ["api_token"] and not resolved["services"]["observer"].get("secrets"), message(
        en="Declare the file-backed api_token secret and grant it only to app.",
        fr="Déclarez le secret fichier api_token et accordez-le seulement à app.",
    )
    mounts = services["app"]["Mounts"]
    assert len(mounts) == 1 and mounts[0]["Source"] == TOKEN and mounts[0]["Destination"] == "/run/secrets/api_token" and not mounts[0]["RW"] and not services["observer"]["Mounts"], message(
        en="Mount only the read-only token file for app; observer must have no mounts.",
        fr="Montez seulement le fichier jeton en lecture seule pour app ; observer ne doit avoir aucun montage.",
    )
    denied = host.run("docker exec %s test -e /run/secrets/api_token", services["observer"]["Id"])
    assert denied.rc == 1, message(
        en="Observer must not see the secret file.",
        fr="Observer ne doit pas voir le fichier secret.",
    )


def test_secret_is_consumed_without_metadata_or_log_leaks(host):
    services, metadata = _services(host)
    token = host.file(TOKEN).content_string
    expected = host.file("/root/.lab-compose-secret.sha256").content_string.strip()
    assert hashlib.sha256(token.encode()).hexdigest() == expected, message(
        en="Keep the supplied pedagogical token unchanged.",
        fr="Gardez le jeton pédagogique fourni inchangé.",
    )
    _fingerprint(host, services["app"], expected)
    config = _compose(host, "config", "--format", "json")
    assert config.rc == 0, message(
        en="Cannot render the configuration for the leak check.",
        fr="Impossible de rendre la configuration pour le contrôle de fuite.",
    )
    for container in services.values():
        logs = host.run("docker logs %s", container["Id"])
        assert logs.rc == 0 and token.strip() not in metadata + config.stdout + logs.stdout + logs.stderr, message(
            en="Do not put the token in environment, labels, commands, rendered configuration or logs.",
            fr="Ne placez pas le jeton dans l'environnement, les labels, les commandes, la configuration rendue ou les journaux.",
        )


def test_recreation_consumes_a_rotated_secret_then_restores_it(host):
    services, _ = _services(host)
    original = host.file(TOKEN).content_string
    rotated = secrets.token_hex(32) + "\n"
    try:
        written = host.run("printf %s > %s", rotated, TOKEN)
        assert written.rc == 0, message(
            en="Cannot prepare the controlled token rotation.",
            fr="Impossible de préparer la rotation contrôlée du jeton.",
        )
        result = _compose(host, "up", "-d", "--force-recreate", "--no-build", "--pull", "never")
        assert result.rc == 0, message(
            en=f"Recreation with the rotated token must succeed: {result.stderr[-500:]}",
            fr=f"La recréation avec le jeton renouvelé doit réussir : {result.stderr[-500:]}",
        )
        after, _ = _services(host)
        assert services["app"]["Id"] != after["app"]["Id"], message(
            en="Recreate the consumer to read the rotated token.",
            fr="Recréez le consommateur pour lire le jeton renouvelé.",
        )
        _fingerprint(host, after["app"], hashlib.sha256(rotated.encode()).hexdigest())
    finally:
        restored = host.run("printf %s > %s", original, TOKEN)
        assert restored.rc == 0, message(
            en="Cannot restore the token file.",
            fr="Impossible de restaurer le fichier jeton.",
        )
        result = _compose(host, "up", "-d", "--force-recreate", "--no-build", "--pull", "never")
        assert result.rc == 0, message(
            en="Cannot restart the consumer with the original token.",
            fr="Impossible de redémarrer le consommateur avec le jeton original.",
        )
        after, _ = _services(host)
        _fingerprint(host, after["app"], hashlib.sha256(original.encode()).hexdigest())
