"""Collecte sur la VM : la mesure est une, les verdicts sont plusieurs.

CETTE SONDE NE JUGE PRESQUE RIEN, et c'est le changement. Elle portait trente
assertions, dont la première qui tombait masquait les vingt-neuf suivantes sur
une charge de deux minutes. Elle mesure maintenant, et rend ses faits : les
verdicts sont dans `test_functional.py`, un par famille d'exigences.

Ce qui reste assertif ici est exactement ce sans quoi RIEN n'est mesurable : les
deux composants doivent tourner, et ils doivent répondre. Un relevé pris sur une
stack éteinte ne dit rien sur la configuration, il dit que la stack est éteinte.

CE QUI NE TRAVERSE JAMAIS LE LIEN : le témoin d'en-tête et les journaux bruts.
La sonde en rend des booléens et les enregistrements de corrélation (qui ne
portent que des identifiants frais et des valeurs métier), jamais le texte. Le
secret reste sur la machine qui le fabrique.
"""

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
PINNED = (
    "python:3.14.10-slim-trixie@sha256:"
    "3cabfd7d7aaf394e6040e79fa1eec6ca1c52b74ed9188650472695d9a9326999"
)
ATTENTE = (
    "import time,urllib.request\n"
    "deadline=time.monotonic()+5\n"
    "while True:\n"
    " try:\n"
    "  urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=1).close()\n"
    "  break\n"
    " except OSError:\n"
    "  assert time.monotonic()<deadline, 'Component readiness timed out'\n"
    "  time.sleep(0.05)\n"
)


def message(en: str, fr: str) -> str:
    return fr if os.environ.get("DSOXLAB_LANG", "en").lower().startswith("fr") else en


def docker(*args, timeout=30):
    result = subprocess.run(
        ["docker", *args], check=False, text=True, capture_output=True, timeout=timeout
    )
    assert result.returncode == 0, message(
        en=f"Docker operation failed: {args[0]} {result.stderr.strip()[-200:]}",
        fr=f"L'operation Docker echoue : {args[0]} {result.stderr.strip()[-200:]}",
    )
    return result.stdout.strip()


def containers(project):
    """Les deux composants, sans lesquels il n'y a rien à mesurer."""
    ids = docker(
        "ps", "-q", "--filter", f"label=com.docker.compose.project={project}"
    ).split()
    assert len(ids) == 2, message(
        en=f"Start both supplied components ({len(ids)} running)",
        fr=f"Demarrez les deux composants fournis ({len(ids)} en cours)",
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


def _faits(service):
    """Ce que la configuration de ce composant est, sans en juger."""
    quota, period = docker(
        "exec", service["Id"], "cat", "/sys/fs/cgroup/cpu.max"
    ).split()
    return {
        "image_epinglee": service["Image"] == docker(
            "image", "inspect", PINNED, "--format", "{{.Id}}"
        ),
        "en_cours": bool(service["State"]["Running"]),
        "privilegie": bool(service["HostConfig"]["Privileged"]),
        "cap_add": service["HostConfig"]["CapAdd"] or [],
        "label": service["Config"]["Labels"].get("dsoxlab.lab"),
        "cgroupns": service["HostConfig"]["CgroupnsMode"],
        "quota": quota,
        "period": int(period),
    }


def _journaux(service, witness, identities):
    """Les journaux réduits à ce qui peut traverser le lien, et rien de plus."""
    texte = docker("logs", service["Id"])
    enregistrements = []
    for ligne in texte.splitlines():
        if ligne.startswith("{"):
            try:
                enregistrements.append(json.loads(ligne))
            except ValueError:
                continue
    return {
        "temoin_present": witness in texte,
        "autorisation_presente": "authorization" in texte.lower(),
        # Une liste par identité : le test y lit le compte ET le contenu, donc
        # il peut distinguer « trace absente » de « trace dupliquée » de « trace
        # fausse », trois défauts qui appellent trois gestes différents.
        "traces": [
            [r for r in enregistrements if r.get("request_id") == rid]
            for rid in identities
        ],
    }


def collecter(project, count=16):
    """Un relevé complet d'une stack sous charge bornée.

    Tout est rendu, rien n'est jugé, sauf la disponibilité : une charge envoyée
    à un composant qui ne répond pas encore mesurerait le démarrage.
    """
    services = containers(project)
    for service in services.values():
        docker("exec", service["Id"], "python", "-c", ATTENTE)
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

    # Témoin et identités frais à chaque passage : une corrélation qui marche
    # parce que les identifiants sont ceux de la fois précédente ne marche pas.
    witness = uuid.uuid4().hex
    identities = [uuid.uuid4().hex for _ in range(count)]
    quantites = [index % 20 + 1 for index in range(count)]
    before = {role: stats(service) for role, service in services.items()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(request, base, rid, quantites[index], witness)
            for index, rid in enumerate(identities)
        ]
        reponses = [future.result(timeout=20) for future in futures]
    after = {role: stats(service) for role, service in services.items()}
    invalide = request(base, uuid.uuid4().hex, 0, witness)

    return {
        "count": count,
        "identites": identities,
        "quantites": quantites,
        "faits": {role: _faits(service) for role, service in services.items()},
        "reponses": reponses,
        "invalide": invalide,
        "journaux": {
            role: _journaux(service, witness, identities)
            for role, service in services.items()
        },
        "delta": {
            role: {
                cle: after[role][cle] - before[role][cle]
                for cle in ("usage_usec", "nr_throttled", "throttled_usec")
            }
            for role in services
        },
    }


def variante_dangereuse():
    """Un correctif de surface, dérivé de la stack de l'apprenant.

    Quotas corrects, corrélation correcte, et journaux du calculateur laissés
    bavards. Le test applique son PROPRE critère de journaux sûrs à ce relevé et
    exige qu'il refuse : c'est ainsi que ce critère prouve qu'il peut refuser,
    plutôt que de passer sur une stack bien configurée sans jamais être éprouvé.
    """
    import yaml

    config = yaml.safe_load((WORK / "compose.yaml").read_text())
    essai = PROJECT + "-trial-" + uuid.uuid4().hex[:10]
    chemin = WORK / (essai + ".json")
    for service in config["services"].values():
        service.pop("container_name", None)
        service["volumes"] = [f"{WORK}:/app:ro"]
        service.setdefault("environment", {})
        service["environment"]["CORRELATE"] = "1"
        service["environment"]["SAFE_LOGS"] = "1"
    config["services"]["worker"]["environment"]["SAFE_LOGS"] = "0"
    config["services"]["worker"]["cpus"] = 0.25
    config["services"]["gateway"]["cpus"] = 1.0
    config["services"]["gateway"]["ports"] = ["127.0.0.1::8080"]
    chemin.write_text(json.dumps(config))
    try:
        docker("compose", "-p", essai, "-f", str(chemin), "up", "-d", "--pull", "never")
        return collecter(essai, count=4)
    finally:
        subprocess.run(
            ["docker", "compose", "-p", essai, "-f", str(chemin),
             "down", "--volumes", "--remove-orphans"],
            check=False, capture_output=True, timeout=25,
        )
        chemin.unlink(missing_ok=True)


def main():
    docker(
        "compose", "-p", PROJECT, "-f", str(WORK / "compose.yaml"),
        "up", "-d", "--force-recreate", "--pull", "never",
    )
    print(json.dumps({
        "apprenant": collecter(PROJECT),
        "variante": variante_dangereuse(),
    }))


if __name__ == "__main__":
    main()
