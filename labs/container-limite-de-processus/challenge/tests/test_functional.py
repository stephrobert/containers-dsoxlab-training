"""A finite 24-process burst, only after checking the effective 16-task cap."""

import json

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_process_cap_really_rejects_a_finite_burst(host):
    found = host.run(
        "docker ps -q --filter label=com.docker.compose.project=dsoxlab-container-limite-de-processus "
        "--filter label=com.docker.compose.service=worker"
    )
    ids = found.stdout.split()
    assert found.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    config = info["HostConfig"]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == "container-limite-de-processus", message(fr="Conserver le label", en="Preserve the label")
    assert config["PidsLimit"] == 16 and 0 < config["Memory"] <= 67108864, message(fr="Plafonner à 16 tâches et 64 Mio maximum", en="Cap at 16 tasks and at most 64 MiB")
    maximum = host.run("docker exec %s cat /sys/fs/cgroup/pids.max", cid)
    assert maximum.rc == 0 and maximum.stdout.strip() == "16", message(fr="Le cgroup doit porter la limite", en="Cgroup must carry the limit")
    before = host.run("docker exec %s cat /sys/fs/cgroup/pids.events", cid)
    assert before.rc == 0, message(fr="Lire les événements avant la sonde", en="Read events before the probe")
    count = int(dict(line.split() for line in before.stdout.splitlines())["max"])
    host.run(
        "timeout 8 docker exec %s sh -c "
        "'for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24; do sleep 2 & done; wait'",
        cid,
    )
    host.run("sleep 3")
    after = host.run("docker exec %s cat /sys/fs/cgroup/pids.events", cid)
    assert after.rc == 0 and int(dict(line.split() for line in after.stdout.splitlines())["max"]) > count, message(fr="Le noyau doit refuser au moins une création", en="Kernel must reject at least one creation")
    state = json.loads(host.run("docker inspect %s", cid).stdout)[0]["State"]
    assert state["Running"] and not state["OOMKilled"], message(fr="Le service doit survivre sans OOM", en="Service must survive without OOM")
