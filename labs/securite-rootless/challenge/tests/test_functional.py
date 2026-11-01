"""Verify the dedicated Docker daemon runs in rootless mode."""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_dedicated_daemon_is_active_and_rootless(host):
    state_file = host.file("/opt/dsoxlab-securite-rootless/state.json")
    assert state_file.exists, message(
        en="The prepared rootless daemon state is missing.",
        fr="L'état préparé du démon rootless est absent.",
    )
    state = json.loads(state_file.content_string)
    service = host.run("systemctl is-active dsoxlab-rootless.service")
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
