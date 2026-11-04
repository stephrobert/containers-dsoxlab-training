"""Une racine en lecture seule, un espace runtime borné, et le service vivant.

Pourquoi trois contrôles, et pourquoi ils ne lisent plus la déclaration
----------------------------------------------------------------------

Le fichier précédent portait **un** `def test_` et huit assertions enchaînées.
Au masquage habituel s'ajoutait un défaut plus grave, et c'est un FAUX ROUGE :
il refusait un travail juste.

IL LISAIT `HostConfig.Tmpfs`, c'est-à-dire la déclaration faite au démon. Or
Compose offre deux écritures pour le même montage, et elles n'alimentent pas le
même champ. Mesuré sur `docker.lab` :

=========================  ==========================  ==========================
                           forme courte ``tmpfs:``     forme longue ``volumes:``
=========================  ==========================  ==========================
``HostConfig.Tmpfs``       ``{"/run": "noexec,..."}``  **null**
``HostConfig.Mounts``      ``null``                    le tmpfs, avec SizeBytes
``df -Pk /run`` dedans     4096 Ko                     4096 Ko
``mount`` dedans           nosuid,nodev,noexec,4096k   nosuid,nodev,noexec,4096k
verdict de l'ancien test   accepté                     **refusé**
=========================  ==========================  ==========================

Dans le conteneur, les deux formes sont **indiscernables**. L'ancien contrôle
refusait donc sur une question d'écriture, pas d'état. Et il y a plus savoureux :
la forme longue obtient `nosuid,nodev,noexec` **sans qu'on les déclare**, Docker
les posant par défaut. Un apprenant qui choisissait cette écriture satisfaisait
les exigences d'options sans les écrire, et se faisait refuser quand même.

LES DEUX CONTRÔLES NE LISENT DONC PLUS QUE LE SYSTÈME, par `mount` et `df` dans
le conteneur :

1. la racine refuse réellement une écriture ;
2. `/run` est un tmpfs borné à 4 Mio, avec `noexec` et `nosuid` appliqués, et le
   service y écrit toujours son heartbeat.

POURQUOI DEUX ET NON TROIS. Le heartbeat a d'abord été écrit comme un contrôle à
part, et le cycle a rendu ROUGE : il PASSE sur l'état initial, puisque le service
tourne et l'actualise dès le départ. C'est une exigence de PRÉSERVATION, pas un
objectif, et un contrôle qui passe avant tout travail accorde des points pour
rien.

Il n'est pas pour autant accessoire : une racine en lecture seule obtenue en
cassant le service remplirait les deux exigences et viderait le lab de son sens.
Le heartbeat prouve que le tmpfs est utilisable PAR LE SERVICE, et non seulement
conforme à une inspection. Il appartient donc au contrôle du tmpfs, dont il est
la dernière preuve.
"""

import json
import time
import uuid

import pytest

from conftest import lab_host, message

LAB = "container-systeme-en-lecture-seule"
PROJET = f"dsoxlab-{LAB}"
RUNTIME = "/run"
TAILLE_KIO = 4096
OPTIONS_EXIGEES = ("noexec", "nosuid")


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _worker(host) -> str:
    """Le conteneur du service, ou un échec qui dit quoi faire.

    Garde-fou de mesure, non exigence : sans un service unique et étiqueté,
    aucun des trois contrôles ne peut observer quoi que ce soit.
    """
    trouve = host.run(
        "docker ps -q --filter label=com.docker.compose.project=%s "
        "--filter label=com.docker.compose.service=worker",
        PROJET,
    )
    ids = trouve.stdout.split()
    assert trouve.rc == 0 and len(ids) == 1, message(
        en=(
            f"Exactly one running `worker` service is required in project "
            f"{PROJET}, found {len(ids)}. Bring the project back up under that "
            "exact name."
        ),
        fr=(
            f"Un seul service `worker` actif est requis dans le projet "
            f"{PROJET}, {len(ids)} trouvé(s). Relancez le projet sous ce nom "
            "exact."
        ),
    )
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the worker: cleanup removes only what carries it.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le worker : le nettoyage ne retire que ce qui le porte.",
    )
    return cid


def test_la_racine_refuse_reellement_une_ecriture(host):
    """Éprouvé par une écriture, et non lu dans `ReadonlyRootfs`.

    Une écriture jetable à la racine doit être refusée, et refusée pour la bonne
    raison : un chemin inexistant ou un droit manquant échoueraient aussi, sans
    rien prouver du montage.
    """
    cid = _worker(host)
    jeton = uuid.uuid4().hex
    chemin = f"/dsoxlab-check-{jeton}"

    essai = host.run("docker exec %s touch %s", cid, chemin)
    try:
        assert essai.rc != 0, message(
            en=(
                f"A write to {chemin} succeeded: the root filesystem is still "
                "writable. The service only needs a runtime space, not its whole "
                "root."
            ),
            fr=(
                f"Une écriture sur {chemin} a réussi : la racine est encore "
                "modifiable. Le service n'a besoin que d'un espace runtime, pas "
                "de toute sa racine."
            ),
        )
        assert "Read-only file system" in essai.stderr, message(
            en=(
                f"The write failed, but not because the filesystem is read-only:\n"
                f"  {essai.stderr.strip()[:200]}\n"
                "Only that refusal proves the mount, and not a missing path or "
                "permission."
            ),
            fr=(
                f"L'écriture a échoué, mais pas parce que le système de fichiers "
                f"est en lecture seule :\n  {essai.stderr.strip()[:200]}\n"
                "Seul ce refus prouve le montage, et non un chemin absent ou un "
                "droit manquant."
            ),
        )
    finally:
        # ON NE RETIRE QUE SA PROPRE SONDE, et seulement si elle a abouti.
        if essai.rc == 0:
            host.run("docker exec %s rm -f %s", cid, chemin)


