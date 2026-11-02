"""Read the remote manifest and recover all blobs without Docker's local cache."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import lab_host, message

REMOTE = "127.0.0.1:15000/catalogue/appli:1.0"
CONSUMER = "dsoxlab-registry:consumer"
CONTAINER = "dsoxlab-registry-consumer"
# LES TYPES D'INDEX SONT DANS L'ACCEPT, et ce n'est pas optionnel :
# mesuré le 2026-11-02, le registre rend 404 quand l'artefact stocké est
# un index OCI et que le client ne l'accepte pas. Docker 29 en magasin
# containerd publie toujours un index.
ACCEPT = ",".join((
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.docker.distribution.manifest.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
))


@pytest.fixture(scope="module")
def host():
    return lab_host("docker.lab")


def _identifie(manifest, servi, attendu):
    """L'artefact publié est-il bien l'image attendue ?

    DEUX FORMES, et une seule preuve. Sous le magasin containerd, Docker 29
    publie un INDEX OCI : il n'a pas de clé `config`, et c'est son propre
    digest qui vaut l'identifiant local de l'image (mesuré le 2026-11-02).
    Sous le magasin classique, le registre sert un manifeste d'image, dont la
    clé `config` porte ce même identifiant.

    `servi` est le digest que le registre annonce pour cette référence, et il
    est relevé indépendamment de `attendu` : les comparer reste une mesure, pas
    une tautologie.
    """
    if "config" in manifest:
        return manifest["config"].get("digest") == attendu
    return bool(manifest.get("manifests")) and servi == attendu

def _publication(host):
    expected = json.loads(host.run("sudo cat /root/.lab-registry-push.json").stdout)
    result = host.run(
        "curl --fail --silent --show-error --max-time 8 -H %s -D %s %s",
        f"Accept: {ACCEPT}", "/tmp/dsoxlab-push-pull.headers",
        "http://127.0.0.1:15000/v2/catalogue/appli/manifests/1.0",
    )
    assert result.rc == 0, message(
        en=f"The registry does not serve catalogue/appli:1.0. Tag and push the local release: {result.stderr}",
        fr=f"Le registre ne sert pas catalogue/appli:1.0. Étiquetez et poussez la release locale : {result.stderr}",
    )
    manifest = json.loads(result.stdout)
    entetes = host.run("cat %s", "/tmp/dsoxlab-push-pull.headers")
    servi = next(
        (l.split(":", 1)[1].strip() for l in entetes.stdout.splitlines()
         if l.lower().startswith("docker-content-digest:")),
        "",
    )
    assert _identifie(manifest, servi, expected["image"]), message(
        en="The published artifact does not identify the supplied release image.",
        fr="L'artefact publié n'identifie pas l'image de release fournie.",
    )
    return expected, manifest


def test_registry_serves_the_exact_release(host):
    _, manifest = _publication(host)
    # UN INDEX NE PORTE PAS `layers`, il porte des manifestes. On descend
    # d'un cran, ce qu'un client fait pour choisir sa plateforme, et on
    # pèse les couches là où elles sont vraiment.
    if "layers" not in manifest:
        plateforme = manifest["manifests"][0]["digest"]
        descendu = host.run(
            "curl --fail --silent --show-error --max-time 8 -H %s %s",
            f"Accept: {ACCEPT}",
            f"http://127.0.0.1:15000/v2/catalogue/appli/manifests/{plateforme}",
        )
        assert descendu.rc == 0, message(
            en="The index entry does not resolve to a platform manifest.",
            fr="L'entrée de l'index ne résout aucun manifeste de plateforme.",
        )
        manifest = json.loads(descendu.stdout)
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
        # SES COUCHES, ET PLUS SON `Id`. Mesuré le 2026-11-02 : une archive
        # `docker-archive` ne porte qu'un manifeste de plateforme, donc
        # `docker load` rend un identifiant DIFFERENT de l'index publié,
        # fatalement. `.RootFS.Layers`, lui, est identique de part en part :
        # c'est la même arborescence, et c'est elle qu'il faut prouver.
        identity = host.run(
            "docker image inspect %s --format %s", CONSUMER,
            "{{range .RootFS.Layers}}{{println .}}{{end}}",
        )
        attendues = host.run(
            "docker image inspect %s --format %s", expected["image"],
            "{{range .RootFS.Layers}}{{println .}}{{end}}",
        )
        assert identity.rc == attendues.rc == 0 and identity.stdout.split() and (
            identity.stdout.split() == attendues.stdout.split()
        ), message(
            en="The recovered image does not carry the supplied release layers.",
            fr="L'image récupérée ne porte pas les couches de la release fournie.",
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
