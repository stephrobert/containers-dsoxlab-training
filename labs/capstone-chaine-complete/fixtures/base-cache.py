"""Remove seeded bases only when this lab introduced them and nobody shares them."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASES = [
    "python:3.13.8-slim-bookworm@sha256:61169c2bdb8e6bb44a8dfad33f569d324d52f079fded9a204b322a6fb9c9f799",
    "postgres:17.6-alpine3.22@sha256:ef257d85f76e48da1c64832459b59fcaba1a4dac97bf5d7450c77753542eee94",
    "registry:2.8.3@sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373",
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
