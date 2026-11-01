"""Verify that the audit account remains but loses Docker group access."""

from __future__ import annotations

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_auditor_exists_without_docker_group_membership(host):
    account = host.run("getent passwd dsoxlab-auditor")
    assert account.rc == 0, message(
        en="Keep the dedicated dsoxlab-auditor account.",
        fr="Conservez le compte dédié dsoxlab-auditor.",
    )
    groups = host.run("id -Gn dsoxlab-auditor")
    assert groups.rc == 0 and "docker" not in groups.stdout.split(), message(
        en="Remove only dsoxlab-auditor from the privileged docker group.",
        fr="Retirez uniquement dsoxlab-auditor du groupe privilégié docker.",
    )
