"""Build image filesystems from actual Debian packages, never invented metadata."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/opt/lab-image-scan")
EXPECTED = {
    "bookworm": "177c30ea1177be8a77c1ee8705099919ce0906a29e68173e49244f863c4604ab",
    "legacy.deb": "92247c2c011ec4c01f5832a38de0ec1a9c2cfac5c6c5dc229e5a1ac81148854c",
    "fixed.deb": "d97c29db9d9d1d125580be5d7b2e1170adb47e5a8b4481841718be95fa652e68",
}
for filename, digest in EXPECTED.items():
    if hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() != digest:
        raise SystemExit(f"Corrupt supplied fixture: {filename}")
database = ROOT / "database"
database.mkdir(exist_ok=True)
(database / "bookworm").write_bytes((ROOT / "bookworm").read_bytes())
for name in ("legacy", "fixed"):
    directory = ROOT / name
    rootfs = directory / "rootfs"
    rootfs.mkdir(parents=True, exist_ok=True)
    package = ROOT / f"{name}.deb"
    subprocess.run(["dpkg-deb", "-x", str(package), str(rootfs)], check=True)
    control = subprocess.check_output(["dpkg-deb", "-f", str(package)], text=True)
    status = rootfs / "var/lib/dpkg/status"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(control + "Status: install ok installed\n\n")
    (directory / "Dockerfile").write_text(
        'FROM scratch\nLABEL dsoxlab.lab="image-scan-de-vulnerabilites"\n'
        'COPY rootfs/ /\nCMD ["/not-executable-library-fixture"]\n'
    )
    binaries = {str(p.relative_to(rootfs)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in rootfs.rglob("libssl.so.*") if p.is_file() and not p.is_symlink()}
    (ROOT / f"{name}-binaries.json").write_text(json.dumps(binaries))
