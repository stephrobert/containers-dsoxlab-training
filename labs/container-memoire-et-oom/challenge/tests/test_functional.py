"""Bounded allocation, guarded by the effective memory and swap limits."""

import json

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_memory_cgroup_contains_a_real_oom(host):
    found = host.run(
        "docker ps -q --filter label=com.docker.compose.project=dsoxlab-container-memoire-et-oom "
        "--filter label=com.docker.compose.service=worker"
    )
    ids = found.stdout.split()
    assert found.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    config = info["HostConfig"]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == "container-memoire-et-oom", message(fr="Conserver le label", en="Preserve the label")
    assert config["Memory"] == 33554432 and config["MemorySwap"] == 33554432 and not config["OomKillDisable"], message(fr="Limiter à 32 Mio sans swap, sans désactiver l'OOM", en="Limit to 32 MiB without swap or disabling OOM")
    limits = host.run("docker exec %s sh -c 'cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.swap.max'", cid)
    assert limits.rc == 0 and limits.stdout.split() == ["33554432", "0"], message(fr="Vérifier les limites effectives avant allocation", en="Verify effective limits before allocation")
    margin = host.run("awk '/MemAvailable/ {print $2}' /proc/meminfo")
    assert margin.rc == 0 and int(margin.stdout) > 131072, message(fr="Marge mémoire hôte insuffisante pour la sonde", en="Insufficient host memory margin for probe")
    before = host.run("docker exec %s cat /sys/fs/cgroup/memory.events", cid)
    assert before.rc == 0, message(fr="Lire les événements avant la sonde", en="Read events before the probe")
    killed = int(dict(line.split() for line in before.stdout.splitlines())["oom_kill"])
    probe = host.run(
        "timeout 10 docker exec %s awk 'BEGIN {s=\"x\"; for(i=0;i<26;i++) s=s s; print length(s)}'",
        cid,
    )
    assert probe.rc not in (0, 124), message(fr="La sonde bornée doit subir un OOM, pas un délai", en="Bounded probe must hit OOM, not a timeout")
    after = host.run("docker exec %s cat /sys/fs/cgroup/memory.events", cid)
    assert after.rc == 0 and int(dict(line.split() for line in after.stdout.splitlines())["oom_kill"]) > killed, message(fr="Un oom_kill réel doit être compté", en="A real oom_kill must be counted")
    state = json.loads(host.run("docker inspect %s", cid).stdout)[0]["State"]
    assert state["Running"], message(fr="L'OOM de la sonde ne doit pas tuer PID 1", en="Probe OOM must not kill PID 1")
