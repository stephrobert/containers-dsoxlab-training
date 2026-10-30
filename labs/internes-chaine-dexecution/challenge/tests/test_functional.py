"""Tests fonctionnels du lab internes-chaine-dexecution : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que le processus d'un conteneur n'est l'enfant d'aucun des
programmes qu'on croit. La chaîne, mesurée sur docker.lab le 2026-10-30 :

    sleep (le processus du conteneur)
      ← containerd-shim-runc-v2  (un par conteneur)
        ← PID 1                  (le gestionnaire de services, PAS le démon)

Le démon et containerd sont deux services distincts, de PID distincts, et
AUCUN des deux n'est le parent du shim.

UNE IDÉE REÇUE QUE LA MESURE A DÉMENTIE, et elle a changé ce fichier. La
première version du quatrième contrôle faisait redémarrer le démon pour
constater que les conteneurs y survivent. Mesuré sur docker.lab le 2026-10-30 :
c'est FAUX par défaut. Sans `live-restore`, le démon arrête ses conteneurs en
partant et les relance, avec un PID neuf et un `StartedAt` neuf.

Le détachement du shim rend la survie POSSIBLE, il ne la produit pas. Un lab ne
peut pas faire constater une chose fausse, donc le contrôle démontre autrement
la même propriété de la chaîne : un shim PAR conteneur, tous détachés du même
parent. Et il ne touche à aucun service, ce qui est une qualité : redémarrer un
service plusieurs fois dans un cycle de validation finit par déclencher la
limite de systemd.

AUCUN PID N'EST ÉCRIT DANS CE FICHIER. Tout est demandé au système au moment de
la notation. Les PID changent à chaque démarrage : il n'y a rien à recopier d'un
passage précédent.

LE RUNTIME EST LU DANS DEUX SOURCES, et c'est volontaire : le moteur déclare un
défaut, et chaque conteneur déclare le sien. Les deux coïncident ici, et ne
coïncideraient pas sur une machine qui en installe plusieurs. Le contrôle
accepte celui du conteneur, qui est le seul vrai.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
nécessaire pour lire la ligne de commande complète des processus du moteur.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

CONTENEUR = "maillon"
SECOND = "maillon-bis"
ATELIER = "/opt/lab-chaine"
REPONSES = f"{ATELIER}/reponses.txt"

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


def _paires(host, chemin: str, quoi: str) -> dict[str, str]:
    """Un fichier `clé=valeur`, réduit à ses paires.

    Tolérant sur la forme (espaces, lignes vides, commentaires, casse de la
    clé), strict sur le fond : c'est le contenu qui est noté, pas la mise en
    page.
    """
    f = host.file(chemin)
    if not f.exists:
        pytest.fail(message(
            en=f"{chemin} is missing: {quoi}",
            fr=f"{chemin} est absent : {quoi}",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def _lire_reponses(host) -> dict[str, str]:
    return _paires(
        host, REPONSES,
        message(
            en="the mission asks for three lines in it: shim=, parent_du_shim= "
               "and runtime=",
            fr="la mission demande d'y écrire trois lignes : shim=, "
               "parent_du_shim= et runtime=",
        ),
    )


def _shim_du_conteneur(host, nom: str = CONTENEUR) -> str:
    """Le PID du shim qui porte ce conteneur, trouvé par son identifiant.

    Par l'identifiant du conteneur et non par le nom du programme : la machine
    peut porter plusieurs shims, et seul celui dont la ligne de commande cite
    cet identifiant est le bon.
    """
    res = host.run("docker container inspect %s --format %s", nom, "{{.Id}}")
    identifiant = res.stdout.strip()
    if res.rc != 0 or not identifiant:
        pytest.fail(message(
            en=f"container `{nom}` does not exist. Replay the lab with "
               "`dsoxlab reset`.",
            fr=f"le conteneur `{nom}` n'existe pas. Rejouez le lab avec "
               "`dsoxlab reset`.",
        ))
    liste = host.run("ps -eo pid,args")
    for ligne in liste.stdout.splitlines():
        if identifiant in ligne and "shim" in ligne:
            return ligne.split()[0]
    return ""


def test_la_reponse_nomme_le_shim_de_ce_conteneur(host) -> None:
    """L'intermédiaire, et il y en a un PAR conteneur.

    Ce n'est pas un détail d'implémentation : c'est ce qui permet à un conteneur
    de vivre sa vie sans que les autres en dépendent, et c'est pour cela que la
    machine en porte autant que de conteneurs.

    Le contrôle accepte le PID du shim, et le trouve par l'identifiant du
    conteneur : répondre le PID d'un shim voisin ne compte pas.
    """
    attendu = _shim_du_conteneur(host)
    if not attendu:
        pytest.skip(message(
            en=f"no shim carries `{CONTENEUR}`: the setup did not finish",
            fr=f"aucun shim ne porte `{CONTENEUR}` : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("shim", "")
    assert annonce, message(
        en="the `shim=` line is empty. Between the engine and your container's "
           "process, an intermediary carries it, and there is one per "
           "container.",
        fr="la ligne `shim=` est vide. Entre le moteur et le processus de votre "
           "conteneur, un intermédiaire le porte, et il y en a un par "
           "conteneur.",
    )
    assert annonce == attendu, message(
        en=f"the announced PID is not the shim of `{CONTENEUR}`.\n"
           f"  you wrote : {annonce}\n"
           "The machine carries as many shims as containers: the right one is "
           "the one whose command line cites this container's identifier. It is "
           "also the parent of the container's process.",
        fr=f"le PID annoncé n'est pas le shim de `{CONTENEUR}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "La machine porte autant de shims que de conteneurs : le bon est "
           "celui dont la ligne de commande cite l'identifiant de ce conteneur. "
           "C'est aussi le parent du processus du conteneur.",
    )


def test_la_reponse_nomme_le_parent_du_shim(host) -> None:
    """La réponse qui surprend, et tout le lab en découle.

    Le parent du shim n'est ni le démon, ni containerd : c'est le gestionnaire
    de services de la machine. Le shim en a été détaché à dessein, et c'est ce
    détachement qui rend les conteneurs indépendants du démon.

    Le contrôle lit le parent réel plutôt que d'attendre une valeur écrite : sur
    une machine réglée autrement, le détachement pourrait aboutir ailleurs, et
    ce lab suivrait au lieu de devenir faux.
    """
    shim = _shim_du_conteneur(host)
    if not shim:
        pytest.skip(message(
            en=f"no shim carries `{CONTENEUR}`: the setup did not finish",
            fr=f"aucun shim ne porte `{CONTENEUR}` : le setup n'a pas abouti",
        ))
    res = host.run("ps -o ppid= -p %s", shim)
    attendu = res.stdout.strip()
    if not attendu:
        pytest.skip(message(
            en=f"the parent of shim {shim} cannot be read",
            fr=f"le parent du shim {shim} est illisible",
        ))

    annonce = _lire_reponses(host).get("parent_du_shim", "")
    assert annonce, message(
        en="the `parent_du_shim=` line is empty. Look at it twice before "
           "concluding you were wrong: the answer is surprising, and it is the "
           "point of the question.",
        fr="la ligne `parent_du_shim=` est vide. Regardez-la deux fois avant de "
           "conclure que vous vous êtes trompé : la réponse surprend, et c'est "
           "le but de la question.",
    )
    assert annonce == attendu, message(
        en=f"the announced PID is not the shim's parent.\n"
           f"  you wrote : {annonce}\n"
           "Neither the daemon nor containerd is its parent. The shim was "
           "detached on purpose, and that detachment is what makes containers "
           "independent of the daemon.",
        fr=f"le PID annoncé n'est pas le parent du shim.\n"
           f"  vous avez écrit : {annonce}\n"
           "Ni le démon ni containerd n'en est le parent. Le shim en a été "
           "détaché à dessein, et ce détachement est ce qui rend les conteneurs "
           "indépendants du démon.",
    )


def test_la_reponse_nomme_le_runtime_employe(host) -> None:
    """Le programme qui crée réellement le conteneur, et il est remplaçable.

    Le moteur ne crée pas les conteneurs lui-même : il délègue à un runtime, et
    ce runtime est un choix. Le savoir est ce qui rend compréhensible qu'on
    puisse en installer un autre, pour isoler plus fort ou pour mesurer
    autrement.

    Le contrôle lit celui que LE CONTENEUR déclare, et non le défaut du moteur :
    sur une machine qui en installe plusieurs, les deux diffèrent, et seul celui
    du conteneur dit la vérité sur ce conteneur.
    """
    res = host.run(
        "docker container inspect %s --format %s", CONTENEUR, "{{.HostConfig.Runtime}}"
    )
    attendu = res.stdout.strip()
    if res.rc != 0 or not attendu:
        pytest.skip(message(
            en=f"`{CONTENEUR}` declares no runtime: the setup did not finish",
            fr=f"`{CONTENEUR}` ne déclare aucun runtime : le setup n'a pas "
               "abouti",
        ))

    annonce = _lire_reponses(host).get("runtime", "").lower()
    assert annonce, message(
        en="the `runtime=` line is empty. The engine does not create containers "
           "itself: it delegates to a runtime, and that runtime is a choice.",
        fr="la ligne `runtime=` est vide. Le moteur ne crée pas les conteneurs "
           "lui-même : il délègue à un runtime, et ce runtime est un choix.",
    )
    assert annonce == attendu.lower(), message(
        en=f"the announced runtime is not the one `{CONTENEUR}` declares.\n"
           f"  you wrote : {annonce}\n"
           "Two sources state it: the engine's default, and the container's "
           "own. On a machine with several installed they differ, and only the "
           "container's tells the truth about this container.",
        fr=f"le runtime annoncé n'est pas celui que déclare `{CONTENEUR}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "Deux sources l'indiquent : le défaut du moteur, et celui du "
           "conteneur. Sur une machine qui en installe plusieurs, les deux "
           "diffèrent, et seul celui du conteneur dit la vérité sur ce "
           "conteneur.",
    )


def test_chaque_conteneur_a_son_propre_shim(host) -> None:
    """Un intermédiaire PAR conteneur, et non un pour tous.

    Ce n'est pas un détail d'implémentation : c'est ce qui permet à un conteneur
    de vivre sa vie sans que les autres en dépendent. Un shim unique ferait de
    sa chute la chute de tous.

    Trois faits en un contrôle, parce qu'ils ne se séparent pas : le second
    conteneur existe, son shim est DIFFÉRENT du premier, et les deux shims ont
    le MÊME parent. Sans le troisième, deux shims distincts pourraient venir de
    deux chaînes différentes, et la démonstration serait incomplète.

    POURQUOI CE GESTE ET PAS UN REDÉMARRAGE DU DÉMON. La première version de ce
    lab faisait redémarrer le démon pour constater que les conteneurs y
    survivent. Mesuré sur docker.lab le 2026-10-30 : c'est faux par défaut, sans
    `live-restore` le conteneur est relancé avec un PID neuf. Le détachement du
    shim rend la survie POSSIBLE, il ne la produit pas, et le lab ne peut pas
    faire constater une chose fausse.
    """
    premier = _shim_du_conteneur(host)
    if not premier:
        pytest.skip(message(
            en=f"no shim carries `{CONTENEUR}`: the setup did not finish",
            fr=f"aucun shim ne porte `{CONTENEUR}` : le setup n'a pas abouti",
        ))

    etat = host.run(
        "docker container inspect %s --format %s", SECOND, "{{.State.Status}}"
    )
    assert etat.rc == 0, message(
        en=f"no container named `{SECOND}` exists. A second one has to be "
           "started, to check that the intermediary is per container and not "
           "shared.",
        fr=f"aucun conteneur nommé `{SECOND}` n'existe. Il faut en lancer un "
           "second, pour vérifier que l'intermédiaire est par conteneur et non "
           "partagé.",
    )
    assert etat.stdout.strip() == "running", message(
        en=f"`{SECOND}` is in state `{etat.stdout.strip()}`, not `running`: a "
           "stopped container has no shim any more.",
        fr=f"`{SECOND}` est dans l'état `{etat.stdout.strip()}`, pas "
           "`running` : un conteneur arrêté n'a plus de shim.",
    )

    second = _shim_du_conteneur(host, SECOND)
    assert second, message(
        en=f"no shim carries `{SECOND}`, although it is running.",
        fr=f"aucun shim ne porte `{SECOND}`, alors qu'il tourne.",
    )
    assert second != premier, message(
        en=f"`{SECOND}` and `{CONTENEUR}` share the same shim ({premier}).\n"
           "There is one per container, and that is what lets a container live "
           "its own life: a single shim would make its fall everyone's fall.",
        fr=f"`{SECOND}` et `{CONTENEUR}` partagent le même shim ({premier}).\n"
           "Il y en a un par conteneur, et c'est ce qui permet à un conteneur de "
           "vivre sa vie : un shim unique ferait de sa chute la chute de tous.",
    )

    parents = {}
    for nom, shim in ((CONTENEUR, premier), (SECOND, second)):
        res = host.run("ps -o ppid= -p %s", shim)
        parents[nom] = res.stdout.strip()
    assert parents[CONTENEUR] and parents[CONTENEUR] == parents[SECOND], message(
        en=f"the two shims do not have the same parent.\n"
           f"  {CONTENEUR} : {parents[CONTENEUR] or '?'}\n"
           f"  {SECOND} : {parents[SECOND] or '?'}\n"
           "Both are detached towards the same place, and that is what makes "
           "them independent of the engine that created them.",
        fr=f"les deux shims n'ont pas le même parent.\n"
           f"  {CONTENEUR} : {parents[CONTENEUR] or '?'}\n"
           f"  {SECOND} : {parents[SECOND] or '?'}\n"
           "Les deux sont détachés vers le même endroit, et c'est ce qui les "
           "rend indépendants du moteur qui les a créés.",
    )
