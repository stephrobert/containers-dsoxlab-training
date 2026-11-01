"""Execute the learner's local CI against success, failure and changed source."""

from __future__ import annotations

import json
import shlex
import uuid

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-compose-ci"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _run(host, *, fail=False):
    token = uuid.uuid4().hex[:12]
    project = f"dsoxlab-ci-{token}"
    trial = f"{ROOT}/trials/{token}"
    value = f"release-{token}"
    prepared = host.run(
        "mkdir -p %s/source %s/artifacts && cp %s/source/* %s/source/ && printf '%%s' %s > %s/source/value.txt",
        trial, trial, ROOT, trial, value, trial,
    )
    assert prepared.rc == 0, message(
        en="Cannot prepare the isolated CI trial.", fr="Impossible de préparer l'essai CI isolé.",
    )
    try:
        command = shlex.join([
            "env", f"PROJECT={project}", f"SOURCE_DIR={trial}/source",
            f"ARTIFACT_DIR={trial}/artifacts", f"EXPECTED_VALUE={value}",
            f"TEST_FAIL={int(fail)}", "timeout", "120", f"{ROOT}/ci.sh",
        ])
        result = host.run(command)
        report = host.run("cat %s/artifacts/result.json", trial)
        containers = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={project}")
        networks = host.run("docker network ls -q --filter %s", f"label=com.docker.compose.project={project}")
        assert containers.rc == networks.rc == 0 and not containers.stdout.strip() and not networks.stdout.strip(), message(
            en="The CI must remove its containers and network on success AND failure.",
            fr="La CI doit retirer ses conteneurs et son réseau en succès ET en échec.",
        )
        assert report.rc == 0, message(
            en="Run the supplied test container and retain artifacts/result.json.",
            fr="Exécutez le conteneur de test fourni et conservez artifacts/result.json.",
        )
        data = json.loads(report.stdout)
        assert data.get("observed") == value and data.get("expected") == value, message(
            en="Build and query this trial's changed source, not a cached previous release.",
            fr="Construisez et interrogez la source modifiée de cet essai, pas une ancienne livraison en cache.",
        )
        assert data.get("passed") is (not fail), message(
            en="Preserve the actual test verdict, including TEST_FAIL=1.",
            fr="Conservez le verdict réel du test, y compris TEST_FAIL=1.",
        )
        return result
    finally:
        host.run(
            "docker ps -aq --filter %s | xargs -r docker rm -f; "
            "docker network ls -q --filter %s | xargs -r docker network rm; "
            "docker image ls -q --filter reference=%s | xargs -r docker image rm -f; rm -rf %s",
            f"label=com.docker.compose.project={project}",
            f"label=com.docker.compose.project={project}", f"{project}-api", trial,
        )


def test_success_builds_waits_tests_and_cleans(host):
    result = _run(host)
    assert result.rc == 0, message(
        en="A successful test must yield CI exit code zero.",
        fr="Un test réussi doit donner un code de sortie CI nul.",
    )


def test_failed_test_fails_ci_and_still_cleans(host):
    result = _run(host, fail=True)
    assert result.rc not in (0, 124, 127), message(
        en="Return the failing test's exit status, not success, timeout or a missing command.",
        fr="Retournez le statut du test échoué, pas un succès, un délai expiré ou une commande absente.",
    )


def test_fresh_source_is_rebuilt_on_each_invocation(host):
    for _ in range(2):
        result = _run(host)
        assert result.rc == 0, message(
            en="Repeated CI runs must rebuild changed source and remain independent.",
            fr="Les exécutions répétées doivent reconstruire la source modifiée et rester indépendantes.",
        )
