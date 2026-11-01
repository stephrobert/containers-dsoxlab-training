"""Measure the complete local delivery and eight isolated failure/recovery cycles."""

from __future__ import annotations

import hashlib
import json
import shlex
import time
import uuid

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-delivery"
PROJECT = "dsoxlab-delivery"
LABEL = "capstone-chaine-complete"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _compose(host, args):
    return host.run(shlex.join([
        "docker", "compose", "-p", PROJECT, "--env-file", f"{ROOT}/release.env",
        "-f", f"{ROOT}/compose.yaml", *args,
    ]))


def _json_file(host, name):
    result = host.run("cat %s/%s", ROOT, name)
    assert result.rc == 0, message(
        en=f"Retain {name} as actual delivery evidence.",
        fr=f"Conservez {name} comme preuve réelle de livraison.",
    )
    return json.loads(result.stdout)


def _request(host, path="/ready", data=None):
    program = (
        "import json,urllib.request; "
        f"req=urllib.request.Request('http://127.0.0.1:18088{path}', "
        f"data={repr(json.dumps(data).encode()) if data is not None else 'None'}, "
        "headers={'Content-Type':'application/json'}); "
        "r=urllib.request.urlopen(req, timeout=4); print(r.read().decode())"
    )
    return host.run(shlex.join(["/usr/bin/python3", "-c", program]))


def _state(host, *, wait=False):
    found = host.run(
        "docker ps -aq --filter %s --filter %s",
        f"label=com.docker.compose.project={PROJECT}", f"label=dsoxlab.lab={LABEL}",
    )
    assert found.rc == 0 and len(found.stdout.split()) == 2, message(
        en="Deploy exactly the labelled api/db delivery services before earning points.",
        fr="Déployez exactement les services api/db labellisés avant tout point.",
    )
    deadline = time.monotonic() + 20
    while True:
        inspected = host.run(shlex.join(["docker", "inspect", *found.stdout.split()]))
        assert inspected.rc == 0, message(
            en="Cannot inspect the delivered services.", fr="Impossible d'inspecter les services livrés.",
        )
        containers = json.loads(inspected.stdout)
        services = {c["Config"]["Labels"]["com.docker.compose.service"]: c for c in containers}
        ready = _request(host)
        healthy = set(services) == {"api", "db"} and all(
            c["State"]["Running"] and c["State"].get("Health", {}).get("Status") == "healthy"
            for c in containers
        ) and ready.rc == 0 and json.loads(ready.stdout).get("ready") is True
        if healthy or not wait or time.monotonic() >= deadline:
            break
        time.sleep(0.5)
    assert healthy, message(
        en="Both services must be healthy and /ready must genuinely query PostgreSQL.",
        fr="Les deux services doivent être sains et /ready doit interroger réellement PostgreSQL.",
    )
    return services


def _wait_ready(host):
    _state(host, wait=True)


def _write(host, key, value):
    result = _request(host, "/items", {"key": key, "value": value})
    assert result.rc == 0 and json.loads(result.stdout).get("stored") is True, message(
        en="The API must durably write the supplied item to PostgreSQL.",
        fr="L'API doit écrire durablement l'élément fourni dans PostgreSQL.",
    )


def _read(host, key, value):
    result = _request(host, f"/items/{key}")
    assert result.rc == 0 and json.loads(result.stdout).get("value") == value, message(
        en="The previously written item must remain readable after disruption.",
        fr="L'élément écrit auparavant doit rester lisible après perturbation.",
    )


