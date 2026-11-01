"""Scan real image dpkg metadata with debsecan and an immutable offline database."""

import argparse
import datetime
import hashlib
import json
import subprocess
import uuid
from pathlib import Path

ROOT = Path("/opt/lab-image-scan")
DATABASE_SHA = "177c30ea1177be8a77c1ee8705099919ce0906a29e68173e49244f863c4604ab"
TARGET = "CVE-2023-0286"


def command(args):
    return subprocess.check_output(args, text=True)


def scan(image):
    database = ROOT / "database/bookworm"
    if hashlib.sha256(database.read_bytes()).hexdigest() != DATABASE_SHA:
        raise SystemExit("The dated scanner database has changed / La base datée a changé")
    image_id = command(["docker", "image", "inspect", "--format", "{{.Id}}", image]).strip()
    directory = ROOT / "extractions" / uuid.uuid4().hex
    directory.mkdir(parents=True)
    container = command([
        "docker", "create", "--label", "dsoxlab.lab=image-scan-de-vulnerabilites",
        image_id,
    ]).strip()
    try:
        subprocess.run(["docker", "cp", f"{container}:/var/lib/dpkg/status",
                        str(directory / "status")], check=True, capture_output=True)
        status = (directory / "status").read_text()
        if "Status: install ok installed" not in status:
            raise SystemExit("Missing installed package inventory / Inventaire absent")
        output = command([
            "debsecan", "--config", "/dev/null", "--source", (ROOT / "database").as_uri(),
            "--suite", "bookworm", "--status", str(directory / "status"),
            "--format", "detail",
        ])
        return {
            "image_id": image_id, "database_sha256": DATABASE_SHA,
            "database_date": "2026-11-01T11:37:02Z",
            "scanned_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "scanner": f"debsecan {command(['dpkg-query', '-W', '-f=${Version}', 'debsecan']).strip()}",
            "status_sha256": hashlib.sha256(status.encode()).hexdigest(),
            "output": output, "policy_cve": TARGET, "blocked": TARGET in output,
        }
    finally:
        subprocess.run(["docker", "rm", container], check=True, capture_output=True)
        (directory / "status").unlink(missing_ok=True)
        directory.rmdir()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("report")
    args = parser.parse_args()
    result = scan(args.image)
    Path(args.report).write_text(json.dumps(result, indent=2) + "\n")
    raise SystemExit(1 if result["blocked"] else 0)
