"""Remove seeded bases only when this lab introduced them and nobody shares them."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASES = [
    "python:3.14.10-slim-trixie@sha256:3cabfd7d7aaf394e6040e79fa1eec6ca1c52b74ed9188650472695d9a9326999",
    "postgres:18.6-alpine3.24@sha256:10a5c69a83035ab5239f5620d708520e8b28f5aa1f2b20143e6024532edadfb5",
    "registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3",
]


def inspect(reference):
    result = subprocess.run(["docker", "image", "inspect", reference], capture_output=True, text=True)
    return json.loads(result.stdout)[0] if result.returncode == 0 else None


snapshot = ROOT / "base-ids-before.json"
if sys.argv[1] == "snapshot":
    if not snapshot.exists():
        result = subprocess.check_output(["docker", "image", "ls", "-aq", "--no-trunc"], text=True)
        snapshot.write_text(json.dumps(result.split()))
elif snapshot.exists():
    original = set(json.loads(snapshot.read_text()))
    containers = subprocess.check_output(["docker", "ps", "-aq"], text=True).split()
    used = set()
    if containers:
        used = {c["Image"] for c in json.loads(subprocess.check_output(
            ["docker", "inspect", *containers], text=True))}
    for reference in BASES:
        image = inspect(reference)
        if not image or image["Id"] in original | used:
            continue
        repo, digest = reference.split("@")
        allowed = {repo, repo.split(":")[0] + "@" + digest}
        refs = set(image.get("RepoTags") or []) | set(image.get("RepoDigests") or [])
        if refs - allowed:
            continue
        for ref in sorted(refs):
            if inspect(ref):
                subprocess.run(["docker", "image", "rm", "--no-prune", ref], check=True)
        if inspect(image["Id"]):
            subprocess.run(["docker", "image", "rm", "--no-prune", image["Id"]], check=True)
