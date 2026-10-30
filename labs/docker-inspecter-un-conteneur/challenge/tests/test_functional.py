"""Tests fonctionnels du lab docker-inspecter-un-conteneur : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un conteneur en marche s'interroge, et que chaque
question a sa commande : ses journaux, son inspection, sa table des ports, et
la copie d'un fichier qu'il a écrit. Le lab précédent enseignait les états ;
celui-ci enseigne ce qu'on peut en savoir sans les changer.

LE PRINCIPE QUI TIENT TOUT LE FICHIER : LA VÉRITÉ EST RECALCULÉE ICI, au moment
de la notation, en interrogeant le moteur. Aucune réponse attendue n'est écrite
dans ce fichier, ni dans le setup, ni dans l'énoncé : le jeton et la séquence
sont tirés par le conteneur depuis /dev/urandom, l'adresse et le port sont
choisis par le moteur. Un apprenant ne peut donc pas recopier la réponse d'un
passage précédent, parce qu'elle a changé.

C'est aussi ce qui rend ces contrôles honnêtes : ils ne vérifient pas qu'une
commande a été tapée, ils confrontent CE QUE L'APPRENANT AFFIRME à ce que la
machine porte réellement. Un apprenant qui atteint la bonne valeur par un autre
chemin a appris la même chose, et c'est très bien.

POURQUOI LE CONTENEUR DOIT TOURNER À LA FIN. Les quatre contrôles interrogent un
conteneur vivant. Celui qui l'arrête pour le fouiller perd son adresse IP et sa
table des ports, que le moteur ne conserve pas : deux contrôles refusent alors,
et leur message le dit, parce que la cause n'est pas devinable.

CE QU'ON NE MESURE PAS. Jamais la commande. `docker logs` ou la lecture du
fichier journal de l'hôte donnent le même jeton ; `docker port`, `docker
inspect` ou `ss` donnent le même port ; `docker cp` et une redirection de
`docker exec` sortent le même fichier. Les trois chemins comptent.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import re

import pytest

from conftest import lab_host, message

CONTENEUR = "greffier"
ATELIER = "/opt/lab-inspection"
REPONSES = f"{ATELIER}/reponses.txt"
TRACE_SUR_L_HOTE = f"{ATELIER}/trace.log"
TRACE_DANS_LE_CONTENEUR = "/var/log/greffier/trace.log"

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


def _conteneur_tourne(host) -> None:
    """Le préalable des quatre contrôles, dit une fois et clairement.

    Un conteneur arrêté perd son adresse et sa table des ports : le signaler
    explicitement vaut mieux que de laisser deux contrôles refuser sur une
    valeur vide, ce qui ferait chercher la faute dans la réponse écrite.
    """
    res = host.run(
        "docker container inspect %s --format %s", CONTENEUR, "{{.State.Status}}"
    )
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{CONTENEUR}` does not exist any more. All four "
               "checks question a LIVE container: replay the lab with "
               "`dsoxlab reset`.",
            fr=f"le conteneur `{CONTENEUR}` n'existe plus. Les quatre "
               "contrôles interrogent un conteneur VIVANT : rejouez le lab "
               "avec `dsoxlab reset`.",
        ))
    etat = res.stdout.strip()
    if etat != "running":
        pytest.fail(message(
            en=f"container `{CONTENEUR}` is in state `{etat}`, not `running`. "
               "A stopped container no longer has an address or a port table: "
               "you question a running container, you do not stop it to search "
               "it. `docker start` puts it back, but its values have changed.",
            fr=f"le conteneur `{CONTENEUR}` est dans l'état `{etat}`, pas "
               "`running`. Un conteneur arrêté n'a plus d'adresse ni de table "
               "des ports : on interroge un conteneur en marche, on ne "
               "l'arrête pas pour le fouiller. `docker start` le remet en "
               "marche, mais ses valeurs ont changé.",
        ))


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
               "it: jeton=, adresse= and port=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire trois "
               "lignes : jeton=, adresse= et port=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def _attendu(host, cle: str) -> str:
    """Une valeur demandée au moteur, et le refus s'il ne la donne pas.

    Les trois valeurs se lisent de trois façons différentes, et c'est le sujet
    du lab : un motif dans les journaux, un champ de l'inspection, une entrée
    de la table des ports.
    """
    if cle == "jeton":
        res = host.run("docker logs %s", CONTENEUR)
        trouve = re.search(r"jeton-de-session=([0-9a-f]+)", res.stdout + res.stderr)
        return trouve.group(1) if trouve else ""
    if cle == "adresse":
        res = host.run(
            "docker container inspect %s --format %s",
            CONTENEUR, "{{.NetworkSettings.IPAddress}}",
        )
        return res.stdout.strip()
    res = host.run("docker port %s 80/tcp", CONTENEUR)
    # `docker port` rend une ligne par famille d'adresses (0.0.0.0 et [::]) :
    # le port de l'hôte est le même sur les deux, on prend la première.
    premiere = res.stdout.strip().splitlines()[0] if res.stdout.strip() else ""
    return premiere.rsplit(":", 1)[-1].strip()


def test_la_reponse_nomme_le_jeton_annonce_au_demarrage(host) -> None:
    """Le jeton n'existe que dans les journaux du conteneur.

    Il est tiré par le conteneur lui-même au démarrage : il n'est écrit dans
    aucun fichier du dépôt, ne figure pas dans l'énoncé, et change à chaque
    `run`. Le lire suppose donc d'avoir consulté la sortie du conteneur, par
    `docker logs` ou par le fichier journal que le moteur tient sur l'hôte.
    """
    _conteneur_tourne(host)
    attendu = _attendu(host, "jeton")
    if not attendu:
        pytest.skip(message(
            en=f"`{CONTENEUR}` has not announced any session token: the setup "
               "did not finish",
            fr=f"`{CONTENEUR}` n'a annoncé aucun jeton de session : le setup "
               "n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("jeton", "")
    assert annonce, message(
        en="the `jeton=` line is empty. The container announced a session "
           "token when it started, and it is written nowhere on this machine: "
           "its output is the only place it exists.",
        fr="la ligne `jeton=` est vide. Le conteneur a annoncé un jeton de "
           "session à son démarrage, et il n'est écrit nulle part sur cette "
           "machine : sa sortie est le seul endroit où il existe.",
    )
    assert annonce == attendu, message(
        en=f"the announced token is not the one `{CONTENEUR}` carries.\n"
           f"  you wrote : {annonce}\n"
           "A fresh token is drawn at each run, so a value from a previous "
           "pass is no longer valid.",
        fr=f"le jeton annoncé n'est pas celui que porte `{CONTENEUR}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "Un jeton neuf est tiré à chaque passage : une valeur relevée lors "
           "d'un passage précédent n'est plus valable.",
    )


def test_la_reponse_nomme_l_adresse_donnee_par_le_moteur(host) -> None:
    """L'adresse du conteneur, que le moteur attribue et ne publie pas.

    Elle n'est ni dans l'image, ni dans la commande, ni sur l'hôte : c'est le
    moteur qui la choisit à la création, et l'inspection du conteneur est ce
    qui la rend. C'est la question que se pose tout dépannage réseau.
    """
    _conteneur_tourne(host)
    attendu = _attendu(host, "adresse")
    if not attendu:
        pytest.skip(message(
            en=f"the engine reports no address for `{CONTENEUR}`: the setup "
               "did not finish",
            fr=f"le moteur ne donne aucune adresse à `{CONTENEUR}` : le setup "
               "n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("adresse", "")
    assert annonce, message(
        en="the `adresse=` line is empty. The engine gives the container an "
           "address when it creates it, and only inspecting the container "
           "tells you which one.",
        fr="la ligne `adresse=` est vide. Le moteur donne une adresse au "
           "conteneur en le créant, et seule l'inspection du conteneur dit "
           "laquelle.",
    )
    assert annonce == attendu, message(
        en=f"the announced address is not the one the engine gave.\n"
           f"  you wrote : {annonce}\n"
           "This is the container's own address, not the host's and not the "
           "gateway's. It is reassigned at each creation.",
        fr=f"l'adresse annoncée n'est pas celle que le moteur a donnée.\n"
           f"  vous avez écrit : {annonce}\n"
           "C'est l'adresse du conteneur lui-même, pas celle de l'hôte ni "
           "celle de la passerelle. Elle est réattribuée à chaque création.",
    )


def test_la_reponse_nomme_le_port_publie_sur_l_hote(host) -> None:
    """Le port de l'hôte, choisi par le moteur et non par le lab.

    Le conteneur a été lancé avec `-p 0:80`, qui laisse le moteur prendre un
    port éphémère : personne ne l'a écrit, pas même le setup. Le piège est de
    répondre `80`, qui est le port DU CONTENEUR, celui qu'on connaissait déjà.
    """
    _conteneur_tourne(host)
    attendu = _attendu(host, "port")
    if not attendu:
        pytest.skip(message(
            en=f"`{CONTENEUR}` publishes nothing on 80/tcp: the setup did not "
               "finish",
            fr=f"`{CONTENEUR}` ne publie rien sur 80/tcp : le setup n'a pas "
               "abouti",
        ))

    annonce = _lire_reponses(host).get("port", "")
    assert annonce, message(
        en="the `port=` line is empty. The container publishes its port 80 on "
           "a port of the HOST, which the engine chose on its own.",
        fr="la ligne `port=` est vide. Le conteneur publie son port 80 sur un "
           "port de L'HÔTE, que le moteur a choisi tout seul.",
    )
    # Une réponse de la forme `0.0.0.0:32768` est acceptée : elle désigne bien
    # le port demandé, et refuser la mise en forme n'enseignerait rien.
    chiffres = annonce.rsplit(":", 1)[-1].strip()
    assert chiffres == attendu, message(
        en=f"the announced port is not the one the engine published.\n"
           f"  you wrote : {annonce}\n"
           "Expected is the port of the HOST, the left-hand side of the "
           "mapping, not the container's 80. The engine picks a free port at "
           "each creation.",
        fr=f"le port annoncé n'est pas celui que le moteur a publié.\n"
           f"  vous avez écrit : {annonce}\n"
           "Ce qui est attendu est le port de L'HÔTE, celui de gauche dans la "
           "correspondance, pas le 80 du conteneur. Le moteur en prend un "
           "libre à chaque création.",
    )


def test_le_fichier_ecrit_par_le_conteneur_a_ete_sorti_a_l_identique(host) -> None:
    """Un fichier né après le démarrage, et qui n'est dans aucune image.

    Le conteneur l'écrit lui-même, avec une séquence tirée au hasard : il ne
    peut donc pas être reconstitué de mémoire ni recopié d'un passage
    précédent. Le faire sortir est le geste qu'on pose en vrai pour emporter
    un journal ou une empreinte avant de détruire un conteneur.
    """
    _conteneur_tourne(host)
    dedans = host.run(
        "docker exec %s cat %s", CONTENEUR, TRACE_DANS_LE_CONTENEUR
    )
    if dedans.rc != 0:
        pytest.skip(message(
            en=f"{TRACE_DANS_LE_CONTENEUR} cannot be read inside "
               f"`{CONTENEUR}`: the setup did not finish",
            fr=f"{TRACE_DANS_LE_CONTENEUR} est illisible dans `{CONTENEUR}` : "
               "le setup n'a pas abouti",
        ))

    sorti = host.file(TRACE_SUR_L_HOTE)
    assert sorti.exists, message(
        en=f"{TRACE_SUR_L_HOTE} is missing. The container wrote "
           f"{TRACE_DANS_LE_CONTENEUR} AFTER it started: that file is in no "
           "image, and it has to be taken out of the container.",
        fr=f"{TRACE_SUR_L_HOTE} est absent. Le conteneur a écrit "
           f"{TRACE_DANS_LE_CONTENEUR} APRÈS son démarrage : ce fichier n'est "
           "dans aucune image, et il faut le sortir du conteneur.",
    )
    assert sorti.content_string == dedans.stdout, message(
        en=f"{TRACE_SUR_L_HOTE} exists but differs from the file the "
           "container carries. It is expected AS IS, not retyped: the trace "
           "carries a sequence drawn at random, which is exactly what cannot "
           "be reconstructed by hand.\n"
           f"  in the container : {dedans.stdout.strip()[:120]}\n"
           f"  on the host      : {sorti.content_string.strip()[:120]}",
        fr=f"{TRACE_SUR_L_HOTE} existe mais diffère du fichier que porte le "
           "conteneur. Il est attendu À L'IDENTIQUE, pas recopié à la main : "
           "la trace porte une séquence tirée au hasard, précisément ce qui ne "
           "se reconstitue pas.\n"
           f"  dans le conteneur : {dedans.stdout.strip()[:120]}\n"
           f"  sur l'hôte        : {sorti.content_string.strip()[:120]}",
    )
