"""Check registry platform identities and real AMD64/ARM64 workload execution."""

from __future__ import annotations

import json
import shlex
import uuid

import pytest

from conftest import lab_host, message

REFERENCE = "127.0.0.1:15318/workshop/probe:release"
ACCEPT = (
    "application/vnd.docker.distribution.manifest.list.v2+json,"
    "application/vnd.oci.image.index.v1+json"
)


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _image_variants(manifests):
    """Les manifestes d'IMAGE de l'index, sans les attestations de provenance.

    POURQUOI ON NE COMPTE PAS LES ENTREES DE L'INDEX. Mesure du 2026-11-03 sur
    Engine 29.9.2 et Buildx 0.38.1, registre local : une poussee
    `--platform linux/amd64,linux/arm64 --push` qui laisse la provenance a son
    DEFAUT produit un index de QUATRE entrees, les deux variantes plus deux
    manifestes d'attestation en `unknown/unknown`, annotes
    `vnd.docker.reference.type=attestation-manifest`. La meme poussee avec
    `--provenance=false` en produit deux.

    Compter les entrees refusait donc la voie que la lecon enseigne, en
    annoncant « deux manifestes distincts » a un apprenant qui venait d'en
    livrer deux. C'est le defaut qu'un test doit eviter : accuser le travail
    pour une forme que l'enonce n'a jamais exigee.

    LE TEMOIN DU MEME BANC dit que rien d'autre ne change : le digest de la
    variante amd64 de l'index a quatre entrees se tire par `docker pull` et son
    `docker image inspect` rend bien `amd64`. Seule la LECTURE de l'index etait
    fautive, pas ce qui en decoule.

    Les deux criteres sont appliques, et non l'un ou l'autre : l'annotation dit
    l'intention, la plateforme `unknown` dit la forme, et un futur buildx peut
    tres bien changer l'une sans l'autre.
    """
    variants = []
    for entry in manifests:
        annotations = entry.get("annotations") or {}
        platform = entry.get("platform") or {}
        if annotations.get("vnd.docker.reference.type") == "attestation-manifest":
            continue
        if "unknown" in (platform.get("os"), platform.get("architecture")):
            continue
        variants.append(entry)
    return variants


def _index(host):
    program = (
        "import json,urllib.request;"
        "r=urllib.request.urlopen(urllib.request.Request("
        "'http://127.0.0.1:15318/v2/workshop/probe/manifests/release',"
        f"headers={{'Accept':{ACCEPT!r}}}),timeout=5);"
        "print(json.dumps({'digest':r.headers['Docker-Content-Digest'],"
        "'index':json.load(r)}))"
    )
    result = host.run(shlex.join(["python3", "-c", program]))
    assert result.rc == 0, message(
        en="Publish the release image index to the workshop registry.",
        fr="Publiez l'index de release dans le registre de l'atelier.",
    )
    measured = json.loads(result.stdout)
    variants = _image_variants(measured["index"].get("manifests", []))
    platforms = [
        (entry.get("platform", {}).get("os"), entry.get("platform", {}).get("architecture"))
        for entry in variants
    ]
    assert len(variants) == 2 and set(platforms) == {
        ("linux", "amd64"), ("linux", "arm64"),
    } and len({entry["digest"] for entry in variants}) == 2, message(
        en="A release needs two distinct image variants, one Linux AMD64 and one "
           "Linux ARM64. Provenance attestation manifests do not count.",
        fr="Une release exige deux variantes d'image distinctes, Linux AMD64 et "
           "Linux ARM64. Les manifestes d'attestation de provenance ne comptent pas.",
    )
    measured["variants"] = variants
    return measured


def test_published_index_identifies_two_distinct_platforms(host):
    _index(host)


@pytest.mark.parametrize("architecture", ["amd64", "arm64"])
def test_each_platform_executes_the_real_workload_and_rejects_invalid_input(host, architecture):
    measured = _index(host)
    value = uuid.uuid4().int % 900000 + 1
    selected = next(
        entry for entry in measured["variants"]
        if entry["platform"]["architecture"] == architecture
    )
    # The classic image store cannot retain two platforms under one index digest.
    reference = REFERENCE.split(":release")[0] + "@" + selected["digest"]
    pulled = host.run("docker pull --platform %s %s", f"linux/{architecture}", reference)
    assert pulled.rc == 0, message(
        en="Pull the chosen platform by its manifest digest from the published index.",
        fr="Tirez la plateforme par le digest de son manifeste dans l'index publié.",
    )
    inspected = host.run("docker image inspect %s", reference)
    assert inspected.rc == 0 and json.loads(inspected.stdout)[0]["Architecture"] == architecture, message(
        en="The pulled image configuration must agree with the index platform.",
        fr="La configuration de l'image tirée doit correspondre à la plateforme de l'index.",
    )
    container = f"dsoxlab-multiarch-inspect-{architecture}"
    created = host.run("docker create --name %s --platform %s %s 1", container, f"linux/{architecture}", reference)
    assert created.rc == 0, message(
        en="Create a stopped inspection container for the selected manifest.",
        fr="Créez un conteneur d'inspection arrêté pour le manifeste choisi.",
    )
    try:
        program = (
            "import io,struct,subprocess,tarfile;"
            f"data=subprocess.check_output(['docker','cp',{(container + ':/probe')!r},'-']);"
            "archive=tarfile.open(fileobj=io.BytesIO(data));"
            "probe=archive.extractfile('probe').read(20);"
            "print(probe[:4].hex(),struct.unpack('<H',probe[18:20])[0])"
        )
        binary = host.run(shlex.join(["python3", "-c", program]))
        assert binary.rc == 0 and binary.stdout.strip() == f"7f454c46 {62 if architecture == 'amd64' else 183}", message(
            en="The actual ELF executable must target the declared architecture, not just its metadata.",
            fr="L'exécutable ELF réel doit cibler l'architecture déclarée, pas seulement ses métadonnées.",
        )
    finally:
        removed = host.run("docker rm %s", container)
        assert removed.rc == 0, message(
            en="Remove the temporary inspection container.",
            fr="Retirez le conteneur temporaire d'inspection.",
        )
    result = host.run(
        "docker run --rm --network none --platform %s %s %s",
        f"linux/{architecture}", reference, str(value),
    )
    assert result.rc == 0, message(
        en="Actually execute both platforms; ARM64 uses the VM-local QEMU interpreter.",
        fr="Exécutez réellement les deux plateformes ; ARM64 utilise QEMU dans la VM.",
    )
    assert json.loads(result.stdout) == {
        "architecture": architecture, "input": value, "square": value * value,
    }, message(
        en="The executed binary must report its real architecture and compute the fresh input.",
        fr="Le binaire exécuté annonce son architecture réelle et calcule l'entrée nouvelle.",
    )
    invalid = host.run(
        "docker run --rm --network none --platform %s %s invalid",
        f"linux/{architecture}", reference,
    )
    assert invalid.rc == 2 and not invalid.stdout.strip(), message(
        en="Both platform variants must reject malformed input with exit status 2.",
        fr="Les deux variantes refusent une entrée invalide avec un code de sortie 2.",
    )
