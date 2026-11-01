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


def _state(host):
    found = host.run(
        "docker ps -aq --filter %s --filter %s",
        f"label=com.docker.compose.project={PROJECT}", f"label=dsoxlab.lab={LABEL}",
    )
    assert found.rc == 0 and len(found.stdout.split()) == 2, message(
        en="Deploy exactly the labelled api/db delivery services before earning points.",
        fr="Déployez exactement les services api/db labellisés avant tout point.",
    )
    inspected = host.run(shlex.join(["docker", "inspect", *found.stdout.split()]))
    assert inspected.rc == 0, message(
        en="Cannot inspect the delivered services.", fr="Impossible d'inspecter les services livrés.",
    )
    containers = json.loads(inspected.stdout)
    services = {c["Config"]["Labels"]["com.docker.compose.service"]: c for c in containers}
    ready = _request(host)
    assert set(services) == {"api", "db"} and all(
        c["State"]["Running"] and c["State"].get("Health", {}).get("Status") == "healthy"
        for c in containers
    ) and ready.rc == 0 and json.loads(ready.stdout).get("ready") is True, message(
        en="Both services must be healthy and /ready must genuinely query PostgreSQL.",
        fr="Les deux services doivent être sains et /ready doit interroger réellement PostgreSQL.",
    )
    return services


def _wait_ready(host):
    for _ in range(40):
        result = _request(host)
        if result.rc == 0:
            return
        time.sleep(0.5)
    pytest.fail(message(
        en="API availability was not restored.", fr="La disponibilité API n'a pas été rétablie.",
    ))


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
