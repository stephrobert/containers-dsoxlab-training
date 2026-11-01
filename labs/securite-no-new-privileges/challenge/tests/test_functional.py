"""Verify inherited no_new_privs and a real, harmless setuid execution."""

import json

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_setuid_cannot_elevate(host):
    result = host.run(
        "docker ps -q --filter label=com.docker.compose.project=dsoxlab-securite-no-new-privileges "
        "--filter label=com.docker.compose.service=worker"
    )
    ids = result.stdout.split()
    assert result.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == "securite-no-new-privileges", message(fr="Conserver le label", en="Preserve the label")
    assert any(option in ("no-new-privileges", "no-new-privileges:true") for option in info["HostConfig"]["SecurityOpt"] or []), message(fr="Activer no-new-privileges", en="Enable no-new-privileges")
    original = host.run("cat /opt/dsoxlab-securite-no-new-privileges/.probe-image-id")
    assert original.rc == 0 and info["Image"] == original.stdout.strip(), message(fr="Conserver l'image de la sonde originale", en="Keep the original probe image")
    status = host.run("docker exec %s cat /proc/1/status", cid)
    flag = next(line.split()[1] for line in status.stdout.splitlines() if line.startswith("NoNewPrivs:"))
    assert status.rc == 0 and flag == "1", message(fr="PID 1 doit porter le drapeau", en="PID 1 must carry the flag")
    mode = host.run("docker exec %s stat -c '%%u:%%a' /usr/local/bin/identity", cid)
    assert mode.rc == 0 and mode.stdout.strip() == "0:4755", message(fr="Garder le véritable binaire setuid", en="Keep the real setuid binary")
    probe = host.run("docker exec --user 1000:1000 %s /usr/local/bin/identity", cid)
    assert probe.rc == 0 and probe.stdout.strip() == "1000:1000", message(fr="Le setuid ne doit plus élever l'EUID", en="Setuid must no longer elevate EUID")
