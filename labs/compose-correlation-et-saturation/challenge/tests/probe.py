"""Bounded business load, cgroup attribution and a deliberately unsafe variant."""

import concurrent.futures
import json
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.request
import uuid

LAB = "compose-correlation-et-saturation"
PROJECT = "dsoxlab-" + LAB + "-stack"
WORK = pathlib.Path("/opt/dsoxlab-" + LAB)


def message(en: str, fr: str) -> str:
    return fr if os.environ.get("DSOXLAB_LANG", "en").lower().startswith("fr") else en


def docker(*args, timeout=30):
    result = subprocess.run(
        ["docker", *args], check=False, text=True, capture_output=True, timeout=timeout
    )
    assert result.returncode == 0, message(
        en=f"Docker operation failed: {args[0]}",
        fr=f"L'operation Docker echoue : {args[0]}",
    )
    return result.stdout.strip()


def containers(project):
    ids = docker(
        "ps", "-q", "--filter", f"label=com.docker.compose.project={project}"
    ).split()
    assert len(ids) == 2, message(
        en="Start both supplied components", fr="Demarrez les deux composants fournis",
    )
    items = json.loads(docker("inspect", *ids))
    return {c["Config"]["Labels"]["com.docker.compose.service"]: c for c in items}


def stats(container):
    return {
        key: int(value)
        for key, value in (
            line.split()
            for line in docker(
                "exec", container["Id"], "cat", "/sys/fs/cgroup/cpu.stat"
            ).splitlines()
        )
    }


def request(base, rid, quantity, witness):
    req = urllib.request.Request(
        base + f"/quote?quantity={quantity}",
        headers={"X-Request-ID": rid, "Authorization": "Bearer " + witness},
    )
    try:
        with urllib.request.urlopen(req, timeout=18) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def assess(project, count=16):
    services = containers(project)
    pinned = "python:3.13.8-slim-bookworm@sha256:61169c2bdb8e6bb44a8dfad33f569d324d52f079fded9a204b322a6fb9c9f799"
    image = docker("image", "inspect", pinned, "--format", "{{.Id}}")
    for service in services.values():
        assert service["Image"] == image and service["State"]["Running"]
        assert (
            not service["HostConfig"]["Privileged"]
            and not service["HostConfig"]["CapAdd"]
        )
        assert service["Config"]["Labels"].get("dsoxlab.lab") == LAB
        assert service["HostConfig"]["CgroupnsMode"] == "private"
    limits = {}
    for role, service in services.items():
        quota, period = docker(
            "exec", service["Id"], "cat", "/sys/fs/cgroup/cpu.max"
        ).split()
        assert quota != "max", message(
            en="Use hard CPU quotas, not relative shares",
            fr="Utilisez des quotas CPU stricts, pas des poids relatifs",
        )
        limits[role] = int(quota) / int(period)
    assert limits == {"gateway": 1.0, "worker": 0.25}, message(
        en="Keep the gateway at one CPU and isolate the worker at a quarter CPU",
        fr="Gardez un CPU pour la passerelle et un quart de CPU pour le calculateur",
    )
    for service in services.values():
        docker(
            "exec",
            service["Id"],
            "python",
            "-c",
            "import time,urllib.request\n"
            "deadline=time.monotonic()+5\n"
            "while True:\n"
            " try:\n"
            "  urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=1).close()\n"
            "  break\n"
            " except OSError:\n"
            "  assert time.monotonic()<deadline, 'Component readiness timed out'\n"
            "  time.sleep(0.05)\n",
        )
    base = (
        "http://127.0.0.1:"
        + docker("port", services["gateway"]["Id"], "8080/tcp").split(":")[-1]
    )
    deadline = time.monotonic() + 5
    while True:
        try:
            with urllib.request.urlopen(base + "/health", timeout=1):
                break
        except OSError:
            assert time.monotonic() < deadline, message(
                en="Gateway readiness timed out",
                fr="Le delai de disponibilite de la passerelle est depasse",
            )
            time.sleep(0.05)
    # Use a fresh witness and fresh identities; never print headers or raw logs.
    witness = uuid.uuid4().hex
    identities = [uuid.uuid4().hex for _ in range(count)]
    before = {role: stats(service) for role, service in services.items()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(request, base, rid, index % 20 + 1, witness)
            for index, rid in enumerate(identities)
        ]
        results = [future.result(timeout=20) for future in futures]
    after = {role: stats(service) for role, service in services.items()}
    for index, (status, body) in enumerate(results):
        quantity = index % 20 + 1
        assert status == 200 and body == {
            "request_id": identities[index],
            "quantity": quantity,
            "total_cents": quantity * 125,
        }, message(
            en=f"Business response or fresh request correlation is wrong (HTTP {status})",
            fr=f"La reponse metier ou la correlation est incorrecte (HTTP {status})",
        )
    assert request(base, uuid.uuid4().hex, 0, witness) == (
        400,
        {"error": "invalid_quote"},
    ), message(
        en="Invalid domain request must be rejected",
        fr="La requete metier invalide doit etre refusee",
    )
    for role, service in services.items():
        text = docker("logs", service["Id"])
        assert witness not in text and "authorization" not in text.lower(), message(
            en="Sensitive headers leaked into component logs",
            fr="Des en-tetes sensibles apparaissent dans les journaux des composants",
        )
        records = [
            json.loads(line) for line in text.splitlines() if line.startswith("{")
        ]
        for index, rid in enumerate(identities):
            matches = [r for r in records if r.get("request_id") == rid]
            quantity = index % 20 + 1
            assert len(matches) == 1 and matches[0] == {
                "component": role,
                "event": "quote_finished",
                "request_id": rid,
                "quantity": quantity,
                "total_cents": quantity * 125,
            }, message(
                en="End-to-end JSON business trace is incomplete or duplicated",
                fr="La trace metier JSON de bout en bout est incomplete ou dupliquee",
            )
    delta = {
        role: {key: after[role][key] - before[role][key] for key in before[role]}
        for role in services
    }
    worker = delta["worker"]
    assert (
        worker["nr_throttled"] > 0
        and worker["throttled_usec"] > 0
        and worker["usage_usec"] >= count * 100000
    ), message(
        en="No measured worker CPU saturation",
        fr="Aucune saturation CPU mesuree du calculateur",
    )
    assert worker["usage_usec"] > delta["gateway"]["usage_usec"] * 2, message(
        en="Measured work is not attributable to the calculator",
        fr="La charge mesuree n'est pas attribuable au calculateur",
    )
    return {
        role: {
            k: delta[role][k] for k in ("usage_usec", "nr_throttled", "throttled_usec")
        }
        for role in services
    }


