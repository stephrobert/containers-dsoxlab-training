"""Recover a complete delivery without source registry or Docker cache."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import PurePosixPath

import pytest

from conftest import lab_host, message

WORK = "/opt/lab-air-gap"
ARCHIVE = f"{WORK}/livraison.tar"
DELIVERED = "dsoxlab-air-gap:livree"
TRIAL = "dsoxlab-air-gap:verification"
REGISTRY = "dsoxlab-air-gap-registry"


@pytest.fixture
def host():
    return lab_host("docker.lab")


@contextmanager
def _delivery(host):
    archive = host.file(ARCHIVE)
    assert archive.is_file and archive.size > 0, message(
        en=f"Deliver a nonempty Docker archive at {ARCHIVE}, not just a registry reference.",
        fr=f"Livrez une archive Docker non vide dans {ARCHIVE}, pas seulement une référence de registre.",
    )
    checksum = host.file(f"{ARCHIVE}.sha256")
    actual = host.run("sha256sum %s", ARCHIVE)
    assert checksum.is_file and actual.rc == 0, message(
        en="Provide livraison.tar.sha256 and a readable archive.",
        fr="Fournissez livraison.tar.sha256 et une archive lisible.",
    )
    expected_line = actual.stdout.split()[0] + "  livraison.tar"
    assert checksum.content_string.strip() == expected_line, message(
        en="The SHA-256 receipt must name livraison.tar and match its complete current bytes.",
        fr="Le reçu SHA-256 doit nommer livraison.tar et correspondre à tous ses octets actuels.",
    )
    created = host.run("mktemp -d %s", f"{WORK}/verification.XXXXXXXX")
    directory = created.stdout.strip()
    assert created.rc == 0 and PurePosixPath(directory).parent == PurePosixPath(WORK) and PurePosixPath(directory).name.startswith("verification."), message(
        en="Cannot create a fresh independent archive reader.",
        fr="Impossible de créer un lecteur d'archive indépendant neuf.",
    )
    try:
        copied = host.run(
            "skopeo copy %s %s",
            f"docker-archive:{ARCHIVE}:{DELIVERED}", f"dir:{directory}/image",
        )
        assert copied.rc == 0, message(
            en=f"A cache-free client cannot read every config and layer from the delivery: {copied.stderr[-600:]}",
            fr=f"Un client sans cache ne peut pas lire toute la configuration et toutes les couches de la livraison : {copied.stderr[-600:]}",
        )
        expected = json.loads(host.file("/root/.lab-air-gap.json").content_string)
        manifest = json.loads(host.file(f"{directory}/image/manifest.json").content_string)
        assert manifest.get("config", {}).get("digest") == expected["image"] and manifest.get("layers"), message(
            en="The delivery must contain the exact published product and its layers, not an exported container filesystem.",
            fr="La livraison doit contenir le produit publié exact et ses couches, pas un export du système de fichiers d'un conteneur.",
        )
        yield expected, directory
    finally:
        removed = host.run("rm -rf -- %s", directory)
        assert removed.rc == 0, message(
            en="Cannot remove the isolated archive reader.",
            fr="Impossible de retirer le lecteur d'archive isolé.",
        )


def test_delivery_is_complete_and_has_a_matching_checksum(host):
    with _delivery(host):
        pass


def test_delivery_recovers_and_runs_with_the_source_registry_stopped(host):
    assert host.file(ARCHIVE).is_file, message(
        en="Create the delivery archive before attempting offline recovery.",
        fr="Créez l'archive de livraison avant d'essayer la récupération hors ligne.",
    )
    inspected = host.run("docker inspect %s --format %s", REGISTRY, "{{.State.Running}}")
    assert inspected.rc == 0, message(
        en="The source registry bench must still exist.",
        fr="Le registre d'origine du banc doit toujours exister.",
    )
    running = inspected.stdout.strip() == "true"
    try:
        if running:
            stopped = host.run("docker stop %s", REGISTRY)
            assert stopped.rc == 0, message(
                en="Cannot stop the source registry for the offline trial.",
                fr="Impossible d'arrêter le registre d'origine pour l'essai hors ligne.",
            )
        unreachable = host.run(
            "curl --noproxy '*' --silent --show-error --max-time 3 http://127.0.0.1:15006/v2/"
        )
        assert unreachable.rc == 7, message(
            en="The source registry must be unreachable during the offline trial.",
            fr="Le registre d'origine doit être inaccessible pendant l'essai hors ligne.",
        )
        with _delivery(host) as (expected, directory):
            repacked = host.run(
                "skopeo copy %s %s",
                f"dir:{directory}/image", f"docker-archive:{directory}/recovered.tar:{TRIAL}",
            )
            assert repacked.rc == 0, message(
                en="Cannot repack the independently recovered delivery for Docker.",
                fr="Impossible de reconditionner la livraison récupérée indépendamment pour Docker.",
            )
            loaded = host.run("docker load -i %s", f"{directory}/recovered.tar")
            assert loaded.rc == 0, message(
                en="Docker cannot load the recovered offline image.",
                fr="Docker ne peut pas charger l'image récupérée hors ligne.",
            )
            identity = host.run("docker image inspect %s --format %s", TRIAL, "{{.Id}}")
            assert identity.rc == 0 and identity.stdout.strip() == expected["image"], message(
                en="The offline image must retain the published image identity.",
                fr="L'image hors ligne doit conserver l'identité publiée.",
            )
            product = host.run("docker run --rm --pull never --network none %s", TRIAL)
            assert product.rc == 0 and product.stdout.strip() == expected["release"], message(
                en="The recovered product must run without pulling or networking and print the published release.",
                fr="Le produit récupéré doit tourner sans pull ni réseau et afficher la release publiée.",
            )
    finally:
        if running:
            started = host.run("docker start %s", REGISTRY)
            assert started.rc == 0, message(
                en="Cannot restore the source registry after the offline trial.",
                fr="Impossible de restaurer le registre d'origine après l'essai hors ligne.",
            )
            ready = host.run(
                "curl --noproxy '*' --fail --silent --show-error --retry 10 --retry-connrefused --retry-delay 1 --max-time 3 http://127.0.0.1:15006/v2/"
            )
            assert ready.rc == 0, message(
                en="The restored source registry does not answer.",
                fr="Le registre d'origine restauré ne répond pas.",
            )
        images = host.run("docker image ls -q --filter reference=%s", TRIAL)
        assert images.rc == 0, message(
            en="Cannot inspect the offline trial image for cleanup.",
            fr="Impossible d'inspecter l'image d'essai hors ligne pour le nettoyage.",
        )
        if images.stdout.strip():
            removed = host.run("docker image rm -f %s", TRIAL)
            assert removed.rc == 0, message(
                en="Cannot remove the offline trial image.",
                fr="Impossible de retirer l'image d'essai hors ligne.",
            )
