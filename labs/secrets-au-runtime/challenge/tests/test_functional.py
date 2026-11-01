"""Only hashes and yes/no leakage verdicts leave the VM, never the token."""

import json
import time

import pytest

from conftest import lab_host, message

WORK = "/opt/dsoxlab-secrets-au-runtime"

@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_runtime_secret_is_read_only_used_and_not_leaked(host):
    found = host.run(
        "docker ps -q --filter label=com.docker.compose.project=dsoxlab-secrets-au-runtime "
        "--filter label=com.docker.compose.service=worker"
    )
    ids = found.stdout.split()
    assert found.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    # Inspect only the mount fields here: arbitrary environment values stay on the VM.
    mount_result = host.run("docker inspect -f '{{json .Mounts}}' %s", cid)
    assert mount_result.rc == 0, message(fr="Lire les montages", en="Read mounts")
    mounts = json.loads(mount_result.stdout)
    token_mounts = [mount for mount in mounts if mount["Destination"] == "/run/secrets/token"]
    assert len(token_mounts) == 1 and not token_mounts[0]["RW"], message(fr="Un secret monté en lecture seule requis", en="A read-only mounted secret is required")
    assert token_mounts[0]["Type"] == "bind" and token_mounts[0]["Source"] == WORK + "/secrets/token", message(fr="Utiliser la source privée fournie", en="Use the supplied private source")
    source = host.run("LC_ALL=C stat -c '%%a:%%F' %s/secrets/token", WORK)
    assert source.rc == 0 and source.stdout.strip() == "600:regular file", message(fr="Source privée 0600 requise", en="Private 0600 source required")
    expected = host.run("sha256sum %s/secrets/token | cut -d ' ' -f 1", WORK)
    assert expected.rc == 0 and len(expected.stdout.strip()) == 64, message(fr="Lire uniquement l'empreinte attendue", en="Read only the expected digest")
    actual = None
    for _ in range(5):
        actual = host.run(
            "docker exec %s sh -c 'test \"$(cat /run/result 2>/dev/null)\" = \"$1\"' sh %s",
            cid, expected.stdout.strip(),
        )
        if actual.rc == 0:
            break
        time.sleep(1)
    assert actual is not None and actual.rc == 0, message(fr="L'application doit consommer le secret", en="Application must consume the secret")
    denied = host.run("docker exec %s sh -c 'printf x >> /run/secrets/token'", cid)
    after = host.run("sha256sum %s/secrets/token | cut -d ' ' -f 1", WORK)
    assert denied.rc != 0 and after.rc == 0 and after.stdout.strip() == expected.stdout.strip(), message(
        fr="Une vraie écriture doit échouer sans modifier le secret",
        en="A real write must fail without changing the secret",
    )
    scanner = r"""
import json, pathlib, subprocess, sys
root = pathlib.Path(sys.argv[2])
secret = (root / "secrets/token").read_bytes().strip()
def docker(*args):
    result = subprocess.run(["docker", *args], capture_output=True, check=True, timeout=5)
    return result.stdout + result.stderr
info_bytes = docker("inspect", sys.argv[1])
info = json.loads(info_bytes)[0]
payloads = [info_bytes, docker("logs", sys.argv[1]),
            docker("image", "inspect", info["Image"]),
            docker("history", "--no-trunc", info["Image"])]
for path in root.rglob("*"):
    if path.is_file() and (path.suffix in (".yaml", ".yml", ".env") or path.name in ("Dockerfile", ".env")):
        payloads.append(path.read_bytes())
safe = len(secret) == 48 and info["Config"]["Labels"].get("dsoxlab.lab") == "secrets-au-runtime"
base = json.loads(docker("image", "inspect", "alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f"))[0]
safe = safe and info["Image"] == base["Id"]
safe = safe and all(secret not in payload for payload in payloads)
print("safe" if safe else "leaked-or-invalid")
"""
    verdict = host.run("python3 -c %s %s %s", scanner, cid, WORK)
    assert verdict.rc == 0 and verdict.stdout.strip() == "safe", message(fr="Aucune valeur secrète dans inspect, logs, image, historique ou configuration", en="No secret value in inspect, logs, image, history or configuration")
