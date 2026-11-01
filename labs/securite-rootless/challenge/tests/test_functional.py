"""Verify the dedicated Docker daemon runs in rootless mode."""

from __future__ import annotations

import json
import shlex
import time
import uuid

import pytest

from conftest import lab_host, message

IMAGE = "python:3.13.8-slim-bookworm@sha256:61169c2bdb8e6bb44a8dfad33f569d324d52f079fded9a204b322a6fb9c9f799"


def _user_systemctl(host, state, *args):
    return host.run(shlex.join([
        "sudo", "-n", "-u", "dsoxlab-rootless", "env",
        f"XDG_RUNTIME_DIR=/run/user/{state['uid']}",
        f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{state['uid']}/bus",
        "systemctl", "--user", *args,
    ]))


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _rootless_state(host):
    state_file = host.file("/opt/dsoxlab-securite-rootless/state.json")
    assert state_file.exists, message(
        en="The prepared rootless daemon state is missing.",
        fr="L'état préparé du démon rootless est absent.",
    )
    state = json.loads(state_file.content_string)
    service = _user_systemctl(host, state, "is-active", "dsoxlab-rootless.service")
    assert service.rc == 0 and service.stdout.strip() == "active", message(
        en="Start the dedicated dsoxlab-rootless service.",
        fr="Démarrez le service dédié dsoxlab-rootless.",
    )
    info = host.run(
        "docker -H unix://%s info --format '{{json .SecurityOptions}}'",
        state["socket"],
    )
    assert info.rc == 0, message(
        en=f"The rootless Docker socket is not responding: {info.stderr[-500:]}",
        fr=f"Le socket Docker rootless ne répond pas : {info.stderr[-500:]}",
    )
    security_options = json.loads(info.stdout)
    assert any("rootless" in option.lower() for option in security_options), message(
        en="The dedicated daemon must report rootless mode.",
        fr="Le démon dédié doit indiquer le mode rootless.",
    )
    return state


def test_dedicated_daemon_is_active_and_rootless(host):
    state = _rootless_state(host)
    process = _user_systemctl(host, state, "show", "dsoxlab-rootless.service", "--property", "MainPID", "--value")
    account = host.run("id -u dsoxlab-rootless")
    owner = host.run("ps -o uid= -p %s", process.stdout.strip())
    assert process.rc == account.rc == owner.rc == 0 and (
        owner.stdout.strip() == account.stdout.strip() != "0"
    ), message(
        en="The real service process must belong to the dedicated unprivileged account.",
        fr="Le processus réel du service doit appartenir au compte non privilégié dédié.",
    )


def test_rootless_network_and_data_survive_container_recreation(host):
    state = _rootless_state(host)

    def docker(*args):
        return host.run(shlex.join(["docker", "-H", f"unix://{state['socket']}", *args]))

    loaded = host.run(
        "docker image save %s | docker -H unix://%s image load", IMAGE, state["socket"],
    )
    assert loaded.rc == 0, message(
        en="Load the pinned workload into the separate rootless image store.",
        fr="Chargez l'image épinglée dans le stockage distinct du moteur rootless.",
    )
    image = host.run("docker image inspect %s --format '{{.Id}}'", IMAGE)
    assert image.rc == 0 and image.stdout.strip().startswith("sha256:"), message(
        en="Identify the exact pinned image loaded into the rootless engine.",
        fr="Identifiez l'image épinglée exacte chargée dans le moteur rootless.",
    )
    image_id = image.stdout.strip()
    suffix = uuid.uuid4().hex[:12]
    name = f"dsoxlab-rootless-check-{suffix}"
    network = name + "-net"
    volume = name + "-data"
    marker = uuid.uuid4().hex
    network_created = False
    volume_created = False
    try:
        created_network = docker("network", "create", network)
        network_created = created_network.rc == 0
        assert network_created, message(
            en="The rootless daemon must create its own network.",
            fr="Le démon rootless doit créer son propre réseau.",
        )
        created_volume = docker("volume", "create", volume)
        volume_created = created_volume.rc == 0
        assert volume_created, message(
            en="The rootless daemon must create its own named volume.",
            fr="Le démon rootless doit créer son propre volume nommé.",
        )
        written = docker(
            "run", "--rm", "--network", "none", "-v", f"{volume}:/data", image_id,
            "python", "-c", f"from pathlib import Path; Path('/data/value').write_text({marker!r})",
        )
        assert written.rc == 0, message(
            en="Write a fresh value through a container on the rootless daemon.",
            fr="Écrivez une valeur nouvelle avec un conteneur du démon rootless.",
        )
        for _ in range(2):
            started = docker(
                "run", "-d", "--name", name, "--network", network,
                "--network-alias", "rootless-server", "-p", "127.0.0.1::8080",
                "-v", f"{volume}:/data:ro", image_id, "python", "-m", "http.server",
                "8080", "--bind", "0.0.0.0", "--directory", "/data",  # noqa: S104 -- Inside the container; the VM publication is loopback-only.
            )
            assert started.rc == 0, message(
                en="Start the rootless HTTP workload on a nonprivileged loopback port.",
                fr="Démarrez le service HTTP rootless sur un port loopback non privilégié.",
            )
            port = docker("port", name, "8080/tcp")
            assert port.rc == 0 and port.stdout.strip().startswith("127.0.0.1:"), message(
                en="Rootless publication must stay on loopback.",
                fr="La publication rootless doit rester sur la boucle locale.",
            )
            request = (
                "import urllib.request;"
                f"print(urllib.request.urlopen('http://{port.stdout.strip()}/value',timeout=2).read().decode())"
            )
            for _attempt in range(30):
                response = host.run(shlex.join(["python3", "-c", request]))
                if response.rc == 0:
                    break
                time.sleep(0.2)
            assert response.rc == 0 and response.stdout.strip() == marker, message(
                en="Loopback HTTP must serve the persistent fresh value after each recreation.",
                fr="HTTP sur la boucle locale doit servir la valeur persistante après chaque recréation.",
            )
            program = (
                "import urllib.request;"
                "print(urllib.request.urlopen('http://rootless-server:8080/value',timeout=3).read().decode())"
            )
            peer = docker("run", "--rm", "--network", network, image_id, "python", "-c", program)
            denied = docker("run", "--rm", "--network", "none", image_id, "python", "-c", program)
            assert peer.rc == 0 and peer.stdout.strip() == marker and denied.rc != 0, message(
                en="An authorized rootless network peer succeeds; a networkless peer is refused.",
                fr="Un pair du réseau rootless réussit ; un pair sans réseau est refusé.",
            )
            removed = docker("rm", "-f", name)
            assert removed.rc == 0, message(
                en="Remove only the trial container while preserving its named volume.",
                fr="Retirez seulement le conteneur d'essai en gardant son volume nommé.",
            )
    finally:
        if docker("container", "inspect", name).rc == 0:
            removed = docker("rm", "-f", name)
            assert removed.rc == 0, message(
                en="Remove the remaining rootless trial container.",
                fr="Retirez le conteneur rootless d'essai restant.",
            )
        for kind, name, created in [
            ("volume", volume, volume_created), ("network", network, network_created),
        ]:
            if created:
                removed = docker(kind, "rm", name)
                assert removed.rc == 0, message(
                    en="Remove each created rootless trial object without touching other objects.",
                    fr="Retirez chaque objet rootless d'essai créé sans toucher aux autres objets.",
                )
