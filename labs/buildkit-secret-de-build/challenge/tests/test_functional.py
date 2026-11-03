"""Verify a real private product, fresh credentials and all saved image layers."""

from __future__ import annotations

import base64
import json
import secrets
from pathlib import Path

import pytest

from conftest import lab_host, lab_host_ip, message

WORK = "/opt/lab-buildkit-secret"
STATE = "/root/.lab-buildkit-secret.json"
IMAGE = "dsoxlab-secret:finale"
TRIAL_IMAGE = "dsoxlab-secret:test"
BUILDER = "dsoxlab-secret-test"
BUILDKIT = "moby/buildkit@sha256:99368f3e46177c6405b9740e4461d91cee004128daeecca78d4ceac50ec1da5c"
INSPECTOR = (Path(__file__).resolve().parents[2] / "fixtures/inspect-image.py").read_text()
CONTEXT_INSPECTOR = (
    Path(__file__).resolve().parents[2] / "fixtures/inspect-context.py"
).read_text()


@pytest.fixture(scope="module")
def host():
    return lab_host("docker.lab")


def _require_product(host):
    state = json.loads(host.run("sudo cat %s", STATE).stdout)
    product = host.run("docker run --rm %s", IMAGE)
    assert product.rc == 0 and product.stdout == state["artifact"] + "\n", message(
        en=f"Build {IMAGE} so it serves the exact private product, not an empty or fixed answer.",
        fr=f"Construisez {IMAGE} pour qu'elle rende le produit privé exact, pas une réponse vide ou fixe.",
    )
    return state


def _inspect(host, image, token_path):
    result = host.run("sudo python3 -c %s %s %s", INSPECTOR, image, token_path)
    assert result.rc == 0, message(
        en=f"Image inspection failed: {result.stderr[-500:]}",
        fr=f"L'inspection de l'image a échoué : {result.stderr[-500:]}",
    )
    return json.loads(result.stdout)


def test_product_and_secret_absent_from_image(host):
    _require_product(host)
    report = _inspect(host, IMAGE, f"{WORK}/depot.token")
    assert report["clean"], message(
        en=f"The secret is still in {report.get('surface')}. Runtime deletion does not remove saved layers or history.",
        fr=f"Le secret reste dans {report.get('surface')}. Une suppression ne retire ni les couches sauvegardées ni l'historique.",
    )


def test_secret_never_enters_the_build_context(host):
    """Le scenario l'exige deux fois, et rien ne le mesurait.

    « Le secret pedagogique est dans /opt/lab-buildkit-secret/depot.token, hors
    du contexte de build », puis « il ne doit pas etre copie dans le contexte ».
    Les trois autres controles inspectent l'IMAGE, et un fichier present dans le
    contexte mais jamais `COPY` n'entre dans aucune couche : l'exigence etait
    donc invisible, et l'apprenant la croyait notee.

    Ce controle porte sur le REPERTOIRE, sans exception pour `.dockerignore`.
    Un secret exclu ne part pas au demon, mais il reste sur le disque, dans ce
    qu'on versionne, et une exclusion s'oublie. Le message le dit a l'apprenant
    plutot que de le laisser deviner.
    """
    _require_product(host)
    result = host.run("sudo python3 -c %s %s %s",
                      CONTEXT_INSPECTOR, f"{WORK}/appli", f"{WORK}/depot.token")
    assert result.rc == 0, message(
        en=f"Build context inspection failed: {result.stderr[-500:]}",
        fr=f"L'inspection du contexte a échoué : {result.stderr[-500:]}",
    )
    report = json.loads(result.stdout)
    # UNE SURFACE NON LUE N'EST PAS UNE SURFACE PROPRE : on leve plutot que de
    # noter l'apprenant sur ce qu'on n'a pas regarde.
    assert not report["illisibles"], message(
        en="Could not read inside the build context: "
           + ", ".join(report["illisibles"]),
        fr="Impossible de lire dans le contexte de build : "
           + ", ".join(report["illisibles"]),
    )
    surfaces = ", ".join(f"{f['chemin']} ({f['ou']})" for f in report["fuites"])
    assert report["propre"], message(
        en=f"The credential file must stay OUT of the build context directory, "
           f"even excluded by .dockerignore: an exclusion gets forgotten, and the "
           f"secret then follows the tree. Found in {surfaces}. Pass it with "
           f"--secret id=depot,src={WORK}/depot.token, whose path is outside "
           f"{WORK}/appli.",
        fr=f"Le fichier d'identifiant doit rester HORS du répertoire de contexte, "
           f"même exclu par .dockerignore : une exclusion s'oublie, et le secret "
           f"suit alors l'arborescence. Trouvé dans {surfaces}. Passez-le par "
           f"--secret id=depot,src={WORK}/depot.token, dont le chemin est en "
           f"dehors de {WORK}/appli.",
    )


