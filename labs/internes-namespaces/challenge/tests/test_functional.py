"""Tests fonctionnels du lab internes-namespaces : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un namespace est une VUE, pas une barrière. Le PID 1
d'un conteneur est un processus ordinaire de l'hôte, sous un autre PID, avec sa
ligne de commande lisible. Rien n'est caché à l'hôte : seul le conteneur a une
vue restreinte.

LA LEÇON DE SÉCURITÉ, mesurée sur docker.lab le 2026-10-30. Docker isole six
namespaces et pas le septième :

| namespace | isolé du conteneur |
| pid, net, mnt, uts, ipc, cgroup | oui |
| **user** | **non, partagé avec l'hôte** |

`user:[4026531837]` est identique de part et d'autre. Conséquence : root dans le
conteneur est root sur l'hôte. Ce n'est pas une faille, c'est le réglage par
défaut, et c'est ce qui rend tant d'autres précautions nécessaires. Le troisième
contrôle fait trouver ce namespace, parce qu'on ne se méfie bien que de ce qu'on
a constaté soi-même.

AUCUNE VALEUR N'EST ÉCRITE DANS CE FICHIER. Le PID est demandé au moteur, les
identifiants de namespace sont lus dans `/proc`, et le namespace partagé est
trouvé par COMPARAISON, pas par une liste écrite d'avance. Le jour où Docker
activera l'isolation des utilisateurs par défaut, le troisième contrôle suivra
au lieu de devenir faux.

LE QUATRIÈME CONTRÔLE DEMANDE UN GESTE, et il regarde l'effet plutôt que
l'option : un conteneur doit VOIR le processus de son voisin. Lire
`.HostConfig.PidMode` serait plus simple et noterait l'intention ; vérifier
qu'il le voit note le résultat, et accepte tout chemin qui y mène.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
indispensable ici, puisque les contrôles lisent `/proc/<pid>/ns/`, dont les
liens ne sont résolvables que par root.
"""

from __future__ import annotations

import re

import pytest

from conftest import lab_host, message

CONTENEUR = "cloisonne"
INDISCRET = "indiscret"
MARQUEUR = "987654"
ATELIER = "/opt/lab-namespaces"
REPONSES = f"{ATELIER}/reponses.txt"

# Les sept namespaces qu'un processus porte sous Linux. La liste sert à les
# COMPARER, jamais à écrire d'avance lequel est partagé : c'est la mesure qui
# le dit.
NAMESPACES = ("pid", "net", "mnt", "uts", "ipc", "user", "cgroup")

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui
    les lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier.
    """
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def pid_hote(host) -> str:
    """Le PID que le processus du conteneur porte sur l'hôte.

    Demandé au moteur, qui le connaît : c'est la source la plus directe, et
    elle évite de dépendre de la façon dont `ps` est appelé.
    """
    res = host.run(
        "docker container inspect %s --format %s", CONTENEUR, "{{.State.Pid}}"
    )
    pid = res.stdout.strip()
    if res.rc != 0 or not pid or pid == "0":
        pytest.fail(message(
            en=f"container `{CONTENEUR}` has no process on the host: it is not "
               "running. Replay the lab with `dsoxlab reset`.",
            fr=f"le conteneur `{CONTENEUR}` n'a aucun processus sur l'hôte : il "
               "ne tourne pas. Rejouez le lab avec `dsoxlab reset`.",
        ))
    return pid


def _lire_reponses(host) -> dict[str, str]:
    """Le formulaire, réduit à ses paires clé=valeur.

    Tolérant sur la forme (espaces, lignes vides, commentaires, casse de la
    clé), strict sur le fond : c'est le contenu qui est noté, pas la mise en
    page.
    """
    f = host.file(REPONSES)
    if not f.exists:
        pytest.fail(message(
            en=f"{REPONSES} is missing. The mission asks for three lines in "
               "it: pid_hote=, ns_pid= and partage=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire trois "
               "lignes : pid_hote=, ns_pid= et partage=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def _namespace(host, pid: str, nom: str) -> str:
    """L'identifiant d'un namespace d'un processus, de la forme `pid:[1234]`."""
    res = host.run("readlink /proc/%s/ns/%s", pid, nom)
    return res.stdout.strip() if res.rc == 0 else ""