def test_registry_manifest_digest_pull_and_deployed_identity(host):
    services = _state(host)
    inspected_registry = host.run("docker inspect dsoxlab-delivery-registry")
    assert inspected_registry.rc == 0, message(
        en="Keep the lab-only registry available.",
        fr="Gardez le registre réservé au lab disponible.",
    )
    registry_container = json.loads(inspected_registry.stdout)[0]
    assert registry_container["Config"]["Labels"].get("dsoxlab.lab") == LABEL and (
        registry_container["HostConfig"]["PortBindings"] == {
            "5000/tcp": [{"HostIp": "127.0.0.1", "HostPort": "15088"}],
        }
    ), message(
        en="The registry must remain owned by this lab and published only on loopback 15088.",
        fr="Le registre reste réservé au lab et publié seulement sur boucle locale 15088.",
    )
    evidence = _json_file(host, "delivery.json")
    digest = evidence["registry_digest"]
    reference = f"127.0.0.1:15088/delivery/api:1.0@{digest}"
    request = (
        "import json,urllib.request; "
        "req=urllib.request.Request('http://127.0.0.1:15088/v2/delivery/api/manifests/1.0', "
        "headers={'Accept':'application/vnd.docker.distribution.manifest.v2+json'}); "
        "r=urllib.request.urlopen(req,timeout=5); "
        "print(json.dumps({'digest':r.headers['Docker-Content-Digest'],'manifest':json.load(r)}))"
    )
    result = host.run(shlex.join(["/usr/bin/python3", "-c", request]))
    assert result.rc == 0, message(
        en="Publish the actual release to the lab-only registry.",
        fr="Publiez la vraie livraison dans le registre réservé au lab.",
    )
    registry = json.loads(result.stdout)
    pulled = host.run("docker pull %s", reference)
    inspected = host.run("docker image inspect %s", reference)
    assert pulled.rc == inspected.rc == 0, message(
        en="The immutable published reference must really be pullable.",
        fr="La référence immuable publiée doit pouvoir être réellement tirée.",
    )
    image = json.loads(inspected.stdout)[0]
    assert digest == registry["digest"] and registry["manifest"]["config"]["digest"] == image["Id"] and (
        evidence["image_id"] == evidence["pulled_id"] == services["api"]["Image"] == image["Id"]
    ) and evidence["reference"] == services["api"]["Config"]["Image"] == reference, message(
        en="Source artifact, manifest, digest pull and deployed image must share the same identity.",
        fr="Artefact, manifeste, pull par digest et image déployée doivent partager la même identité.",
    )


def test_restore_application_and_new_data_on_a_fresh_second_vm(host):
    services = _state(host)
    key, value = "restore-" + uuid.uuid4().hex, uuid.uuid4().hex
    _write(host, key, value)
    restored = lab_host("docker-client.lab")
    existing = restored.run(
        "docker ps -aq --filter label=com.docker.compose.project=dsoxlab-delivery-restore"
    )
    assert existing.rc == 0 and not existing.stdout.strip(), message(
        en="Restore onto a fresh second-VM project, not another database on the source.",
        fr="Restaurez dans un projet vierge sur la seconde VM, pas une autre base sur la source.",
    )
    try:
        _restore_and_check(host, services, restored, key, value)
    finally:
        cleaned = restored.run(
            "set -eu; project=dsoxlab-delivery-restore; "
            "ids=$(docker ps -aq --filter label=com.docker.compose.project=$project); "
            "if test -n \"$ids\"; then docker rm -f $ids; fi; "
            "ids=$(docker network ls -q --filter label=com.docker.compose.project=$project); "
            "if test -n \"$ids\"; then docker network rm $ids; fi; "
            "ids=$(docker volume ls -q --filter label=com.docker.compose.project=$project); "
            "if test -n \"$ids\"; then docker volume rm $ids; fi"
        )
        assert cleaned.rc == 0, message(
            en="Remove only the fresh second-VM trial project and its data.",
            fr="Retirez seulement le projet d'essai vierge de la seconde VM et ses données.",
        )


def test_dependency_interruption_recovers_without_restarting_the_api(host):
    services = _state(host)
    key, value = "dependency-" + uuid.uuid4().hex, uuid.uuid4().hex
    _write(host, key, value)
    try:
        paused = host.run("docker pause %s", services["db"]["Id"])
        assert paused.rc == 0 and _request(host).rc != 0, message(
            en="A paused database must make business readiness fail, even while the API process lives.",
            fr="Une base suspendue doit faire échouer la disponibilité métier même si le processus API vit.",
        )
    finally:
        resumed = host.run("docker unpause %s", services["db"]["Id"])
        assert resumed.rc == 0, message(
            en="Restore only the interrupted dependency.",
            fr="Rétablissez seulement la dépendance interrompue.",
        )
    _wait_ready(host)
    after = _state(host)
    assert (
        after["api"]["Id"] == services["api"]["Id"]
        and after["api"]["State"]["StartedAt"] == services["api"]["State"]["StartedAt"]
        and after["api"]["RestartCount"] == services["api"]["RestartCount"]
    ), message(
        en="The existing API must recover when its dependency returns; unhealthy is not an automatic restart.",
        fr="L'API existante doit reprendre au retour de sa dépendance ; unhealthy ne signifie pas redémarrage automatique.",
    )
    _read(host, key, value)


