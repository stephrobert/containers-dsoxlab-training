"""Measure effective cgroup v2 budgets and actual CPU throttling."""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, message

PROJECT = "dsoxlab-ressources"
COMPOSE = "/opt/lab-compose-resources/compose.yaml"
IMAGE = "alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _worker(host):
    found = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={PROJECT}")
    assert found.rc == 0 and len(found.stdout.split()) == 1, message(
        en="Start exactly one worker in Compose project dsoxlab-ressources.",
        fr="Démarrez exactement un worker dans le projet Compose dsoxlab-ressources.",
    )
    result = host.run("docker inspect %s", found.stdout.strip())
    image = host.run("docker image inspect %s --format %s", IMAGE, "{{.Id}}")
    assert result.rc == image.rc == 0, message(
        en="Cannot inspect the worker and supplied image.",
        fr="Impossible d'inspecter le worker et l'image fournie.",
    )
    worker = json.loads(result.stdout)[0]
    assert worker["State"]["Running"] and worker["Config"]["Labels"].get("com.docker.compose.service") == "worker" and worker["Image"] == image.stdout.strip() and not worker["Mounts"] and not worker["HostConfig"]["Privileged"] and not worker["HostConfig"]["CapAdd"] and worker["HostConfig"]["CgroupnsMode"] == "private", message(
        en="Run the supplied Alpine worker without mounts, privileges or host cgroup namespace.",
        fr="Exécutez le worker Alpine fourni sans montages, privilèges ni namespace cgroup hôte.",
    )
    return worker


def _cgroup(host, worker, name):
    result = host.run("docker exec %s cat %s", worker["Id"], f"/sys/fs/cgroup/{name}")
    assert result.rc == 0, message(
        en=f"Cannot read effective cgroup v2 control {name}.",
        fr=f"Impossible de lire le contrôle cgroup v2 effectif {name}.",
    )
    return result.stdout.strip()


def _budgets(host, worker):
    assert worker["HostConfig"]["Memory"] == 134217728 and _cgroup(host, worker, "memory.max") == "134217728", message(
        en="Enforce a 128 MiB hard memory limit in both Docker and the cgroup.",
        fr="Appliquez une limite mémoire dure de 128 Mio dans Docker et le cgroup.",
    )
    assert worker["HostConfig"]["PidsLimit"] == 64 and _cgroup(host, worker, "pids.max") == "64", message(
        en="Enforce a 64-process limit in both Docker and the cgroup.",
        fr="Appliquez une limite de 64 processus dans Docker et le cgroup.",
    )
    cpu = _cgroup(host, worker, "cpu.max").split()
    assert len(cpu) == 2 and cpu[0] != "max" and int(cpu[0]) * 2 == int(cpu[1]), message(
        en="Enforce a CPU quota equal to half a core, not a relative share.",
        fr="Appliquez un quota CPU d'un demi-cœur, pas un poids relatif.",
    )


def test_memory_and_process_budgets_are_effective(host):
    _budgets(host, _worker(host))


def test_half_cpu_budget_actually_throttles_a_bounded_workload(host):
    worker = _worker(host)
    _budgets(host, worker)
    before = dict(line.split() for line in _cgroup(host, worker, "cpu.stat").splitlines())
    trial = host.run("docker exec %s timeout 3 sh -c %s", worker["Id"], "while :; do :; done")
    assert trial.rc == 143, message(
        en="The bounded three-second CPU trial must stop on its timeout.",
        fr="L'essai CPU borné à trois secondes doit s'arrêter sur son délai.",
    )
    after = dict(line.split() for line in _cgroup(host, worker, "cpu.stat").splitlines())
    assert int(after["nr_throttled"]) > int(before["nr_throttled"]) and int(after["throttled_usec"]) > int(before["throttled_usec"]), message(
        en="The cgroup must report actual CPU throttling during the bounded workload.",
        fr="Le cgroup doit signaler un bridage CPU réel pendant la charge bornée.",
    )


def test_recreation_keeps_all_effective_budgets(host):
    before = _worker(host)
    _budgets(host, before)
    result = host.run("docker compose -p %s -f %s up -d --force-recreate --no-build --pull never", PROJECT, COMPOSE)
    assert result.rc == 0, message(
        en=f"Recreation from the declaration must succeed: {result.stderr[-500:]}",
        fr=f"La recréation depuis la déclaration doit réussir : {result.stderr[-500:]}",
    )
    after = _worker(host)
    assert before["Id"] != after["Id"], message(
        en="Compose must replace the worker, not retain a manually limited container.",
        fr="Compose doit remplacer le worker, pas garder un conteneur limité manuellement.",
    )
    _budgets(host, after)