def test_le_runtime_est_un_tmpfs_borne_avec_ses_options(host):
    """Ce que le conteneur VOIT, et non ce qui a été déclaré au démon.

    C'est ici que l'ancien contrôle produisait un faux rouge. Il lisait
    `HostConfig.Tmpfs`, que la forme longue de Compose n'alimente pas, alors que
    les deux formes donnent le même montage à l'intérieur. `mount` et `df` sont
    indifférents à l'écriture choisie.
    """
    cid = _worker(host)

    monte = host.run("docker exec %s sh -c %s", cid, f"mount | grep ' {RUNTIME} '")
    assert monte.rc == 0 and monte.stdout.strip(), message(
        en=(
            f"{RUNTIME} is not a separate mount inside the container. With a "
            "read-only root, it needs its own writable tmpfs."
        ),
        fr=(
            f"{RUNTIME} n'est pas un montage distinct dans le conteneur. Avec une "
            "racine en lecture seule, il lui faut son propre tmpfs modifiable."
        ),
    )
    ligne = monte.stdout.strip()
    assert "type tmpfs" in ligne, message(
        en=f"{RUNTIME} is mounted but not as a tmpfs:\n  {ligne[:200]}",
        fr=f"{RUNTIME} est monté mais pas en tmpfs :\n  {ligne[:200]}",
    )

    manquantes = [o for o in OPTIONS_EXIGEES if o not in ligne]
    assert not manquantes, message(
        en=(
            f"The {RUNTIME} tmpfs misses {manquantes} among its applied options:\n"
            f"  {ligne[:200]}\n"
            "A writable space that can execute or elevate is no longer a bounded "
            "runtime space."
        ),
        fr=(
            f"Il manque {manquantes} aux options appliquées du tmpfs {RUNTIME} :\n"
            f"  {ligne[:200]}\n"
            "Un espace modifiable qui peut exécuter ou élever n'est plus un "
            "espace runtime borné."
        ),
    )

    taille = host.run("docker exec %s df -Pk %s", cid, RUNTIME)
    assert taille.rc == 0 and taille.stdout.strip(), message(
        en=f"Cannot read the size of {RUNTIME}: {taille.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"La taille de {RUNTIME} est illisible : {taille.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    kio = int(taille.stdout.splitlines()[-1].split()[1])
    assert kio == TAILLE_KIO, message(
        en=(
            f"{RUNTIME} holds {kio} kiB instead of {TAILLE_KIO}. Unbounded, a "
            "tmpfs takes its share from the host's memory."
        ),
        fr=(
            f"{RUNTIME} porte {kio} kio au lieu de {TAILLE_KIO}. Non borné, un "
            "tmpfs prend sa part sur la mémoire de l'hôte."
        ),
    )
    # LE SERVICE ÉCRIT-IL ENCORE DANS CE TMPFS ? C'est la dernière preuve de ce
    # contrôle, et non un contrôle à part : le heartbeat passe sur l'état
    # initial, donc il ne peut rien noter seul. Il refuse en revanche un
    # durcissement obtenu en cassant le service.
    jeton = uuid.uuid4().hex
    sonde = f"{RUNTIME}/dsoxlab-check-{jeton}"

    try:
        ecriture = host.run("docker exec %s touch %s", cid, sonde)
        assert ecriture.rc == 0, message(
            en=(
                f"{RUNTIME} is not usable: {ecriture.stderr.strip()[:160]}\n"
                "The service writes its heartbeat there every second; a space it "
                "cannot write to stops it."
            ),
            fr=(
                f"{RUNTIME} n'est pas utilisable : {ecriture.stderr.strip()[:160]}\n"
                "Le service y écrit son heartbeat chaque seconde ; un espace où "
                "il ne peut pas écrire l'arrête."
            ),
        )

        lu = host.run("docker exec %s cat %s/heartbeat", cid, RUNTIME)
        assert lu.rc == 0 and lu.stdout.strip().isdigit(), message(
            en=(
                f"No readable heartbeat in {RUNTIME}: "
                f"{(lu.stderr or lu.stdout).strip()[:160]}\n"
                "The service must keep running through the hardening."
            ),
            fr=(
                f"Aucun heartbeat lisible dans {RUNTIME} : "
                f"{(lu.stderr or lu.stdout).strip()[:160]}\n"
                "Le service doit continuer de tourner malgré le durcissement."
            ),
        )
        depart = int(lu.stdout.strip())

        # ON ATTEND QU IL AVANCE, et on ne se contente pas de sa présence : un
        # fichier figé prouverait seulement qu'il a existé.
        avance = depart
        for _ in range(4):
            time.sleep(1)
            relu = host.run("docker exec %s cat %s/heartbeat", cid, RUNTIME)
            if relu.rc == 0 and relu.stdout.strip().isdigit():
                avance = int(relu.stdout.strip())
                if avance > depart:
                    break
        assert avance > depart, message(
            en=(
                f"The heartbeat stays at {depart} after four seconds: the service "
                "is no longer updating it. A frozen file only proves it once "
                "existed."
            ),
            fr=(
                f"Le heartbeat reste à {depart} après quatre secondes : le "
                "service ne l'actualise plus. Un fichier figé prouve seulement "
                "qu'il a existé."
            ),
        )
    finally:
        host.run("docker exec %s rm -f %s", cid, sonde)
