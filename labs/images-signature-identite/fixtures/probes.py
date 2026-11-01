"""Produce fresh cryptographic counterexamples, never a fabricated verdict."""

import json
import pathlib
import secrets
import subprocess

root = pathlib.Path("/opt/lab-image-signature")
bench = root / "bench"
def named(suffix):
    return bench / (secrets.token_hex(16) + suffix)


artifact = named(".bin")
artifact.write_bytes(secrets.token_bytes(4096))
cases = {"artifact": str(artifact.relative_to(root))}
for signer in ("approved", "other", "rogue"):
    signature = named(".sig")
    certificate = named(".crt")
    certificate.write_bytes((root / "keys" / f"{signer}.crt").read_bytes())
    subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", str(root / "keys" / f"{signer}.key"),
         "-out", str(signature), str(artifact)],
        check=True,
    )
    cases[signer] = {"signature": str(signature.relative_to(root)), "certificate": str(certificate.relative_to(root))}
altered = named(".bin")
altered.write_bytes(artifact.read_bytes() + b"\x01")
cases["altered"] = str(altered.relative_to(root))
print(json.dumps(cases))
