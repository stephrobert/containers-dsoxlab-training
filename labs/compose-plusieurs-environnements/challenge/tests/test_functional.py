"""Measure merged overrides and isolation during independent replacement."""

from __future__ import annotations

import json
import secrets
import shlex

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-compose-env"
ENVIRONMENTS = {"dev": ("development", 18090, 67108864), "prod": ("production", 18091, 134217728)}


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _compose(host, env, *args):
    host = _environment_host(host, env)
    return host.run(shlex.join([
        "docker", "compose", "-p", f"dsoxlab-env-{env}",
        "-f", f"{ROOT}/compose.yaml", "-f", f"{ROOT}/{env}.yaml", *args,
    ]))


def _environment_host(host, environment):
    return host if environment == "dev" else lab_host("docker-client.lab")


def _container_host(host, app):
    environment = app["Config"]["Labels"]["com.docker.compose.project"].removeprefix("dsoxlab-env-")
    return _environment_host(host, environment)


def _apps(host):
    unchanged = host.run("cd %s && sha256sum -c /root/.lab-compose-env.sha256", ROOT)
    assert unchanged.rc == 0, message(
        en="Keep the supplied base compose.yaml unchanged; use environment overrides.",
        fr="Gardez compose.yaml fourni inchangé ; utilisez les surcharges d'environnement.",
    )
    apps = {}
    image = host.run("docker image inspect dsoxlab-compose-env:app")
    assert image.rc == 0, message(
        en="Keep the supplied image.",
        fr="Gardez l'image fournie.",
    )
    original = json.loads(image.stdout)[0]
    prepared_id = host.file("/root/.lab-compose-env-image.id").content_string.strip()
    assert original["Id"] == prepared_id, message(
        en="Keep the prepared immutable image; promotion must not substitute a rebuilt artifact.",
        fr="Gardez l'image immuable préparée ; la promotion ne doit pas substituer un artefact reconstruit.",
    )
    for env, (name, port, memory) in ENVIRONMENTS.items():
        target = _environment_host(host, env)
        unchanged = target.run("cd %s && sha256sum -c /root/.lab-compose-env.sha256", ROOT)
        assert unchanged.rc == 0, message(
            en="Keep the same base declaration on each VM.",
            fr="Gardez la même déclaration de base sur chaque VM.",
        )
        project = f"dsoxlab-env-{env}"
        found = target.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={project}")
        assert found.rc == 0 and len(found.stdout.split()) == 1, message(
            en=f"Start exactly one app in project {project}.",
            fr=f"Démarrez exactement une app dans le projet {project}.",
        )
        inspected = target.run("docker inspect %s", found.stdout.strip())
        assert inspected.rc == 0, message(
            en=f"Cannot inspect {env}.",
            fr=f"Impossible d'inspecter {env}.",
        )
        app = json.loads(inspected.stdout)[0]
        assert app["State"]["Running"] and app["Config"]["Labels"].get("com.docker.compose.service") == "app" and app["Image"] == original["Id"] and all(
            app["Config"][key] == original["Config"][key] for key in ("Cmd", "Entrypoint")
        ), message(
            en=f"Run the supplied app image and command in {env}.",
            fr=f"Exécutez l'image et la commande app fournies dans {env}.",
        )
        values = dict(item.split("=", 1) for item in app["Config"]["Env"])
        assert values.get("APP_ENV") == name and app["HostConfig"]["Memory"] == memory and app["HostConfig"]["PortBindings"] == {
            "8080/tcp": [{"HostIp": "127.0.0.1", "HostPort": str(port)}],
        }, message(
            en=f"Apply the correct {env} environment, memory limit and loopback publication.",
            fr=f"Appliquez l'environnement, la mémoire et la publication loopback corrects pour {env}.",
        )
        mounts = app["Mounts"]
        assert len(mounts) == 1 and mounts[0]["Type"] == "volume" and mounts[0]["Destination"] == "/data" and mounts[0]["RW"], message(
            en="Use only the inherited named data volume.",
            fr="Utilisez seulement le volume nommé de données hérité.",
        )
        volume = target.run("docker volume inspect %s", mounts[0]["Name"])
        assert volume.rc == 0 and (json.loads(volume.stdout)[0]["Labels"] or {}).get("com.docker.compose.project") == project, message(
            en="Each data volume must belong to its own Compose project.",
            fr="Chaque volume doit appartenir à son propre projet Compose.",
        )
        response = target.run("curl --noproxy '*' -fsS --retry 10 --retry-connrefused --retry-delay 1 --max-time 3 %s", f"http://127.0.0.1:{port}/environment.txt")
        assert response.rc == 0 and response.stdout.strip() == name, message(
            en=f"The {env} endpoint must serve its actual environment identity.",
            fr=f"Le point d'accès {env} doit servir l'identité réelle de son environnement.",
        )
        apps[env] = app
    assert apps["dev"]["Mounts"][0]["Name"] != apps["prod"]["Mounts"][0]["Name"] and not (
        set(apps["dev"]["NetworkSettings"]["Networks"]) & set(apps["prod"]["NetworkSettings"]["Networks"])
    ), message(
        en="Development and production must share neither volumes nor networks.",
        fr="Développement et production ne doivent partager ni volumes ni réseaux.",
    )
    return apps


