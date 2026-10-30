"""Tests fonctionnels du challenge reseau-diagnostic-dns : quatre contrôles de poids égal.

C'EST UNE ÉPREUVE, et cela change ce que les messages doivent dire. Un lab
guide : son message nomme le geste qui manque. Un challenge évalue : son message
nomme le SYMPTÔME précis et s'arrête là. Aucun message de ce fichier ne dit
« rattachez le conteneur » ni « posez un alias ». Les indices sont là pour ça,
et ils coûtent des points.

LA PANNE POSÉE, qui n'est dite nulle part dans l'énoncé :
  1. `boutique` et `catalogue` sont sur deux réseaux dédiés DIFFÉRENTS ;
  2. l'application cherche la base sous le nom `base`, et le conteneur
     s'appelle `catalogue` ;
  3. `catalogue` publie un port sur toutes les interfaces.

TROIS SYMPTÔMES, UNE CORRECTION POSSIBLE : recréer `catalogue` sur le réseau de
`boutique`, avec l'alias et sans publication. C'est ce qui fait la valeur de
l'épreuve, et c'est pourquoi les quatre contrôles sont de poids égal : ils
mesurent le même diagnostic vu de quatre côtés.

POURQUOI LE CONTRÔLE 4 EXIGE LE VRAI NOM. Sans lui, renommer le conteneur en
`base` satisferait les trois autres, et l'apprenant n'aurait rien appris des
alias réseau. L'exigence est annoncée dans l'énoncé, donc ce n'est pas un piège :
l'exploitation doit continuer à désigner le conteneur par son nom réel, ce qui
est la vraie raison pour laquelle les alias existent.

Mesuré sur docker.lab le 2026-10-30 : un alias posé sur un réseau laisse le vrai
nom résoudre. Les deux exigences sont donc satisfiables ensemble, et seul un
renommage les oppose.

LES CONTRÔLES LISENT LA RÉPONSE, jamais la seule connexion : le proxy de Docker
accepte avant que quoi que ce soit écoute. Un test qui se contenterait d'un
`connect()` réussi déclarerait joignable un service absent.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import re

import pytest

from conftest import lab_host, message

APPLICATION = "boutique"
BASE = "catalogue"
NOM_ATTENDU = "base"
PORT = 80

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


def _tourne(host, nom: str) -> None:
    """Le préalable de chaque contrôle.

    Cette épreuve fait recréer des conteneurs : un nom manquant veut presque
    toujours dire qu'un conteneur a été détruit et pas relancé. Le message le
    dit, parce que c'est une information d'état et non un indice de résolution.
    """
    res = host.run(
        "docker container inspect %s --format %s", nom, "{{.State.Status}}"
    )
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{nom}` does not exist. The two container names are "
               "part of the brief, and the checks look for them by name: if you "
               "recreated it, it has to carry the same name.",
            fr=f"le conteneur `{nom}` n'existe pas. Les deux noms de conteneurs "
               "font partie de l'énoncé, et les contrôles les cherchent "
               "nommément : si vous l'avez recréé, il doit porter le même nom.",
        ))
    etat = res.stdout.strip()
    if etat != "running":
        pytest.fail(message(
            en=f"container `{nom}` is in state `{etat}`, not `running`. A "
               "stopped container has no address and answers nothing.",
            fr=f"le conteneur `{nom}` est dans l'état `{etat}`, pas `running`. "
               "Un conteneur arrêté n'a plus d'adresse et ne répond rien.",
        ))


def _adresses(host, nom: str) -> set[str]:
    """Toutes les adresses qu'un conteneur porte, sur tous ses réseaux.

    Toutes, et non celle d'un réseau nommé : l'épreuve n'impose aucun nom de
    réseau, puisqu'elle note le résultat et non le chemin. Un apprenant qui
    règle la panne en créant un troisième réseau a réglé la panne.
    """
    res = host.run(
        "docker container inspect %s --format %s",
        nom,
        "{{range .NetworkSettings.Networks}}{{println .IPAddress}}{{end}}",
    )
    if res.rc != 0:
        return set()
    return {ligne.strip() for ligne in res.stdout.splitlines() if ligne.strip()}


def _resout(host, depuis: str, nom: str) -> str:
    """L'adresse qu'un nom rend depuis un conteneur, ou une chaîne vide.

    `nslookup` plutôt qu'une connexion : on veut distinguer « le nom ne résout
    pas » de « le nom résout mais rien ne répond », qui sont deux pannes
    différentes et deux contrôles différents.
    """
    res = host.run("docker exec %s nslookup %s", depuis, nom)
    if res.rc != 0:
        return ""
    adresses = re.findall(r"Address:\s*([0-9.]+)", res.stdout)
    # La première adresse est celle du résolveur lui-même : c'est la réponse
    # qui nous intéresse, donc la dernière ligne utile.
    return adresses[-1] if adresses else ""


def _repond(host, depuis: str, cible: str, port: int) -> bool:
    """Vrai si un service RÉPOND, sur ce nom et ce port, vu de ce conteneur.

    La réponse est lue, jamais la seule connexion : le proxy de Docker accepte
    avant que quoi que ce soit écoute. Plusieurs tentatives, parce que
    l'écouteur est relancé après chaque connexion.
    """
    for _ in range(4):
        res = host.run("docker exec %s nc -w 3 %s %s", depuis, cible, str(port))
        if "jeton=" in res.stdout:
            return True
    return False


def test_le_nom_attendu_par_l_application_se_resout(host) -> None:
    """Le symptôme de départ, et il se mesure sur la résolution seule.

    Le nom que l'application porte en dur doit rendre une adresse que la base
    porte RÉELLEMENT. Vérifier les deux évite de valider une résolution qui
    pointerait ailleurs, ce qui est un cas réel dès qu'un nom traîne dans un
    résolveur.
    """
    _tourne(host, APPLICATION)
    _tourne(host, BASE)
    trouvee = _resout(host, APPLICATION, NOM_ATTENDU)
    assert trouvee, message(
        en=f"from `{APPLICATION}`, the name `{NOM_ATTENDU}` does not resolve at "
           "all.\n"
           "That is the symptom the application reports, and it is where the "
           "diagnosis starts: nothing answers because nothing is named.",
        fr=f"depuis `{APPLICATION}`, le nom `{NOM_ATTENDU}` ne se résout pas du "
           "tout.\n"
           "C'est le symptôme que remonte l'application, et c'est par là que "
           "commence le diagnostic : rien ne répond parce que rien ne porte ce "
           "nom.",
    )
    portees = _adresses(host, BASE)
    assert trouvee in portees, message(
        en=f"`{NOM_ATTENDU}` resolves to {trouvee}, but `{BASE}` does not carry "
           "that address.\n"
           f"  addresses of `{BASE}`: {', '.join(sorted(portees)) or '(none)'}\n"
           "The name points somewhere else, which is worse than not resolving: "
           "the application would talk to the wrong thing.",
        fr=f"`{NOM_ATTENDU}` se résout vers {trouvee}, mais `{BASE}` ne porte "
           "pas cette adresse.\n"
           f"  adresses de `{BASE}` : {', '.join(sorted(portees)) or '(aucune)'}\n"
           "Le nom pointe ailleurs, ce qui est pire que de ne pas résoudre : "
           "l'application parlerait à autre chose.",
    )


def test_l_application_joint_sa_base_par_ce_nom(host) -> None:
    """Résoudre n'est pas joindre, et les deux pannes sont distinctes.

    Un résolveur peut répondre pour une adresse qu'aucune route n'atteint. Ce
    contrôle est donc séparé du précédent à dessein : leurs causes sont
    différentes, et leurs messages doivent l'être aussi.
    """
    _tourne(host, APPLICATION)
    _tourne(host, BASE)
    assert _repond(host, APPLICATION, NOM_ATTENDU, PORT), message(
        en=f"from `{APPLICATION}`, nothing answers on `{NOM_ATTENDU}` port "
           f"{PORT}.\n"
           "Resolving is not reaching: a resolver can answer for an address no "
           "route reaches. If the previous check passed, the name is right and "
           "the path is not.",
        fr=f"depuis `{APPLICATION}`, rien ne répond sur `{NOM_ATTENDU}` port "
           f"{PORT}.\n"
           "Résoudre n'est pas joindre : un résolveur peut répondre pour une "
           "adresse qu'aucune route n'atteint. Si le contrôle précédent passe, "
           "le nom est bon et le chemin ne l'est pas.",
    )


def test_la_base_ne_publie_aucun_port(host) -> None:
    """La faute que l'audit a relevée, et elle est indépendante des autres.

    Une base n'a aucune raison d'être joignable depuis l'extérieur : son
    application l'atteint par le réseau des conteneurs. Rien ne retire un port
    publié sur un conteneur existant, ce qui est en soi une information du
    diagnostic.
    """
    _tourne(host, BASE)
    res = host.run("docker port %s %s/tcp", BASE, str(PORT))
    # `docker port` ÉCHOUE sur un conteneur qui ne publie rien, et n'écrit pas
    # une sortie vide : vérifié le 2026-10-30. Le code de retour est donc la
    # vraie information.
    if res.rc != 0:
        return
    publications = [
        ligne.strip() for ligne in res.stdout.splitlines() if ligne.strip()
    ]
    assert not publications, message(
        en=f"`{BASE}` still publishes a port:\n  {', '.join(publications)}\n"
           "A database has no reason to be reachable from the outside: its "
           "application reaches it through the container network. That is what "
           "the audit reported.",
        fr=f"`{BASE}` publie encore un port :\n  {', '.join(publications)}\n"
           "Une base n'a aucune raison d'être joignable depuis l'extérieur : "
           "son application l'atteint par le réseau des conteneurs. C'est ce "
           "que l'audit a relevé.",
    )


def test_le_nom_reel_de_la_base_se_resout_aussi(host) -> None:
    """L'exploitation doit continuer à désigner le conteneur par son nom.

    Cette exigence figure dans l'énoncé, donc ce n'est pas un piège. Elle écarte
    la correction par renommage, qui réglerait le symptôme et ferait perdre la
    compétence : un nom supplémentaire s'ajoute, il ne remplace pas.

    C'est aussi la situation réelle : l'application a son nom à elle, écrit dans
    une configuration qu'on ne peut pas changer, et l'exploitation garde le
    sien, celui des journaux et des inventaires.
    """
    _tourne(host, APPLICATION)
    _tourne(host, BASE)
    trouvee = _resout(host, APPLICATION, BASE)
    assert trouvee, message(
        en=f"from `{APPLICATION}`, the real name `{BASE}` no longer resolves.\n"
           "The brief asks for both: the name the application carries, and the "
           "one operations uses. An additional name is added, it does not "
           "replace.",
        fr=f"depuis `{APPLICATION}`, le nom réel `{BASE}` ne se résout plus.\n"
           "L'énoncé demande les deux : celui que porte l'application, et celui "
           "dont se sert l'exploitation. Un nom supplémentaire s'ajoute, il ne "
           "remplace pas.",
    )
    portees = _adresses(host, BASE)
    assert trouvee in portees, message(
        en=f"`{BASE}` resolves to {trouvee}, but the container does not carry "
           "that address.\n"
           f"  addresses of `{BASE}`: {', '.join(sorted(portees)) or '(none)'}",
        fr=f"`{BASE}` se résout vers {trouvee}, mais le conteneur ne porte pas "
           "cette adresse.\n"
           f"  adresses de `{BASE}` : {', '.join(sorted(portees)) or '(aucune)'}",
    )