def test_targeted_maintenance_preserves_live_reads_and_a_restorable_backup(host):
    services = _state(host)
    key, value = "maintenance-" + uuid.uuid4().hex, uuid.uuid4().hex
    _write(host, key, value)
    suffix = uuid.uuid4().hex[:12]
    prefix = "dsoxlab-delivery-maintenance-" + suffix
    trial_label = "dsoxlab.maintenance-trial=" + suffix
    keeper, disposable = prefix + "-keep", prefix + "-delete"
    volume, junk_volume, junk_network = keeper + "-data", disposable + "-data", disposable + "-net"
    scratch = "maintenance_" + suffix
    database_created = False
    try:
        for kind, name, purpose in [
            ("volume", volume, "preserve"), ("volume", junk_volume, "jetable"),
            ("network", junk_network, "jetable"),
        ]:
            created = host.run(shlex.join([
                "docker", kind, "create", "--label", trial_label,
                "--label", f"dsoxlab.lab={LABEL}", "--label", f"dsoxlab.maintenance={purpose}", name,
            ]))
            assert created.rc == 0, message(
                en="Prepare bounded maintenance witnesses.",
                fr="Préparez des témoins de maintenance bornés.",
            )
        written = host.run(shlex.join([
            "docker", "run", "--name", keeper, "--network", "none", "--user", "0",
            "--label", trial_label, "--label", "dsoxlab.maintenance=preserve",
            "-v", f"{volume}:/data", "--entrypoint", "/opt/venv/bin/python",
            services["api"]["Image"], "-c",
            f"from pathlib import Path; Path('/data/value').write_text({value!r})",
        ]))
        created = host.run(shlex.join([
            "docker", "create", "--name", disposable, "--network", "none",
            "--label", trial_label, "--label", "dsoxlab.maintenance=jetable",
            services["api"]["Image"], "/bin/true",
        ]))
        assert written.rc == created.rc == 0, message(
            en="A stopped data-bearing container is not disposable; prepare both cases.",
            fr="Un conteneur arrêté porteur de données n'est pas jetable ; préparez les deux cas.",
        )
        probe = (
            "import json,subprocess,time,urllib.request;"
            "start=time.monotonic(); failures=[]; samples=0;"
            "process=subprocess.Popen(['/opt/lab-delivery/maintenance.sh']);\n"
            "while process.poll() is None:\n"
            " try:\n"
            f"  result=json.load(urllib.request.urlopen('http://127.0.0.1:18088/items/{key}',timeout=2))\n"
            f"  if result.get('value')!={value!r}: failures.append('wrong business value')\n"
            " except OSError as error: failures.append(str(error))\n"
            " samples+=1\n"
            " if time.monotonic()-start>45:\n"
            "  process.kill(); process.wait(); failures.append('maintenance timeout'); break\n"
            " time.sleep(0.1)\n"
            "print('MAINTENANCE='+json.dumps({'rc':process.wait(),'samples':samples,"
            "'failures':failures,'seconds':time.monotonic()-start}))\n"
        )
        measured = host.run(shlex.join(["python3", "-c", probe]))
        reports = [line.removeprefix("MAINTENANCE=") for line in measured.stdout.splitlines() if line.startswith("MAINTENANCE=")]
        assert measured.rc == 0 and len(reports) == 1, message(
            en="Measure live business reads throughout the maintenance command.",
            fr="Mesurez les lectures métier pendant la commande de maintenance.",
        )
        report = json.loads(reports[0])
        assert report["rc"] == 0 and report["samples"] > 0 and not report["failures"] and report["seconds"] <= 45, message(
            en="Targeted maintenance must finish within 45 seconds without interrupting business reads.",
            fr="La maintenance ciblée finit en 45 secondes sans interrompre les lectures métier.",
        )
        inventory = _json_file(host, "maintenance.json")
        keeper_id = host.run("docker inspect %s --format '{{.Id}}'", keeper)
        assert keeper_id.rc == 0 and keeper_id.stdout.strip() in {item["Id"] for item in inventory["containers"]} and (
            volume in {item["Name"] for item in inventory["volumes"]}
            and services["api"]["Image"] in {item["Id"] for item in inventory["images"]}
        ), message(
            en="Record measured pre-maintenance container, volume and image inventory without secret environment values.",
            fr="Conservez l'inventaire réel préalable conteneurs/volumes/images sans valeurs secrètes d'environnement.",
        )
        for kind, name in [("container", disposable), ("volume", junk_volume), ("network", junk_network)]:
            assert host.run("docker %s inspect %s", kind, name).rc != 0, message(
                en="Remove explicitly disposable, unused trial objects.",
                fr="Retirez les objets d'essai explicitement jetables et inutilisés.",
            )
        after = _state(host)
        assert all(after[name]["Id"] == services[name]["Id"] for name in ["api", "db"]), message(
            en="Do not recreate the active delivery services during maintenance.",
            fr="Ne recréez pas les services actifs pendant la maintenance.",
        )
        read = host.run(shlex.join([
            "docker", "run", "--rm", "--network", "none", "--label", trial_label,
            "-v", f"{volume}:/data:ro", "--entrypoint", "/opt/venv/bin/python",
            services["api"]["Image"], "-c", "from pathlib import Path; print(Path('/data/value').read_text())",
        ]))
        kept = host.run("docker start -a %s", keeper)
        assert kept.rc == read.rc == 0 and read.stdout.strip() == value, message(
            en="Preserve the stopped container and its data-bearing volume.",
            fr="Préservez le conteneur arrêté et son volume porteur de données.",
        )
        created_db = host.run("docker exec %s createdb -U delivery %s", services["db"]["Id"], scratch)
        assert created_db.rc == 0, message(
            en="Create a separate scratch database to prove backup usability.",
            fr="Créez une base d'essai séparée pour éprouver la sauvegarde.",
        )
        database_created = True
        restored = host.run(
            "docker exec -i %s pg_restore --no-owner --no-privileges -U delivery -d %s < /opt/lab-delivery/maintenance.dump",
            services["db"]["Id"], scratch,
        )
        rows = host.run(
            "docker exec %s psql -X -A -t -U delivery -d %s -c %s",
            services["db"]["Id"], scratch, f"SELECT value FROM items WHERE key='{key}'",  # noqa: S608 -- Generated UUID key only.
        )
        assert restored.rc == rows.rc == 0 and rows.stdout.strip() == value, message(
            en="The pre-maintenance backup must actually restore fresh business data.",
            fr="La sauvegarde préalable restaure réellement la donnée métier nouvelle.",
        )
        _read(host, key, value)
    finally:
        if database_created:
            dropped = host.run("docker exec %s dropdb -U delivery %s", services["db"]["Id"], scratch)
            assert dropped.rc == 0, message(en="Remove the scratch database.", fr="Retirez la base d'essai.")
        cleaned = host.run(
            "set -eu; label=%s; "
            "ids=$(docker ps -aq --filter label=$label); if test -n \"$ids\"; then docker rm -f $ids; fi; "
            "ids=$(docker network ls -q --filter label=$label); if test -n \"$ids\"; then docker network rm $ids; fi; "
            "ids=$(docker volume ls -q --filter label=$label); if test -n \"$ids\"; then docker volume rm $ids; fi",
            trial_label,
        )
        assert cleaned.rc == 0, message(
            en="Remove only this maintenance trial's objects.",
            fr="Retirez seulement les objets de cet essai de maintenance.",
        )


