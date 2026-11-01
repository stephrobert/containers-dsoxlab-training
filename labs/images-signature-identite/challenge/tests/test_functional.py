"""Verify real signatures, issuer trust, approved identity and tamper rejection."""

from __future__ import annotations

import json

from conftest import lab_host, message

WORK = "/opt/lab-image-signature"


def _verify(host, artifact, signature, certificate):
    return host.run(
        "python3 %s %s %s %s", f"{WORK}/verify.py",
        f"{WORK}/{artifact}", f"{WORK}/{signature}", f"{WORK}/{certificate}",
    )


def _ready(host):
    for name in ("ca.crt", "policy.json"):
        result = host.run("cmp %s %s", f"{WORK}/trust/{name}", f"{WORK}/bench/{name}")
        assert result.rc == 0, message(
            en="Preserve the administratively approved CA and identity policy.",
            fr="Préservez la CA et la politique d'identité approuvées administrativement.",
        )
    policy = json.loads(host.file(f"{WORK}/trust/policy.json").content_string)
    assert policy == {"identity": "spiffe://dsoxlab/release/builder", "algorithm": "sha256"}, message(
        en="The policy must explicitly bind the approved identity and SHA-256.",
        fr="La politique doit lier explicitement l'identité approuvée et SHA-256.",
    )
    digest = host.run("cd %s && sha256sum --check bench/archive.sha256", WORK)
    assert digest.rc == 0, message(en="Preserve the prepared container archive.", fr="Préservez l'archive de conteneur préparée.")
    accepted = _verify(host, "archive.tar", "archive.sig", "keys/approved.crt")
    assert accepted.rc == 0, message(
        en="Accept the genuine archive only after cryptographic and signer identity verification.",
        fr="Acceptez l'archive authentique seulement après vérification cryptographique et de l'identité.",
    )
    generated = host.run("python3 %s", f"{WORK}/probes.py")
    assert generated.rc == 0, message(en="Generate fresh real signatures for the checks.", fr="Générer des signatures réelles neuves pour les contrôles.")
    cases = json.loads(generated.stdout)
    fresh = _verify(host, cases["artifact"], **cases["approved"])
    assert fresh.rc == 0, message(
        en="The verifier must accept fresh content signed by the approved identity, not recognize one fixture.",
        fr="Le vérificateur doit accepter du contenu neuf signé par l'identité approuvée, pas reconnaître une seule fixture.",
    )
    return cases


def test_approved_signer_accepts_a_real_archive_and_rejects_altered_bytes():
    host = lab_host("docker.lab")
    cases = _ready(host)
    altered = _verify(host, cases["altered"], **cases["approved"])
    assert altered.rc == 1, message(
        en="Changing the signed bytes must cause a deliberate verification refusal (exit 1).",
        fr="Modifier les octets signés doit entraîner un refus explicite de vérification (code 1).",
    )
    prepared = host.run("cp %s %s && printf x >> %s", f"{WORK}/archive.tar", f"{WORK}/bench/altered-archive.tar", f"{WORK}/bench/altered-archive.tar")
    assert prepared.rc == 0, message(en="Prepare an altered real container archive.", fr="Préparer une véritable archive de conteneur altérée.")
    try:
        archive = _verify(host, "bench/altered-archive.tar", "archive.sig", "keys/approved.crt")
        assert archive.rc == 1, message(en="The altered container archive must be refused.", fr="L'archive de conteneur altérée doit être refusée.")
    finally:
        removed = host.run("rm -f %s", f"{WORK}/bench/altered-archive.tar")
        assert removed.rc == 0, message(en="Remove the altered trial archive.", fr="Retirer l'archive d'essai altérée.")


def test_ca_valid_but_wrong_identity_is_rejected():
    host = lab_host("docker.lab")
    cases = _ready(host)
    valid = host.run("openssl verify -purpose any -CAfile %s %s", f"{WORK}/trust/ca.crt", f"{WORK}/keys/other.crt")
    assert valid.rc == 0, message(en="The counterexample must have a valid chain.", fr="Le contre-exemple doit avoir une chaîne valide.")
    wrong = _verify(host, cases["artifact"], **cases["other"])
    assert wrong.rc == 1, message(
        en="A valid signature from the trusted CA but another identity must be refused.",
        fr="Une signature valide issue de la CA de confiance mais d'une autre identité doit être refusée.",
    )


def test_other_private_key_and_self_asserted_approved_identity_are_rejected():
    host = lab_host("docker.lab")
    cases = _ready(host)
    for certificate in ("approved", "rogue"):
        refused = _verify(host, cases["artifact"], cases["rogue"]["signature"], cases[certificate]["certificate"])
        assert refused.rc == 1, message(
            en="Refuse both a different private key and a self-issued certificate claiming the approved identity.",
            fr="Refusez une autre clé privée et un certificat auto-émis revendiquant l'identité approuvée.",
        )
