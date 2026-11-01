"""Measure one-shot migration, idempotence and failed-dependency gating."""

from __future__ import annotations

import json
import secrets
import shlex

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-compose-migrate"
PROJECT = "dsoxlab-migration"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _compose(host, args, project=PROJECT, override=False):
    command = ["docker", "compose", "-p", project, "-f", f"{ROOT}/compose.yaml"]
    if override:
        command += ["-f", f"{ROOT}/failure.yaml"]
    return host.run(shlex.join([*command, *args]))


def _services(host, project=PROJECT):
    found = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={project}")
    assert found.rc == 0 and len(found.stdout.split()) == 2, message(
        en="Declare exactly app and migrate services in the migration project.",
        fr="Déclarez exactement les services app et migrate dans le projet de migration.",
    )
    result = host.run(shlex.join(["docker", "inspect", *found.stdout.split()]))
    assert result.rc == 0, message(
        en="Cannot inspect the migration services.",
        fr="Impossible d'inspecter les services de migration.",
    )
    services = {c["Config"]["Labels"].get("com.docker.compose.service"): c for c in json.loads(result.stdout)}
    assert set(services) == {"app", "migrate"}, message(
        en="Name the services app and migrate.",
        fr="Nommez les services app et migrate.",
    )
    image = host.run("docker image inspect dsoxlab-compose-migrate:app --format %s", "{{.Id}}")
    assert image.rc == 0 and all(c["Image"] == image.stdout.strip() for c in services.values()), message(
        en="Both services must use the supplied migration image.",
        fr="Les deux services doivent utiliser l'image de migration fournie.",
    )
    mounts = []
    for name, container in services.items():
        assert len(container["Mounts"]) == 1 and container["Mounts"][0]["Type"] == "volume" and container["Mounts"][0]["Destination"] == "/data" and container["Mounts"][0]["RW"], message(
            en=f"Mount only the writable shared data volume at /data on {name}.",
            fr=f"Montez seulement le volume partagé accessible en écriture sur /data dans {name}.",
        )
        mounts.append(container["Mounts"][0]["Name"])
        expected_command = [f"/usr/local/bin/{'app' if name == 'app' else 'migrate'}.sh"]
        assert container["Config"]["Cmd"] == expected_command and not container["Config"]["Entrypoint"], message(
            en=f"Use the supplied {name} script, not a replacement command.",
            fr=f"Utilisez le script {name} fourni, pas une commande de remplacement.",
        )
    assert mounts[0] == mounts[1], message(
        en="The application and migration must share the same database volume.",
        fr="L'application et la migration doivent partager le même volume de base.",
    )
    return services


def _ready(host, services):
    assert services["app"]["State"]["Running"] and services["migrate"]["State"]["Status"] == "exited" and services["migrate"]["State"]["ExitCode"] == 0 and services["migrate"]["HostConfig"]["RestartPolicy"]["Name"] == "no", message(
        en="Keep app running after migrate exits successfully without an automatic restart policy.",
        fr="Gardez app démarrée après la sortie réussie de migrate, sans redémarrage automatique de migrate.",
    )
    ready = host.run("docker exec %s cat /tmp/ready", services["app"]["Id"])
    schema = host.run("docker exec %s sqlite3 /data/app.db %s", services["app"]["Id"], "SELECT count(*) FROM migrations WHERE version=1;")
    assert ready.rc == 0 and schema.rc == 0 and schema.stdout.strip() == "1", message(
        en="The app must start against a real successfully migrated database.",
        fr="L'application doit démarrer sur une vraie base migrée avec succès.",
    )


def _record_query(host, app, sql, nonce):
    return host.run(shlex.join([
        "docker", "exec", app, "sqlite3", "/data/app.db",
        ".parameter init", f".parameter set @nonce '{nonce}'", sql,
    ]))


def test_one_shot_migration_and_successful_dependency(host):
    services = _services(host)
    _ready(host, services)
    config = _compose(host, ["config", "--format", "json"])
    assert config.rc == 0, message(
        en="The Compose declaration must resolve.",
        fr="La déclaration Compose doit être résolue.",
    )
    dependency = json.loads(config.stdout)["services"]["app"].get("depends_on", {}).get("migrate", {})
    assert dependency.get("condition") == "service_completed_successfully", message(
        en="Gate app on migrate with service_completed_successfully.",
        fr="Conditionnez app à migrate avec service_completed_successfully.",
    )


