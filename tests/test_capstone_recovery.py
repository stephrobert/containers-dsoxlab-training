"""Recovery requires both business readiness and effective Docker health."""

from __future__ import annotations

import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def capstone():
    return runpy.run_path(str(
        ROOT / "labs/capstone-chaine-complete/challenge/tests/test_functional.py"
    ))


def test_recovery_waits_for_docker_health_after_http_recovers(capstone, monkeypatch):
    inspections = []

    def run(command, *args):
        if command.startswith("docker ps"):
            return SimpleNamespace(rc=0, stdout="api-id db-id")
        if command.startswith("docker inspect"):
            inspections.append(True)
            containers = [
                {
                    "Config": {"Labels": {"com.docker.compose.service": service}},
                    "State": {
                        "Running": True,
                        "Health": {"Status": "starting" if len(inspections) == 1 else "healthy"},
                    },
                }
                for service in ("api", "db")
            ]
            return SimpleNamespace(rc=0, stdout=json.dumps(containers))
        raise AssertionError(f"Unexpected command: {command}")

    globals_ = capstone["_wait_ready"].__globals__
    monkeypatch.setitem(
        globals_, "_request",
        lambda *_: SimpleNamespace(rc=0, stdout='{"ready": true}'),
    )
    monkeypatch.setattr(globals_["time"], "sleep", lambda _: None)
    capstone["_wait_ready"](SimpleNamespace(run=run))
    assert len(inspections) == 2


@pytest.mark.parametrize("running,health,ready", [
    (True, "unhealthy", True),
    (False, "healthy", True),
    (True, "healthy", False),
])
def test_recovery_refuses_incomplete_recovery_within_a_bounded_wait(
    capstone, monkeypatch, running, health, ready,
):
    containers = [
        {
            "Config": {"Labels": {"com.docker.compose.service": service}},
            "State": {"Running": running, "Health": {"Status": health}},
        }
        for service in ("api", "db")
    ]

    def run(command, *args):
        if command.startswith("docker ps"):
            return SimpleNamespace(rc=0, stdout="api-id db-id")
        if command.startswith("docker inspect"):
            return SimpleNamespace(rc=0, stdout=json.dumps(containers))
        raise AssertionError(f"Unexpected command: {command}")

    globals_ = capstone["_wait_ready"].__globals__
    monkeypatch.setitem(
        globals_, "_request",
        lambda *_: SimpleNamespace(rc=0, stdout=json.dumps({"ready": ready})),
    )
    clock = iter([0, 21])
    monkeypatch.setattr(globals_["time"], "monotonic", lambda: next(clock))
    with pytest.raises(AssertionError, match="Both services must be healthy"):
        capstone["_wait_ready"](SimpleNamespace(run=run))
