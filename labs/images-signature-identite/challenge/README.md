# A checksum does not identify its author

## The situation

The team ships its container image as an archive. A checksum detects changed
bytes, but whoever changes them can publish a new checksum. The delivery therefore
requires an authenticated author.

On `docker.lab`, `/opt/lab-image-signature` contains `archive.tar`,
`archive.sig`, `keys/approved.crt`, test private keys, and what the administrator
approves: `trust/ca.crt` and `trust/policy.json`. The `verify.py` verifier refuses
everything, because its policy is not written.

## Mission

1. Implement `verify.py ARCHIVE SIGNATURE CERTIFICATE`. Exit 0 only when the
   supplied signature authenticates those exact bytes with the public key of
   a valid certificate chained to `trust/ca.crt`. Exit 1 for a deliberate
   refusal or invalid input.
2. Enforce the exact identity URI in `trust/policy.json`:
   `spiffe://dsoxlab/release/builder`, with SHA-256. Preserve the trust inputs.
   A CA-valid certificate for another identity is not an approved signer.
3. Accept the genuine container archive and fresh content genuinely signed
   by the approved key. Do not recognize filenames, console text or a fixed
   fixture checksum instead of verifying cryptography.
4. Reject altered bytes, a signature produced by another private key, and
   a self-issued certificate claiming the approved URI. Chain validation,
   exact identity policy and byte signature verification are all required.
5. Keep private keys on the VM and outside version control. Use only the
   lab-owned directory and labelled image. Do not add a scanner or claim
   Sigstore, keyless signing or a transparency log.

Three checks make new signatures, good and bad, at each run.
