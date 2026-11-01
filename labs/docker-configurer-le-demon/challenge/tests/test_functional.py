"""Verify daemon log defaults on newly created containers."""

from __future__ import annotations

import json
import shlex
import uuid

import pytest

from conftest import lab_host, message

IMAGE = "alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_new_containers_use_bounded_json_file_logs(host):
    name = f"dsoxlab-log-defaults-{uuid.uuid4().hex[:12]}"
    created = host.run(
        shlex.join(
            [
                "docker",
                "create",
                "--name",
                name,
                "--label",
                "dsoxlab.lab=docker-configurer-le-demon",
                IMAGE,
                "true",
            ]
        )
    )
    assert created.rc == 0, message(
        en=f"Could not create a probe container: {created.stderr[-500:]}",
        fr=f"Impossible de créer le conteneur témoin : {created.stderr[-500:]}",
    )
    try:
        inspected = host.run(shlex.join(["docker", "inspect", name]))
        assert inspected.rc == 0, message(
            en="Could not inspect the newly created probe container.",
            fr="Impossible d'inspecter le nouveau conteneur témoin.",
        )
        log_config = json.loads(inspected.stdout)[0]["HostConfig"]["LogConfig"]
        assert log_config["Type"] == "json-file", message(
            en="New containers must use the json-file logging driver.",
            fr="Les nouveaux conteneurs doivent utiliser le pilote json-file.",
        )
        assert log_config["Config"].get("max-size") == "1m", message(
            en="Set the default log-file size to 1m.",
            fr="Réglez la taille par défaut des journaux à 1m.",
        )
        assert log_config["Config"].get("max-file") == "2", message(
            en="Retain two log files by default.",
            fr="Conservez deux fichiers de journal par défaut.",
        )
    finally:
        host.run(shlex.join(["docker", "rm", "--force", name]))
