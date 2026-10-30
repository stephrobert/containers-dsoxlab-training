"""Tests fonctionnels du lab reseau-bridge-par-defaut : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que le réseau par défaut relie les conteneurs entre eux
et à l'hôte, et qu'il ne leur donne AUCUNE résolution de noms. C'est le réseau
que tout le monde utilise sans le choisir, et ses limites ne se découvrent
qu'en s'y cognant.

LA LEÇON A ÉTÉ MESURÉE AVANT D'ÊTRE ÉCRITE. Sur docker.lab, le 2026-10-30,
depuis un conteneur du réseau par défaut : une connexion vers l'adresse de
`arriere` rend son jeton, la même vers son nom rend « bad address », et
`nslookup` expire sans joindre de serveur. Le lab suivant crée un réseau dédié
et retrouve le DNS : le contraste est la pédagogie.

LE PRINCIPE QUI TIENT TOUT LE FICHIER : LA VÉRITÉ EST RECALCULÉE ICI, au moment
de la notation, en interrogeant le moteur. Aucune adresse n'est écrite dans ce
fichier : le sous-réseau du bridge par défaut dépend de la machine, et un
contrôle qui attendrait `172.17.0.2` serait faux ailleurs.

LE CONTRÔLE QUI DEMANDE UN VRAI PAQUET. Le quatrième. Le jeton ne vit que dans
la réponse TCP de `arriere` : il n'est ni dans ses journaux, ni dans aucun
fichier, et il est tiré au hasard à chaque passage. Le trouver suppose d'avoir
ouvert une connexion.

UNE HONNÊTETÉ SUR CE CONTRÔLE. L'hôte aussi joint le bridge par défaut
directement, donc le jeton peut être obtenu depuis l'hôte plutôt que depuis
`avant`. Ce n'est pas une faille du lab, c'est un fait du réseau par défaut que
le README énonce, et c'est même une information de sécurité utile. Le contrôle
note donc l'état atteint, `avant` porte le jeton, et non le chemin suivi, ce
qui est la règle du dépôt.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import re

import pytest

from conftest import lab_host, message

CLIENT = "avant"
ECOUTEUR = "arriere"
PORT = 8080
ATELIER = "/opt/lab-reseau"
REPONSES = f"{ATELIER}/reponses.txt"
JETON_DANS_LE_CLIENT = "/jeton.txt"

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


def _les_conteneurs_tournent(host) -> None:
    """Le préalable des quatre contrôles, dit une fois et clairement.

    Un conteneur arrêté perd son adresse, et `arriere` arrêté n'écoute plus :
    le signaler explicitement vaut mieux que de laisser trois contrôles
    refuser sur des valeurs vides.
    """
    for nom in (ECOUTEUR, CLIENT):
        res = host.run(
            "docker container inspect %s --format %s", nom, "{{.State.Status}}"
        )
        if res.rc != 0:
            pytest.fail(message(
                en=f"container `{nom}` does not exist any more. Both are needed "
                   "by these checks: replay the lab with `dsoxlab reset`.",
                fr=f"le conteneur `{nom}` n'existe plus. Les deux sont "
                   "nécessaires à ces contrôles : rejouez le lab avec "
                   "`dsoxlab reset`.",
            ))
        etat = res.stdout.strip()
        if etat != "running":
            pytest.fail(message(
                en=f"container `{nom}` is in state `{etat}`, not `running`. A "
                   "stopped container has no address, and `arriere` no longer "
                   "listens. `docker start` puts it back, but the token has "
                   "changed.",
                fr=f"le conteneur `{nom}` est dans l'état `{etat}`, pas "
                   "`running`. Un conteneur arrêté n'a plus d'adresse, et "
                   "`arriere` n'écoute plus. `docker start` le remet en marche, "
                   "mais le jeton a changé.",
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
               "it: adresse=, passerelle= and interface=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire trois "
               "lignes : adresse=, passerelle= et interface=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def _adresse_de_l_ecouteur(host) -> str:
    """L'adresse que le moteur a donnée à `arriere`."""
    res = host.run(
        "docker container inspect %s --format %s",
        ECOUTEUR, "{{.NetworkSettings.IPAddress}}",
    )
    return res.stdout.strip() if res.rc == 0 else ""


def _passerelle(host) -> str:
    """La passerelle du réseau par défaut, telle que le moteur la déclare."""
    res = host.run(
        "docker network inspect bridge --format %s",
        "{{(index .IPAM.Config 0).Gateway}}",
    )
    return res.stdout.strip() if res.rc == 0 else ""


