"""Observe a harmless syscall denied by the container's real filter."""

import json

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_only_reserved_getpgid_argument_is_filtered(host):
    found = host.run(
        "docker ps -q --filter label=com.docker.compose.project=dsoxlab-securite-seccomp "
        "--filter label=com.docker.compose.service=worker"
    )
    ids = found.stdout.split()
    assert found.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    options = info["HostConfig"]["SecurityOpt"] or []
    assert info["Config"]["Labels"].get("dsoxlab.lab") == "securite-seccomp", message(fr="Conserver le label", en="Preserve the label")
    assert any(option.startswith("seccomp=") or option.startswith("seccomp:") for option in options) and not any("unconfined" in option for option in options), message(fr="Charger un filtre explicite", en="Load an explicit filter")
    original = host.run("cat /opt/dsoxlab-securite-seccomp/.probe-image-id")
    assert original.rc == 0 and info["Image"] == original.stdout.strip(), message(fr="Conserver l'image de la sonde originale", en="Keep the original probe image")
    status = host.run("docker exec %s cat /proc/1/status", cid)
    mode = next(line.split()[1] for line in status.stdout.splitlines() if line.startswith("Seccomp:"))
    assert status.rc == 0 and mode == "2", message(fr="Le noyau doit filtrer PID 1", en="Kernel must filter PID 1")
    probe = host.run("docker exec %s /usr/local/bin/syscall-probe", cid)
    assert probe.rc == 0 and probe.stdout.strip() == "getpgid(sentinel)=EPERM getpgid(0)=allowed getpid=allowed", message(fr="Refuser getpgid(2147483647) sans bloquer getpgid(0) ni getpid", en="Deny getpgid(2147483647) without blocking getpgid(0) or getpid")
