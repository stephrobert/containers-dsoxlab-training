"""Check image metadata and every saved layer, including deleted files."""

import base64
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
for args in (["docker", "image", "inspect", image],
             ["docker", "history", "--no-trunc", image]):
    result = subprocess.run(args, capture_output=True, check=True)
    if any(needle in result.stdout for needle in needles):
        print(json.dumps({"clean": False, "surface": "metadata"}))
        sys.exit(0)
with tempfile.TemporaryFile() as archive:
    subprocess.run(["docker", "save", image], stdout=archive, check=True)
    archive.seek(0)
    with tarfile.open(fileobj=archive) as saved:
        for member in saved:
            if not member.isfile():
                continue
            source = saved.extractfile(member)
            if source is None:
                raise RuntimeError("Cannot read an image archive member")
            if member.name.endswith("layer.tar"):
                with tarfile.open(fileobj=io.BytesIO(source.read())) as layer:
                    for entry in layer:
                        if any(n.decode() in entry.name for n in needles):
                            print(json.dumps({"clean": False, "surface": "layer"}))
                            sys.exit(0)
                        if not entry.isfile():
                            continue
                        content = layer.extractfile(entry)
                        if content is None:
                            raise RuntimeError("Cannot read a layer member")
                        tail = b""
                        while chunk := content.read(1024 * 1024):
                            data = tail + chunk
                            if any(n in data for n in needles):
                                print(json.dumps({"clean": False, "surface": "layer"}))
                                sys.exit(0)
                            tail = data[-max(map(len, needles)):]
            elif any(n in source.read() for n in needles):
                print(json.dumps({"clean": False, "surface": "archive"}))
                sys.exit(0)
print(json.dumps({"clean": True}))