def test_la_reponse_nomme_le_pid_du_processus_sur_l_hote(host, pid_hote) -> None:
    """Le même processus, deux PID : c'est toute la définition d'un namespace.

    Le conteneur le voit en 1, l'hôte en plusieurs milliers. Rien n'a été
    dupliqué : c'est une numérotation différente du même objet, et c'est
    pourquoi un namespace ne protège pas l'hôte du conteneur.
    """
    annonce = _lire_reponses(host).get("pid_hote", "")
    assert annonce, message(
        en="the `pid_hote=` line is empty. The container's main process is PID "
           "1 inside, and it also has a PID on the host, because it is one of "
           "its processes.",
        fr="la ligne `pid_hote=` est vide. Le processus principal du conteneur "
           "est le PID 1 à l'intérieur, et il porte aussi un PID sur l'hôte, "
           "puisqu'il est un de ses processus.",
    )
    assert annonce == pid_hote, message(
        en=f"the announced PID is not the one the process carries on the host.\n"
           f"  you wrote : {annonce}\n"
           "A PID is reassigned at each start: a value from a previous pass is "
           "no longer valid. The engine knows this PID, and so does the host's "
           "process list, where the container's command line appears as it is.",
        fr=f"le PID annoncé n'est pas celui que le processus porte sur l'hôte.\n"
           f"  vous avez écrit : {annonce}\n"
           "Un PID est réattribué à chaque démarrage : une valeur relevée lors "
           "d'un passage précédent n'est plus valable. Le moteur connaît ce "
           "PID, et la liste des processus de l'hôte aussi, où la ligne de "
           "commande du conteneur apparaît telle quelle.",
    )


