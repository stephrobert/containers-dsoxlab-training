"""Une barrière de privilèges déclarée, portée par le noyau, et éprouvée.

Pourquoi trois contrôles là où il n'y en avait qu'un
---------------------------------------------------

Le fichier précédent portait **un** `def test_` et sept assertions enchaînées.
Il mesurait les trois bonnes choses, et le défaut était la forme.

LE MASQUAGE. La première assertion qui tombait masquait les six suivantes, et son
message tenait en trois mots : « Un service actif requis ».

LE MÉLANGE DES NATURES. Trois assertions ne sont pas des exigences mais des
garde-fous : qu'un service unique tourne, qu'il porte son label, et que l'image
de la sonde soit l'originale. Les deux dernières sont même des **interdictions**
du scénario, « ne remplacez pas le binaire, ne changez pas son mode », et les
confondre avec les objectifs brouille ce qui est demandé.

Les trois contrôles mesurent trois choses indépendantes :

1. la barrière **déclarée** au runtime ;
2. le drapeau que le **noyau porte** sur PID 1 ;
3. ce que le binaire setuid **ne peut plus obtenir**, éprouvé par une exécution.

1 et 2 ne sont pas redondants : une option acceptée par Docker sans que le noyau
pose le drapeau laisserait l'élévation possible, et c'est `/proc/1/status` qui
tranche. Le troisième ne lit rien, il exécute, et c'est la seule preuve qui ne
dépende d'aucune lecture : un drapeau juste sur le papier n'empêche rien s'il
n'est pas hérité par les processus que l'on lance.
"""

import json

import pytest

from conftest import lab_host, message