def test_bad_release_rolls_back_without_losing_data_and_incompatible_schema_is_refused(host):
    services = _state(host)
    key, value = "rollback-" + uuid.uuid4().hex, uuid.uuid4().hex
    _write(host, key, value)
    bad_image = "dsoxlab-delivery-rollback:bad"
    accepted_image = "dsoxlab-delivery-rollback:accepted"
    dockerfile = (
        f"FROM {accepted_image}\n"
        'LABEL dsoxlab.lab="capstone-chaine-complete"\n'
        'CMD ["python", "-c", "import time; time.sleep(3600)"]\n'
    )
    created = host.run(
        "mkdir -p /opt/lab-delivery/rollback-test && printf %s > /opt/lab-delivery/rollback-test/Dockerfile",
        dockerfile,
    )
    assert created.rc == 0, message(
        en="Prepare a distinct faulty-release fixture without changing source data.",
        fr="Préparez une release fautive distincte sans changer les données source.",
    )
    schema_changed = False
    bad_built = False
    tagged = False
    try:
        tag = host.run("docker tag %s %s", services["api"]["Image"], accepted_image)
        assert tag.rc == 0, message(
            en="Use the actually deployed accepted image as the faulty fixture's base.",
            fr="Utilisez l'image acceptée réellement déployée comme base de la fixture fautive.",
        )
        tagged = True
        built = host.run("docker build --network none -t %s /opt/lab-delivery/rollback-test", bad_image)
        assert built.rc == 0, message(
            en="Build the bounded faulty-release fixture.",
            fr="Construisez la release fautive bornée.",
        )
        bad_built = True
        override = host.run(
            "printf %s > /opt/lab-delivery/incident.yaml",
            f"services:\n  api:\n    image: {bad_image}\n",
        )
        deployed = host.run(
            "docker compose -p dsoxlab-delivery --env-file /opt/lab-delivery/release.env "
            "-f /opt/lab-delivery/compose.yaml -f /opt/lab-delivery/incident.yaml "
            "up -d --no-deps --force-recreate --no-build --pull never api"
        )
        assert override.rc == deployed.rc == 0 and _request(host).rc != 0, message(
            en="The newly deployed image must really break business readiness.",
            fr="L'image nouvellement déployée doit réellement casser la disponibilité métier.",
        )
        rollback = host.run("/opt/lab-delivery/rollback.sh")
        assert rollback.rc == 0, message(
            en=f"Rollback the failed release using the accepted old artifact: {rollback.stderr[-600:]}",
            fr=f"Revenez à l'ancien artefact accepté : {rollback.stderr[-600:]}",
        )
        _wait_ready(host)
        after = _state(host)
        assert after["api"]["Image"] == services["api"]["Image"], message(
            en="Rollback must redeploy the old image identity, not merely repair the failed container command.",
            fr="Le rollback redéploie l'identité de l'ancienne image, pas seulement une commande corrigée.",
        )
        _read(host, key, value)
        changed = host.run(
            "docker exec %s psql -X -v ON_ERROR_STOP=1 -U delivery -d delivery -c %s",
            after["db"]["Id"],
            "ALTER TABLE items ADD COLUMN new_required text NOT NULL DEFAULT ''; "
            "ALTER TABLE items ALTER COLUMN new_required DROP DEFAULT",
        )
        assert changed.rc == 0, message(
            en="Inject a bounded schema change incompatible with old API writes.",
            fr="Injectez un changement de schéma borné incompatible avec les écritures de l'ancienne API.",
        )
        schema_changed = True
        refused = host.run("/opt/lab-delivery/rollback.sh")
        assert refused.rc != 0 and "schema" in (refused.stdout + refused.stderr).lower(), message(
            en="An incompatible data migration must block a blind image rollback and report the schema error.",
            fr="Une migration de données incompatible doit bloquer le rollback aveugle et signaler le schéma.",
        )
        _read(host, key, value)
    finally:
        if schema_changed:
            current = _compose(host, ["ps", "-q", "db"])
            restored_schema = host.run(
                "docker exec %s psql -X -v ON_ERROR_STOP=1 -U delivery -d delivery -c %s",
                current.stdout.strip(), "ALTER TABLE items DROP COLUMN new_required",
            )
            assert restored_schema.rc == 0, message(
                en="Restore only the injected trial column.",
                fr="Retirez seulement la colonne d'essai injectée.",
            )
        recovered = host.run("/opt/lab-delivery/recover.sh")
        assert recovered.rc == 0, message(
            en="Restore the canonical release after the rollback trial.",
            fr="Rétablissez la release canonique après l'essai de rollback.",
        )
        for image, exists in [(bad_image, bad_built), (accepted_image, tagged)]:
            if exists:
                removed = host.run("docker image rm %s", image)
                assert removed.rc == 0, message(
                    en="Remove the trial image/tag without deleting the accepted release.",
                    fr="Retirez l'image/tag d'essai sans supprimer la release acceptée.",
                )
        removed_files = host.run("rm -f /opt/lab-delivery/rollback-test/Dockerfile && rmdir /opt/lab-delivery/rollback-test")
        assert removed_files.rc == 0, message(
            en="Remove only the rollback trial directory.",
            fr="Retirez seulement le répertoire d'essai de rollback.",
        )


