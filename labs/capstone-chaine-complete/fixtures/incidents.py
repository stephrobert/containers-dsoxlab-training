"""Inject exactly one incident, only into the labelled capstone project."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/opt/lab-delivery")
PROJECT = "dsoxlab-delivery"


def run(args):
    return subprocess.check_output(args, text=True).strip()


def service(name):
    ids = run(["docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={PROJECT}",
               "--filter", f"label=com.docker.compose.service={name}",
               "--filter", "label=dsoxlab.lab=capstone-chaine-complete"]).split()
    if len(ids) != 1:
        raise SystemExit("Restore the delivery stack first / Restaurez la stack d'abord")
    return ids[0]


def compose_override(content):
    (ROOT / "incident.yaml").write_text(content)
    run(["docker", "compose", "-p", PROJECT, "--env-file", str(ROOT / "release.env"),
         "-f", str(ROOT / "compose.yaml"), "-f", str(ROOT / "incident.yaml"),
         "up", "-d", "--no-deps", "--force-recreate", "api"])


if __name__ == "__main__":
    number = int(sys.argv[1])
    api, db = service("api"), service("db")
    if number == 1:
        run(["docker", "stop", api])
    elif number == 2:
        run(["docker", "stop", db])
    elif number == 3:
        networks = json.loads(run(["docker", "inspect", api]))[0]["NetworkSettings"]["Networks"]
        network = next(n for n in networks if n.endswith("_backend"))
        run(["docker", "network", "disconnect", network, api])
    elif number == 4:
        (ROOT / "db-password").write_text("invalid-incident-password\n")
    elif number == 5:
        run(["docker", "pause", db])
    elif number == 6:
        run(["docker", "rm", "-f", api])
    elif number == 7:
        compose_override("services:\n  api:\n    environment:\n      DB_PORT: '5433'\n")
    elif number == 8:
        compose_override("services:\n  api:\n    command: ['python', '-c', 'import time; time.sleep(3600)']\n")
    else:
        raise SystemExit("Incident must be 1..8 / Incident entre 1 et 8")
    print("Incident injected. Diagnose without a recipe. / Incident injecté : diagnostiquez sans recette.")