def test_rerunning_the_migration_preserves_new_application_records(host):
    services = _services(host)
    _ready(host, services)
    nonce = secrets.token_hex(24)
    app = services["app"]["Id"]
    inserted = _record_query(host, app, "INSERT INTO records(value) VALUES(@nonce);", nonce)
    assert inserted.rc == 0, message(
        en="Cannot insert the idempotence trial record.",
        fr="Impossible d'insérer l'enregistrement d'essai d'idempotence.",
    )
    try:
        for _ in range(2):
            result = _compose(host, ["run", "--rm", "--no-deps", "migrate"])
            assert result.rc == 0, message(
                en=f"Rerunning migrate must succeed: {result.stderr[-500:]}",
                fr=f"Rejouer migrate doit réussir : {result.stderr[-500:]}",
            )
        record = _record_query(host, app, "SELECT count(*) FROM records WHERE value=@nonce; SELECT count(*) FROM migrations;", nonce)
        assert record.rc == 0 and record.stdout.split() == ["1", "1"], message(
            en="Reruns must preserve the fresh record and keep exactly one migration marker.",
            fr="Les rejeux doivent préserver le nouvel enregistrement et garder un seul marqueur de migration.",
        )
    finally:
        removed = _record_query(host, app, "DELETE FROM records WHERE value=@nonce;", nonce)
        assert removed.rc == 0, message(
            en="Cannot remove the idempotence trial record.",
            fr="Impossible de retirer l'enregistrement d'essai.",
        )


def test_cold_start_and_failed_migration_gate_on_isolated_volumes(host):
    main = _services(host)
    _ready(host, main)
    main_volume = main["app"]["Mounts"][0]["Name"]
    for project, fail in (("dsoxlab-migration-cold", False), ("dsoxlab-migration-failed", True)):
        config = _compose(host, ["config", "--format", "json"], project)
        assert config.rc == 0, message(
            en="The isolated trial configuration must resolve.",
            fr="La configuration d'essai isolé doit être résolue.",
        )
        resolved = json.loads(config.stdout)
        assert all(v.get("name", "").startswith(f"{project}_") and v.get("name") != main_volume and not v.get("external") for v in resolved.get("volumes", {}).values()) and all(
            n.get("name", "").startswith(f"{project}_") and not n.get("external") for n in resolved.get("networks", {}).values()
        ) and all(not s.get("container_name") for s in resolved["services"].values()), message(
            en="Use project-scoped volume, network and container names so trials cannot touch the learner's database.",
            fr="Gardez les noms de volume, réseau et conteneur propres au projet pour isoler les essais de la base apprenante.",
        )
        try:
            if fail:
                written = host.run("printf %s > %s", "services:\n  migrate:\n    command: [sh, -c, 'exit 42']\n", f"{ROOT}/failure.yaml")
                assert written.rc == 0, message(
                    en="Cannot prepare the controlled migration failure.",
                    fr="Impossible de préparer l'échec contrôlé de migration.",
                )
            result = _compose(host, ["up", "-d", "--no-build", "--pull", "never"], project, fail)
            if not fail:
                assert result.rc == 0, message(
                    en=f"A fresh empty volume must be migrated automatically: {result.stderr[-500:]}",
                    fr=f"Un nouveau volume vide doit être migré automatiquement : {result.stderr[-500:]}",
                )
                _ready(host, _services(host, project))
            else:
                found = host.run("docker ps -aq --filter %s --filter %s", f"label=com.docker.compose.project={project}", "label=com.docker.compose.service=app")
                assert found.rc == 0, message(
                    en="Cannot inspect the application after failed migration.",
                    fr="Impossible d'inspecter l'application après l'échec de migration.",
                )
                states = host.run(shlex.join(["docker", "inspect", *found.stdout.split()])) if found.stdout.strip() else None
                assert result.rc != 0 and (states is None or (states.rc == 0 and all(c["State"]["Status"] == "created" for c in json.loads(states.stdout)))), message(
                    en="A failed migration must prevent app from starting at all, not merely make app crash.",
                    fr="Une migration échouée doit empêcher tout démarrage de app, pas simplement provoquer son plantage.",
                )
        finally:
            cleaned = _compose(host, ["down", "--volumes", "--remove-orphans"], project, fail)
            assert cleaned.rc == 0, message(
                en=f"Cannot clean the isolated trial project: {cleaned.stderr[-500:]}",
                fr=f"Impossible de nettoyer le projet d'essai isolé : {cleaned.stderr[-500:]}",
            )
    removed = host.run("rm -f %s", f"{ROOT}/failure.yaml")
    assert removed.rc == 0, message(
        en="Cannot remove the trial override.",
        fr="Impossible de retirer la surcharge d'essai.",
    )
