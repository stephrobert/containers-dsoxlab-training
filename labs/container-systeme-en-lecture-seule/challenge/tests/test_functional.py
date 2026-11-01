"""Prove read-only root, bounded writable tmpfs, and a live application."""

import json
import time
import uuid

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_read_only_root_with_bounded_runtime_storage(host):
    found = host.run(
        "docker ps -q --filter label=com.docker.compose.project=dsoxlab-container-systeme-en-lecture-seule "
        "--filter label=com.docker.compose.service=worker"
    )
    ids = found.stdout.split()
    assert found.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    config = info["HostConfig"]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == "container-systeme-en-lecture-seule", message(fr="Conserver le label", en="Preserve the label")
    assert config["ReadonlyRootfs"], message(fr="La racine doit être réellement en lecture seule", en="Root must actually be read-only")
    assert "/run" in config["Tmpfs"], message(fr="Utiliser un tmpfs pour /run", en="Use tmpfs for /run")
    options = config["Tmpfs"]["/run"].split(",")
    assert "noexec" in options and "nosuid" in options, message(fr="Limiter les usages du tmpfs", en="Restrict tmpfs usage")
    size = host.run("docker exec %s df -Pk /run", cid)
    assert size.rc == 0 and int(size.stdout.splitlines()[-1].split()[1]) == 4096, message(fr="Le tmpfs doit être limité à 4 Mio", en="Tmpfs must be capped at 4 MiB")
    token = uuid.uuid4().hex
    try:
        root = host.run("docker exec %s touch /dsoxlab-check-%s", cid, token)
        assert root.rc != 0 and "Read-only file system" in root.stderr, message(fr="Refuser une vraie écriture à la racine", en="Deny a real root write")
        writable = host.run("docker exec %s touch /run/dsoxlab-check-%s", cid, token)
        assert writable.rc == 0, message(fr="/run doit rester utilisable", en="/run must remain usable")
        heartbeat = host.run("docker exec %s cat /run/heartbeat", cid)
        assert heartbeat.rc == 0 and heartbeat.stdout.strip().isdigit(), message(fr="Le service doit encore fonctionner", en="Service must still work")
        initial = int(heartbeat.stdout.strip())
        for _ in range(3):
            time.sleep(1)
            heartbeat = host.run("docker exec %s cat /run/heartbeat", cid)
            if heartbeat.rc == 0 and heartbeat.stdout.strip().isdigit() and int(heartbeat.stdout.strip()) > initial:
                break
        assert heartbeat.rc == 0 and heartbeat.stdout.strip().isdigit() and int(heartbeat.stdout.strip()) > initial, message(fr="Le heartbeat doit continuer à progresser", en="Heartbeat must continue advancing")
    finally:
        host.run("docker exec %s rm -f /run/dsoxlab-check-%s /dsoxlab-check-%s", cid, token, token)