@pytest.fixture(scope="module")
def trials(host):
    _require_product(host)
    original = host.run("sudo cat %s", STATE).stdout
    directory = host.run("mktemp -d /tmp/dsoxlab-secret-test.XXXXXXXX")
    temporary = directory.stdout.strip()
    assert (
        directory.rc == 0
        and Path(temporary).parent == Path("/tmp")  # noqa: S108 - validate mktemp's result before cleanup
        and Path(temporary).name.startswith("dsoxlab-secret-test.")
    ), message(
        en="Cannot create the isolated trial directory.",
        fr="Impossible de créer le répertoire isolé de test.",
    )
    created = False
    try:
        copied = host.run("cp -a %s %s/context", f"{WORK}/appli", temporary)
        assert copied.rc == 0, message(
            en="Cannot copy the build context for independent trials.",
            fr="Impossible de copier le contexte pour les essais indépendants.",
        )
        result = host.run(
            "docker buildx create --name %s --driver docker-container --driver-opt %s",
            BUILDER, f"image={BUILDKIT}",
        )
        assert result.rc == 0, message(
            en=f"Cannot create a test builder: {result.stderr}",
            fr=f"Impossible de créer un constructeur de test : {result.stderr}",
        )
        created = True
        token = "lab-" + secrets.token_hex(16)
        artifact = "artifact-" + secrets.token_hex(16)
        state = json.dumps({"token": token, "artifact": artifact})
        result = host.run("printf '%%s' %s | sudo tee %s >/dev/null", state, STATE)
        assert result.rc == 0, message(
            en="Cannot rotate the private repository's trial identity.",
            fr="Impossible de renouveler l'identité d'essai du dépôt privé.",
        )
        result = host.run("printf '%%s' %s > %s/token", token, temporary)
        assert result.rc == 0, message(
            en="Cannot write the trial secret.",
            fr="Impossible d'écrire le secret d'essai.",
        )
        url = f"http://{lab_host_ip('docker.lab')}:18083/artifact"
        command = (
            "docker buildx build --builder %s --no-cache --progress plain --load "
            "--build-arg %s --secret %s -t %s %s/context"
        )
        good = host.run(
            command, BUILDER, f"DEPOT_URL={url}",
            f"id=depot,src={temporary}/token", TRIAL_IMAGE, temporary,
        )
        product = host.run("docker run --rm %s", TRIAL_IMAGE) if good.rc == 0 else None
        report = _inspect(host, TRIAL_IMAGE, f"{temporary}/token") if good.rc == 0 else None
        wrong_token = secrets.token_hex(16)
        written_wrong = host.run("printf '%%s' %s > %s/wrong", wrong_token, temporary)
        assert written_wrong.rc == 0, message(
            en="Write the unauthorized trial credential.",
            fr="Écrivez l'identifiant d'essai non autorisé.",
        )
        wrong = host.run(
            command, BUILDER, f"DEPOT_URL={url}",
            f"id=depot,src={temporary}/wrong", TRIAL_IMAGE, temporary,
        )
        absent = host.run(
            "docker buildx build --builder %s --no-cache --progress plain --load "
            "--build-arg %s -t %s %s/context",
            BUILDER, f"DEPOT_URL={url}", TRIAL_IMAGE, temporary,
        )
        if report is not None:
            logs = "".join(result.stdout + result.stderr for result in [good, wrong, absent])
            variants = [
                variant for secret in [token, wrong_token]
                for variant in [
                    secret, base64.b64encode(secret.encode()).decode(), secret.encode().hex(),
                ]
            ]
            report["logs_clean"] = not any(variant in logs for variant in variants)
        yield good, product, report, artifact, wrong, absent
    finally:
        restored = host.run("printf '%%s' %s | sudo tee %s >/dev/null", original, STATE)
        removed = host.run("rm -rf -- %s", temporary)
        if created:
            removed_builder = host.run("docker buildx rm -f %s", BUILDER)
            assert removed_builder.rc == 0, message(
                en="Cannot remove the test builder.",
                fr="Impossible de retirer le constructeur de test.",
            )
        if host.run("docker image inspect %s", TRIAL_IMAGE).rc == 0:
            deleted = host.run("docker image rm -f %s", TRIAL_IMAGE)
            assert deleted.rc == 0, message(
                en="Cannot remove the trial image.",
                fr="Impossible de retirer l'image d'essai.",
            )
        assert restored.rc == 0 and removed.rc == 0, message(
            en="Cannot restore the repository or remove the trial directory.",
            fr="Impossible de restaurer le dépôt ou de retirer le répertoire d'essai.",
        )


def test_fresh_identity_rebuilds_without_leaks(trials):
    good, product, report, artifact, _, _ = trials
    assert good.rc == 0, message(
        en="A fresh secret passed with --secret id=depot must build without DEPOT_SECRET arguments.",
        fr="Un secret neuf passé avec --secret id=depot doit construire sans argument DEPOT_SECRET.",
    )
    assert product is not None and product.rc == 0 and product.stdout == artifact + "\n", message(
        en="The rebuilt image does not serve the newly issued private product.",
        fr="L'image reconstruite ne rend pas le nouveau produit privé.",
    )
    assert report is not None and report["clean"] and report["logs_clean"], message(
        en="The fresh credentials must not leak into the rebuilt image or captured build logs, including base64/hex forms.",
        fr="Les identifiants ne fuient ni dans l'image reconstruite ni les logs capturés, y compris en base64/hex.",
    )


def test_wrong_and_missing_secrets_are_rejected(trials):
    good, _, _, _, wrong, absent = trials
    assert good.rc == 0 and wrong.rc != 0 and absent.rc != 0, message(
        en="A correct secret must build; a missing or wrong secret must fail, not reuse a cached or fixed product.",
        fr="Le bon secret doit construire ; un secret absent ou faux doit échouer, pas réutiliser un produit fixe ou en cache.",
    )
