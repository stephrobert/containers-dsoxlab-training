"""Verify that the application no longer receives the host Docker socket."""

from __future__ import annotations

import json
import shlex

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_application_container_has_no_host_docker_socket_mount(host):
    inspected = host.run(shlex.join(["docker", "inspect", "dsoxlab-socket-readonly"]))
    assert inspected.rc == 0, message(
        en="The labelled application container is missing.",
        fr="Le conteneur applicatif étiqueté est absent.",
    )
    container = json.loads(inspected.stdout)[0]
    assert container["State"]["Running"], message(
        en="Keep the application container running after removing the socket bind.",
        fr="Laissez le conteneur applicatif actif après le retrait du montage du socket.",
    )
    assert container["Config"]["Labels"].get("dsoxlab.lab") == "securite-socket-lecture-seule", message(
        en="Keep the lab ownership label on the application container.",
        fr="Conservez le label de propriété du lab sur le conteneur applicatif.",
    )
    socket_mounts = [
        mount
        for mount in container["Mounts"]
        if mount["Source"] == "/var/run/docker.sock"
        or mount["Destination"] == "/var/run/docker.sock"
    ]
    assert not socket_mounts, message(
        en="Remove the host Docker socket mount entirely; read-only does not make its API safe.",
        fr="Retirez entièrement le montage du socket Docker hôte ; le mode lecture seule ne sécurise pas son API.",
    )
