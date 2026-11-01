# Signature and approved identity

**Language:** [English](README.md) · [Français](README.fr.md)

## Bytes, keys and identity

A SHA-256 digest identifies bytes. A signature binds bytes to a private key.
A verified certificate binds its public key to an identity under a trusted
issuer. The delivery policy must check all three; a valid signature by the
wrong team remains unacceptable.

For a neutral disposable example, create a message and a synthetic key:

```sh
printf 'workshop message\n' > note.txt
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out workshop.key
openssl pkey -in workshop.key -pubout -out workshop.pub
openssl dgst -sha256 -sign workshop.key -out note.sig note.txt
openssl dgst -sha256 -verify workshop.pub -signature note.sig note.txt
```

These commands demonstrate byte verification only. They do not establish
which identity owns `workshop.pub`. In a certificate-based gate, first use
`openssl verify` against an administratively approved CA. Read the exact
approved URI SAN only from that validated certificate, extract its public
key, then verify the detached signature over the delivered bytes.
Never trust a subject string or a certificate bundled by its own signer
without validating the chain. Reject malformed inputs and tool errors.

## Local trust model

This lab implements RSA/SHA-256 detached signatures with OpenSSL and a local
X.509 CA. It is not Sigstore, keyless OIDC, a transparency log or an online
identity authority. Private keys and short-lived certificates are generated
only inside the VM. The administrator's `trust/ca.crt` and `trust/policy.json`
are trust inputs, not data supplied by an archive publisher. The exercise
assumes the local administrator is trusted; it does not defend against root
replacing the verifier or issuing new certificates with the CA key.

`archive.tar` is a real Docker save of a fresh image built from a
digest-pinned public base. The signature covers the archive bytes, not a
registry tag, a Docker content-trust record or a remotely published OCI
signature. Re-exporting the same image can change archive bytes and requires
a new signature. This lab authenticates provenance and integrity; it does
not assess vulnerabilities. Scanning belongs to the separate CVE lab.

## Counterexamples

The checks use fresh random bytes and real signatures, not expected console
text. The approved identity must succeed. A second identity signed by the
same CA must fail, as must a self-issued certificate claiming the approved
URI, a signature made by another key, and altered bytes.

[Mission](scenario.md) · [Requirements](challenge/README.md)
