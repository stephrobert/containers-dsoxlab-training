"""Remote black-box trial. Only private, labelled trial resources are removed."""

import concurrent.futures
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid

LAB = "container-arret-transactionnel"
PROJECT = "dsoxlab-" + LAB + "-stack"


def message(en: str, fr: str) -> str:
    """Match conftest's language choice without importing it on the VM."""
    return fr if os.environ.get("DSOXLAB_LANG", "en").lower().startswith("fr") else en


def docker(*args, timeout=20):
    result = subprocess.run(
        ["docker", *args], check=False, text=True, capture_output=True, timeout=timeout
    )
    assert result.returncode == 0, message(
        en=f"Docker operation failed: {args[0]}",
        fr=f"L'opération Docker échoue : {args[0]}",
    )
    return result.stdout.strip()


def read(base, path):
    try:
        with urllib.request.urlopen(base + path, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def wait_for(predicate, seconds=5):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            value = predicate()
            if value:
                return value
        except (OSError, ValueError):
            pass
        time.sleep(0.04)
    raise AssertionError(message(
        en="HTTP transaction barrier or readiness deadline exceeded",
        fr="Le délai de la barrière HTTP ou de disponibilité est dépassé",
    ))


def main():
    found = docker(
        "ps", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}"
    )
    assert len(found.split()) == 1, message(
        en="Start the supplied ledger project",
        fr="Démarrez le projet de registre fourni",
    )
    original = json.loads(docker("inspect", found))[0]
    assert original["State"]["Running"]
    assert (
        not original["HostConfig"]["Privileged"]
        and not original["HostConfig"]["CapAdd"]
    )
    assert original["Config"]["Labels"].get("dsoxlab.lab") == LAB
    assert original["Config"]["User"] == "10001:10001" and (
        original["HostConfig"]["ReadonlyRootfs"]
        and docker("exec", original["Id"], "id", "-u") == "10001"
    ), message(
        en="The transaction service must run as UID/GID 10001 with a read-only root filesystem",
        fr="Le service transactionnel doit tourner sous UID/GID 10001 avec une racine en lecture seule",
    )
    data = next(m for m in original["Mounts"] if m["Destination"] == "/data")
    assert data["Type"] == "volume", message(
        en="Use durable storage for the domain database",
        fr="Utilisez un stockage durable pour la base métier",
    )
    app = next(m for m in original["Mounts"] if m["Destination"] == "/app")
    pinned = "python:3.13.8-slim-bookworm@sha256:61169c2bdb8e6bb44a8dfad33f569d324d52f079fded9a204b322a6fb9c9f799"
    assert original["Image"] == docker(
        "image", "inspect", pinned, "--format", "{{.Id}}"
    )
    trial = PROJECT + "-trial-" + uuid.uuid4().hex[:10]
    volume = trial + "-data"
    docker("volume", "create", "--label", f"dsoxlab.lab={LAB}", volume)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def start(mode=None):
        entry = original["Config"]["Entrypoint"]
        assert entry, message(
            en="The supplied entry process must remain executable",
            fr="Le processus d'entrée fourni doit rester exécutable",
        )
        args = [
            "run",
            "-d",
            "--name",
            trial,
            "--label",
            f"dsoxlab.lab={LAB}",
            "-p",
            "127.0.0.1::8080",
            "--mount",
            f"type=volume,src={volume},dst=/data",
            "--mount",
            f"type=bind,src={app['Source']},dst=/app,readonly",
            "--entrypoint",
            entry[0],
            "--user",
            original["Config"]["User"],
            "--read-only",
        ]
        for env in original["Config"]["Env"]:
            args += ["-e", env]
        if mode is not None:
            args += ["-e", "SERVICE_MODE=" + mode]
        docker(*args, original["Image"], *entry[1:], *(original["Config"]["Cmd"] or []))
        port = docker("port", trial, "8080/tcp").split(":")[-1]
        base = "http://127.0.0.1:" + port
        wait_for(lambda: read(base, "/health")[0] == 200)
        denied = subprocess.run(
            ["docker", "exec", "--user", "10002:10002", trial, "python", "-c",
             "from pathlib import Path; Path('/data/ledger.sqlite').read_bytes()"],
            check=False, capture_output=True, text=True, timeout=5,
        )
        assert denied.returncode != 0 and "PermissionError" in denied.stderr, message(
            en="An unexpected application UID must be refused access to persistent transactions",
            fr="Un UID applicatif inattendu doit subir un refus d'acces aux transactions persistantes",
        )
        return base

    def begin(base, key):
        future = pool.submit(read, base, "/write?id=" + key)
        wait_for(lambda: read(base, "/inflight")[1] == {"id": key, "begun": True})
        assert not future.done(), message(
            en="The write must really be in flight",
            fr="L'écriture doit réellement être en cours",
        )
        assert read(base, "/record?id=" + key)[0] == 404, message(
            en="Uncommitted data must not be visible",
            fr="Les données non validées ne doivent pas être visibles",
        )
        return future

    try:
        docker(
            "run", "--rm", "--network", "none", "--label", f"dsoxlab.lab={LAB}",
            "--user", "0:0", "--mount", f"type=volume,src={volume},dst=/data",
            "--entrypoint", "python", original["Image"], "-c",
            "import os; os.chown('/data',10001,10001); os.chmod('/data',0o700)",
        )
        base = start()
        first_configuration = read(base, "/configuration")
        assert (
            first_configuration[0] == 200 and "service_mode" in first_configuration[1]
        )
        good = uuid.uuid4().hex
        future = begin(base, good)
        docker("stop", "--time", "8", trial, timeout=12)
        assert future.result(timeout=2) == (200, {"id": good, "value": "accepted"}), message(
            en="Graceful stop interrupted the domain request",
            fr="L'arrêt gracieux a interrompu la requête métier",
        )
        status = json.loads(docker("inspect", trial))[0]["State"]
        assert status["ExitCode"] == 0, message(
            en="The service was killed instead of drained",
            fr="Le service a été tué au lieu de terminer les requêtes",
        )
        events = [
            json.loads(line)
            for line in docker("logs", trial).splitlines()
            if line.startswith("{")
        ]
        relevant = [e["event"] for e in events if e.get("request_id") == good]
        assert relevant == [
            "transaction_started",
            "signal_received",
            "transaction_committed",
            "request_finished",
        ]
        assert events[-1]["event"] == "drained"
        docker("rm", trial)
        second_mode = "alternate-" + uuid.uuid4().hex[:10]
        base = start(second_mode)
        assert read(base, "/configuration") == (200, {"service_mode": second_mode})
        assert first_configuration[1]["service_mode"] != second_mode, message(
            en="Two configurations of the same service must produce distinct HTTP observations",
            fr="Deux configurations du même service doivent produire des observations HTTP distinctes",
        )
        assert read(base, "/record?id=" + good) == (
            200,
            {"id": good, "value": "accepted"},
        )
        lost = uuid.uuid4().hex
        future = begin(base, lost)
        docker("kill", "--signal", "KILL", trial)
        try:
            future.result(timeout=2)
        except (OSError, ValueError):
            pass
        else:
            raise AssertionError(message(
                en="SIGKILL must abort the held request",
                fr="SIGKILL doit abandonner la requête retenue par la barrière",
            ))
        assert json.loads(docker("inspect", trial))[0]["State"]["ExitCode"] == 137
        forced = docker("logs", trial)
        assert "transaction_committed" not in forced and "signal_received" not in forced
        docker("rm", "-f", trial)
        base = start()
        assert read(base, "/record?id=" + lost)[0] == 404, message(
            en="Forced stop unexpectedly committed the transaction",
            fr="L'arrêt forcé a validé la transaction de façon inattendue",
        )
        assert read(base, "/record?id=" + good) == (
            200,
            {"id": good, "value": "accepted"},
        ), message(
            en="Previously committed data was damaged",
            fr="Les données précédemment validées ont été endommagées",
        )
        fresh = uuid.uuid4().hex
        future = begin(base, fresh)
        read(base, "/release")
        assert future.result(timeout=2)[0] == 200, message(
            en="Database cannot accept a write after recovery",
            fr="La base ne peut plus accepter d'écriture après la reprise",
        )
        assert read(base, "/record?id=" + fresh)[1]["value"] == "accepted"
        print(
            json.dumps(
                {
                    "graceful": "committed-and-recreated",
                    "forced": "aborted-only-inflight",
                    "database": "usable",
                }
            )
        )
    finally:
        subprocess.run(
            ["docker", "rm", "-f", trial], check=False, capture_output=True, timeout=12
        )
        pool.shutdown(wait=True)
        subprocess.run(
            ["docker", "volume", "rm", volume],
            check=False,
            capture_output=True,
            timeout=12,
        )


if __name__ == "__main__":
    main()