def test_la_reponse_nomme_le_namespace_pid_du_conteneur(host, pid_hote) -> None:
    """L'identifiant du namespace, qui prouve qu'on est allé le lire.

    Un namespace n'a pas de nom : il a un numéro d'inode, que le noyau expose
    par un lien dans `/proc`. Le donner suppose d'avoir trouvé où ils vivent,
    ce qui est le préalable de toute enquête sur l'isolation.
    """
    attendu = _namespace(host, pid_hote, "pid")
    if not attendu:
        pytest.skip(message(
            en=f"cannot read /proc/{pid_hote}/ns/pid: the setup did not finish",
            fr=f"/proc/{pid_hote}/ns/pid est illisible : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("ns_pid", "")
    assert annonce, message(
        en="the `ns_pid=` line is empty. A namespace has no name, it has an "
           "inode number, which the kernel exposes through a link in /proc.",
        fr="la ligne `ns_pid=` est vide. Un namespace n'a pas de nom, il a un "
           "numéro d'inode, que le noyau expose par un lien dans /proc.",
    )
    # La forme `pid:[4026532423]` est attendue, mais le numéro seul est
    # accepté : c'est lui qui identifie le namespace, et refuser la mise en
    # forme n'enseignerait rien.
    chiffres_attendus = re.findall(r"\d+", attendu)
    chiffres_annonces = re.findall(r"\d+", annonce)
    assert chiffres_annonces == chiffres_attendus, message(
        en=f"the announced PID namespace is not `{CONTENEUR}`'s.\n"
           f"  you wrote : {annonce}\n"
           "It is read on the container's process, not on the host's: the "
           "host's would be the one this namespace is isolated FROM.",
        fr=f"le namespace PID annoncé n'est pas celui de `{CONTENEUR}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "Il se lit sur le processus du conteneur, pas sur celui de l'hôte : "
           "celui de l'hôte serait celui DONT ce namespace est isolé.",
    )


def test_la_reponse_nomme_le_namespace_partage_avec_l_hote(host, pid_hote) -> None:
    """Le namespace que Docker n'isole pas, et qui change tout.

    Il est trouvé par COMPARAISON, jamais par une liste écrite d'avance : le
    jour où l'isolation des utilisateurs sera active par défaut, ce contrôle
    suivra au lieu de devenir faux.

    C'est la leçon de sécurité du lab : root dans un conteneur est root sur
    l'hôte, et on ne se méfie bien que de ce qu'on a constaté soi-même.
    """
    partages = [
        nom for nom in NAMESPACES
        if _namespace(host, pid_hote, nom)
        and _namespace(host, pid_hote, nom) == _namespace(host, "1", nom)
    ]
    if not partages:
        pytest.skip(message(
            en="the container shares no namespace with the host: this engine "
               "isolates more than the one the lab was written on, and the "
               "question has no answer any more",
            fr="le conteneur ne partage aucun namespace avec l'hôte : ce moteur "
               "isole plus que celui sur lequel le lab a été écrit, et la "
               "question n'a plus de réponse",
        ))

    annonce = _lire_reponses(host).get("partage", "").lower()
    assert annonce, message(
        en="the `partage=` line is empty. Compare the container's namespaces "
           "with those of the host's process 1: one of the seven is identical "
           "on both sides.",
        fr="la ligne `partage=` est vide. Comparez les namespaces du conteneur "
           "à ceux du processus 1 de l'hôte : l'un des sept est identique des "
           "deux côtés.",
    )
    propre = annonce.replace("namespace", "").strip(" :[]")
    assert propre in partages, message(
        en=f"`{annonce}` is not the namespace shared with the host.\n"
           f"  shared: {', '.join(partages)}\n"
           "The answer is a name among the seven, and it is found by comparing "
           "the two sides, not by guessing. The one that is shared is also the "
           "one that explains why root in a container is a security subject.",
        fr=f"`{annonce}` n'est pas le namespace partagé avec l'hôte.\n"
           f"  partagé : {', '.join(partages)}\n"
           "La réponse est un nom parmi les sept, et elle se trouve en "
           "comparant les deux côtés, pas en devinant. Celui qui est partagé "
           "est aussi celui qui explique pourquoi root dans un conteneur est un "
           "sujet de sécurité.",
    )


def test_un_conteneur_voit_les_processus_de_l_hote(host, pid_hote) -> None:
    """Un conteneur peut renoncer à son namespace PID, et tout voir.

    Le contrôle regarde l'EFFET et non l'option : le conteneur doit voir le
    processus de son voisin. Lire `.HostConfig.PidMode` serait plus simple et
    noterait l'intention ; vérifier qu'il le voit note le résultat, et accepte
    tout chemin qui y mène.

    Et il vérifie le PID sous lequel il le voit : celui de l'HÔTE. C'est ce qui
    distingue « il voit les processus de l'hôte » de « il voit ses propres
    processus », que rien d'autre ne séparerait.
    """
    res = host.run(
        "docker container inspect %s --format %s", INDISCRET, "{{.State.Status}}"
    )
    assert res.rc == 0, message(
        en=f"no container named `{INDISCRET}` exists. It has to be launched "
           "with the host's view of processes, so that it sees its neighbour's "
           f"`sleep {MARQUEUR}`.",
        fr=f"aucun conteneur nommé `{INDISCRET}` n'existe. Il faut le lancer "
           "avec la vue des processus de l'hôte, pour qu'il voie le "
           f"`sleep {MARQUEUR}` de son voisin.",
    )
    assert res.stdout.strip() == "running", message(
        en=f"`{INDISCRET}` is in state `{res.stdout.strip()}`, not `running`: a "
           "stopped container sees nothing.",
        fr=f"`{INDISCRET}` est dans l'état `{res.stdout.strip()}`, pas "
           "`running` : un conteneur arrêté ne voit rien.",
    )

    vu = host.run("docker exec %s sh -c %s", INDISCRET, "ps -o pid,args")
    lignes = [
        ligne for ligne in vu.stdout.splitlines()
        if MARQUEUR in ligne and "grep" not in ligne
    ]
    assert lignes, message(
        en=f"`{INDISCRET}` does not see the `sleep {MARQUEUR}` of "
           f"`{CONTENEUR}`.\n"
           "By default a container has its own view of processes, and sees only "
           "its own. It has to give that up to see the host's.",
        fr=f"`{INDISCRET}` ne voit pas le `sleep {MARQUEUR}` de "
           f"`{CONTENEUR}`.\n"
           "Par défaut un conteneur a sa propre vue des processus, et ne voit "
           "que les siens. Il faut y renoncer pour voir ceux de l'hôte.",
    )
    assert any(pid_hote in ligne.split()[:1] for ligne in lignes), message(
        en=f"`{INDISCRET}` sees a `sleep {MARQUEUR}`, but not under the host's "
           f"PID ({pid_hote}).\n"
           f"  seen: {lignes[0].strip()[:80]}\n"
           "Seeing it under another PID would mean it is its own process, not "
           "the neighbour's: that is exactly what the two numberings "
           "distinguish.",
        fr=f"`{INDISCRET}` voit un `sleep {MARQUEUR}`, mais pas sous le PID de "
           f"l'hôte ({pid_hote}).\n"
           f"  vu : {lignes[0].strip()[:80]}\n"
           "Le voir sous un autre PID voudrait dire que c'est son propre "
           "processus, et non celui du voisin : c'est précisément ce que les "
           "deux numérotations distinguent.",
    )
