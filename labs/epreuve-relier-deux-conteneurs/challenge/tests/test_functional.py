"""Tests fonctionnels de l'épreuve relier-deux-conteneurs : cinq contrôles de poids égal.

C'EST UNE ÉPREUVE, et cela change ce que les messages doivent dire. Un lab
guide : son message nomme le geste qui manque. Un challenge évalue : son message
nomme le SYMPTÔME précis et s'arrête là. Aucun message de ce fichier ne dit
« créez un réseau » ni « posez un alias ». Les indices sont là pour ça, et ils
coûtent des points.

CE QUE CETTE ÉPREUVE MESURE, et ce qu'elle ne mesure plus.

Elle est l'épreuve du module « exposer et relier », qui enseigne trois choses :
publier un port sur une interface choisie, se donner un réseau et un alias, et
isoler un service avec un réseau sans issue. Elle note leur COMBINAISON.

Elle redisait auparavant le lab de la leçon sur la résolution de noms : quatre
de ses cinq contrôles y portaient, et le troisième enseignement du module,
l'isolement, n'était mesuré nulle part dans le catalogue. Une épreuve de fin de
module ne rejoue pas le lab d'une leçon antérieure.

LA PANNE POSÉE, qui n'est dite nulle part dans l'énoncé :
  1. les deux conteneurs sont sur le réseau PAR DÉFAUT, qui donne une adresse,
     une route vers l'extérieur, et aucune résolution de nom entre conteneurs ;
  2. le nom que la vitrine interroge, `stock`, n'est porté par personne ;
  3. `inventaire` publie un port sur toutes les interfaces ;
  4. `inventaire` peut sortir vers l'extérieur, ce qu'une base n'a pas à faire ;
  5. `vitrine` publie elle aussi sur toutes les interfaces.

L'EXIGENCE CRITIQUE est le port publié sur l'inventaire, et elle porte
désormais sur CE SEUL FAIT. Elle en mêlait deux, le port et le réseau, si bien
qu'un apprenant qui ratait le réseau perdait son exigence critique pour une
raison qui n'était pas celle que l'énoncé annonce. Le barème dit 75 sur 100 ;
une base exposée fait échouer même à 80.

COMMENT L'ISOLEMENT SE PROUVE, et c'est mesuré le 2026-11-02 sur 29.9.2 : un
conteneur sur un réseau interne n'a AUCUNE route par défaut, là où un conteneur
sur un réseau ordinaire en a une. On lit ce fait, et non une tentative de
connexion vers l'extérieur : celle-ci passerait au vert sur une machine sans
accès sortant, c'est-à-dire pour la mauvaise raison, et le resterait le jour où
l'isolement disparaîtrait.

CE QUE LES CONTRÔLES NE MESURENT PAS, délibérément : le NOM du réseau, et le
chemin suivi. L'épreuve note l'état final. Un apprenant qui crée un réseau
nommé autrement, ou qui s'y prend en quatre gestes au lieu de deux, a réglé la
panne et reçoit la même note.

LES CONTRÔLES LISENT LA RÉPONSE, jamais la seule connexion : le proxy de Docker
accepte dès le `run`, avant que quoi que ce soit écoute. Vérifié dans ce dépôt :
une connexion réussit sur un `-p 8299:1234` dont le conteneur n'écoute nulle
part. Un test qui se contenterait d'un `connect()` réussi déclarerait joignable
un service absent.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'une autre épreuve.
"""

from __future__ import annotations

import json
import re

import pytest

from conftest import lab_host, message

FRONTAL = "vitrine"
BASE = "inventaire"
NOM_CHERCHE = "stock"
IMAGE = "lab-relier:1.0"
PORT_SERVICE = 80
PORT_PUBLIE = 18311
INTERFACE_ATTENDUE = "127.0.0.1"

