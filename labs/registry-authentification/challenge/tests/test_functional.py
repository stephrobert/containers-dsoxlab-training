"""Measure registry authorization and real authenticated transfers."""

from __future__ import annotations

import json
import secrets

import pytest

from conftest import lab_host, message

REGISTRY = "registry-auth.lab.test:15445"
WORK = "/opt/lab-registry-auth"
CA = f"{WORK}/certs/ca.crt"
CLIENT = f"{WORK}/client"
IMAGE = f"{REGISTRY}/catalogue/appli:1.0"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _request(host, path, credentials=None, method="GET"):
    auth = " --user %s" if credentials is not None else ""
    args = [CA, method, f"https://{REGISTRY}{path}"]
    if credentials is not None:
        args.append(credentials)
    return host.run(
        "curl --noproxy '*' --silent --show-error --max-time 8 --cacert %s "
        "--request %s --output /dev/null --write-out '%%{http_code}' %s" + auth,
        *args,
    )


def _state(host):
    return json.loads(host.file("/root/.lab-registry-auth.json").content_string)


def _protected(host):
    anonymous = _request(host, "/v2/")
    assert anonymous.rc == 0 and anonymous.stdout == "401", message(
        en="The verified HTTPS registry API must reject anonymous access with 401.",
        fr="L'API HTTPS vérifiée du registre doit refuser l'accès anonyme avec 401.",
    )
    headers = host.run(
        "curl --noproxy '*' --silent --show-error --max-time 8 --cacert %s --dump-header - --output /dev/null %s",
        CA, f"https://{REGISTRY}/v2/",
    )
    assert headers.rc == 0 and 'www-authenticate: basic realm=' in headers.stdout.lower(), message(
        en="The registry must issue an HTTP Basic authentication challenge.",
        fr="Le registre doit émettre un challenge d'authentification HTTP Basic.",
    )
    state = _state(host)
    wrong = _request(host, "/v2/", f"{state['username']}:{secrets.token_hex(24)}")
    assert wrong.rc == 0 and wrong.stdout == "401", message(
        en="Wrong credentials must be rejected with 401, not accepted or crash the server.",
        fr="Des identifiants erronés doivent être refusés avec 401, pas acceptés ni faire planter le serveur.",
    )
    valid = _request(host, "/v2/", f"{state['username']}:{state['password']}")
    assert valid.rc == 0 and valid.stdout == "200", message(
        en="The supplied account must reach the registry over verified HTTPS.",
        fr="Le compte fourni doit atteindre le registre en HTTPS vérifié.",
    )
    return state


def test_anonymous_and_wrong_credentials_are_rejected(host):
    _protected(host)
    anonymous_manifest = _request(host, "/v2/catalogue/appli/manifests/1.0")
    anonymous_upload = _request(host, "/v2/catalogue/probe/blobs/uploads/", method="POST")
    assert all(r.rc == 0 and r.stdout == "401" for r in (anonymous_manifest, anonymous_upload)), message(
        en="Both downloading manifests and starting uploads must reject anonymous clients.",
        fr="Le téléchargement de manifestes et le démarrage d'un upload doivent refuser les clients anonymes.",
    )


