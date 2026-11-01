"""Rebuild after moving the registry tag; inspect products and approved layers."""

from __future__ import annotations

import json
import secrets
import shlex
from pathlib import Path

import pytest

from conftest import lab_host, message

WORK = "/opt/lab-image-pin"
IMAGE = "dsoxlab-pin:finale"
TRIAL = "dsoxlab-pin:test"
REPO = "127.0.0.1:15004/socle"


@pytest.fixture(scope="module")
def host():
    return lab_host("docker.lab")


def _expected(host):
    result = host.run("sudo cat /root/.lab-image-pin.json")
    assert result.rc == 0, message(
        en="The bench reference is unavailable; rerun the setup.",
        fr="La référence du banc est indisponible ; rejouez le setup.",
    )
    return json.loads(result.stdout)


def _require_approved(host):
    expected = _expected(host)
    product = host.run("docker run --rm --network none %s", IMAGE)
    assert product.rc == 0 and product.stdout == expected["base"] + "\n" + expected["source"] + "\n", message(
        en=f"Build {IMAGE} with the approved base and the current source, not the moved stable tag.",
        fr=f"Construisez {IMAGE} avec le socle approuvé et la source courante, pas avec le tag stable déplacé.",
    )
    result = host.run("docker image inspect %s --format %s", IMAGE, "{{json .RootFS.Layers}}")
    assert result.rc == 0 and json.loads(result.stdout)[:len(expected["layers"])] == expected["layers"], message(
        en="The delivered image must really derive from the approved base layers.",
        fr="L'image livrée doit réellement dériver des couches du socle approuvé.",
    )
    return expected


def test_approved_base_and_source_are_delivered(host):
    _require_approved(host)


@pytest.fixture(scope="module")
def rebuilds(host):
    expected = _require_approved(host)
    created = host.run("mktemp -d /tmp/dsoxlab-pin-test.XXXXXXXX")
    directory = created.stdout.strip()
    assert (
        created.rc == 0
        and Path(directory).parent == Path("/tmp")  # noqa: S108 - verify mktemp before removing the trial
        and Path(directory).name.startswith("dsoxlab-pin-test.")
    ), message(
        en="Cannot create the isolated rebuild context.",
        fr="Impossible de créer le contexte isolé de reconstruction.",
    )
    tag = host.run("skopeo inspect --tls-verify=false %s", f"docker://{REPO}:stable")
    assert tag.rc == 0, message(
        en="Cannot read the tag before its mutation.",
        fr="Impossible de lire le tag avant sa mutation.",
    )
    original = f"{REPO}@{json.loads(tag.stdout)['Digest']}"
    try:
        copied = host.run("cp -a %s/appli %s/context", WORK, directory)
        assert copied.rc == 0, message(
            en="Cannot copy the learner's context.",
            fr="Impossible de copier le contexte de l'apprenant.",
        )
        outputs = []
        layers = []
        sources = []
        for reference in (expected["reference"], f"{REPO}:replacement"):
            moved = host.run(
                "skopeo copy --src-tls-verify=false --dest-tls-verify=false %s %s",
                f"docker://{reference}", f"docker://{REPO}:stable",
            )
            assert moved.rc == 0, message(
                en=f"Cannot change the bench's stable tag: {moved.stderr[-500:]}",
                fr=f"Impossible de changer le tag stable du banc : {moved.stderr[-500:]}",
            )
            source = "source-" + secrets.token_hex(16)
            written = host.run("printf '%%s\\n' %s > %s/context/source.txt", source, directory)
            assert written.rc == 0, message(
                en="Cannot change the trial source.",
                fr="Impossible de changer la source d'essai.",
            )
            built = host.run("docker build --pull --no-cache -t %s %s/context", TRIAL, directory)
            assert built.rc == 0, message(
                en=f"Rebuilding the supplied Dockerfile failed: {built.stderr[-1000:]}",
                fr=f"La reconstruction du Dockerfile fourni a échoué : {built.stderr[-1000:]}",
            )
            outputs.append(host.run("docker run --rm --network none %s", TRIAL))
            inspected = host.run("docker image inspect %s --format %s", TRIAL, "{{json .RootFS.Layers}}")
            assert inspected.rc == 0, message(
                en="Cannot inspect the rebuilt image layers.",
                fr="Impossible d'inspecter les couches de l'image reconstruite.",
            )
            layers.append(json.loads(inspected.stdout))
            sources.append(source)
        yield expected, outputs, layers, sources
    finally:
        restored = host.run(
            "skopeo copy --src-tls-verify=false --dest-tls-verify=false %s %s",
            f"docker://{original}", f"docker://{REPO}:stable",
        )
        images = host.run(
            "docker image ls -aq --filter dangling=true --filter label=dsoxlab.lab=images-epingler-par-digest"
        ).stdout.split()
        if host.run("docker image inspect %s", TRIAL).rc == 0:
            images.append(TRIAL)
        if images:
            removed_images = host.run(shlex.join(["docker", "image", "rm", "-f", *images]))
            assert removed_images.rc == 0, message(
                en="Cannot remove the trial image.",
                fr="Impossible de retirer l'image d'essai.",
            )
        removed = host.run("rm -rf -- %s", directory)
        assert restored.rc == 0 and removed.rc == 0, message(
            en="Cannot restore the registry tag or remove the trial directory.",
            fr="Impossible de restaurer le tag du registre ou de retirer le répertoire d'essai.",
        )


def test_source_changes_rebuild_the_product(rebuilds):
    expected, outputs, _, sources = rebuilds
    assert all(
        output.rc == 0 and output.stdout == expected["base"] + "\n" + source + "\n"
        for output, source in zip(outputs, sources, strict=True)
    ), message(
        en="Each rebuilt product must contain its new source and the approved base, even after moving stable.",
        fr="Chaque produit reconstruit doit contenir sa nouvelle source et le socle approuvé, même après déplacement de stable.",
    )


def test_moving_the_base_tag_does_not_change_base_layers(rebuilds):
    expected, _, layers, _ = rebuilds
    assert all(current[:len(expected["layers"])] == expected["layers"] for current in layers), message(
        en="The base layers changed with stable. Pin the FROM to the approved registry manifest.",
        fr="Les couches du socle ont changé avec stable. Épinglez le FROM au manifeste approuvé du registre.",
    )