# Les réseaux que le moteur fournit lui-même. Aucun des deux conteneurs ne doit
# finir sur `bridge` : c'est lui qui ne résout pas les noms.
RESEAUX_DU_MOTEUR = {"bridge", "host", "none"}

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui les
    lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier.
    """
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def article(host) -> str:
    """La donnée témoin, lue dans le LABEL de l'image fournie.

    Elle est lue là et non dans un fichier de l'hôte, parce que l'épreuve
    demande de recréer les deux conteneurs : une donnée portée par l'image
    survit à la recréation, donc le contrôle de la traversée ne punit pas la
    bonne façon de s'y prendre.
    """
    res = host.run(
        "docker image inspect %s --format %s",
        IMAGE,
        '{{index .Config.Labels "dsoxlab.article"}}',
    )
    if res.rc != 0 or not res.stdout.strip():
        pytest.fail(message(
            en=f"image `{IMAGE}` is gone, or no longer carries the lab's witness "
               "value. It is the image the brief provides: it is not to be "
               "rebuilt, and the containers are recreated FROM it.",
            fr=f"l'image `{IMAGE}` a disparu, ou ne porte plus la donnée témoin "
               "du lab. C'est l'image que l'énoncé fournit : elle n'est pas à "
               "reconstruire, et les conteneurs se recréent À PARTIR d'elle.",
        ))
    return res.stdout.strip()


def test_la_vitrine_ne_publie_que_sur_l_interface_demandee(host) -> None:
    """Publier n'est pas publier partout, et l'énoncé le demande explicitement.

    Un `-p 18311:80` écoute sur TOUTES les interfaces de l'hôte, donc sur le
    réseau de l'entreprise. Lier la publication à une adresse est le geste que
    le module enseigne, et l'énoncé le réclame : la vitrine ne doit être
    joignable que depuis la machine.

    Le contrôle lit `HostConfig.PortBindings`, qui porte l'intention déclarée,
    ET `docker port`, qui porte ce que le moteur a réellement ouvert.
    """
    _tourne(host, FRONTAL)
    res = host.run("docker container inspect %s", FRONTAL)
    assert res.rc == 0, message(
        en=f"container `{FRONTAL}` cannot be inspected.",
        fr=f"le conteneur `{FRONTAL}` ne peut pas être inspecté.",
    )
    liaisons = json.loads(res.stdout)[0]["HostConfig"]["PortBindings"] or {}
    attendu = f"{PORT_SERVICE}/tcp"
    publies = sorted(liaisons)
    assert publies == [attendu], message(
        en=f"`{FRONTAL}` does not publish exactly one port.\n"
           f"  published: {', '.join(publies) or '(none)'}\n"
           f"  expected : {attendu} only\n"
           "The brief asks for one way in, and only one.",
        fr=f"`{FRONTAL}` ne publie pas exactement un port.\n"
           f"  publiés : {', '.join(publies) or '(aucun)'}\n"
           f"  attendu : {attendu} seul\n"
           "L'énoncé demande une seule entrée, et une seule.",
    )
    hotes = {(l.get("HostIp") or "", l.get("HostPort") or "")
             for l in liaisons[attendu] or []}
    assert hotes == {(INTERFACE_ATTENDUE, str(PORT_PUBLIE))}, message(
        en=f"`{FRONTAL}` is published, but not where the brief asks.\n"
           f"  bindings: {', '.join(f'{i or '0.0.0.0'}:{p}' for i, p in sorted(hotes)) or '(none)'}\n"
           f"  expected: {INTERFACE_ATTENDUE}:{PORT_PUBLIE}\n"
           "An empty or 0.0.0.0 address means every interface of the host, so "
           "the company network as well.",
        fr=f"`{FRONTAL}` est publiée, mais pas là où l'énoncé le demande.\n"
           f"  liaisons : {', '.join(f'{i or '0.0.0.0'}:{p}' for i, p in sorted(hotes)) or '(aucune)'}\n"
           f"  attendu  : {INTERFACE_ATTENDUE}:{PORT_PUBLIE}\n"
           "Une adresse vide ou 0.0.0.0 désigne toutes les interfaces de "
           "l'hôte, donc le réseau de l'entreprise aussi.",
    )



def test_la_base_repond_a_un_alias_distinct_de_son_nom(host) -> None:
    """C07b : un réseau à soi, et un ALIAS.

    Ce n'est pas la résolution de nom en général, qui s'apprend plus tôt et se
    mesure ailleurs : c'est le fait de donner à un service un nom de service,
    distinct du nom du conteneur, que les autres emploient. C'est ce qui permet
    de remplacer le conteneur sans toucher à ce qui l'interroge.

    LE CONTRÔLE LIT LA DÉCLARATION, dans `NetworkSettings.Networks[*].Aliases`,
    et pas seulement la résolution : un conteneur qu'on aurait renommé `stock`
    résoudrait aussi, et n'aurait rien appris de l'alias.
    """
    _tourne(host, BASE)
    res = host.run("docker container inspect %s", BASE)
    assert res.rc == 0, message(
        en=f"container `{BASE}` cannot be inspected.",
        fr=f"le conteneur `{BASE}` ne peut pas être inspecté.",
    )
    reseaux = json.loads(res.stdout)[0]["NetworkSettings"]["Networks"] or {}
    alias = {a for infos in reseaux.values() for a in (infos.get("Aliases") or [])}
    assert NOM_CHERCHE in alias, message(
        en=f"nothing answers to `{NOM_CHERCHE}` on `{BASE}`'s networks.\n"
           f"  declared aliases: {', '.join(sorted(alias)) or '(none)'}\n"
           f"The name `{NOM_CHERCHE}` is written in the shop window's "
           "configuration and does not change. A container renamed to it would "
           "resolve too, and would tie the caller to one container.",
        fr=f"rien ne répond à `{NOM_CHERCHE}` sur les réseaux de `{BASE}`.\n"
           f"  alias déclarés : {', '.join(sorted(alias)) or '(aucun)'}\n"
           f"Le nom `{NOM_CHERCHE}` est écrit dans la configuration de la "
           "vitrine et ne se change pas. Un conteneur qu'on renommerait ainsi "
           "résoudrait aussi, et lierait l'appelant à un conteneur précis.",
    )
    assert NOM_CHERCHE != BASE, message(
        en="the alias and the container name must differ.",
        fr="l'alias et le nom du conteneur doivent différer.",
    )
    vu = _resout(host, FRONTAL, NOM_CHERCHE)
    assert vu and vu in _adresses(host, BASE), message(
        en=f"`{FRONTAL}` does not resolve `{NOM_CHERCHE}` to `{BASE}`.\n"
           f"  resolved to: {vu or '(nothing)'}\n"
           f"  `{BASE}` addresses: {', '.join(sorted(_adresses(host, BASE))) or '(none)'}\n"
           "An alias only answers to those who share the network that carries "
           "it.",
        fr=f"`{FRONTAL}` ne résout pas `{NOM_CHERCHE}` vers `{BASE}`.\n"
           f"  résolu en : {vu or '(rien)'}\n"
           f"  adresses de `{BASE}` : {', '.join(sorted(_adresses(host, BASE))) or '(aucune)'}\n"
           "Un alias ne répond qu'à ceux qui partagent le réseau qui le porte.",
    )


def test_la_base_est_sur_un_reseau_sans_issue(host) -> None:
    """C07c : isoler, et le prouver.

    Une base de données n'a aucune raison de sortir. C'est ce qui transforme
    une lecture non autorisée en fuite : sans issue, la donnée reste là où elle
    est, même quand le service est compromis.

    DEUX FAITS, ET LE SECOND EST CELUI QUI PROUVE. Le premier est déclaratif :
    tous les réseaux auxquels la base est rattachée sont `Internal`. Le second
    est observé DANS le conteneur : il n'a aucune route par défaut.

    On ne tente PAS une connexion vers l'extérieur, et c'est délibéré. Mesuré
    le 2026-11-02 : un conteneur sur un réseau interne n'a aucune route par
    défaut, là où un conteneur ordinaire en a une. Une tentative de connexion,
    elle, passerait au vert sur une machine privée d'accès sortant, donc pour
    la mauvaise raison, et le resterait le jour où l'isolement disparaîtrait.
    """
    _tourne(host, BASE)
    res = host.run("docker container inspect %s", BASE)
    assert res.rc == 0, message(
        en=f"container `{BASE}` cannot be inspected.",
        fr=f"le conteneur `{BASE}` ne peut pas être inspecté.",
    )
    reseaux = json.loads(res.stdout)[0]["NetworkSettings"]["Networks"] or {}
    assert reseaux, message(
        en=f"`{BASE}` is attached to no network at all, so nothing can reach it.",
        fr=f"`{BASE}` n'est rattaché à aucun réseau, donc rien ne peut "
           "l'atteindre.",
    )
    ouverts = []
    for nom in sorted(reseaux):
        interne = host.run(
            "docker network inspect %s --format %s", nom, "{{.Internal}}")
        if interne.stdout.strip().lower() != "true":
            ouverts.append(nom)
    assert not ouverts, message(
        en=f"`{BASE}` sits on a network that has a way out.\n"
           f"  open networks: {', '.join(ouverts)}\n"
           "A database has no reason to reach the outside, and that is what "
           "turns an unauthorised read into a leak.",
        fr=f"`{BASE}` est posé sur un réseau qui a une issue.\n"
           f"  réseaux ouverts : {', '.join(ouverts)}\n"
           "Une base n'a aucune raison de joindre l'extérieur, et c'est ce qui "
           "transforme une lecture non autorisée en fuite.",
    )
    routes = host.run("docker exec %s ip route", BASE)
    defauts = [l for l in routes.stdout.splitlines() if l.startswith("default")]
    assert routes.rc == 0 and not defauts, message(
        en=f"`{BASE}` still has a default route, so it can leave.\n"
           f"  {' / '.join(defauts) or routes.stderr.strip()[:200]}\n"
           "The declaration is not the effect: this is read inside the "
           "container.",
        fr=f"`{BASE}` porte encore une route par défaut, donc il peut sortir.\n"
           f"  {' / '.join(defauts) or routes.stderr.strip()[:200]}\n"
           "La déclaration n'est pas l'effet : ceci se lit dans le conteneur.",
    )


def test_l_inventaire_ne_publie_aucun_port(host) -> None:
    """L'EXIGENCE CRITIQUE, et elle porte sur UN SEUL fait.

    Elle en mêlait deux, le port publié et le réseau d'attache, si bien qu'un
    apprenant qui ratait le réseau perdait son exigence critique pour une
    raison qui n'est pas celle que l'énoncé annonce. L'isolement se mesure
    désormais pour lui-même, dans son propre contrôle.

    Une base n'a aucune raison d'être joignable depuis l'extérieur : sa vitrine
    l'atteint par le réseau des conteneurs. Rien ne retire un port publié sur
    un conteneur existant, ce qui est en soi une information du diagnostic.
    """
    _tourne(host, BASE)
    res = host.run("docker container inspect %s", BASE)
    assert res.rc == 0, message(
        en=f"container `{BASE}` cannot be inspected.",
        fr=f"le conteneur `{BASE}` ne peut pas être inspecté.",
    )
    liaisons = json.loads(res.stdout)[0]["HostConfig"]["PortBindings"] or {}
    assert not liaisons, message(
        en=f"`{BASE}` still publishes a port:\n"
           f"  {', '.join(sorted(liaisons))}\n"
           "A database has no reason to be reachable from the outside: its shop "
           "window reaches it through the container network. That is what the "
           "audit reported, and no total makes up for it.",
        fr=f"`{BASE}` publie encore un port :\n"
           f"  {', '.join(sorted(liaisons))}\n"
           "Une base n'a aucune raison d'être joignable depuis l'extérieur : sa "
           "vitrine l'atteint par le réseau des conteneurs. C'est ce que "
           "l'audit a relevé, et aucun total ne le compense.",
    )


def test_la_requete_metier_aboutit_malgre_l_isolement(host, article) -> None:
    """LA COMBINAISON, et c'est pour elle que cette épreuve existe.

    Chacune des trois exigences se règle facilement seule, et deux d'entre
    elles se contrarient : isoler la base la coupe de tout, publier le frontal
    demande au contraire une issue. La seule façon de tenir les deux est de
    poser le frontal sur les DEUX réseaux, ce qu'aucun contrôle ne demande
    nommément.

    La lecture se fait depuis l'hôte, sur l'interface que l'énoncé impose,
    comme le ferait le relais qui portera la façade.
    """
    _tourne(host, FRONTAL)
    _tourne(host, BASE)
    rendu = _lire_la_vitrine(host)
    attendu = f"article={article}"
    assert attendu in rendu, message(
        en=f"the business request does not come back through the front end.\n"
           f"  what came back: {rendu.strip()[:200] or '(nothing)'}\n"
           f"  expected      : {attendu}\n"
           "Isolating the database must not cut the service: the front end "
           "still has to reach it.",
        fr=f"la requête métier ne revient pas à travers le frontal.\n"
           f"  ce qui revient : {rendu.strip()[:200] or '(rien)'}\n"
           f"  attendu        : {attendu}\n"
           "Isoler la base ne doit pas couper le service : le frontal doit "
           "toujours l'atteindre.",
    )

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
    règle la panne avec un réseau nommé autrement a réglé la panne.
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
    # La première adresse est celle du résolveur lui-même : c'est la réponse qui
    # nous intéresse, donc la dernière ligne utile.
    return adresses[-1] if adresses else ""


def _lire_la_vitrine(host) -> str:
    """Ce que la vitrine répond, lu depuis l'hôte sur l'interface demandée.

    Plusieurs tentatives, pour deux raisons mesurées : l'écouteur est relancé
    après chaque connexion, et la vitrine interroge l'inventaire AVANT
    d'accepter la connexion suivante. La première réponse après une correction
    peut donc encore porter l'état d'avant, et une seule lecture rendrait un
    verdict sur une réponse périmée.
    """
    dernier = ""
    for _ in range(6):
        res = host.run(
            "nc -w 3 %s %s", INTERFACE_ATTENDUE, str(PORT_PUBLIE)
        )
        dernier = res.stdout
        if "article=" in dernier and "article=injoignable" not in dernier:
            return dernier
    return dernier
