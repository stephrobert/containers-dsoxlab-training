"""Measure a service-scoped file secret without exposing its content."""

from __future__ import annotations

import hashlib
import json
import shlex
import time

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-compose-secret"
PROJECT = "dsoxlab-compose-secrets"
TOKEN = f"{ROOT}/credentials/token.txt"
TOKEN_SUIVANT = f"{ROOT}/credentials/token-next.txt"
BASE = "alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _compose(host, *args):
    return host.run(shlex.join(["docker", "compose", "-p", PROJECT, "-f", f"{ROOT}/compose.yaml", *args]))


def _services(host):
    found = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={PROJECT}")
    assert found.rc == 0 and len(found.stdout.split()) == 2, message(
        en="Start exactly app and observer in project dsoxlab-compose-secrets.",
        fr="Démarrez exactement app et observer dans le projet dsoxlab-compose-secrets.",
    )
    result = host.run(shlex.join(["docker", "inspect", *found.stdout.split()]))
    assert result.rc == 0, message(
        en="Cannot inspect the secret consumers.",
        fr="Impossible d'inspecter les consommateurs du secret.",
    )
    services = {c["Config"]["Labels"].get("com.docker.compose.service"): c for c in json.loads(result.stdout)}
    assert set(services) == {"app", "observer"} and all(c["State"]["Running"] for c in services.values()), message(
        en="Both app and observer must run.",
        fr="App et observer doivent être démarrés.",
    )
    for name, reference in (("app", "dsoxlab-compose-secret:app"), ("observer", BASE)):
        image = host.run("docker image inspect %s", reference)
        assert image.rc == 0, message(
            en=f"Keep the supplied image for {name}.",
            fr=f"Gardez l'image fournie pour {name}.",
        )
        original = json.loads(image.stdout)[0]
        if name == "app":
            protected = host.file("/root/.lab-compose-secret-image").content_string.strip()
            assert original["Id"] == protected, message(
                en="Keep the actual prepared app image identity; replacing its mutable tag is not allowed.",
                fr="Gardez l'identité réelle de l'image app préparée ; remplacer son tag mutable est interdit.",
            )
        assert services[name]["Image"] == original["Id"] and not services[name]["Config"]["Entrypoint"], message(
            en=f"Use the supplied {name} image without replacing its entrypoint.",
            fr=f"Utilisez l'image {name} fournie sans remplacer son entrypoint.",
        )
        if name == "app":
            assert services[name]["Config"]["Cmd"] == original["Config"]["Cmd"], message(
                en="Keep the supplied secret consumer command.",
                fr="Gardez la commande fournie de consommation du secret.",
            )
    return services, result.stdout


def _fingerprint(host, app, expected):
    for _ in range(20):
        result = host.run("docker exec %s cat /tmp/fingerprint", app["Id"])
        if result.rc == 0:
            break
        time.sleep(0.1)
    assert result.rc == 0 and result.stdout.strip() == expected, message(
        en="The app must consume the current mounted secret at startup.",
        fr="L'application doit consommer le secret actuellement monté au démarrage.",
    )


def test_compose_grants_the_file_secret_only_to_app(host):
    services, _ = _services(host)
    config = _compose(host, "config", "--format", "json")
    assert config.rc == 0, message(
        en="The Compose declaration must resolve.",
        fr="La déclaration Compose doit être résolue.",
    )
    resolved = json.loads(config.stdout)
    assert resolved.get("secrets", {}).get("api_token", {}).get("file") == TOKEN and [
        s["source"] for s in resolved["services"]["app"].get("secrets", [])
    ] == ["api_token"] and not resolved["services"]["observer"].get("secrets"), message(
        en="Declare the file-backed api_token secret and grant it only to app.",
        fr="Déclarez le secret fichier api_token et accordez-le seulement à app.",
    )
    mounts = services["app"]["Mounts"]
    assert len(mounts) == 1 and mounts[0]["Source"] == TOKEN and mounts[0]["Destination"] == "/run/secrets/api_token" and not mounts[0]["RW"] and not services["observer"]["Mounts"], message(
        en="Mount only the read-only token file for app; observer must have no mounts.",
        fr="Montez seulement le fichier jeton en lecture seule pour app ; observer ne doit avoir aucun montage.",
    )
    denied = host.run("docker exec %s test -e /run/secrets/api_token", services["observer"]["Id"])
    assert denied.rc == 1, message(
        en="Observer must not see the secret file.",
        fr="Observer ne doit pas voir le fichier secret.",
    )


