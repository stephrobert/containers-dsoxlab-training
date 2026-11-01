"""Verify that a custom-format dump restores the actual PostgreSQL rows."""

from __future__ import annotations

import json
import secrets
import shlex

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


@pytest.fixture
def restore_host():
    return lab_host("docker-client.lab")


def _psql(host, database, sql):
    return host.run(
        shlex.join(
            [
                "sudo",
                "-n",
                "-u",
                "postgres",
                "--",
                "psql",
                "-X",
                "-A",
                "-t",
                "-v",
                "ON_ERROR_STOP=1",
                "-d",
                database,
                "-c",
                sql,
            ]
        )
    )


def _rows(host, database):
    result = _psql(
        host,
        database,
        "SELECT id || '|' || region || '|' || total_cents FROM orders ORDER BY id",
    )
    assert result.rc == 0, message(
        en=f"Cannot read the orders table in {database}: {result.stderr[-500:]}",
        fr=f"Impossible de lire la table orders dans {database} : {result.stderr[-500:]}",
    )
    return result.stdout.splitlines()


def _sql_literal(value):
    return "'" + value.replace("'", "''") + "'"


def test_custom_dump_restores_the_seeded_rows_on_a_second_vm(host, restore_host):
    state_file = host.file("/opt/lab-postgres-sauvegarde/state.json")
    assert state_file.exists, message(
        en="The PostgreSQL source fixture is missing.",
        fr="Le jeu de données PostgreSQL source est absent.",
    )
    state = json.loads(state_file.content_string)
    backup = f"{state['backup_dir']}/orders.dump"
    dump = host.run(shlex.join(["head", "-c", "5", backup]))
    assert dump.rc == 0 and dump.stdout == "PGDMP", message(
        en="Create a PostgreSQL custom-format dump at the required backup path.",
        fr="Créez une sauvegarde PostgreSQL au format personnalisé au chemin demandé.",
    )
    expected = state["rows"]
    assert _rows(host, state["source_db"]) == expected, message(
        en="The live source fixture changed; preserve its original rows.",
        fr="Le jeu de données source a changé ; conservez ses lignes d'origine.",
    )
    restored = _psql(
        restore_host,
        "postgres",
        "SELECT COALESCE(shobj_description(oid, 'pg_database'), '') FROM pg_database WHERE datname = "  # noqa: S608 -- _sql_literal escapes SQL string literals.
        + _sql_literal(state["restored_db"]),
    )
    assert restored.rc == 0 and restored.stdout.strip() == state["ownership"], message(
        en="Create the restore database on docker-client.lab and apply the supplied ownership marker.",
        fr="Créez la base de restauration sur docker-client.lab avec le marqueur fourni.",
    )
    assert _rows(restore_host, state["restored_db"]) == expected, message(
        en="The restored database must contain every source row with its original values.",
        fr="La base restaurée doit contenir chaque ligne source avec ses valeurs d'origine.",
    )
    trial_db = f"dsoxlab_check_{secrets.token_hex(6)}"
    source_dump = host.run("sha256sum %s", backup)
    target_dump = restore_host.run("sha256sum %s", backup)
    assert source_dump.rc == target_dump.rc == 0 and (
        source_dump.stdout.split()[0] == target_dump.stdout.split()[0]
    ), message(
        en="Transfer the exact dump to the second VM; do not recreate rows by hand.",
        fr="Transférez la sauvegarde exacte sur la seconde VM ; ne recréez pas les lignes à la main.",
    )
    created = restore_host.run(
        shlex.join(["sudo", "-n", "-u", "postgres", "--", "createdb", trial_db])
    )
    assert created.rc == 0, message(
        en="Could not create a temporary isolated database for restore verification.",
        fr="Impossible de créer une base isolée temporaire pour vérifier la restauration.",
    )
    try:
        corrupted = restore_host.run(
            shlex.join(["sudo", "-n", "-u", "postgres", "--", "pg_restore",
                        "--no-owner", "--no-privileges", "-d", trial_db, "/dev/null"])
        )
        assert corrupted.rc != 0, message(
            en="The restore command must reject an invalid backup rather than report success.",
            fr="La restauration doit refuser une sauvegarde invalide plutôt qu'annoncer un succès.",
        )
        restored_dump = restore_host.run(
            shlex.join(
                [
                    "sudo",
                    "-n",
                    "-u",
                    "postgres",
                    "--",
                    "pg_restore",
                    "--no-owner",
                    "--no-privileges",
                    "-d",
                    trial_db,
                    backup,
                ]
            )
        )
        assert restored_dump.rc == 0, message(
            en=f"The saved dump cannot be restored: {restored_dump.stderr[-500:]}",
            fr=f"La sauvegarde ne peut pas être restaurée : {restored_dump.stderr[-500:]}",
        )
        assert _rows(restore_host, trial_db) == expected, message(
            en="Restoring the dump into a fresh database must reproduce the source rows.",
            fr="La restauration dans une base vierge doit reproduire les lignes source.",
        )
    finally:
        removed = restore_host.run(
            shlex.join(
                ["sudo", "-n", "-u", "postgres", "--", "dropdb", "--if-exists", trial_db]
            )
        )
        assert removed.rc == 0, message(
            en="Remove the temporary restore database from the second VM.",
            fr="Retirez la base temporaire de restauration sur la seconde VM.",
        )
