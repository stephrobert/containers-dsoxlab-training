"""Tests fonctionnels du lab troubleshoot-conflit-de-port : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que deux conflits de port qui se ressemblent n'ont pas la
même cause, et que les outils Docker sont AVEUGLES à l'une des deux.

MESURÉ SUR docker.lab LE 2026-10-30, et ces deux messages sont le lab :

| Coupable | Message du moteur | `docker ps` le voit | `ss` le voit |
| un conteneur | « port is already allocated » | **oui** | oui, `docker-proxy` |
| un processus de l'hôte | « Error starting userland proxy: listen » | **non** | oui, le programme |

Les deux messages diffèrent, et c'est la clé. Le premier vient du MOTEUR, qui
sait ce qu'il a déjà réservé ; le second vient du SYSTÈME, qui refuse l'écoute.
Un dépanneur qui lit cette différence sait immédiatement s'il doit chercher dans
Docker ou en dehors.

UN TROISIÈME FAIT, QUI SURPREND : le conteneur refusé est CRÉÉ quand même. Son
statut reste `created`, et il occupe donc son nom. C'est pourquoi un second essai
échoue sur « name already in use » et fait croire à une autre panne : deux
messages différents pour une seule cause, et on cherche deux problèmes.

AUCUNE VALEUR N'EST ÉCRITE EN DUR DANS CE FICHIER. Le statut est lu sur le
conteneur, le nom du conteneur coupable est demandé au moteur, et le nom du
programme de l'hôte est lu dans la table des sockets au moment de la notation.

LE QUATRIÈME CONTRÔLE IMPOSE LE BON RÉFLEXE, et c'est une correction venue du
cycle de validation. Une première version demandait de rendre aux intrus le port
qu'ils réclamaient, donc de libérer celui du coupable : à la notation, le
coupable du port n'était alors plus `occupant` mais l'intrus lui-même, et les
réponses des contrôles 2 et 3 devenaient fausses. Le lab se contredisait.

La correction n'est pas technique, elle est pédagogique. Libérer le port est le
geste spontané et le mauvais : on ne coupe pas un service qui tourne pour en
démarrer un autre. Le contrôle exige donc que les intrus tournent sur un AUTRE
port, et que les deux coupables soient TOUJOURS LÀ.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
indispensable ici, car `ss` ne nomme le processus derrière un socket que pour
root.
"""

from __future__ import annotations

import re

import pytest

from conftest import lab_host, message

OCCUPANT = "occupant"
INTRUS_CONTENEUR = "intrus-a"
INTRUS_HOTE = "intrus-b"
# LE TÉMOIN reste en échec du début à la fin : c'est sur lui que se lit
# le statut, parce qu'une valeur de diagnostic ne peut pas se lire sur un
# objet que la réparation modifie.
TEMOIN = "temoin-refuse"
PORT_CONTENEUR = 18200
PORT_HOTE = 18201
ATELIER = "/opt/lab-conflit"
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