def _restore_and_check(host, services, restored, key, value):
    restore = host.run("/opt/lab-delivery/restore.sh")
    assert restore.rc == 0, message(
        en=f"The recovery tool must restore the application on the second VM: {restore.stderr[-800:]}",
        fr=f"L'outil doit restaurer l'application sur la seconde VM : {restore.stderr[-800:]}",
    )
    found = restored.run(
        "docker ps -q --filter label=com.docker.compose.project=dsoxlab-delivery-restore"
    )
    assert found.rc == 0 and len(found.stdout.split()) == 2, message(
        en="Restore both API and PostgreSQL service on the second VM.",
        fr="Restaurez les services API et PostgreSQL sur la seconde VM.",
    )
    inspected = restored.run(shlex.join(["docker", "inspect", *found.stdout.split()]))
    assert inspected.rc == 0, message(
        en="Inspect the actual restored services.",
        fr="Inspectez les services réellement restaurés.",
    )
    target_services = {
        c["Config"]["Labels"]["com.docker.compose.service"]: c
        for c in json.loads(inspected.stdout)
    }
    assert set(target_services) == {"api", "db"} and (
        target_services["api"]["Image"] == services["api"]["Image"]
        and target_services["api"]["HostConfig"]["ReadonlyRootfs"]
        and target_services["api"]["Config"]["User"] == "10001:10001"
        and not target_services["db"]["HostConfig"]["PortBindings"]
    ), message(
        en="Restore the exact accepted artifact without removing its runtime protections or publishing the database.",
        fr="Restaurez l'artefact accepté exact sans retirer ses protections ni publier la base.",
    )
    request = (
        "import json,urllib.request;"
        f"print(urllib.request.urlopen('http://127.0.0.1:18089/items/{key}',timeout=4).read().decode())"
    )
    response = restored.run(shlex.join(["python3", "-c", request]))
    assert response.rc == 0 and json.loads(response.stdout).get("value") == value, message(
        en="The restored HTTP API must serve the fresh business value from its restored database.",
        fr="L'API HTTP restaurée doit servir la valeur métier nouvelle depuis sa base restaurée.",
    )
    query = "SELECT key,value FROM items ORDER BY key"
    original_rows = host.run(
        "docker exec %s psql -X -A -t -U delivery -d delivery -c %s",
        services["db"]["Id"], query,
    )
    target_rows = restored.run(
        "docker exec %s psql -X -A -t -U delivery -d delivery -c %s",
        target_services["db"]["Id"], query,
    )
    assert original_rows.rc == target_rows.rc == 0 and original_rows.stdout == target_rows.stdout, message(
        en="Compare all real source rows with the restored second-VM database.",
        fr="Comparez toutes les lignes source réelles à la base restaurée sur la seconde VM.",
    )
    _read(host, key, value)


