"""Require real HTTPS, strict client verification and Docker's trusted pull."""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_host_ip, message

REGISTRY = "registry-tls.lab.test:15443"
CA = "/opt/lab-registry-tls/certs/ca.crt"
IMAGE = f"{REGISTRY}/catalogue/appli:1.0"


@pytest.fixture(scope="module")
def host():
    return lab_host("docker.lab")


def _https(host):
    result = host.run(
        "curl --noproxy '*' --fail --silent --show-error --max-time 8 --cacert %s %s",
        CA, f"https://{REGISTRY}/v2/",
    )
    assert result.rc == 0 and json.loads(result.stdout) == {}, message(
        en=f"The registry must answer over HTTPS with its CA and correct hostname: {result.stderr[-500:]}",
        fr=f"Le registre doit répondre en HTTPS avec sa CA et le bon nom : {result.stderr[-500:]}",
    )


def test_tls_is_served_without_a_plaintext_fallback(host):
    _https(host)
    plain = host.run(
        "curl --noproxy '*' --silent --max-time 5 -o /dev/null -w '%%{http_code}' %s",
        f"http://{REGISTRY}/v2/",
    )
    assert plain.stdout.strip() != "200", message(
        en="The registry still serves the API over plaintext HTTP.",
        fr="Le registre sert encore l'API en HTTP non chiffré.",
    )


def test_docker_trusts_the_ca_and_pulls_the_expected_product(host):
    _https(host)
    pulled = host.run("docker pull %s", IMAGE)
    assert pulled.rc == 0, message(
        en=f"Docker cannot pull through TLS. Install the registry CA in certs.d: {pulled.stderr[-600:]}",
        fr=f"Docker ne tire pas via TLS. Installez la CA du registre dans certs.d : {pulled.stderr[-600:]}",
    )
    state = json.loads(host.run("sudo cat /root/.lab-registry-tls.json").stdout)
    identity = host.run("docker image inspect %s --format %s", IMAGE, "{{.Id}}")
    assert identity.rc == 0 and identity.stdout.strip() == state["image"], message(
        en="The pull did not recover the expected image identity.",
        fr="Le pull n'a pas récupéré l'identité d'image attendue.",
    )
    product = host.run("docker run --rm --network none %s", IMAGE)
    assert product.rc == 0 and product.stdout == state["release"] + "\n", message(
        en="The pulled image does not run the expected product without networking.",
        fr="L'image tirée n'exécute pas le produit attendu sans réseau.",
    )
    trusted = host.run("sudo cmp %s %s", CA, f"/etc/docker/certs.d/{REGISTRY}/ca.crt")
    assert trusted.rc == 0, message(
        en="Install the supplied CA as Docker's registry ca.crt, not as an insecure exception.",
        fr="Installez la CA fournie comme ca.crt du registre Docker, pas comme exception insecure.",
    )


def test_wrong_hostname_is_rejected_and_no_insecure_exception_is_added(host):
    _https(host)
    wrong = host.run(
        "curl --noproxy '*' --silent --show-error --max-time 8 --cacert %s "
        "--resolve %s %s",
        CA, f"wrong-registry.lab.test:15443:{lab_host_ip('docker.lab')}",
        "https://wrong-registry.lab.test:15443/v2/",
    )
    assert wrong.rc == 60, message(
        en="A hostname not covered by the certificate must fail TLS verification.",
        fr="Un nom absent du certificat doit échouer à la vérification TLS.",
    )
    pulled = host.run("docker pull %s", IMAGE)
    assert pulled.rc == 0, message(
        en="A Docker pull must succeed with the installed CA.",
        fr="Un pull Docker doit réussir avec la CA installée.",
    )
    info = host.run("docker info --format %s", "{{json .RegistryConfig}}")
    assert info.rc == 0, message(
        en="Cannot inspect Docker's effective registry trust settings.",
        fr="Impossible d'inspecter la confiance effective des registres Docker.",
    )
    registry = json.loads(info.stdout).get("IndexConfigs", {}).get(REGISTRY)
    assert registry is None or registry.get("Secure") is True, message(
        en="Docker treats this registry as insecure; remove the exception instead of bypassing certificate checks.",
        fr="Docker traite ce registre comme insecure ; retirez l'exception au lieu de contourner la vérification du certificat.",
    )
    trusted = f"/etc/docker/certs.d/{REGISTRY}/ca.crt"
    saved = f"/etc/docker/certs.d/{REGISTRY}/ca.saved"
    assert not host.file(saved).exists, message(
        en="A previous trust trial was interrupted; restore ca.saved before checking.",
        fr="Un essai de confiance précédent a été interrompu ; restaurez ca.saved avant de vérifier.",
    )
    moved = host.run("sudo mv %s %s", trusted, saved)
    assert moved.rc == 0, message(
        en="Cannot temporarily remove the registry-specific CA for the trust check.",
        fr="Impossible de retirer temporairement la CA propre au registre pour le contrôle.",
    )
    try:
        untrusted = host.run("docker pull %s", IMAGE)
        assert untrusted.rc != 0 and "x509" in untrusted.stderr.lower(), message(
            en="Without its private CA, Docker must reject the registry certificate, not pull through an insecure bypass.",
            fr="Sans sa CA privée, Docker doit refuser le certificat du registre, pas tirer par un contournement insecure.",
        )
    finally:
        restored = host.run("sudo mv %s %s", saved, trusted)
        assert restored.rc == 0, message(
            en="Cannot restore the registry's CA after the trust check.",
            fr="Impossible de restaurer la CA du registre après le contrôle.",
        )
