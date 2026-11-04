"""Un secret fourni au runtime, consommé, et qui ne fuit nulle part.

Pourquoi trois contrôles là où il n'y en avait qu'un
---------------------------------------------------

Le fichier précédent portait **un** `def test_` et neuf assertions enchaînées.
Il mesurait beaucoup, et bien : jusqu'à un scanner qui cherche la valeur du
secret dans l'inspection, les journaux, l'image, son historique et tous les
fichiers de configuration du répertoire de travail. Ce scanner est le cœur du
sujet, et il est conservé tel quel.

LE MASQUAGE. La première assertion qui tombait masquait les huit suivantes, et
son message tenait en trois mots, « Un service actif requis ».

Les trois contrôles mesurent trois choses indépendantes :

1. le secret est **fourni par un montage** en lecture seule, et il **ne fuit
   nulle part** ;
2. l'application l'a **consommé**, prouvé par l'empreinte qu'elle écrit ;
3. une écriture réelle depuis le conteneur est **refusée**, sans modifier la
   source.

POURQUOI LE SCANNER VIT DANS LE PREMIER, et non à part. Il PASSE sur l'état
initial : rien n'est monté, donc rien n'a fui. Un contrôle qui passe avant tout
travail accorde des points pour rien.

Il n'est pas accessoire pour autant, et c'est même l'énoncé du lab : « fournir un
secret sans le publier ». Fournir et ne pas publier sont les deux faces d'une
même exigence, et les séparer rendrait la seconde mesurable à vide. Un apprenant
qui collerait le jeton dans une variable d'environnement en plus du montage
satisfait le montage et échoue ici, dans le même contrôle.

C'est la huitième fois aujourd'hui que ce cas se présente dans ce catalogue, et
la règle est établie : ce qui est vrai avant tout travail ne peut pas être un
contrôle, et appartient à celui dont il conditionne le sens.
"""

from __future__ import annotations

import json
import time

import pytest

from conftest import lab_host, message

LAB = "secrets-au-runtime"
PROJET = f"dsoxlab-{LAB}"
WORK = f"/opt/dsoxlab-{LAB}"
SOURCE = f"{WORK}/secrets/token"
DESTINATION = "/run/secrets/token"
BASE = (
    "alpine:3.24.3@sha256:"
    "be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a"
)

# LE SCANNER EST REPRIS MOT POUR MOT de la version précédente, et il est le cœur
# du sujet. Il tourne SUR LA VM, parce qu'il doit lire la valeur du secret pour
# la chercher ailleurs : elle ne traverse donc jamais la liaison de test, et
# aucun message d'assertion ne peut la rendre.
SCANNER = r"""
import json, pathlib, subprocess, sys
root = pathlib.Path(sys.argv[2])
secret = (root / "secrets/token").read_bytes().strip()
def docker(*args):
    result = subprocess.run(["docker", *args], capture_output=True, check=True, timeout=5)
    return result.stdout + result.stderr
info_bytes = docker("inspect", sys.argv[1])
info = json.loads(info_bytes)[0]
payloads = [info_bytes, docker("logs", sys.argv[1]),
            docker("image", "inspect", info["Image"]),
            docker("history", "--no-trunc", info["Image"])]
for path in root.rglob("*"):
    if path.is_file() and (path.suffix in (".yaml", ".yml", ".env") or path.name in ("Dockerfile", ".env")):
        payloads.append(path.read_bytes())
safe = len(secret) == 48 and info["Config"]["Labels"].get("dsoxlab.lab") == "secrets-au-runtime"
base = json.loads(docker("image", "inspect", sys.argv[3]))[0]
safe = safe and info["Image"] == base["Id"]
safe = safe and all(secret not in payload for payload in payloads)
print("safe" if safe else "leaked-or-invalid")
"""


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _worker(host) -> str:
    """Le conteneur du service, ou un échec qui dit quoi faire."""
    trouve = host.run(
        "docker ps -q --filter label=com.docker.compose.project=%s "
        "--filter label=com.docker.compose.service=worker",
        PROJET,
    )
    ids = trouve.stdout.split()
    assert trouve.rc == 0 and len(ids) == 1, message(
        en=f"Exactly one running `worker` service is required in project "
           f"{PROJET}, found {len(ids)}. Bring the project back up under that "
           "exact name before providing the secret.",
        fr=f"Un seul service `worker` actif est requis dans le projet {PROJET}, "
           f"{len(ids)} trouvé(s). Relancez le projet sous ce nom exact avant de "
           "fournir le secret.",
    )
    return ids[0]