def test_sbom_matches_real_installed_packages_and_source(host):
    services = _state(host)
    sbom = _json_file(host, "sbom.spdx.json")
    measured = host.run(
        "docker exec %s /opt/venv/bin/python /app/sbom.py %s",
        services["api"]["Id"], services["api"]["Image"],
    )
    assert measured.rc == 0, message(
        en="Inventory actual packages in the final API image.",
        fr="Inventoriez les vrais paquets de l'image API finale.",
    )
    fresh = json.loads(measured.stdout)
    inventory = host.run(
        "docker exec %s /opt/venv/bin/python -c %s", services["api"]["Id"],
        "import hashlib,importlib.metadata,json,subprocess; from pathlib import Path; "
        "print(json.dumps({'python':[[d.metadata['Name'],d.version] for d in importlib.metadata.distributions()],"
        "'debian':subprocess.check_output(['dpkg-query','-W','-f','${Package}\\t${Version}\\n'],text=True),"
        "'source':hashlib.sha256(Path('/app/api.py').read_bytes()).hexdigest()}))",
    )
    assert inventory.rc == 0, message(
        en="Measure installed package versions and source independently of the SBOM emitter.",
        fr="Mesurez versions installées et source indépendamment du générateur SBOM.",
    )
    actual = json.loads(inventory.stdout)
    versions = {(p["name"], p.get("versionInfo")) for p in sbom.get("packages", [])}
    expected = {tuple(p) for p in actual["python"]}
    expected.update(tuple(line.split("\t")) for line in actual["debian"].splitlines())
    application = next((p for p in sbom.get("packages", []) if p["name"] == "delivery-api"), {})
    assert expected <= versions and application.get("checksums") == [
        {"algorithm": "SHA256", "checksumValue": actual["source"]},
    ], message(
        en="SPDX entries must match independently measured real packages and the application hash.",
        fr="Les entrées SPDX correspondent aux vrais paquets mesurés indépendamment et au hash applicatif.",
    )
    assert sbom.get("spdxVersion") == "SPDX-2.3" and sbom.get("documentNamespace") == fresh["documentNamespace"] and (
        sbom.get("packages") == fresh["packages"] and sbom.get("relationships") == fresh["relationships"]
    ) and any(p["name"] == "psycopg2-binary" and p["versionInfo"] == "2.9.11" for p in sbom["packages"]), message(
        en="SPDX must match real Debian/Python inventories and the actual API source checksum.",
        fr="Le SPDX doit correspondre aux inventaires Debian/Python et à la somme du vrai code API.",
    )


