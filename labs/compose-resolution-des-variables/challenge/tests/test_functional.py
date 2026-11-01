"""Measure interpolation, container environment and shell precedence."""

from __future__ import annotations

import json
import secrets
import shlex
import time

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-compose-vars"
PROJECT = "dsoxlab-resolution-variables"
IMAGE = "alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _compose(host, args, release=None):
    command = ["env", "-u", "APP_RELEASE", "-u", "IMAGE_REF", "-u", "APP_MODE", "-u", "RUNTIME_ONLY"]
    if release is not None:
        command.append(f"APP_RELEASE={release}")
    command.extend([
        "docker", "compose", "--env-file", f"{ROOT}/deploy.env",
        "-p", PROJECT, "-f", f"{ROOT}/compose.yaml", *args,
    ])
    return host.run(shlex.join(command))


def _expected(host):
    verified = host.run("cd %s && sha256sum -c /root/.lab-compose-vars.sha256", ROOT)
    assert verified.rc == 0, message(
        en="Keep deploy.env, runtime.env and .env unchanged; repair only compose.yaml.",
        fr="Gardez deploy.env, runtime.env et .env inchangés ; réparez seulement compose.yaml.",
    )
    return json.loads(host.file("/root/.lab-compose-vars.json").content_string)


def _container(host):
    found = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={PROJECT}")
    assert found.rc == 0 and len(found.stdout.split()) == 1, message(
        en="Start exactly one container in the dsoxlab-resolution-variables Compose project.",
        fr="Démarrez exactement un conteneur dans le projet Compose dsoxlab-resolution-variables.",
    )
    result = host.run("docker inspect %s", found.stdout.strip())
    assert result.rc == 0, message(
        en="Cannot inspect the project's container.",
        fr="Impossible d'inspecter le conteneur du projet.",
    )
    container = json.loads(result.stdout)[0]
    assert container["State"]["Running"] and container["Config"]["Labels"].get("com.docker.compose.service") == "app", message(
        en="The app service must be running and managed by Compose.",
        fr="Le service app doit être démarré et géré par Compose.",
    )
    image = host.run("docker image inspect %s --format %s", IMAGE, "{{.Id}}")
    assert image.rc == 0 and container["Image"] == image.stdout.strip() and not container["Mounts"], message(
        en="Use the supplied pinned Alpine image without replacement mounts.",
        fr="Utilisez l'image Alpine épinglée fournie sans montages de remplacement.",
    )
    return container


def _runtime(host, release, runtime_only):
    container = _container(host)
    env = dict(item.split("=", 1) for item in container["Config"]["Env"])
    assert all(env.get(key) == value for key, value in {
        "APP_RELEASE": release, "APP_MODE": "production", "RUNTIME_ONLY": runtime_only,
    }.items()), message(
        en="The actual container environment must combine the resolved release, production override and runtime-only value.",
        fr="L'environnement réel doit réunir la release résolue, la surcharge production et la valeur propre au runtime.",
    )
    for _ in range(20):
        report = host.run("docker exec %s cat /tmp/report", container["Id"])
        if report.rc == 0:
            break
        time.sleep(0.1)
    assert report.rc == 0 and report.stdout.strip() == f"production:{release}:{runtime_only}", message(
        en="The startup report must expand variables inside the container, not prematurely in Compose.",
        fr="Le rapport au démarrage doit développer les variables dans le conteneur, pas prématurément dans Compose.",
    )
    return container


def test_explicit_deployment_file_resolves_the_image_and_release(host):
    _container(host)
    expected = _expected(host)
    result = _compose(host, ["config", "--format", "json"])
    assert result.rc == 0, message(
        en=f"Compose must resolve the declaration with deploy.env: {result.stderr[-600:]}",
        fr=f"Compose doit résoudre la déclaration avec deploy.env : {result.stderr[-600:]}",
    )
    services = json.loads(result.stdout)["services"]
    assert set(services) == {"app"} and services["app"]["image"] == IMAGE and services["app"]["environment"].get("APP_RELEASE") == expected["release"], message(
        en="Resolve IMAGE_REF and APP_RELEASE from deploy.env instead of the implicit .env or literal values.",
        fr="Résolvez IMAGE_REF et APP_RELEASE depuis deploy.env plutôt que depuis .env ou des valeurs littérales.",
    )


def test_runtime_environment_and_startup_expansion(host):
    expected = _expected(host)
    _runtime(host, expected["release"], expected["runtime_only"])


def test_shell_release_wins_and_recreation_restores_the_baseline(host):
    expected = _expected(host)
    before = _runtime(host, expected["release"], expected["runtime_only"])
    alternate = f"shell-{secrets.token_hex(16)}"
    try:
        result = _compose(host, ["up", "-d", "--force-recreate", "--no-build", "--pull", "never"], alternate)
        assert result.rc == 0, message(
            en=f"Recreation with a shell override must succeed: {result.stderr[-600:]}",
            fr=f"La recréation avec surcharge du shell doit réussir : {result.stderr[-600:]}",
        )
        after = _runtime(host, alternate, expected["runtime_only"])
        assert before["Id"] != after["Id"], message(
            en="Compose must recreate the container with the alternate release.",
            fr="Compose doit recréer le conteneur avec la release alternative.",
        )
    finally:
        restored = _compose(host, ["up", "-d", "--force-recreate", "--no-build", "--pull", "never"])
        assert restored.rc == 0, message(
            en=f"Cannot restore the deployment after the precedence trial: {restored.stderr[-600:]}",
            fr=f"Impossible de restaurer le déploiement après l'essai de priorité : {restored.stderr[-600:]}",
        )
        _runtime(host, expected["release"], expected["runtime_only"])