def main():
    import yaml

    docker(
        "compose",
        "-p",
        PROJECT,
        "-f",
        str(WORK / "compose.yaml"),
        "up",
        "-d",
        "--force-recreate",
        "--pull",
        "never",
    )
    measurement = assess(PROJECT)
    # A surface fix (correct quota and correlation but unsafe worker logs) is rejected.
    config = yaml.safe_load((WORK / "compose.yaml").read_text())
    trial = PROJECT + "-trial-" + uuid.uuid4().hex[:10]
    path = WORK / (trial + ".json")
    for service in config["services"].values():
        service.pop("container_name", None)
        service["volumes"] = [f"{WORK}:/app:ro"]
        service["environment"]["CORRELATE"] = "1"
        service["environment"]["SAFE_LOGS"] = "1"
    config["services"]["worker"]["environment"]["SAFE_LOGS"] = "0"
    config["services"]["worker"]["cpus"] = 0.25
    config["services"]["gateway"]["cpus"] = 1.0
    config["services"]["gateway"]["ports"] = ["127.0.0.1::8080"]
    path.write_text(json.dumps(config))
    try:
        docker("compose", "-p", trial, "-f", str(path), "up", "-d", "--pull", "never")
        try:
            assess(trial, count=4)
        except AssertionError as error:
            assert str(error) == message(
                en="Sensitive headers leaked into component logs",
                fr="Des en-tetes sensibles apparaissent dans les journaux des composants",
            ), message(
                en="Unsafe representative variant failed for an unrelated reason",
                fr="La variante dangereuse echoue pour une raison sans rapport",
            )
        else:
            raise AssertionError(message(
                en="Unsafe representative configuration received a full verdict",
                fr="La configuration dangereuse obtient un verdict plein",
            ))
    finally:
        subprocess.run(
            [
                "docker",
                "compose",
                "-p",
                trial,
                "-f",
                str(path),
                "down",
                "--volumes",
                "--remove-orphans",
            ],
            check=False,
            capture_output=True,
            timeout=25,
        )
        path.unlink(missing_ok=True)
    print(
        json.dumps(
            {"cgroups": measurement, "unsafe_variant": "rejected", "fresh_requests": 16}
        )
    )


if __name__ == "__main__":
    main()
