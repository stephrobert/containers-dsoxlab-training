"""Measure readiness separately from liveness and dependency gating."""

from __future__ import annotations

import json
import shlex
import time

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-compose-health"
PROJECT = "dsoxlab-health"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _compose(host, args, project=PROJECT, override=False):
    command = ["docker", "compose", "-p", project, "-f", f"{ROOT}/compose.yaml"]
    if override:
        command += ["-f", f"{ROOT}/trial.yaml"]
    return host.run(shlex.join([*command, *args]))


def _services(host, project=PROJECT):
    found = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={project}")
    assert found.rc == 0 and len(found.stdout.split()) == 2, message(
        en="Create exactly backend and app in the Compose health project.",
        fr="Créez exactement backend et app dans le projet Compose de santé.",
    )
    result = host.run(shlex.join(["docker", "inspect", *found.stdout.split()]))
    assert result.rc == 0, message(
        en="Cannot inspect the health project.",
        fr="Impossible d'inspecter le projet de santé.",
    )
    services = {c["Config"]["Labels"].get("com.docker.compose.service"): c for c in json.loads(result.stdout)}
    assert set(services) == {"app", "backend"}, message(
        en="Name the services app and backend.",
        fr="Nommez les services app et backend.",
    )
    for name, container in services.items():
        image = host.run("docker image inspect %s", f"dsoxlab-compose-health:{name}")
        assert image.rc == 0, message(
            en=f"Keep the supplied {name} image.",
            fr=f"Gardez l'image {name} fournie.",
        )
        original = json.loads(image.stdout)[0]
        assert container["Image"] == original["Id"] and not container["Mounts"] and all(
            container["Config"][key] == original["Config"][key] for key in ("Cmd", "Entrypoint")
        ) and container["HostConfig"]["RestartPolicy"]["Name"] == "no", message(
            en="Use supplied images and commands without mounts or restart policies hiding startup failures.",
            fr="Gardez les images et commandes sans montages ni redémarrages masquant les échecs de démarrage.",
        )
    return services


def _health(host, backend, expected):
    for _ in range(60):
        result = host.run("docker inspect %s", backend["Id"])
        assert result.rc == 0, message(
            en="Cannot inspect the backend health state.",
            fr="Impossible d'inspecter la santé du backend.",
        )
        container = json.loads(result.stdout)[0]
        if container["State"].get("Health", {}).get("Status") == expected:
            return container
        time.sleep(0.5)
    pytest.fail(message(
        en=f"Backend health must become {expected} within 30 seconds.",
        fr=f"La santé du backend doit devenir {expected} sous 30 secondes.",
    ))


def _ready(host, services):
    _health(host, services["backend"], "healthy")
    assert all(c["State"]["Running"] for c in services.values()), message(
        en="Both services must run after backend readiness.",
        fr="Les deux services doivent tourner après disponibilité du backend.",
    )
    observed = host.run("docker exec %s cat /tmp/observed", services["app"]["Id"])
    assert observed.rc == 0 and observed.stdout.strip() == "ready", message(
        en="App must successfully consume the readiness endpoint at startup.",
        fr="App doit consommer le point de disponibilité avec succès au démarrage.",
    )


def test_backend_health_and_successful_readiness_dependency(host):
    _ready(host, _services(host))
    config = _compose(host, ["config", "--format", "json"])
    assert config.rc == 0, message(
        en="The Compose declaration must resolve.",
        fr="La déclaration Compose doit être résolue.",
    )
    app = json.loads(config.stdout)["services"]["app"]
    assert app.get("depends_on", {}).get("backend", {}).get("condition") == "service_healthy", message(
        en="Gate app on backend with service_healthy.",
        fr="Conditionnez app à backend avec service_healthy.",
    )


def test_unready_backend_becomes_unhealthy_while_http_stays_alive(host):
    services = _services(host)
    _ready(host, services)
    backend = services["backend"]
    try:
        removed = host.run("docker exec %s rm /www/ready", backend["Id"])
        assert removed.rc == 0, message(
            en="Cannot simulate loss of readiness.",
            fr="Impossible de simuler la perte de disponibilité.",
        )
        unhealthy = _health(host, backend, "unhealthy")
        live = host.run("docker exec %s wget -T 2 -qO- http://127.0.0.1:8080/live", backend["Id"])
        assert unhealthy["State"]["Running"] and live.rc == 0 and live.stdout.strip() == "alive", message(
            en="Loss of readiness must be detected even while the process and HTTP liveness remain available.",
            fr="La perte de disponibilité doit être détectée même si le processus et la sonde de vie HTTP répondent.",
        )
    finally:
        restored = host.run("docker exec %s sh -c %s", backend["Id"], "printf 'ready\\n' > /www/ready")
        assert restored.rc == 0, message(
            en="Cannot restore backend readiness.",
            fr="Impossible de restaurer la disponibilité du backend.",
        )
        _health(host, backend, "healthy")


def test_slow_and_never_ready_backends_gate_fresh_application_startup(host):
    _ready(host, _services(host))
    for project, blocked in (("dsoxlab-health-cold", False), ("dsoxlab-health-blocked", True)):
        config = _compose(host, ["config", "--format", "json"], project)
        assert config.rc == 0, message(
            en="The trial configuration must resolve.",
            fr="La configuration d'essai doit être résolue.",
        )
        resolved = json.loads(config.stdout)
        assert not resolved.get("volumes") and all(n.get("name", "").startswith(project + "_") and not n.get("external") for n in resolved.get("networks", {}).values()) and all(
            not s.get("container_name") and not s.get("ports") for s in resolved["services"].values()
        ), message(
            en="Keep the exercise internal and project-scoped so cold trials cannot collide with the running application.",
            fr="Gardez l'exercice interne et propre au projet pour isoler les essais à froid de l'application active.",
        )
        try:
            written = host.run("printf %s > %s", f"services:\n  backend:\n    environment:\n      START_DELAY: '8'\n      BLOCK_READY: '{int(blocked)}'\n", f"{ROOT}/trial.yaml")
            assert written.rc == 0, message(
                en="Cannot prepare the controlled readiness trial.",
                fr="Impossible de préparer l'essai contrôlé de disponibilité.",
            )
            result = _compose(host, ["up", "-d", "--no-build", "--pull", "never"], project, True)
            services = _services(host, project)
            if blocked:
                assert result.rc != 0 and services["app"]["State"]["Status"] == "created", message(
                    en="A never-ready backend must prevent app from ever starting.",
                    fr="Un backend jamais disponible doit empêcher tout démarrage de app.",
                )
            else:
                assert result.rc == 0, message(
                    en=f"Startup must wait for the slower backend: {result.stderr[-500:]}",
                    fr=f"Le démarrage doit attendre le backend plus lent : {result.stderr[-500:]}",
                )
                _ready(host, services)
        finally:
            cleaned = _compose(host, ["down", "--remove-orphans"], project, True)
            removed = host.run("rm -f %s", f"{ROOT}/trial.yaml")
            assert cleaned.rc == removed.rc == 0, message(
                en="Cannot remove the isolated readiness trial.",
                fr="Impossible de retirer l'essai de disponibilité isolé.",
            )