def test_saved_docker_login_pulls_the_actual_product(host):
    state = _protected(host)
    pulled = host.run("docker --config %s pull %s", CLIENT, IMAGE)
    assert pulled.rc == 0, message(
        en=f"Log in using the dedicated client directory, then pull the product: {pulled.stderr[-500:]}",
        fr=f"Connectez-vous avec le répertoire client dédié, puis tirez le produit : {pulled.stderr[-500:]}",
    )
    inspected = host.run("docker image inspect %s --format %s", IMAGE, "{{.Id}}")
    assert inspected.rc == 0 and inspected.stdout.strip() == state["image"], message(
        en="The pull must retrieve the published product, not a substitute image.",
        fr="Le pull doit récupérer le produit publié, pas une image de remplacement.",
    )
    result = host.run("docker run --rm --network none %s", IMAGE)
    assert result.rc == 0 and result.stdout.strip() == state["release"], message(
        en="The pulled product must print the prepared release without network access.",
        fr="Le produit tiré doit afficher la release préparée sans accès réseau.",
    )
    trusted = f"/etc/docker/certs.d/{REGISTRY}/ca.crt"
    saved = f"/etc/docker/certs.d/{REGISTRY}/ca.saved"
    assert not host.file(saved).exists, message(
        en="Restore ca.saved from an interrupted trust trial before checking.",
        fr="Restaurez ca.saved d'un contrôle de confiance interrompu avant de vérifier.",
    )
    moved = host.run("mv %s %s", trusted, saved)
    assert moved.rc == 0, message(
        en="Cannot temporarily remove the registry-specific CA.",
        fr="Impossible de retirer temporairement la CA propre au registre.",
    )
    try:
        untrusted = host.run("docker --config %s pull %s", CLIENT, IMAGE)
        assert untrusted.rc != 0 and "x509" in untrusted.stderr.lower(), message(
            en="Docker must reject this private certificate without its CA, even with valid credentials.",
            fr="Docker doit refuser ce certificat privé sans sa CA, même avec des identifiants valides.",
        )
    finally:
        restored = host.run("mv %s %s", saved, trusted)
        assert restored.rc == 0, message(
            en="Cannot restore the registry CA after the trust trial.",
            fr="Impossible de restaurer la CA du registre après le contrôle.",
        )


def test_saved_login_can_publish_and_retrieve_a_new_product(host):
    _protected(host)
    tag = f"{REGISTRY}/catalogue/probe:{secrets.token_hex(8)}"
    nonce = secrets.token_hex(24)
    context = f"{WORK}/probe"
    try:
        prepared = host.run(
            "mkdir -p %s && printf '%%s\\n' %s > %s && cp %s %s",
            context, nonce, f"{context}/release.txt", f"{WORK}/appli/Dockerfile", f"{context}/Dockerfile",
        )
        assert prepared.rc == 0, message(
            en="Cannot prepare a fresh product for the publication check.",
            fr="Impossible de préparer un produit neuf pour le contrôle de publication.",
        )
        built = host.run("docker build -t %s %s", tag, context)
        assert built.rc == 0, message(
            en=f"Cannot build the publication probe: {built.stderr[-500:]}",
            fr=f"Impossible de construire la sonde de publication : {built.stderr[-500:]}",
        )
        pushed = host.run("docker --config %s push %s", CLIENT, tag)
        assert pushed.rc == 0, message(
            en=f"The saved Docker login must allow a real push: {pushed.stderr[-500:]}",
            fr=f"La connexion Docker enregistrée doit permettre un vrai push : {pushed.stderr[-500:]}",
        )
        removed = host.run("docker image rm %s", tag)
        assert removed.rc == 0, message(
            en="Cannot remove the local probe before checking its transfer back.",
            fr="Impossible de retirer la sonde locale avant de contrôler son transfert retour.",
        )
        pulled = host.run("docker --config %s pull %s", CLIENT, tag)
        assert pulled.rc == 0, message(
            en="The newly published product must be retrievable with the saved login.",
            fr="Le produit nouvellement publié doit être récupérable avec la connexion enregistrée.",
        )
        result = host.run("docker run --rm --network none %s", tag)
        assert result.rc == 0 and result.stdout.strip() == nonce, message(
            en="The round trip must preserve the fresh product's content.",
            fr="L'aller-retour doit conserver le contenu du produit neuf.",
        )
    finally:
        images = host.run("docker image ls -q --filter reference=%s", tag)
        assert images.rc == 0, message(
            en="Cannot inspect trial images for cleanup.",
            fr="Impossible d'inspecter les images d'essai pour le nettoyage.",
        )
        if images.stdout.strip():
            removed = host.run("docker image rm -f %s", tag)
            assert removed.rc == 0, message(
                en="Cannot remove the trial image.",
                fr="Impossible de retirer l'image d'essai.",
            )
