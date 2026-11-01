"""Prove a named volume keeps fresh writes rather than reseeding lost data."""

from __future__ import annotations

import json
import secrets
import shlex
import time

import pytest

from conftest import lab_host, message

PROJECT = "dsoxlab-persistance"
COMPOSE = "/opt/lab-compose-persist/compose.yaml"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _compose(host, *args):
    result = host.run(shlex.join(["docker", "compose", "-p", PROJECT, "-f", COMPOSE, *args]))
    assert result.rc == 0, message(
        en=f"Compose operation failed: {result.stderr[-600:]}",
        fr=f"L'opération Compose a échoué : {result.stderr[-600:]}",
    )


def _app(host):
    found = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={PROJECT}")
    assert found.rc == 0 and len(found.stdout.split()) == 1, message(
        en="Start exactly one app service in project dsoxlab-persistance.",
        fr="Démarrez exactement un service app dans le projet dsoxlab-persistance.",
    )
    inspected = host.run("docker inspect %s", found.stdout.strip())
    assert inspected.rc == 0, message(
        en="Cannot inspect the app container.",
        fr="Impossible d'inspecter le conteneur app.",
    )
    app = json.loads(inspected.stdout)[0]
    image = host.run("docker image inspect dsoxlab-compose-persist:app")
    assert image.rc == 0, message(
        en="Keep the supplied application image.",
        fr="Conservez l'image applicative fournie.",
    )
    original = json.loads(image.stdout)[0]
    assert app["State"]["Running"] and app["Config"]["Labels"].get("com.docker.compose.service") == "app" and app["Image"] == original["Id"] and all(
        app["Config"][key] == original["Config"][key] for key in ("Cmd", "Entrypoint")
    ), message(
        en="Run the supplied app image and command as a Compose service.",
        fr="Exécutez l'image et la commande app fournies comme service Compose.",
    )
    identity = host.run("docker exec %s id -u", app["Id"])
    rights = host.run("docker exec %s stat -c %s /data", app["Id"], "%u:%g:%a")
    assert identity.rc == rights.rc == 0 and identity.stdout.strip() == "10001" and (
        rights.stdout.strip() == "10001:10001:700"
        and app["HostConfig"]["ReadonlyRootfs"]
    ), message(
        en="Run UID 10001 with read-only rootfs and /data owned by UID/GID 10001, mode 0700.",
        fr="Exécutez sous UID 10001, racine en lecture seule et /data appartenant à UID/GID 10001, mode 0700.",
    )
    mounts = app["Mounts"]
    assert len(mounts) == 1 and mounts[0]["Type"] == "volume" and mounts[0]["Destination"] == "/data" and mounts[0]["RW"], message(
        en="Mount only a writable named volume at /data; no bind or anonymous replacement.",
        fr="Montez seulement un volume nommé accessible en écriture sur /data, sans remplacement par bind ou volume anonyme.",
    )
    volume = host.run("docker volume inspect %s", mounts[0]["Name"])
    assert volume.rc == 0, message(
        en="Cannot inspect the data volume.",
        fr="Impossible d'inspecter le volume de données.",
    )
    labels = json.loads(volume.stdout)[0]["Labels"] or {}
    assert labels.get("com.docker.compose.project") == PROJECT and labels.get("com.docker.compose.volume") == "data", message(
        en="Declare the named volume data in this Compose project.",
        fr="Déclarez le volume nommé data dans ce projet Compose.",
    )
    return app, mounts[0]["Name"]


def _denied_access(host, app):
    denied = host.run(
        "docker exec --user 10002:10002 %s sh -c %s", app["Id"],
        "test ! -r /data/value.txt && test ! -w /data/value.txt "
        "&& ! cat /data/value.txt && ! touch /data/unauthorized",
    )
    outside = host.run(
        "docker exec %s sh -c %s", app["Id"],
        "! touch /tmp/unauthorized",
    )
    assert denied.rc == outside.rc == 0, message(
        en="Another UID must neither read nor write application data; the app cannot write outside /data.",
        fr="Un autre UID ne doit ni lire ni écrire les données ; l'application ne doit pas écrire hors de /data.",
    )


def _read(host, app):
    for _ in range(20):
        result = host.run("docker exec %s cat /data/value.txt", app["Id"])
        if result.rc == 0:
            return result.stdout
        time.sleep(0.1)
    pytest.fail(message(
        en="The app did not initialize /data/value.txt.",
        fr="L'application n'a pas initialisé /data/value.txt.",
    ))


def _write(host, app, value):
    result = host.run("docker exec %s sh -c %s", app["Id"], f"printf %s {shlex.quote(value)} > /data/value.txt")
    assert result.rc == 0, message(
        en="Cannot write the trial data.",
        fr="Impossible d'écrire les données d'essai.",
    )


def test_named_volume_contains_the_initial_application_data(host):
    app, _ = _app(host)
    _denied_access(host, app)
    expected = json.loads(host.file("/root/.lab-compose-persist.json").content_string)["value"]
    assert _read(host, app).strip() == expected, message(
        en="The volume must contain the supplied initial data.",
        fr="Le volume doit contenir les données initiales fournies.",
    )


@pytest.mark.parametrize("operation", ["recreate", "down-up"])
def test_fresh_data_survives_container_replacement(host, operation):
    before, volume = _app(host)
    _denied_access(host, before)
    original = _read(host, before)
    alternate = secrets.token_hex(32)
    try:
        _write(host, before, alternate)
        if operation == "down-up":
            _compose(host, "down")
            retained = host.run("docker volume inspect %s", volume)
            assert retained.rc == 0, message(
                en="Compose down without --volumes must retain the named data volume.",
                fr="Compose down sans --volumes doit conserver le volume nommé de données.",
            )
        _compose(host, "up", "-d", "--force-recreate", "--no-build", "--pull", "never")
        after, after_volume = _app(host)
        _denied_access(host, after)
        assert before["Id"] != after["Id"] and volume == after_volume and _read(host, after) == alternate, message(
            en="A new container must reuse the same volume and keep the fresh write, not reseed the original.",
            fr="Un nouveau conteneur doit réutiliser le même volume et garder la nouvelle écriture, pas réinitialiser l'original.",
        )
    finally:
        _compose(host, "up", "-d", "--no-build", "--pull", "never")
        restored, _ = _app(host)
        _write(host, restored, original)