def _champ(host, nom: str, format_go: str) -> str:
    """Un champ de l'inspection d'un conteneur, ou une chaîne vide."""
    res = host.run("docker container inspect %s --format %s", nom, format_go)
    return res.stdout.strip() if res.rc == 0 else ""


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
               "it: statut_intrus=, coupable_a= and coupable_b=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire trois "
               "lignes : statut_intrus=, coupable_a= et coupable_b=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def test_la_reponse_donne_le_statut_du_conteneur_refuse(host) -> None:
    """Le conteneur refusé existe quand même, et il occupe son nom.

    C'est le fait qui fait chercher deux problèmes là où il n'y en a qu'un : le
    second essai échoue sur un message tout différent, qui parle de nom déjà
    pris, et on croit avoir cassé autre chose entre-temps.

    Le statut le dit en un mot, et il n'est pas celui d'un conteneur qui s'est
    arrêté.
    """
    attendu = _champ(host, TEMOIN, "{{.State.Status}}")
    if not attendu:
        pytest.skip(message(
            en=f"container `{TEMOIN}` does not exist: the setup did not finish",
            fr=f"le conteneur `{TEMOIN}` n'existe pas : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("statut_intrus", "").lower()
    assert annonce, message(
        en=f"the `statut_intrus=` line is empty. `{TEMOIN}` refused to start, "
           "and it exists all the same: read its status.",
        fr=f"la ligne `statut_intrus=` est vide. `{TEMOIN}` a refusé de "
           "démarrer, et il existe tout de même : lisez son statut.",
    )
    assert annonce == attendu.lower(), message(
        en=f"the announced status is not `{TEMOIN}`'s.\n"
           f"  you wrote : {annonce}\n"
           "A refused container is created all the same, and it occupies its "
           "name. That is why a second attempt fails on a completely different "
           "message, about a name already in use, and makes you look for a "
           "second problem that does not exist.",
        fr=f"le statut annoncé n'est pas celui de `{TEMOIN}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "Un conteneur refusé est créé quand même, et il occupe son nom. "
           "C'est pourquoi un second essai échoue sur un message tout "
           "différent, qui parle de nom déjà pris, et fait chercher un second "
           "problème qui n'existe pas.",
    )


def test_la_reponse_nomme_le_conteneur_coupable(host) -> None:
    """Le coupable que Docker montre, et c'est le cas facile.

    Le message du moteur parle d'un port « déjà alloué » : cette formulation
    dit que c'est LUI qui l'a réservé, donc que le coupable est un de ses
    conteneurs. La liste des conteneurs le nomme aussitôt.

    Le contrôle le demande au moteur plutôt que de l'écrire : si le setup
    changeait de nom, il suivrait.
    """
    res = host.run("docker ps --format %s", "{{.Names}} {{.Ports}}")
    attendu = ""
    for ligne in res.stdout.splitlines():
        if re.search(rf":{PORT_CONTENEUR}\b", ligne):
            attendu = ligne.split()[0]
            break
    if not attendu:
        pytest.skip(message(
            en=f"no running container publishes port {PORT_CONTENEUR}: the "
               "setup did not finish, or the port has been freed",
            fr=f"aucun conteneur en marche ne publie le port "
               f"{PORT_CONTENEUR} : le setup n'a pas abouti, ou le port a été "
               "libéré",
        ))

    annonce = _lire_reponses(host).get("coupable_a", "")
    assert annonce, message(
        en="the `coupable_a=` line is empty. The engine's message says the port "
           "is already allocated: that wording means the engine reserved it "
           "itself, so the culprit is one of its containers.",
        fr="la ligne `coupable_a=` est vide. Le message du moteur dit que le "
           "port est déjà alloué : cette formulation signifie que c'est lui qui "
           "l'a réservé, donc que le coupable est un de ses conteneurs.",
    )
    assert annonce == attendu, message(
        en=f"`{annonce}` is not the container occupying port "
           f"{PORT_CONTENEUR}.\n"
           "The list of running containers shows the published ports next to "
           "the names: the culprit is there.",
        fr=f"`{annonce}` n'est pas le conteneur qui occupe le port "
           f"{PORT_CONTENEUR}.\n"
           "La liste des conteneurs en marche montre les ports publiés à côté "
           "des noms : le coupable y est.",
    )


def test_la_reponse_nomme_le_programme_de_l_hote(host) -> None:
    """Le coupable que Docker ne montre pas, et c'est celui qui coûte du temps.

    Le second message ne parle pas d'allocation : il parle d'une écoute
    refusée. Cette formulation vient du système, pas du moteur, et elle dit que
    le coupable est HORS de Docker.

    Mesuré : `docker ps` ne rend rien du tout dans ce cas, là où la table des
    sockets nomme le programme en une ligne. Un dépanneur qui ne connaît que
    les outils Docker tourne alors en rond.
    """
    res = host.run("ss -ltnp")
    attendu = ""
    for ligne in res.stdout.splitlines():
        if re.search(rf":{PORT_HOTE}\b", ligne):
            trouve = re.search(r'users:\(\("([^"]+)"', ligne)
            if trouve:
                attendu = trouve.group(1)
                break
    if not attendu:
        pytest.skip(message(
            en=f"no process of the host is listening on port {PORT_HOTE}: the "
               "setup did not finish, or the port has been freed",
            fr=f"aucun processus de l'hôte n'écoute sur le port {PORT_HOTE} : "
               "le setup n'a pas abouti, ou le port a été libéré",
        ))

    annonce = _lire_reponses(host).get("coupable_b", "")
    assert annonce, message(
        en="the `coupable_b=` line is empty. Do not look on Docker's side: it "
           "shows nothing here, and that is precisely what wastes time. A "
           "system tool names the program in one line.",
        fr="la ligne `coupable_b=` est vide. Ne cherchez pas du côté de "
           "Docker : il ne montre rien ici, et c'est précisément ce qui fait "
           "perdre du temps. Un outil système nomme le programme en une ligne.",
    )
    propre = annonce.split("/")[0].split(":")[0].strip()
    assert propre == attendu, message(
        en=f"`{annonce}` is not the program occupying port {PORT_HOTE}.\n"
           "The socket table gives the name of the process behind each "
           "listening port, and it is the only tool that sees this one: the "
           "engine never reserved this port, so it knows nothing about it.",
        fr=f"`{annonce}` n'est pas le programme qui occupe le port "
           f"{PORT_HOTE}.\n"
           "La table des sockets donne le nom du processus derrière chaque port "
           "en écoute, et c'est le seul outil qui voit celui-ci : le moteur n'a "
           "jamais réservé ce port, donc il n'en sait rien.",
    )


def test_les_deux_conteneurs_tournent_sans_couper_les_coupables(host) -> None:
    """La réparation, et le lab impose le bon réflexe plutôt que le réflexe.

    Libérer le port serait le geste spontané, et c'est le mauvais : on ne coupe
    pas un service qui tourne pour en démarrer un autre. Le bon geste
    d'exploitation est de DÉPLACER le nouveau venu, ce qui règle le conflit sans
    rien casser.

    Le contrôle exige donc les deux moitiés : les intrus tournent, et les deux
    coupables sont TOUJOURS LÀ. Sans la seconde, la réponse la plus destructrice
    passerait, et le lab enseignerait exactement ce qu'il faut éviter.

    UNE FAUTE DE CONCEPTION CORRIGÉE ICI, et le cycle de validation l'a
    attrapée. Une première version demandait de rendre aux intrus le port
    qu'ils réclamaient, donc de libérer celui du coupable. À la notation, le
    coupable du port n'était alors plus `occupant` mais l'intrus lui-même, et
    les réponses écrites aux contrôles 2 et 3 devenaient fausses. Le lab se
    contredisait.
    """
    for nom, port_pris in (
        (INTRUS_CONTENEUR, PORT_CONTENEUR),
        (INTRUS_HOTE, PORT_HOTE),
    ):
        etat = _champ(host, nom, "{{.State.Status}}")
        assert etat, message(
            en=f"container `{nom}` does not exist any more. It had to be made "
               "to run, not removed: the lab's names are part of the brief.",
            fr=f"le conteneur `{nom}` n'existe plus. Il fallait le faire "
               "tourner, pas le supprimer : les noms du lab font partie de "
               "l'énoncé.",
        )
        assert etat == "running", message(
            en=f"`{nom}` is in state `{etat}`, not `running`.\n"
               f"Its port {port_pris} was taken by something that is still "
               "needed. Move the newcomer rather than cutting what works.",
            fr=f"`{nom}` est dans l'état `{etat}`, pas `running`.\n"
               f"Son port {port_pris} était pris par quelque chose qui sert "
               "encore. Déplacez le nouveau venu plutôt que de couper ce qui "
               "marche.",
        )

        publications = host.run("docker port %s 80/tcp", nom)
        publies = publications.stdout.strip()
        assert publies, message(
            en=f"`{nom}` runs but publishes nothing. It has to publish its port "
               "80 on a port of the host, just on another one than the taken "
               "one.",
            fr=f"`{nom}` tourne mais ne publie rien. Il doit publier son port "
               "80 sur un port de l'hôte, simplement un autre que celui qui "
               "était pris.",
        )
        assert not re.search(rf":{port_pris}\b", publies), message(
            en=f"`{nom}` publishes on port {port_pris}, the very one that was "
               "taken.\n"
               f"  it publishes: {publies}\n"
               "So the port was freed, which means something was cut. That is "
               "the reflex the lab exists to correct: a taken port is often "
               "taken for a reason.",
            fr=f"`{nom}` publie sur le port {port_pris}, celui-là même qui était "
               "pris.\n"
               f"  il publie : {publies}\n"
               "Le port a donc été libéré, c'est-à-dire que quelque chose a été "
               "coupé. C'est le réflexe que ce lab existe pour corriger : un "
               "port pris l'est souvent pour une raison.",
        )

    # LA SECONDE MOITIÉ, et elle est indissociable : les deux coupables doivent
    # être encore là. Sans elle, tout couper passerait le contrôle.
    occupant_tourne = _champ(host, OCCUPANT, "{{.State.Status}}")
    assert occupant_tourne == "running", message(
        en=f"`{OCCUPANT}` is no longer running (state: "
           f"{occupant_tourne or 'absent'}).\n"
           "It was holding its port, and nothing said it was useless. Solving a "
           "conflict by stopping what was already working is the mistake this "
           "lab exists to correct.",
        fr=f"`{OCCUPANT}` ne tourne plus (état : "
           f"{occupant_tourne or 'absent'}).\n"
           "Il tenait son port, et rien ne disait qu'il était inutile. Résoudre "
           "un conflit en arrêtant ce qui marchait déjà est la faute que ce lab "
           "existe pour corriger.",
    )

    ecoute = host.run("ss -ltn")
    assert re.search(rf":{PORT_HOTE}\b", ecoute.stdout), message(
        en=f"nothing listens on port {PORT_HOTE} any more: the host's program "
           "has been killed.\n"
           "It was outside Docker, and nothing said it was useless either. The "
           "conflict is solved by moving the container, not by killing what it "
           "collided with.",
        fr=f"plus rien n'écoute sur le port {PORT_HOTE} : le programme de l'hôte "
           "a été tué.\n"
           "Il était hors de Docker, et rien ne disait qu'il était inutile non "
           "plus. Le conflit se règle en déplaçant le conteneur, pas en tuant "
           "ce qu'il a rencontré.",
    )
