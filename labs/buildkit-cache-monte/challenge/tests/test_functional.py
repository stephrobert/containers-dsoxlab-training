"""Observe cold/warm builds, not Dockerfile syntax or elapsed time."""

from __future__ import annotations

import hashlib
import secrets
from pathlib import Path

import pytest

from conftest import lab_host, message

WORK = "/opt/lab-buildkit-cache"
BUILDER = "dsoxlab-cache-test"
IMAGE = "dsoxlab-cache:test"
BUILDKIT = "moby/buildkit@sha256:cec9f139f45e93c5c69c60f8b07cfad9f43f4ef6b6a6cd917527fea5ff2e3dea"
CACHE_INSPECTOR = """
import io
import subprocess
import sys
import tarfile
import tempfile
with tempfile.TemporaryFile() as output:
    subprocess.run(["docker", "save", sys.argv[1]], stdout=output, check=True)
    output.seek(0)
    with tarfile.open(fileobj=output) as image:
        for member in image:
            if not member.isfile():
                continue
            content = image.extractfile(member)
            if content is None:
                raise RuntimeError("Cannot read image archive")
            data = content.read()
            if not tarfile.is_tarfile(io.BytesIO(data)):
                continue
            with tarfile.open(fileobj=io.BytesIO(data)) as layer:
                for entry in layer:
                    path = entry.name.removeprefix("./").lstrip("/")
                    if entry.isfile() and entry.size and path.startswith("cache/"):
                        sys.exit(10)
"""


def _receipt(host):
    result = host.run("docker run --rm %s cat /produit/receipt.txt", IMAGE)
    assert result.rc == 0, message(
        en=f"Cannot read the built product: {result.stderr}",
        fr=f"Impossible de lire le produit construit : {result.stderr}",
    )
    return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)


@pytest.fixture(scope="module")
def builds():
    host = lab_host("docker.lab")
    tool = (Path(__file__).resolve().parents[2] / "fixtures/fabriquer.sh").read_text()
    assert host.file(f"{WORK}/fabriquer.sh").content_string == tool, message(
        en="Restore the supplied fabrication tool; change the Dockerfile, not the measurement instrument.",
        fr="Restaurez l'outil de fabrication fourni ; changez le Dockerfile, pas l'instrument de mesure.",
    )
    original = host.file(f"{WORK}/source/version.txt").content_string
    dependency = host.file(f"{WORK}/depot/dependency.txt").content_string
    created = False
    try:
        result = host.run(
            "docker buildx create --name %s --driver docker-container --driver-opt %s",
            BUILDER, f"image={BUILDKIT}",
        )
        assert result.rc == 0, message(
            en=f"Cannot create the isolated builder: {result.stderr}",
            fr=f"Impossible de créer le constructeur isolé : {result.stderr}",
        )
        created = True
        receipts = []
        versions = []
        products = []
        for _ in range(2):
            version = secrets.token_hex(12)
            host.run("printf '%%s\\n' %s > %s", version, f"{WORK}/source/version.txt")
            result = host.run(
                "docker buildx build --builder %s --load --progress plain -t %s %s",
                BUILDER, IMAGE, WORK,
            )
            assert result.rc == 0, message(
                en=f"The build failed: {result.stderr[-1800:]}",
                fr=f"La construction a échoué : {result.stderr[-1800:]}",
            )
            receipts.append(_receipt(host))
            versions.append(version)
            product = host.run("docker run --rm %s cat /produit/dependency.txt", IMAGE)
            products.append(product)
        cache = host.run("docker run --rm %s sh -c %s", IMAGE, "test ! -e /cache || test -z \"$(ls -A /cache)\"")
        layers = host.run("python3 -c %s %s", CACHE_INSPECTOR, IMAGE)
        assert layers.rc in (0, 10), message(
            en=f"Cannot inspect cache files in saved layers: {layers.stderr[-500:]}",
            fr=f"Impossible d'inspecter les fichiers de cache dans les couches sauvegardées : {layers.stderr[-500:]}",
        )
        if layers.rc != 0:
            cache = layers
        yield receipts, versions, products, cache, dependency
    finally:
        host.run("printf %s %s > %s", "%s", original, f"{WORK}/source/version.txt")
        if created:
            result = host.run("docker buildx rm -f %s", BUILDER)
            assert result.rc == 0, message(
                en=f"Cannot remove the test builder: {result.stderr}",
                fr=f"Impossible de retirer le constructeur de test : {result.stderr}",
            )
        if host.run("docker image inspect %s", IMAGE).rc == 0:
            host.run("docker image rm -f %s", IMAGE)


def test_cold_build_and_product(builds):
    receipts, versions, products, _, dependency = builds
    assert receipts[1].get("cache") == "hit", message(
        en="First restore dependency reuse, then prove the cold build and its product.",
        fr="Rétablissez d'abord la réutilisation des dépendances, puis prouvez le build à froid et son produit.",
    )
    digest = hashlib.sha256(dependency.encode()).hexdigest()
    assert all(
        receipt.get("source") == version
        and receipt.get("dependency") == digest
        and product.rc == 0 and product.stdout == dependency
        for receipt, version, product in zip(receipts, versions, products, strict=True)
    ), message(
        en="Both builds must produce the current source and the exact dependency.",
        fr="Les deux builds doivent produire la source courante et la dépendance exacte.",
    )
    assert receipts[0].get("cache") == "miss", message(
        en="The first build must work with an empty cache.",
        fr="Le premier build doit fonctionner avec un cache vide.",
    )


def test_dependency_reused_when_source_changes(builds):
    receipts, _, _, _, _ = builds
    assert receipts[1].get("cache") == "hit", message(
        en="Changing the source installed the dependency again. Mount a persistent build cache.",
        fr="Changer la source a réinstallé la dépendance. Montez un cache de build persistant.",
    )
    assert receipts[0].get("empreinte") and receipts[0]["empreinte"] != receipts[1].get("empreinte"), message(
        en="The build step must actually run again, not return a cached or fixed receipt.",
        fr="L'étape doit réellement rejouer, pas rendre un reçu en cache ou écrit en dur.",
    )


def test_cache_is_not_shipped(builds):
    _, _, _, cache, _ = builds
    assert cache.rc == 0, message(
        en="The dependency cache is present in the final image; keep it outside image layers.",
        fr="Le cache des dépendances est dans l'image finale ; gardez-le hors de ses couches.",
    )
