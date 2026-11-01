"""Owned-resource lifecycle; preserve all image IDs present before setup."""

import json
import pathlib
import subprocess
import sys

WORK = pathlib.Path(__file__).resolve().parent
LAB = WORK.name.removeprefix("dsoxlab-")
PREFIX = "dsoxlab-" + LAB + "-"
PROJECT = PREFIX + "stack"
STATE = WORK / ".ownership.json"
PIN = "python:3.13.8-slim-bookworm@sha256:61169c2bdb8e6bb44a8dfad33f569d324d52f079fded9a204b322a6fb9c9f799"


def docker(*args):
    return subprocess.run(["docker", *args], text=True, capture_output=True, check=True, timeout=150).stdout.strip()


def cleanup():
    if not STATE.exists():
        raise RuntimeError("No ownership record: refusing cleanup")
    state = json.loads(STATE.read_text())
    for kind, query in (("container", ["ps", "-aq"]), ("network", ["network", "ls", "-q"]), ("volume", ["volume", "ls", "-q"])):
        objects = docker(*query, "--filter", "label=dsoxlab.lab=" + LAB).split()
        for item in objects:
            inspected = json.loads(docker(kind, "inspect", item))[0]
            name = inspected.get("Name", "").lstrip("/")
            identity = inspected.get("Id", name)
            if name.startswith(PREFIX) and identity not in state["resources"][kind]:
                docker(kind, "rm", *(["-f"] if kind == "container" else []), item)
    images = docker("image", "ls", "-q", "--no-trunc", "--filter", "label=dsoxlab.lab=" + LAB).split()
    for image in set(images):
        if image not in state["images"]:
            docker("image", "rm", image)
    pin = subprocess.run(["docker", "image", "inspect", PIN], capture_output=True, text=True, timeout=10)
    if pin.returncode == 0 and json.loads(pin.stdout)[0]["Id"] not in state["images"]:
        docker("image", "rm", PIN)


def setup():
    if STATE.exists():
        raise RuntimeError("Owned state already exists; clean before running again")
    baseline = {
        "images": docker("image", "ls", "-aq", "--no-trunc").split(),
        "resources": {
            "container": docker("ps", "-aq", "--no-trunc").split(),
            "network": docker("network", "ls", "-q", "--no-trunc").split(),
            "volume": docker("volume", "ls", "-q").split(),
        },
    }
    STATE.write_text(json.dumps(baseline))
    # Reject pre-existing names even when they do not carry our label.
    for kind, ids in baseline["resources"].items():
        if ids:
            for obj in json.loads(docker(kind, "inspect", *ids)):
                if obj.get("Name", "").lstrip("/").startswith(PREFIX):
                    raise RuntimeError("Pre-existing lab-prefixed resource; refusing collision")
    docker("pull", PIN)
    if LAB == "reseau-pare-feu-cible":
        import ipaddress
        networks = baseline["resources"]["network"]
        for network in json.loads(docker("network", "inspect", *networks)) if networks else []:
            for config in network["IPAM"].get("Config") or []:
                subnet = config.get("Subnet")
                if subnet and ":" not in subnet:
                    existing = ipaddress.ip_network(subnet)
                    if any(existing.overlaps(ipaddress.ip_network(target)) for target in ("172.30.201.0/24", "172.30.202.0/24")):
                        raise RuntimeError("Dedicated lab subnet overlaps a pre-existing network")
        tag = PREFIX + "image"
        existing = subprocess.run(["docker", "image", "inspect", tag], capture_output=True, timeout=10)
        if existing.returncode == 0:
            raise RuntimeError("Pre-existing lab image tag; refusing overwrite")
        docker("build", "--label", "dsoxlab.lab=" + LAB, "-t", tag, str(WORK))
    docker("compose", "-p", PROJECT, "-f", str(WORK / "compose.yaml"), "up", "-d", "--pull", "never")


if __name__ == "__main__":
    if sys.argv[1] == "setup":
        setup()
    elif sys.argv[1] == "cleanup":
        cleanup()
    else:
        raise RuntimeError("Unknown lifecycle action")
