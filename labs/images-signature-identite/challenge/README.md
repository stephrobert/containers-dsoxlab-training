# Mission: accept only the approved release signer

Work on `docker.lab` in `/opt/lab-image-signature`, not in local challenge/work.
The fixture provides `archive.tar`, `archive.sig`, `keys/approved.crt`,
runtime-generated synthetic private keys, and the administrator's trust inputs.

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

`dsoxlab check images-signature-identite` generates real fresh positive and
negative signatures. `dsoxlab clean images-signature-identite` removes
the archive, generated keys and only images added by this lab.
