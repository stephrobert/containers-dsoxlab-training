"""Verify bounded log retention on the dedicated service container."""

from __future__ import annotations

import json
import shlex

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_service_container_has_bounded_json_file_logs(host):
    inspected = host.run(shlex.join(["docker", "inspect", "dsoxlab-log-rotation"]))
    assert inspected.rc == 0, message(
        en="The labelled demonstration service is missing.",
        fr="Le service de démonstration étiqueté est absent.",
    )
    container = json.loads(inspected.stdout)[0]
    assert container["State"]["Running"], message(
        en="The demonstration service must remain running.",
        fr="Le service de démonstration doit rester actif.",
    )
    assert container["Config"]["Labels"].get("dsoxlab.lab") == "docker-rotation-des-journaux", message(
        en="Keep the lab ownership label on the service.",
        fr="Conservez le label de propriété du lab sur le service.",
    )
    log_config = container["HostConfig"]["LogConfig"]
    assert log_config["Type"] == "json-file", message(
        en="Use the json-file driver for this service.",
        fr="Utilisez le pilote json-file pour ce service.",
    )
    assert log_config["Config"].get("max-size") == "1k", message(
        en="Cap each service log file at 1k.",
        fr="Plafonnez chaque fichier de journal du service à 1k.",
    )
    assert log_config["Config"].get("max-file") == "3", message(
        en="Retain three service log files.",
        fr="Conservez trois fichiers de journal du service.",
    )