def test_la_reponse_nomme_l_adresse_de_l_ecouteur(host) -> None:
    """L'adresse du conteneur à joindre, que le moteur a choisie.

    Sur le réseau par défaut, c'est la seule façon de désigner un autre
    conteneur : le nom ne se résout pas. L'adresse est donc la clé de tout le
    reste, et c'est aussi ce qui rend ce réseau impraticable en vrai, puisqu'une
    adresse change à chaque création.
    """
    _les_conteneurs_tournent(host)
    attendu = _adresse_de_l_ecouteur(host)
    if not attendu:
        pytest.skip(message(
            en=f"the engine reports no address for `{ECOUTEUR}`: the setup did "
               "not finish",
            fr=f"le moteur ne donne aucune adresse à `{ECOUTEUR}` : le setup "
               "n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("adresse", "")
    assert annonce, message(
        en="the `adresse=` line is empty. On the default network, the address "
           "is the only way to designate another container: its name does not "
           "resolve.",
        fr="la ligne `adresse=` est vide. Sur le réseau par défaut, l'adresse "
           "est la seule façon de désigner un autre conteneur : son nom ne se "
           "résout pas.",
    )
    assert annonce == attendu, message(
        en=f"the announced address is not the one `{ECOUTEUR}` carries.\n"
           f"  you wrote : {annonce}\n"
           f"This is `{ECOUTEUR}`'s own address, not the host's and not the "
           "gateway's. It is reassigned at each creation.",
        fr=f"l'adresse annoncée n'est pas celle que porte `{ECOUTEUR}`.\n"
           f"  vous avez écrit : {annonce}\n"
           f"C'est l'adresse de `{ECOUTEUR}` lui-même, pas celle de l'hôte ni "
           "celle de la passerelle. Elle est réattribuée à chaque création.",
    )


def test_la_reponse_nomme_la_passerelle_du_reseau_par_defaut(host) -> None:
    """La passerelle, qui est l'hôte vu depuis les conteneurs.

    C'est par elle que tout sort, et c'est aussi l'adresse par laquelle un
    conteneur joint un service de l'hôte. Elle se lit dans l'inspection du
    RÉSEAU, pas dans celle d'un conteneur, et c'est la distinction que ce
    contrôle fait acquérir.
    """
    _les_conteneurs_tournent(host)
    attendu = _passerelle(host)
    if not attendu:
        pytest.skip(message(
            en="the engine reports no gateway for the default network: the "
               "setup did not finish",
            fr="le moteur ne donne aucune passerelle au réseau par défaut : le "
               "setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("passerelle", "")
    assert annonce, message(
        en="the `passerelle=` line is empty. It is read by inspecting the "
           "NETWORK, not a container: a container knows its own address, the "
           "network knows its gateway.",
        fr="la ligne `passerelle=` est vide. Elle se lit en inspectant le "
           "RÉSEAU, pas un conteneur : un conteneur connaît sa propre adresse, "
           "le réseau connaît sa passerelle.",
    )
    assert annonce == attendu, message(
        en=f"the announced gateway is not the one the default network "
           "declares.\n"
           f"  you wrote : {annonce}\n"
           "The gateway is the host as the containers see it. It is usually the "
           "first address of the subnet, but reading it beats assuming it.",
        fr=f"la passerelle annoncée n'est pas celle que déclare le réseau par "
           "défaut.\n"
           f"  vous avez écrit : {annonce}\n"
           "La passerelle est l'hôte tel que les conteneurs le voient. C'est "
           "en général la première adresse du sous-réseau, mais la lire vaut "
           "mieux que la supposer.",
    )


def test_la_reponse_nomme_l_interface_de_l_hote(host) -> None:
    """Le pont existe sur l'hôte, et il porte un nom.

    C'est le contrôle qui relie les deux mondes : la passerelle que les
    conteneurs voient est une adresse portée par une interface réelle de
    l'hôte. Tant qu'on ne l'a pas vue, le réseau des conteneurs reste une
    abstraction.
    """
    _les_conteneurs_tournent(host)
    passerelle = _passerelle(host)
    if not passerelle:
        pytest.skip(message(
            en="the engine reports no gateway for the default network: the "
               "setup did not finish",
            fr="le moteur ne donne aucune passerelle au réseau par défaut : le "
               "setup n'a pas abouti",
        ))

    # L'interface est cherchée PAR SON ADRESSE plutôt que par son nom : le pont
    # du réseau par défaut s'appelle `docker0` sur une installation ordinaire,
    # mais ce nom est configurable, et un contrôle qui l'attendrait en dur
    # serait faux sur une machine réglée autrement.
    res = host.run("ip -o -4 addr show")
    attendues = {
        ligne.split()[1]
        for ligne in res.stdout.splitlines()
        if re.search(rf"\s{re.escape(passerelle)}/", ligne)
    }
    if not attendues:
        pytest.skip(message(
            en=f"no host interface carries the gateway {passerelle}: the setup "
               "did not finish",
            fr=f"aucune interface de l'hôte ne porte la passerelle "
               f"{passerelle} : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("interface", "")
    assert annonce, message(
        en="the `interface=` line is empty. The gateway the containers see is "
           "an address carried by a REAL interface of the host: find which one.",
        fr="la ligne `interface=` est vide. La passerelle que voient les "
           "conteneurs est une adresse portée par une interface RÉELLE de "
           "l'hôte : trouvez laquelle.",
    )
    # Une réponse de la forme `docker0@if3` ou `docker0:` est acceptée : elle
    # désigne bien l'interface, et refuser la mise en forme n'enseignerait rien.
    nom = annonce.split("@")[0].rstrip(":").strip()
    assert nom in attendues, message(
        en=f"no interface of the host named `{nom}` carries the gateway "
           f"{passerelle}.\n"
           "This is an interface of the HOST, not of a container, and it is the "
           "bridge the engine created. `ip addr` on the host shows it, and the "
           "engine also names it in the network's options.",
        fr=f"aucune interface de l'hôte nommée `{nom}` ne porte la passerelle "
           f"{passerelle}.\n"
           "C'est une interface de L'HÔTE, pas d'un conteneur, et c'est le pont "
           "que le moteur a créé. `ip addr` sur l'hôte le montre, et le moteur "
           "le nomme aussi dans les options du réseau.",
    )


def test_le_client_porte_le_jeton_obtenu_par_une_connexion(host) -> None:
    """Un vrai paquet a circulé, et le jeton le prouve.

    Le jeton ne vit que dans la réponse TCP de `arriere` : il n'est ni dans ses
    journaux, ni dans aucun fichier, et il est tiré au hasard à chaque passage.
    Le fichier est attendu DANS `avant`, parce que c'est là que l'état compte.
    """
    _les_conteneurs_tournent(host)
    adresse = _adresse_de_l_ecouteur(host)
    if not adresse:
        pytest.skip(message(
            en=f"the engine reports no address for `{ECOUTEUR}`: the setup did "
               "not finish",
            fr=f"le moteur ne donne aucune adresse à `{ECOUTEUR}` : le setup "
               "n'a pas abouti",
        ))

    # La vérité est redemandée à `arriere`, et plusieurs fois : son `nc` est
    # relancé après chaque connexion, donc une tentative peut tomber dans la
    # fenêtre où il n'écoute pas encore.
    attendu = ""
    for _ in range(5):
        res = host.run("nc -w 3 %s %s", adresse, str(PORT))
        trouve = re.search(r"jeton=([0-9a-f]+)", res.stdout)
        if trouve:
            attendu = trouve.group(1)
            break
    if not attendu:
        pytest.skip(message(
            en=f"`{ECOUTEUR}` answers no token on port {PORT}: the setup did "
               "not finish",
            fr=f"`{ECOUTEUR}` ne répond aucun jeton sur le port {PORT} : le "
               "setup n'a pas abouti",
        ))

    lu = host.run("docker exec %s cat %s", CLIENT, JETON_DANS_LE_CLIENT)
    assert lu.rc == 0, message(
        en=f"{JETON_DANS_LE_CLIENT} cannot be read inside `{CLIENT}`: "
           f"{lu.stderr.strip()}\n"
           f"The file is expected INSIDE `{CLIENT}`, not on the host: that is "
           "where the state matters.",
        fr=f"{JETON_DANS_LE_CLIENT} est illisible dans `{CLIENT}` : "
           f"{lu.stderr.strip()}\n"
           f"Le fichier est attendu DANS `{CLIENT}`, pas sur l'hôte : c'est là "
           "que l'état compte.",
    )
    assert attendu in lu.stdout, message(
        en=f"{JETON_DANS_LE_CLIENT} does not carry the token `{ECOUTEUR}` "
           "answers.\n"
           f"  found: {lu.stdout.strip()[:120] or '(empty)'}\n"
           "The token lives only in the TCP answer, and a fresh one is drawn at "
           "each run. On this network the name does not resolve: the address is "
           "what you connect to.",
        fr=f"{JETON_DANS_LE_CLIENT} ne porte pas le jeton que répond "
           f"`{ECOUTEUR}`.\n"
           f"  trouvé : {lu.stdout.strip()[:120] or '(vide)'}\n"
           "Le jeton ne vit que dans la réponse TCP, et un jeton neuf est tiré "
           "à chaque passage. Sur ce réseau, le nom ne se résout pas : c'est "
           "l'adresse qu'on joint.",
    )
