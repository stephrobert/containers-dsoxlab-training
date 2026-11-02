"""Prove the running identity, its product and remote availability by digest."""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, message

CONTAINER = "dsoxlab-digest-app"


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

def _original(host):
    expected = json.loads(host.run("sudo cat /root/.lab-registry-digest.json").stdout)
    result = host.run("docker container inspect %s", CONTAINER)
    assert result.rc == 0, message(
        en=f"Start the recovered release as {CONTAINER}.",
        fr=f"Démarrez la release retrouvée sous le nom {CONTAINER}.",
    )
    container = json.loads(result.stdout)[0]
    assert container["State"]["Running"] and container["Image"] == expected["image"], message(
        en="The running container is not the original image: the stable tag now points elsewhere.",
        fr="Le conteneur en cours n'est pas l'image d'origine : le tag stable pointe ailleurs.",
    )
    return expected, container


def test_original_product_is_in_service(host):
    expected, _ = _original(host)
    result = host.run("docker exec %s cat /release.txt", CONTAINER)
    assert result.rc == 0 and result.stdout == expected["release"] + "\n", message(
        en="The running image does not contain the original delivery's product.",
        fr="L'image en service ne contient pas le produit de la livraison d'origine.",
    )


def test_runtime_reference_is_immutable(host):
    expected, container = _original(host)
    assert container["Config"]["Image"] == expected["reference"], message(
        en="The runtime still uses a tag or image ID; use the registry reference pinned to the delivery's manifest digest.",
        fr="L'exécution utilise encore un tag ou un ID d'image ; utilisez la référence du registre épinglée au digest de manifeste du bon de livraison.",
    )


def test_original_manifest_remains_available_independently(host):
    expected, _ = _original(host)
    result = host.run(
        "skopeo inspect --raw --tls-verify=false %s",
        f"docker://{expected['reference']}",
    )
    assert result.rc == 0, message(
        en=f"The original digest is not available from the registry: {result.stderr[-500:]}",
        fr=f"Le digest d'origine n'est pas disponible dans le registre : {result.stderr[-500:]}",
    )
    manifest = json.loads(result.stdout)
    servi = host.run(
        "skopeo inspect --tls-verify=false --format %s %s",
        "{{.Digest}}", f"docker://{expected['reference']}",
    )
    assert _identifie(manifest, servi.stdout.strip(), expected["image"]), message(
        en="The independently fetched artifact does not identify the original image.",
        fr="L'artefact récupéré indépendamment n'identifie pas l'image d'origine.",
    )
    stable = host.run(
        "skopeo inspect --raw --tls-verify=false docker://127.0.0.1:15002/catalogue/appli:stable"
    )
    stable_servi = host.run(
        "skopeo inspect --tls-verify=false --format %s %s",
        "{{.Digest}}",
        "docker://127.0.0.1:15002/catalogue/appli:stable",
    )
    assert stable.rc == 0 and _identifie(
        json.loads(stable.stdout), stable_servi.stdout.strip(),
        expected["replacement"],
    ), message(
        en="Keep stable pointing at its replacement: recover the original digest instead of rewriting the tag.",
        fr="Gardez stable sur son remplacement : retrouvez le digest d'origine au lieu de réécrire le tag.",
    )
