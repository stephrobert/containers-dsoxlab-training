"""Verify the completed Compose stack and its shared release data."""

from __future__ import annotations

import json
import shlex
import time

import pytest

from conftest import lab_host, message

PROJECT = "dsoxlab-compose-capstone"
COMPOSE = "/opt/lab-compose-capstone/compose.yaml"
PORT = 18092


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _stack(host):
    found = host.run(
        "docker ps -aq --filter label=com.docker.compose.project=%s", PROJECT
    )
    assert found.rc == 0 and len(found.stdout.split()) == 2, message(
        en="Start exactly the writer and web services in the required Compose project.",
        fr="Démarrez exactement les services writer et web dans le projet Compose demandé.",
    )
    services = {}
    for container_id in found.stdout.split():
        inspected = host.run("docker inspect %s", container_id)
        assert inspected.rc == 0, message(
            en="Cannot inspect a Compose service.",
            fr="Impossible d'inspecter un service Compose.",
        )
        container = json.loads(inspected.stdout)[0]
        service = container["Config"]["Labels"].get("com.docker.compose.service")
        assert service in {"writer", "web"} and service not in services, message(
            en="The project must contain one writer and one web service.",
            fr="Le projet doit contenir un service writer et un service web.",
        )
        services[service] = container
    assert set(services) == {"writer", "web"}, message(
        en="The Compose project is missing a required service.",
        fr="Il manque un service requis dans le projet Compose.",
    )
    writer, web = services["writer"], services["web"]
    image = host.run("docker image inspect dsoxlab-compose-capstone:service")
    assert image.rc == 0, message(
        en="Cannot inspect the supplied stack image.",
        fr="Impossible d'inspecter l'image de stack fournie.",
    )
    image_config = json.loads(image.stdout)[0]
    for role, container in services.items():
        environment = dict(item.split("=", 1) for item in container["Config"]["Env"])
        assert container["Image"] == image_config["Id"] and environment.get("ROLE") == role and container["Config"]["Entrypoint"] == image_config["Config"]["Entrypoint"] and container["Config"]["Cmd"] == image_config["Config"]["Cmd"] and not container["HostConfig"]["Privileged"] and not container["HostConfig"]["CapAdd"], message(
            en=f"Keep the supplied image, command and ROLE={role}, without privileged mode or extra capabilities.",
            fr=f"Gardez l'image, la commande fournies et ROLE={role}, sans mode privilégié ni capacité supplémentaire.",
        )
    assert writer["State"]["Status"] == "exited" and writer["State"]["ExitCode"] == 0, message(
        en="The writer must complete successfully before the web service starts.",
        fr="Le service writer doit terminer avec succès avant le démarrage du service web.",
    )
    for _ in range(20):
        web_config = host.run("docker inspect %s", web["Id"])
        assert web_config.rc == 0, message(
            en="Cannot inspect the web healthcheck.",
            fr="Impossible d'inspecter la sonde de santé web.",
        )
        current = json.loads(web_config.stdout)[0]
        if current["State"].get("Health", {}).get("Status") != "starting":
            break
        time.sleep(1)
    assert current["State"]["Running"] and current["State"].get("Health", {}).get("Status") == "healthy", message(
        en="Keep the web service running and healthy.",
        fr="Gardez le service web démarré et sain.",
    )
    healthcheck = current["Config"]["Healthcheck"]
    assert healthcheck and healthcheck["Test"] != ["NONE"] and healthcheck["Test"][0] != "NONE", message(
        en="Configure a real web healthcheck; a running process alone is not readiness.",
        fr="Configurez une vraie sonde web ; un processus démarré ne suffit pas à prouver la disponibilité.",
    )
    writer_mounts = writer["Mounts"]
    web_mounts = web["Mounts"]
    assert (
        len(writer_mounts) == 1
        and len(web_mounts) == 1
        and writer_mounts[0]["Type"] == "volume"
        and web_mounts[0]["Type"] == "volume"
        and writer_mounts[0]["Destination"] == "/data"
        and web_mounts[0]["Destination"] == "/data"
        and writer_mounts[0]["Name"] == web_mounts[0]["Name"]
        and writer_mounts[0]["RW"]
        and not web_mounts[0]["RW"]
    ), message(
        en="Share one named /data volume; the writer needs write access and web must be read-only.",
        fr="Partagez un volume nommé /data ; writer doit pouvoir écrire et web doit le monter en lecture seule.",
    )
    volume = host.run("docker volume inspect %s", writer_mounts[0]["Name"])
    assert volume.rc == 0 and (
        json.loads(volume.stdout)[0]["Labels"] or {}
    ).get("com.docker.compose.project") == PROJECT, message(
        en="The shared volume must belong to this Compose project.",
        fr="Le volume partagé doit appartenir à ce projet Compose.",
    )
    ports = web["HostConfig"]["PortBindings"].get("8080/tcp", [])
    assert ports == [{"HostIp": "127.0.0.1", "HostPort": str(PORT)}], message(
        en="Publish port 8080 only on 127.0.0.1:18092.",
        fr="Publiez le port 8080 uniquement sur 127.0.0.1:18092.",
    )
    return writer, web


def _release(host):
    state = host.file("/opt/lab-compose-capstone/state.json")
    assert state.exists, message(
        en="The supplied release fixture is missing.",
        fr="Le jeu de données de release fourni est absent.",
    )
    return json.loads(state.content_string)["release"]


def _response(host):
    result = host.run(
        shlex.join(
            [
                "curl",
                "--noproxy",
                "*",
                "-fsS",
                "--max-time",
                "3",
                f"http://127.0.0.1:{PORT}/release.txt",
            ]
        )
    )
    assert result.rc == 0, message(
        en="The published web endpoint must serve the shared release file.",
        fr="Le point d'accès web publié doit servir le fichier release partagé.",
    )
    return result.stdout.strip()


def test_ordered_stack_serves_shared_data_after_web_recreation(host):
    writer, web = _stack(host)
    expected = _release(host)
    assert _response(host) == expected, message(
        en="The endpoint must return the supplied release value written by the writer.",
        fr="Le point d'accès doit renvoyer la valeur fournie et écrite par writer.",
    )
    recreated = host.run(
        shlex.join(
            [
                "docker",
                "compose",
                "-p",
                PROJECT,
                "-f",
                COMPOSE,
                "up",
                "-d",
                "--force-recreate",
                "--no-build",
                "--pull",
                "never",
                "web",
            ]
        )
    )
    assert recreated.rc == 0, message(
        en=f"Recreating only web must succeed: {recreated.stderr[-500:]}",
        fr=f"La recréation de web seul doit réussir : {recreated.stderr[-500:]}",
    )
    after_writer, after_web = _stack(host)
    assert (
        writer["Id"] == after_writer["Id"]
        and web["Id"] != after_web["Id"]
        and _response(host) == expected
    ), message(
        en="Recreating web must keep the writer and preserve its release data in the shared volume.",
        fr="La recréation de web doit conserver writer et les données release du volume partagé.",
    )