LAB = "securite-no-new-privileges"
PROJET = f"dsoxlab-{LAB}"
TRAVAIL = f"/opt/dsoxlab-{LAB}"
BINAIRE = "/usr/local/bin/identity"
MODE_ATTENDU = "0:4755"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _worker(host) -> tuple[str, dict]:
    """Le conteneur du service, ou un échec qui nomme ce qui manque.

    Ce garde-fou mêle deux natures, et les messages les distinguent. Qu'un
    service unique tourne et porte son label conditionne toute observation.
    Que l'image soit l'ORIGINALE et que le binaire garde son mode sont au
    contraire deux interdictions explicites du scénario : les franchir est une
    faute, pas un empêchement de mesurer.
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
            "exact name before adding the barrier."
        ),
        fr=(
            f"Un seul service `worker` actif est requis dans le projet "
            f"{PROJET}, {len(ids)} trouvé(s). Relancez le projet sous ce nom "
            "exact avant de poser la barrière."
        ),
    )
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]

    assert info["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the worker: cleanup removes only what carries it.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le worker : le nettoyage ne retire que ce qui le porte.",
    )

    # L IMAGE D ORIGINE, et c'est une interdiction du scénario : remplacer
    # l'image reviendrait à supprimer le binaire setuid plutôt qu'à empêcher
    # l'élévation. L'empreinte a été posée par le setup en lecture seule.
    depart = host.run("cat %s/.probe-image-id", TRAVAIL)
    assert depart.rc == 0 and depart.stdout.strip(), message(
        en=f"Cannot read {TRAVAIL}/.probe-image-id. Not your fault: the check cannot measure anything, report it.",
        fr=f"{TRAVAIL}/.probe-image-id est illisible. Ce n'est pas votre faute : le contrôle ne peut rien mesurer, signalez-le.",
    )
    assert info["Image"] == depart.stdout.strip(), message(
        en=(
            "The worker no longer runs the original probe image. Replacing it "
            "removes the setuid binary instead of preventing elevation, and the "
            "scenario forbids it."
        ),
        fr=(
            "Le worker ne tourne plus l'image de la sonde d'origine. La "
            "remplacer retire le binaire setuid au lieu d'empêcher l'élévation, "
            "et le scénario l'interdit."
        ),
    )

    # LE BINAIRE GARDE SON MODE, l'autre interdiction. On le lit dans le
    # conteneur : c'est là qu'il s'exécute.
    mode = host.run("docker exec %s stat -c '%%u:%%a' %s", cid, BINAIRE)
    assert mode.rc == 0 and mode.stdout.strip(), message(
        en=f"Cannot read the mode of {BINAIRE} inside the worker: {mode.stderr.strip()}. Keep the binary in place.",
        fr=f"Le mode de {BINAIRE} est illisible dans le worker : {mode.stderr.strip()}. Conservez le binaire en place.",
    )
    assert mode.stdout.strip() == MODE_ATTENDU, message(
        en=(
            f"{BINAIRE} is {mode.stdout.strip()} instead of {MODE_ATTENDU}. "
            "Taking the setuid bit away does stop the elevation, by removing what "
            "the exercise asked you to neutralise rather than to delete."
        ),
        fr=(
            f"{BINAIRE} est en {mode.stdout.strip()} au lieu de "
            f"{MODE_ATTENDU}. Retirer le bit setuid arrête bien l'élévation, en "
            "supprimant ce que l'exercice demandait de neutraliser et non "
            "d'effacer."
        ),
    )
    return cid, info


def test_la_barriere_est_declaree_au_runtime(host):
    """Ce qui a été demandé à Docker."""
    _cid, info = _worker(host)
    options = info["HostConfig"]["SecurityOpt"] or []

    assert any(
        o in ("no-new-privileges", "no-new-privileges:true") for o in options
    ), message(
        en=(
            f"The worker declares no no-new-privileges option.\n"
            f"  SecurityOpt: {options or '[]'}\n"
            "It is a runtime option, set on the service, not a property of the "
            "image."
        ),
        fr=(
            f"Le worker ne déclare aucune option no-new-privileges.\n"
            f"  SecurityOpt : {options or '[]'}\n"
            "C'est une option de runtime, posée sur le service, et non une "
            "propriété de l'image."
        ),
    )


def test_le_noyau_porte_le_drapeau_sur_pid_1(host):
    """Ce que le noyau applique, qui est la seule vérité.

    Une option retenue par Docker sans que le noyau pose le drapeau laisserait
    l'élévation possible. `/proc/1/status` tranche.
    """
    cid, _info = _worker(host)

    lu = host.run("docker exec %s cat /proc/1/status", cid)
    assert lu.rc == 0, message(
        en=f"Cannot read /proc/1/status inside the worker: {lu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"/proc/1/status est illisible dans le worker : {lu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    lignes = [ligne for ligne in lu.stdout.splitlines() if ligne.startswith("NoNewPrivs:")]
    assert lignes, message(
        en="/proc/1/status carries no NoNewPrivs line. Not your fault: the check cannot measure anything, report it.",
        fr="/proc/1/status ne porte aucune ligne NoNewPrivs. Ce n'est pas votre faute : le contrôle ne peut rien mesurer, signalez-le.",
    )
    drapeau = lignes[0].split()[1]
    assert drapeau == "1", message(
        en=(
            f"PID 1 announces NoNewPrivs: {drapeau} instead of 1. The option was "
            "retained by Docker but the kernel does not carry it, and it is the "
            "kernel that refuses the elevation."
        ),
        fr=(
            f"PID 1 annonce NoNewPrivs : {drapeau} au lieu de 1. L'option a été "
            "retenue par Docker mais le noyau ne la porte pas, et c'est le noyau "
            "qui refuse l'élévation."
        ),
    )


def test_le_binaire_setuid_n_eleve_plus_l_euid(host):
    """Ce que le binaire ne peut plus obtenir, éprouvé par une exécution.

    Les deux contrôles précédents lisent ; celui-ci exécute. C'est la seule
    preuve qui ne dépende d'aucune lecture, et c'est elle qui compte : le drapeau
    doit être HÉRITÉ par les processus lancés, pas seulement porté par PID 1.

    Le binaire n'affiche que les UID réel et effectif : ni shell, ni modification
    de fichier. Son exécution est donc sans effet sur l'état du lab.
    """
    cid, _info = _worker(host)

    execute = host.run("docker exec --user 1000:1000 %s %s", cid, BINAIRE)
    assert execute.rc == 0, message(
        en=(
            f"{BINAIRE} could not be run as 1000:1000: {execute.stderr.strip()}\n"
            "The binary must stay executable: the exercise asks you to neutralise "
            "the elevation, not the program."
        ),
        fr=(
            f"{BINAIRE} n'a pas pu être exécuté en 1000:1000 : "
            f"{execute.stderr.strip()}\nLe binaire doit rester exécutable : "
            "l'exercice demande de neutraliser l'élévation, non le programme."
        ),
    )
    rendu = execute.stdout.strip()
    assert rendu == "1000:1000", message(
        en=(
            f"The setuid binary announces {rendu} instead of 1000:1000.\n"
            "A `1000:0` means the effective UID was raised to root: the barrier "
            "is not inherited by the processes the service starts."
        ),
        fr=(
            f"Le binaire setuid annonce {rendu} au lieu de 1000:1000.\n"
            "Un `1000:0` signifie que l'UID effectif est passé à root : la "
            "barrière n'est pas héritée par les processus que le service lance."
        ),
    )