def test_secret_is_consumed_without_metadata_or_log_leaks(host):
    services, metadata = _services(host)
    # LA VALEUR EN SERVICE EST LA SUIVANTE, et non celle du départ. Ce
    # contrôle exigeait « le jeton fourni INCHANGÉ », ce qui contredisait
    # frontalement l'épreuve depuis qu'elle demande de le remplacer : le
    # scénario avait été corrigé, pas celui-ci.
    token = host.file(TOKEN).content_string
    suivante = host.file(TOKEN_SUIVANT).content_string
    assert token == suivante, message(
        en="the file the secret mounts does not carry the next value.",
        fr="le fichier monté par le secret ne porte pas la valeur suivante.",
    )
    expected = hashlib.sha256(suivante.encode()).hexdigest()
    _fingerprint(host, services["app"], expected)
    config = _compose(host, "config", "--format", "json")
    assert config.rc == 0, message(
        en="Cannot render the configuration for the leak check.",
        fr="Impossible de rendre la configuration pour le contrôle de fuite.",
    )
    ignored = host.run("git -c safe.directory=%s -C %s check-ignore credentials/token.txt", ROOT, ROOT)
    tracked = host.run("git -c safe.directory=%s -C %s ls-files -- credentials", ROOT, ROOT)
    assert ignored.rc == tracked.rc == 0 and not tracked.stdout.strip(), message(
        en="Keep the real credential outside the repository index with an effective ignore rule.",
        fr="Gardez l'identifiant réel hors de l'index Git avec une exclusion effective.",
    )
    program = (
        "import base64,json,subprocess; from pathlib import Path;"
        f"git=['git','-c','safe.directory={ROOT}','-C','{ROOT}'];"
        f"token=Path({TOKEN!r}).read_bytes().strip();"
        f"suivant=Path({TOKEN_SUIVANT!r}).read_bytes().strip();"
        # LES DEUX VALEURS : l'épreuve en manipule deux, et l'ancienne ne doit
        # pas traîner dans l'historique davantage que la nouvelle.
        "variants=[v for t in (token,suivant) "
        "for v in (t,base64.b64encode(t),t.hex().encode())];"
        "objects=subprocess.check_output(git+['rev-list','--objects','--all'],text=True).splitlines();"
        "blobs=[line.split()[0] for line in objects if "
        "subprocess.check_output(git+['cat-file','-t',line.split()[0]],text=True).strip()=='blob'];"
        "clean=all(not any(v in subprocess.check_output(git+['cat-file','blob',oid]) for v in variants) for oid in blobs);"
        "print(json.dumps({'clean':clean,'blobs':len(blobs)}))"
    )
    scanned = host.run(shlex.join(["python3", "-c", program]))
    assert scanned.rc == 0, message(
        en="Inspect actual reachable Git blobs without printing the credential.",
        fr="Inspectez les blobs Git accessibles sans afficher l'identifiant.",
    )
    history = json.loads(scanned.stdout)
    assert history["clean"] and history["blobs"] > 0, message(
        en="The secret must be absent from all reachable Git history, including base64/hex forms.",
        fr="Le secret est absent de tout l'historique Git accessible, y compris en base64/hex.",
    )
    for container in services.values():
        logs = host.run("docker logs %s", container["Id"])
        assert logs.rc == 0 and token.strip() not in metadata + config.stdout + logs.stdout + logs.stderr, message(
            en="Do not put the token in environment, labels, commands, rendered configuration or logs.",
            fr="Ne placez pas le jeton dans l'environnement, les labels, les commandes, la configuration rendue ou les journaux.",
        )


