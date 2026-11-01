# A digest does not identify its author

The team exports its container image as an archive. A checksum detects
changed bytes, but anyone who changes those bytes can publish a new checksum.
The release gate needs an authenticated author, not a label saying "signed".

A local administrator has approved a signing CA and one release identity.
The archive and a detached signature are ready; the verifier refuses
everything because its policy implementation is missing.

Implement a gate that accepts the approved signer and rejects a valid signer
with another identity, an unrelated key, and altered content.
Work on `docker.lab` in `/opt/lab-image-signature`.
See [the requirements](challenge/README.md).