def _data(host, app):
    host = _container_host(host, app)
    result = host.run("docker exec %s cat /data/value.txt", app["Id"])
    assert result.rc == 0, message(
        en="Cannot read application data.",
        fr="Impossible de lire les données applicatives.",
    )
    return result.stdout


def _write(host, app, value):
    host = _container_host(host, app)
    result = host.run("docker exec %s sh -c %s", app["Id"], f"printf %s {shlex.quote(value)} > /data/value.txt")
    assert result.rc == 0, message(
        en="Cannot write the environment-isolation trial value.",
        fr="Impossible d'écrire la valeur d'essai d'isolation.",
    )


def test_two_merged_deployments_have_distinct_effective_configuration(host):
    _apps(host)
    for env, (name, port, memory) in ENVIRONMENTS.items():
        config = _compose(host, env, "config", "--format", "json")
        assert config.rc == 0, message(
            en=f"The base and {env} override must merge successfully.",
            fr=f"La base et la surcharge {env} doivent fusionner avec succès.",
        )
        resolved = json.loads(config.stdout)["services"]
        assert set(resolved) == {"app"} and "build" not in resolved["app"] and resolved["app"]["environment"]["APP_ENV"] == name and int(resolved["app"]["mem_limit"]) == memory and int(resolved["app"]["ports"][0]["published"]) == port, message(
            en=f"The merged {env} configuration must carry its environment-specific settings.",
            fr=f"La configuration fusionnée {env} doit porter ses réglages spécifiques.",
        )


@pytest.mark.parametrize("environment", ["dev", "prod"])
def test_replacing_one_environment_keeps_its_data_and_does_not_touch_the_other(host, environment):
    before = _apps(host)
    other = "prod" if environment == "dev" else "dev"
    original = _data(host, before[environment])
    other_data = _data(host, before[other])
    alternate = secrets.token_hex(24)
    try:
        _write(host, before[environment], alternate)
        result = _compose(host, environment, "up", "-d", "--force-recreate", "--no-build", "--pull", "never")
        assert result.rc == 0, message(
            en=f"Independent recreation must succeed: {result.stderr[-500:]}",
            fr=f"La recréation indépendante doit réussir : {result.stderr[-500:]}",
        )
        after = _apps(host)
        assert after[environment]["Id"] != before[environment]["Id"] and after[other]["Id"] == before[other]["Id"] and _data(host, after[environment]) == alternate and _data(host, after[other]) == other_data, message(
            en="Replace only the selected environment, preserve its fresh write and leave the other container and data intact.",
            fr="Remplacez seulement l'environnement choisi, gardez sa nouvelle écriture et laissez l'autre conteneur et ses données intacts.",
        )
    finally:
        after = _apps(host)
        _write(host, after[environment], original)
