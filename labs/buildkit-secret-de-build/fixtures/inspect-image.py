"""Check image metadata and every saved layer, including deleted files.

WHY THIS NO LONGER LOOKS FOR `layer.tar`. Measured on 2026-11-02 against Docker
29.9.2 with the containerd image store: `docker save` writes an OCI layout, so
every layer is a `blobs/sha256/<digest>` member compressed with **gzip**, and
no member is named `layer.tar` any more. The previous version tested exactly
that name, never entered its layer branch, read the gzip blob raw, and reported
`{"clean": true}` on an image that demonstrably carried the token in a layer.

An unreadable layer is reported as NOT clean. A reader that could not look must
never conclude that nothing is there.
"""

import base64
import gzip
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

image, token_path = sys.argv[1:]
token = Path(token_path).read_bytes().strip()
needles = (token, base64.b64encode(token), base64.b64encode(b"Bearer " + token))

# Signatures we can name. Only gzip is opened here; the others are reported
# rather than skipped, because skipping one would read as "clean".
MAGIC = (
    (b"\x1f\x8b", "gzip"),
    (b"\x28\xb5\x2f\xfd", "zstd"),
    (b"BZh", "bzip2"),
    (b"\xfd7zXZ", "xz"),
)


def verdict(clean, surface=None):
    report = {"clean": clean}
    if surface is not None:
        report["surface"] = surface
    print(json.dumps(report))
    sys.exit(0)


def decompressed(data):
    """The readable bytes, or None when the compression is beyond this reader."""
    for magic, name in MAGIC:
        if data.startswith(magic):
            return gzip.decompress(data) if name == "gzip" else None
    return data


def carried_by(layer_bytes):
    """True when a layer carries the token, by entry name or by content."""
    with tarfile.open(fileobj=io.BytesIO(layer_bytes)) as layer:
        for entry in layer:
            if any(n.decode("utf-8", "ignore") in entry.name for n in needles):
                return True
            if not entry.isfile():
                continue
            content = layer.extractfile(entry)
            if content is None:
                raise RuntimeError("Cannot read a layer member")
            tail = b""
            while chunk := content.read(1024 * 1024):
                data = tail + chunk
                if any(n in data for n in needles):
                    return True
                tail = data[-max(map(len, needles)):]
    return False


for args in (["docker", "image", "inspect", image],
             ["docker", "history", "--no-trunc", image]):
    result = subprocess.run(args, capture_output=True, check=True)
    if any(needle in result.stdout for needle in needles):
        verdict(False, "metadata")

with tempfile.TemporaryFile() as archive:
    subprocess.run(["docker", "save", image], stdout=archive, check=True)
    archive.seek(0)
    with tarfile.open(fileobj=archive) as saved:
        for member in saved.getmembers():
            if not member.isfile():
                continue
            source = saved.extractfile(member)
            if source is None:
                raise RuntimeError("Cannot read an image archive member")
            readable = decompressed(source.read())
            if readable is None:
                verdict(False, f"a layer this reader cannot open ({member.name})")
            # A layer is a tar; everything else is a descriptor. Failing to
            # open it simply means it is not one.
            try:
                if carried_by(readable):
                    verdict(False, "layer")
                continue
            except tarfile.TarError:
                pass
            if any(needle in readable for needle in needles):
                verdict(False, "archive")

verdict(True)