def _source_privee(host) -> str:
    """La source reste privée, et son empreinte sert de référence.

    Garde-fou : le mode 0600 est déjà celui du départ, donc il ne note rien.
    Mais l'élargir publierait le secret sur la machine, ce que le scénario
    interdit.

    Seule l'EMPREINTE traverse la liaison de test. La valeur du jeton reste sur
    la VM, et aucun message d'assertion ne peut la rendre.
    """
    mode = host.run("LC_ALL=C stat -c '%%a:%%F' %s", SOURCE)
    assert mode.rc == 0, message(
        en=f"The private source {SOURCE} is unreadable: {mode.stderr.strip()[:200]} "
           "Keep it in place: it is what the mount has to point at.",
        fr=f"La source privée {SOURCE} est illisible : {mode.stderr.strip()[:200]} "
           "Conservez-la en place : c'est elle que le montage doit viser.",
    )
    assert mode.stdout.strip() == "600:regular file", message(
        en=f"The source is {mode.stdout.strip()} instead of 600:regular file. "
           "Widening its mode publishes the secret on the machine, which is what "
           "the exercise forbids.",
        fr=f"La source est en {mode.stdout.strip()} au lieu de 600:regular file. "
           "Élargir son mode publie le secret sur la machine, ce que l'exercice "
           "interdit.",
    )
    empreinte = host.run("sha256sum %s | cut -d ' ' -f 1", SOURCE)
    assert empreinte.rc == 0 and len(empreinte.stdout.strip()) == 64, message(
        en="Cannot compute the expected digest of the source. Not your fault: "
           "the check has nothing to compare against, report it.",
        fr="L'empreinte attendue de la source est incalculable. Ce n'est pas "
           "votre faute : le contrôle n'a rien à comparer, signalez-le.",
    )
    return empreinte.stdout.strip()


def test_le_secret_est_fourni_par_un_montage_et_ne_fuit_nulle_part(host):
    """Les deux faces d'une même exigence : fournir, et ne pas publier."""
    cid = _worker(host)
    _source_privee(host)

    lu = host.run("docker inspect -f '{{json .Mounts}}' %s", cid)
    assert lu.rc == 0, message(
        en=f"Cannot read the worker's mounts: {lu.stderr.strip()[:200]}",
        fr=f"Les montages du worker sont illisibles : {lu.stderr.strip()[:200]}",
    )
    montages = [m for m in json.loads(lu.stdout) if m["Destination"] == DESTINATION]
    assert len(montages) == 1, message(
        en=f"{DESTINATION} carries {len(montages)} mounts instead of one. The "
           "secret is provided as a runtime file, not built into the image nor "
           "passed on the command line.",
        fr=f"{DESTINATION} porte {len(montages)} montages au lieu d'un. Le secret "
           "se fournit comme fichier de runtime, ni construit dans l'image ni "
           "passé en ligne de commande.",
    )
    montage = montages[0]
    assert montage["Type"] == "bind", message(
        en=f"{DESTINATION} is a {montage['Type']} mount instead of a bind: it must "
           "point at the supplied private source.",
        fr=f"{DESTINATION} est un montage {montage['Type']} au lieu d'un bind : il "
           "doit viser la source privée fournie.",
    )
    assert montage["Source"] == SOURCE, message(
        en=f"The mount points at {montage['Source']!r} instead of {SOURCE!r}. A "
           "copy elsewhere would be a second place where the secret lives.",
        fr=f"Le montage vise {montage['Source']!r} au lieu de {SOURCE!r}. Une "
           "copie ailleurs serait un second endroit où le secret réside.",
    )
    assert not montage["RW"], message(
        en="The secret is mounted read-write. Reading it does not call for the "
           "right to change it, and the next check proves the refusal.",
        fr="Le secret est monté en lecture-écriture. Le lire ne demande pas le "
           "droit de le modifier, et le contrôle suivant éprouve ce refus.",
    )

    # LE SCANNER, et c'est ici qu'il appartient : « fournir sans publier » est
    # une seule exigence. Il passe sur l'état initial, où rien n'est monté, donc
    # il ne peut pas noter seul ; mais un apprenant qui collerait le jeton dans
    # une variable d'environnement en plus du montage satisfait tout ce qui
    # précède et échoue ici.
    verdict = host.run("python3 -c %s %s %s %s", SCANNER, cid, WORK, BASE)
    assert verdict.rc == 0 and verdict.stdout.strip() == "safe", message(
        en="The secret's value was found outside its mount, or the supplied "
           "application was replaced. It is searched for in `docker inspect`, the "
           "container logs, the image, its history, and every yaml, env or "
           "Dockerfile of the work directory. Providing a secret must not publish "
           "it.",
        fr="La valeur du secret a été trouvée hors de son montage, ou "
           "l'application fournie a été remplacée. Elle est cherchée dans "
           "`docker inspect`, les journaux du conteneur, l'image, son historique, "
           "et chaque yaml, env ou Dockerfile du répertoire de travail. Fournir "
           "un secret ne doit pas le publier.",
    )


