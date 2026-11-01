"""Snapshot only the paths and Docker image references owned by this exercise."""

import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path("/opt/lab-registry-rights")
REGISTRY = "registry-rights.lab.test:15447"
TRUST = pathlib.Path("/etc/docker/certs.d") / REGISTRY
IMAGES = (
    "registry:2.8.3@sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373",
    "cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464",
    "alpine@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f",
)


def docker(*args, check=True):
    return subprocess.run(["docker", *args], check=check, capture_output=True, text=True)


if sys.argv[1] == "snapshot":
    state = ROOT / "baseline.json"
    if state.exists():
        raise SystemExit("Clean this exercise before running setup again.")
    refs = {
        ref: docker("image", "inspect", ref, check=False).returncode == 0
        for ref in IMAGES
    }
    ids = docker("image", "ls", "-aq").stdout.split()
    containers = docker("ps", "-aq").stdout.split()
    trust_existed = TRUST.exists() or TRUST.is_symlink()
    state.write_text(json.dumps({"refs": refs, "ids": ids, "containers": containers, "trust": trust_existed}))
    state.chmod(0o600)
    shutil.copyfile("/etc/hosts", ROOT / "saved-hosts")
    if trust_existed:
        shutil.move(str(TRUST), str(ROOT / "saved-trust"))
elif sys.argv[1] == "clean":
    state = json.loads((ROOT / "baseline.json").read_text())
    for name in set(docker("ps", "-aq", "--filter", "label=dsoxlab.lab=registry-droits-minimaux").stdout.split()) - set(state["containers"]):
        docker("rm", "-f", name)
    for image in set(docker("image", "ls", "-aq", "--filter", "label=dsoxlab.lab=registry-droits-minimaux").stdout.split()) - set(state["ids"]):
        docker("image", "rm", "-f", image)
    for ref, existed in state["refs"].items():
        if not existed:
            docker("image", "rm", ref, check=False)
    if TRUST.is_symlink():
        TRUST.unlink()
    elif TRUST.is_dir():
        shutil.rmtree(TRUST)
    elif TRUST.exists():
        TRUST.unlink()
    if state["trust"]:
        shutil.move(str(ROOT / "saved-trust"), str(TRUST))
    shutil.copyfile(ROOT / "saved-hosts", "/etc/hosts")