def test_le_service_consomme_la_valeur_suivante_apres_une_recreation(host):
    """Le REMPLACEMENT est le geste de l'apprenant, et il se lit dans l'état final.

    Ce contrôle jouait lui-même la rotation : il écrivait un jeton neuf,
    recréait les services, vérifiait, puis restaurait tout. La fiche promettait
    pourtant de « fournir et remplacer » un secret, et l'apprenant ne
    remplaçait rien. Un lab ne note pas un geste qu'il a fait à la place de
    celui qui l'apprend.

    LE LAB POSE DONC UNE VALEUR SUIVANTE, dans `credentials/token-next.txt`, et
    l'énoncé demande de la mettre en service. Trois faits sont lus, et aucune
    commande n'est imposée.

    LE TROISIÈME EST CELUI QUI APPREND LA LEÇON. Les deux pièges de C27 sont un
    `>` qui modifie le fichier monté sans que le service le relise, et un `mv`
    qui laisse le conteneur sur l'ancien inode. Dans les deux cas l'empreinte
    reste celle de l'ancienne valeur, et le conteneur est plus VIEUX que la
    modification du fichier. On lit donc les deux.
    """
    services, _ = _services(host)

    suivante = host.file(TOKEN_SUIVANT)
    assert suivante.exists, message(
        en=f"`{TOKEN_SUIVANT}` is missing: the lab did not prepare the next "
           "value. Replay `dsoxlab run`.",
        fr=f"`{TOKEN_SUIVANT}` est absent : le lab n'a pas préparé la valeur "
           "suivante. Rejouez `dsoxlab run`.",
    )
    attendue = suivante.content_string

    monte = host.file(TOKEN).content_string
    assert monte == attendue, message(
        en="the file the secret mounts does not carry the next value. The "
           "brief asks for that value to be put in service; the secret stays "
           "declared on the same file.",
        fr="le fichier monté par le secret ne porte pas la valeur suivante. "
           "L'énoncé demande de mettre cette valeur en service ; le secret "
           "reste déclaré sur le même fichier.",
    )

    _fingerprint(host, services["app"], hashlib.sha256(attendue.encode()).hexdigest())

    # LE CONTENEUR EST-IL PLUS JEUNE QUE LE FICHIER ? C'est ce qui distingue un
    # service qui a RELU d'un service qui tourne encore sur l'ancienne valeur.
    cree = host.run("docker inspect -f {{.Created}} %s", services["app"]["Id"])
    assert cree.rc == 0, message(
        en="Cannot read the consumer's creation date.",
        fr="Impossible de lire la date de création du consommateur.",
    )
    horodatages = host.run(
        "date -u -d %s +%%s; stat -c %%Y %s", cree.stdout.strip(), TOKEN)
    valeurs = horodatages.stdout.split()
    assert horodatages.rc == 0 and len(valeurs) == 2, message(
        en="Cannot compare the consumer's age with the secret file's.",
        fr="Impossible de comparer l'âge du consommateur à celui du fichier.",
    )
    ne_le, modifie_le = int(valeurs[0]), int(valeurs[1])
    assert ne_le >= modifie_le, message(
        en="the consumer is OLDER than the secret file: it is still running on "
           "the value read at its own start.\n"
           "Compose does not restart a consumer when a mounted file changes, "
           "and rewriting the file in place changes nothing for a container "
           "already running. The consumer has to be recreated.",
        fr="le consommateur est plus VIEUX que le fichier du secret : il tourne "
           "encore sur la valeur lue à son propre démarrage.\n"
           "Compose ne redémarre pas un consommateur quand un fichier monté "
           "change, et réécrire le fichier en place ne change rien pour un "
           "conteneur déjà lancé. Il faut recréer le consommateur.",
    )