def test_buildkit_multistage_secret_receipt_and_runtime_minimisation(host):
    services = _state(host)
    secret_hash = host.run("sha256sum %s/build-token", ROOT)
    receipt = host.run("docker exec %s cat /app/build-receipt", services["api"]["Id"])
    assert secret_hash.rc == receipt.rc == 0 and receipt.stdout.strip() == secret_hash.stdout.split()[0], message(
        en="The runtime must contain the build secret's hash receipt, never the secret itself.",
        fr="Le runtime contient le reçu hash du secret de build, jamais le secret lui-même.",
    )
    absent = host.run(
        "docker exec %s /opt/venv/bin/python -c %s", services["api"]["Id"],
        "from pathlib import Path; import sys; "
        "sys.exit(any(Path(p).exists() for p in ['/app/wheels','/app/requirements.txt','/run/secrets/build_token','/build']))",
    )
    assert absent.rc == 0, message(
        en="Keep build wheels, inputs and raw build secrets out of the final stage.",
        fr="Gardez wheels, entrées de build et secrets bruts hors de l'étape finale.",
    )
    token = uuid.uuid4().hex
    secret_path = f"{ROOT}/trial-secret-{token}"
    tag = f"dsoxlab-capstone:trial-{token}"
    host.run("printf '%%s' %s > %s", token, secret_path)
    try:
        missing = host.run(
            "env DOCKER_BUILDKIT=1 docker build --network=none --no-cache -t %s %s/source",
            tag, ROOT,
        )
        assert missing.rc != 0 and "build_token" in (missing.stdout + missing.stderr), message(
            en="A cache-cold build without the required BuildKit secret must fail for that missing secret.",
            fr="Un build sans cache ni secret BuildKit obligatoire doit échouer pour ce secret manquant.",
        )
        valid = host.run(
            "env DOCKER_BUILDKIT=1 docker build --network=none --no-cache --secret %s -t %s %s/source",
            f"id=build_token,src={secret_path}", tag, ROOT,
        )
        observed = host.run(
            "docker run --rm --network none --label %s --entrypoint cat %s /app/build-receipt",
            f"dsoxlab.lab={LABEL}", tag,
        )
        assert valid.rc == observed.rc == 0 and observed.stdout.strip() == hashlib.sha256(token.encode()).hexdigest(), message(
            en="A fresh offline build must consume the changed secret without baking its value into runtime.",
            fr="Un build frais hors ligne doit consommer le secret modifié sans embarquer sa valeur brute.",
        )
    finally:
        host.run("docker image rm -f %s; rm -f %s", tag, secret_path)


def test_runtime_nonroot_secret_limits_and_health_dependency(host):
    services = _state(host)
    api, db = services["api"], services["db"]
    hc = api["HostConfig"]
    assert api["Config"]["User"] == "10001:10001" and hc["ReadonlyRootfs"] and (
        "ALL" in hc.get("CapDrop", []) and "no-new-privileges:true" in hc.get("SecurityOpt", [])
    ), message(
        en="Run API UID/GID 10001, read-only, all capabilities dropped and no-new-privileges.",
        fr="API UID/GID 10001, lecture seule, capacités toutes retirées et no-new-privileges.",
    )
    for name, ceiling in (("api", 128 * 1024 * 1024), ("db", 256 * 1024 * 1024)):
        config = services[name]["HostConfig"]
        cpus = config["NanoCpus"] or (
            config.get("CpuQuota", 0) * 1_000_000_000 / (config.get("CpuPeriod", 0) or 100000)
        )
        assert 0 < config["Memory"] <= ceiling and 0 < cpus <= 500_000_000, message(
            en=f"Apply real memory and CPU limits to {name}.",
            fr=f"Appliquez de vraies limites mémoire et CPU à {name}.",
        )
    for container in (api, db):
        env = dict(item.split("=", 1) for item in container["Config"]["Env"])
        assert not any(k in env for k in ("POSTGRES_PASSWORD", "DB_PASSWORD", "PGPASSWORD")) and any(
            m["Destination"] == "/run/secrets/db_password" and not m["RW"] for m in container["Mounts"]
        ), message(
            en="Both services must consume a read-only password file, not plaintext environment credentials.",
            fr="Les deux services consomment un secret fichier en lecture seule, pas un mot de passe d'environnement.",
        )
    resolved = _compose(host, ["config", "--format", "json"])
    assert resolved.rc == 0 and json.loads(resolved.stdout)["services"]["api"]["depends_on"]["db"]["condition"] == "service_healthy", message(
        en="Gate API startup on healthy PostgreSQL.",
        fr="Conditionnez le démarrage API à PostgreSQL sain.",
    )
    uid = host.run("docker exec %s id -u", api["Id"])
    assert uid.rc == 0 and uid.stdout.strip() == "10001", message(
        en="Measure UID 10001 in the running API process context.",
        fr="Mesurez UID 10001 dans le contexte d'exécution API.",
    )


