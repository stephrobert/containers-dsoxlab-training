"""Read the remote manifest and recover all blobs without Docker's local cache."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import lab_host, message

REMOTE = "127.0.0.1:15000/catalogue/appli:1.0"
CONSUMER = "dsoxlab-registry:consumer"
CONTAINER = "dsoxlab-registry-consumer"
ACCEPT = "application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.manifest.v1+json"


@pytest.fixture(scope="module")
def host():
    return lab_host("docker.lab")


def _publication(host):
    expected = json.loads(host.run("sudo cat /root/.lab-registry-push.json").stdout)
    result = host.run(
        "curl --fail --silent --show-error --max-time 8 -H %s %s",
        f"Accept: {ACCEPT}",
        "http://127.0.0.1:15000/v2/catalogue/appli/manifests/1.0",
    )
    assert result.rc == 0, message(
        en=f"The registry does not serve catalogue/appli:1.0. Tag and push the local release: {result.stderr}",
        fr=f"Le registre ne sert pas catalogue/appli:1.0. Étiquetez et poussez la release locale : {result.stderr}",
    )
    manifest = json.loads(result.stdout)
    assert manifest.get("config", {}).get("digest") == expected["image"], message(
        en="The published manifest does not identify the supplied release image.",
        fr="Le manifeste publié n'identifie pas l'image de release fournie.",
    )
    return expected, manifest


def test_registry_serves_the_exact_release(host):
    _, manifest = _publication(host)
    assert manifest.get("layers"), message(
        en="The published image has no layers.",
        fr="L'image publiée n'a aucune couche.",
    )


def test_an_independent_client_can_recover_and_run_it(host):
    expected, _ = _publication(host)
    result = host.run("mktemp -d /tmp/dsoxlab-registry-consumer.XXXXXXXX")
    directory = result.stdout.strip()
    assert (
        result.rc == 0
        and Path(directory).parent == Path("/tmp")  # noqa: S108 - validate mktemp's result before cleanup
        and Path(directory).name.startswith("dsoxlab-registry-consumer.")
    ), message(
        en="Cannot create an isolated download directory.",
        fr="Impossible de créer le répertoire isolé de téléchargement.",
    )
    try:
        downloaded = host.run(
            "skopeo copy --retry-times 1 --src-tls-verify=false %s %s",
            f"docker://{REMOTE}", f"docker-archive:{directory}/image.tar:{CONSUMER}",
        )
        assert downloaded.rc == 0, message(
            en=f"An independent client cannot fetch the manifest and every layer: {downloaded.stderr[-600:]}",
            fr=f"Un client indépendant ne récupère pas le manifeste et toutes ses couches : {downloaded.stderr[-600:]}",
        )
        loaded = host.run("docker load -i %s/image.tar", directory)
        assert loaded.rc == 0, message(
            en=f"The downloaded archive cannot be loaded: {loaded.stderr}",
            fr=f"L'archive téléchargée ne peut pas être chargée : {loaded.stderr}",
        )
        identity = host.run("docker image inspect %s --format %s", CONSUMER, "{{.Id}}")
        assert identity.rc == 0 and identity.stdout.strip() == expected["image"], message(
            en="The recovered image is not identical to the supplied release.",
            fr="L'image récupérée n'est pas identique à la release fournie.",
        )
        product = host.run("docker run --name %s --network none %s", CONTAINER, CONSUMER)
        assert product.rc == 0 and product.stdout == expected["release"] + "\n", message(
            en="The recovered image does not run the supplied release without a network.",
            fr="L'image récupérée n'exécute pas la release fournie sans réseau.",
        )
    finally:
        if host.run("docker container inspect %s", CONTAINER).rc == 0:
            removed = host.run("docker rm -f %s", CONTAINER)
            assert removed.rc == 0, message(
                en="Cannot remove the consumer container.",
                fr="Impossible de retirer le conteneur consommateur.",
            )
        if host.run("docker image inspect %s", CONSUMER).rc == 0:
            removed = host.run("docker image rm -f %s", CONSUMER)
            assert removed.rc == 0, message(
                en="Cannot remove the consumer image tag.",
                fr="Impossible de retirer l'étiquette de l'image consommateur.",
            )
        removed = host.run("rm -rf -- %s", directory)
        assert removed.rc == 0, message(
            en="Cannot remove the download directory.",
            fr="Impossible de retirer le répertoire de téléchargement.",
        )