def test_l_application_a_consomme_le_secret(host):
    """Le montage sert-il à quelque chose ?

    L'application fournie écrit l'empreinte SHA-256 du secret dans `/run/result`
    dès qu'il devient lisible, et n'affiche jamais le jeton. Comparer cette
    empreinte à celle de la source prouve que le bon fichier est arrivé au bon
    endroit, sans que la valeur quitte la machine.

    La comparaison se fait DANS le conteneur, avec l'empreinte passée en
    argument : ni le jeton ni son empreinte ne transitent par un message.
    """
    cid = _worker(host)
    attendue = _source_privee(host)

    obtenu = None
    for _ in range(5):
        obtenu = host.run(
            "docker exec %s sh -c 'test \"$(cat /run/result 2>/dev/null)\" = \"$1\"' sh %s",
            cid, attendue,
        )
        if obtenu.rc == 0:
            break
        time.sleep(1)

    assert obtenu is not None and obtenu.rc == 0, message(
        en="The application has not written the expected digest to /run/result. "
           "It writes it as soon as the secret becomes readable at "
           f"{DESTINATION}: an absent digest means the file never arrived, and a "
           "different one means another file arrived.",
        fr="L'application n'a pas écrit l'empreinte attendue dans /run/result. "
           "Elle l'écrit dès que le secret devient lisible sur "
           f"{DESTINATION} : une empreinte absente signifie que le fichier n'est "
           "jamais arrivé, une empreinte différente qu'un autre fichier est "
           "arrivé.",
    )


def test_une_ecriture_reelle_est_refusee_sans_modifier_la_source(host):
    """Le montage en lecture seule tient-il, éprouvé par une écriture ?

    Le contrôle du montage lit `RW` dans l'inspection ; celui-ci essaie. Et il
    vérifie ensuite que la source n'a pas bougé : une écriture qui aurait abouti
    aurait modifié le secret, et l'exercice serait perdu pour tout le monde.

    IL EXIGE LA BONNE RAISON DE L'ÉCHEC, et c'est le cycle qui l'a imposé.
    Sans cette exigence, il PASSAIT sur l'état initial : faute de montage,
    `/run/secrets` n'existe pas, et le shell rend « nonexistent directory »
    avec un code non nul. Un chemin absent échoue comme un refus, et seule
    l'erreur les distingue.
    """
    cid = _worker(host)
    avant = _source_privee(host)

    essai = host.run("docker exec %s sh -c 'printf x >> %s'", cid, DESTINATION)
    assert essai.rc != 0, message(
        en=f"A write to {DESTINATION} succeeded from inside the container: the "
           "mount is not read-only in fact, whatever the inspection says.",
        fr=f"Une écriture sur {DESTINATION} a réussi depuis le conteneur : le "
           "montage n'est pas en lecture seule en fait, quoi qu'en dise "
           "l'inspection.",
    )
    # LA BONNE RAISON DE L ÉCHEC, et sans elle ce contrôle passait sur
    # l'état initial. Mesuré sur la VM, sans montage :
    #
    #     sh: can't create /run/secrets/token: nonexistent directory   rc=1
    #
    # Le contrôle concluait donc au refus alors que rien n'était monté, et
    # le cycle l'a signalé en rendant 1/3 avant le travail.
    #
    # C'est le même défaut que la racine en lecture seule de
    # `container-systeme-en-lecture-seule` : un chemin absent échoue comme
    # un refus, et seule l'erreur distingue les deux.
    trace = (essai.stderr + essai.stdout).lower()
    assert "read-only" in trace, message(
        en=f"The write failed, but not because the mount is read-only: "
           f"{(essai.stderr or essai.stdout).strip()[:200]} A missing path "
           "fails the same way while proving nothing: the secret has to be "
           f"mounted at {DESTINATION} first.",
        fr=f"L'écriture a échoué, mais pas parce que le montage est en "
           f"lecture seule : {(essai.stderr or essai.stdout).strip()[:200]} "
           "Un chemin absent échoue de la même façon sans rien prouver : le "
           f"secret doit d'abord être monté sur {DESTINATION}.",
    )

    apres = _source_privee(host)
    assert apres == avant, message(
        en="The source digest changed after the probe: the secret was modified. "
           "Not your fault if the write was refused; report it.",
        fr="L'empreinte de la source a changé après la sonde : le secret a été "
           "modifié. Ce n'est pas votre faute si l'écriture a été refusée ; "
           "signalez-le.",
    )