def test_network_isolation_and_postgresql_real_write(host):
    services = _state(host)
    api, db = services["api"], services["db"]
    backend = f"{PROJECT}_backend"
    network = host.run("docker network inspect %s", backend)
    assert network.rc == 0, message(
        en="Create the internal backend network.", fr="Créez le réseau backend interne.",
    )
    metadata = json.loads(network.stdout)[0]
    assert metadata["Internal"] and set(metadata["Containers"]) == {api["Id"], db["Id"]} and (
        set(db["NetworkSettings"]["Networks"]) == {backend}
    ) and not db["HostConfig"]["PortBindings"] and api["HostConfig"]["PortBindings"] == {
        "8080/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18088"}],
    }, message(
        en="Isolate DB on internal backend; publish only API on loopback 18088.",
        fr="Isolez DB sur backend interne ; publiez seulement API sur boucle locale 18088.",
    )
    token = uuid.uuid4().hex
    _write(host, token, token)
    query = host.run(
        "docker exec %s psql -U delivery -d delivery -Atc %s",
        db["Id"], "SELECT value FROM items",
    )
    assert query.rc == 0 and token in query.stdout.splitlines(), message(
        en="API writes must actually reach PostgreSQL, not an in-memory fake.",
        fr="Les écritures API doivent atteindre PostgreSQL, pas un faux stockage en mémoire.",
    )
    frontend = f"{PROJECT}_frontend"
    rejected = host.run(
        "docker run --rm --network %s --label %s --entrypoint python %s -c %s",
        frontend, f"dsoxlab.lab={LABEL}", api["Image"],
        "import socket,sys; s=socket.socket(); s.settimeout(2); "
        f"sys.exit(0 if s.connect_ex(('{db['NetworkSettings']['Networks'][backend]['IPAddress']}',5432)) != 0 else 1)",
    )
    assert rejected.rc == 0, message(
        en="A frontend-only container must fail a real TCP connection to PostgreSQL.",
        fr="Un conteneur frontend seul doit subir un vrai refus TCP vers PostgreSQL.",
    )


def test_data_survives_database_and_api_container_replacement(host):
    services = _state(host)
    mounts = [m for m in services["db"]["Mounts"] if m["Destination"] == "/var/lib/postgresql/data"]
    assert len(mounts) == 1 and mounts[0]["Type"] == "volume" and mounts[0]["Name"] == f"{PROJECT}_data", message(
        en="Use the named data volume at PostgreSQL's real data directory.",
        fr="Utilisez le volume nommé data au vrai répertoire de données PostgreSQL.",
    )
    token = uuid.uuid4().hex
    _write(host, token, token)
    rebuilt = _compose(host, ["up", "-d", "--force-recreate", "--wait", "--wait-timeout", "90", "db", "api"])
    assert rebuilt.rc == 0, message(
        en="Recreate both containers without dropping the database volume.",
        fr="Recréez les deux conteneurs sans supprimer le volume de base.",
    )
    current = _state(host)
    assert all(current[n]["Id"] != services[n]["Id"] for n in ("api", "db")), message(
        en="Actually replace both container identities.",
        fr="Remplacez réellement les identités des deux conteneurs.",
    )
    _read(host, token, token)


def test_eight_real_incidents_recover_without_data_loss(host):
    _state(host)
    token = uuid.uuid4().hex
    _write(host, token, token)
    for number in range(1, 9):
        cycle_complete = False
        try:
            injected = host.run("/usr/bin/python3 %s/incidents.py %s", ROOT, str(number))
            assert injected.rc == 0, message(
                en=f"Incident {number} must be injected into the lab stack.",
                fr=f"L'incident {number} doit être injecté dans la stack du lab.",
            )
            failed = False
            for _ in range(15):
                if _request(host).rc != 0:
                    failed = True
                    break
                time.sleep(0.5)
            assert failed, message(
                en=f"Incident {number} must produce a measurable availability failure.",
                fr=f"L'incident {number} doit produire une panne de disponibilité mesurable.",
            )
            recovered = host.run("timeout 120 %s/recover.sh", ROOT)
            assert recovered.rc == 0, message(
                en=f"recover.sh must restore incident {number} within 120 seconds.",
                fr=f"recover.sh doit rétablir l'incident {number} sous 120 secondes.",
            )
            _wait_ready(host)
            _state(host)
            _read(host, token, token)
            cycle_complete = True
        finally:
            if not cycle_complete:
                host.run("timeout 120 %s/recover.sh", ROOT)
