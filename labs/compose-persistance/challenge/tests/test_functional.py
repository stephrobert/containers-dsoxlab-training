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
        # Docker 29 OMET les cles vides de `Config` dans `docker image inspect` :
        # une image sans entrypoint ne porte plus de cle `Entrypoint`, la ou 26
        # rendait `null`. On interroge donc le dictionnaire par `.get`, ce qui fait
        # se valoir deux absences sans rien relacher du controle : une surcharge
        # reste un ecart. Le cote CONTENEUR, lui, garde toutes ses cles.
        app["Config"].get(key) == original["Config"].get(key) for key in ("Cmd", "Entrypoint")
    ), message(
        en="Run the supplied app image and command as a Compose service.",
        fr="Exécutez l'image et la commande app fournies comme service Compose.",
    )
    identity = host.run("docker exec %s id -u", app["Id"])
    rights = host.run("docker exec %s stat -c %s /data", app["Id"], "%u:%g:%a")
    # LA RACINE EN LECTURE SEULE N'EST PLUS EXIGÉE, et c'est une correction
    # d'alignement au programme. Ce contrôle réclamait
    # `app["HostConfig"]["ReadonlyRootfs"]`, qui s'enseigne en C38c, bien après
    # la leçon dont ce lab est la mise en pratique. Un lab d'entraînement doit
    # se jouer avec ce qui vient d'être appris, sinon il n'entraîne pas.
    assert identity.rc == rights.rc == 0 and identity.stdout.strip() == "10001" and (
        rights.stdout.strip() == "10001:10001:700"
    ), message(
        en="Run UID 10001 with /data owned by UID/GID 10001, mode 0700.",
        fr="Exécutez sous UID 10001 avec /data appartenant à UID/GID 10001, mode 0700.",
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
    # LA SECONDE MOITIÉ DE CE CONTRÔLE A ÉTÉ RETIRÉE, et elle méritait de
    # l'être deux fois.
    #
    # Elle jouait `! touch /tmp/unauthorized` sous l'UID de l'application, et se
    # lisait comme un contrôle de cloisonnement. Elle n'en était pas un. Mesuré
    # le 2026-11-02 : `/tmp` est en 1777 dans toute image alpine, donc ce
    # `touch` RÉUSSIT sous n'importe quel UID, et il n'échoue que si la racine
    # est montée en lecture seule.
    #
    # C'était donc l'exigence de racine en lecture seule sous un autre nom, plus
    # trompeuse que l'autre puisque son message parlait de cloisonnement, et
    # elle est enseignée bien plus loin que ce lab.
    #
    # Ce qui reste mesure vraiment quelque chose : un AUTRE UID ne peut ni lire
    # ni écrire les données, et cela tient aux droits de `/data`, que la leçon
    # enseigne.
    assert denied.rc == 0, message(
        en="Another UID must neither read nor write the application data.",
        fr="Un autre UID ne doit ni lire ni écrire les données de l'application.",
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
