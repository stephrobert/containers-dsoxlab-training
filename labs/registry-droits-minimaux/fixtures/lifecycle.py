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
    "registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3",
    "cesanta/docker_auth@sha256:13c3c325f51fe1b7650356fb3613fd833242d73e249e024d00396b1f16496464",
    "alpine@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a",
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
