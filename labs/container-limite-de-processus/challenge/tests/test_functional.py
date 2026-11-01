"""A finite 24-process burst, only after checking the effective 16-task cap."""

import json
import uuid

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
    witness = uuid.uuid4().hex
    reserved = host.run("docker exec %s mktemp", cid)
    path = reserved.stdout.strip()
    assert reserved.rc == 0 and path, message(
        en="Reserve a private receipt file inside the worker.",
        fr="Réservez un fichier de reçu privé dans le worker.",
    )
    try:
        stored = host.run("docker exec %s sh -c %s", cid, f"printf %s {witness} > {path}")
        assert stored.rc == 0, message(
            en="Store a fresh application receipt before task saturation.",
            fr="Conservez un reçu applicatif frais avant saturation des tâches.",
        )
        burst = host.run(
            "timeout 8 docker exec %s sh -c "
            "'for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24; do sleep 2 & done; wait'",
            cid,
        )
        assert burst.rc != 124, message(
            en="The finite process trial must finish, not reach its safety timeout.",
            fr="L'essai de processus fini doit terminer, sans atteindre le délai de sécurité.",
        )
        host.run("sleep 3")
        after = host.run("docker exec %s cat /sys/fs/cgroup/pids.events", cid)
        assert after.rc == 0 and int(dict(line.split() for line in after.stdout.splitlines())["max"]) > count, message(fr="Le noyau doit refuser au moins une création", en="Kernel must reject at least one creation")
        state = json.loads(host.run("docker inspect %s", cid).stdout)[0]["State"]
        retained = host.run("docker exec %s cat %s", cid, path)
        assert state["Running"] and not state["OOMKilled"] and (
            state["StartedAt"] == info["State"]["StartedAt"]
            and retained.rc == 0 and retained.stdout == witness
        ), message(
            en="The original service must resume without OOM or loss of its fresh receipt.",
            fr="Le service original doit reprendre sans OOM ni perte du reçu frais.",
        )
    finally:
        removed = host.run("docker exec %s rm -f %s", cid, path)
        assert removed.rc == 0, message(
            en="Remove only the finite-process-trial receipt.",
            fr="Retirez seulement le reçu de l'essai de processus fini.",
        )
