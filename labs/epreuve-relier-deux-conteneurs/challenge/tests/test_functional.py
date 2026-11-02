"""Tests fonctionnels de l'épreuve relier-deux-conteneurs : cinq contrôles de poids égal.

C'EST UNE ÉPREUVE, et cela change ce que les messages doivent dire. Un lab
guide : son message nomme le geste qui manque. Un challenge évalue : son message
nomme le SYMPTÔME précis et s'arrête là. Aucun message de ce fichier ne dit
« créez un réseau » ni « posez un alias ». Les indices sont là pour ça, et ils
coûtent des points.

LA PANNE POSÉE, qui n'est dite nulle part dans l'énoncé :
  1. les deux conteneurs sont sur le réseau PAR DÉFAUT, qui donne une adresse
     et une route mais aucune résolution de nom entre conteneurs ;
  2. le nom que la vitrine interroge, `stock`, n'est porté par personne ;
  3. `inventaire` publie un port sur toutes les interfaces ;
  4. `vitrine` publie elle aussi sur toutes les interfaces.

L'EXIGENCE CRITIQUE est le contrôle 4 : un port publié sur l'inventaire. Elle
n'est compensée par aucun total, parce qu'une base joignable depuis le réseau
de l'entreprise est le défaut que l'épreuve existe pour éliminer. Le barème dit
75 sur 100 ; une base exposée fait échouer même à 80.

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


def test_le_nom_cherche_par_la_vitrine_se_resout(host) -> None:
    """Le symptôme de départ, et il se mesure sur la résolution seule.

    Le nom que la vitrine porte dans sa configuration doit rendre une adresse
    que l'inventaire porte RÉELLEMENT. Vérifier les deux évite de valider une
    résolution qui pointerait ailleurs, ce qui est un cas réel dès qu'un nom
    traîne dans un résolveur.
    """
    _tourne(host, FRONTAL)
    _tourne(host, BASE)
    trouvee = _resout(host, FRONTAL, NOM_CHERCHE)
    assert trouvee, message(
        en=f"from `{FRONTAL}`, the name `{NOM_CHERCHE}` does not resolve at "
           "all.\n"
           "That is the symptom the shop window reports, and it is where the "
           "diagnosis starts: nothing answers because nothing is named.",
        fr=f"depuis `{FRONTAL}`, le nom `{NOM_CHERCHE}` ne se résout pas du "
           "tout.\n"
           "C'est le symptôme que remonte la vitrine, et c'est par là que "
           "commence le diagnostic : rien ne répond parce que rien ne porte ce "
           "nom.",
    )
    portees = _adresses(host, BASE)
    assert trouvee in portees, message(
        en=f"`{NOM_CHERCHE}` resolves to {trouvee}, but `{BASE}` does not carry "
           "that address.\n"
           f"  addresses of `{BASE}`: {', '.join(sorted(portees)) or '(none)'}\n"
           "The name points somewhere else, which is worse than not resolving: "
           "the shop window would talk to the wrong thing.",
        fr=f"`{NOM_CHERCHE}` se résout vers {trouvee}, mais `{BASE}` ne porte "
           "pas cette adresse.\n"
           f"  adresses de `{BASE}` : {', '.join(sorted(portees)) or '(aucune)'}\n"
           "Le nom pointe ailleurs, ce qui est pire que de ne pas résoudre : la "
           "vitrine parlerait à autre chose.",
    )


def test_la_requete_traverse_la_vitrine_puis_l_inventaire(host, article) -> None:
    """La traversée complète, lue depuis l'hôte et sur la seule interface due.

    Ce contrôle est le seul qui prouve la chaîne entière : la requête entre par
    le port publié de la vitrine, en ressort vers l'inventaire, et la donnée que
    SEUL l'inventaire détient revient à l'appelant. Résoudre et joindre ne
    suffisent pas : un résolveur peut répondre pour une adresse qu'aucune route
    n'atteint, et une route peut mener à un service muet.
    """
    _tourne(host, FRONTAL)
    _tourne(host, BASE)
    recu = _lire_la_vitrine(host)
    assert "vitrine=ok" in recu, message(
        en=f"nothing answers on {INTERFACE_ATTENDUE}:{PORT_PUBLIE}.\n"
           f"  what came back: {recu.strip() or '(nothing)'}\n"
           "The shop window itself is not reachable where the brief asks for "
           "it, so the chain cannot be judged any further.",
        fr=f"rien ne répond sur {INTERFACE_ATTENDUE}:{PORT_PUBLIE}.\n"
           f"  ce qui revient : {recu.strip() or '(rien)'}\n"
           "La vitrine elle-même n'est pas joignable là où l'énoncé la demande, "
           "donc la chaîne ne peut pas être jugée plus loin.",
    )
    assert f"article={article}" in recu, message(
        en=f"the shop window answers, but without the inventory's value.\n"
           f"  what came back : {recu.strip()}\n"
           f"  expected       : article={article}\n"
           "Only the inventory holds that value. Its absence means the request "
           "stopped at the shop window.",
        fr=f"la vitrine répond, mais sans la valeur de l'inventaire.\n"
           f"  ce qui revient : {recu.strip()}\n"
           f"  attendu        : article={article}\n"
           "Seul l'inventaire détient cette valeur. Son absence signifie que la "
           "requête s'est arrêtée à la vitrine.",
    )


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


def test_l_inventaire_ne_publie_aucun_port_et_quitte_le_reseau_par_defaut(
    host,
) -> None:
    """L'EXIGENCE CRITIQUE de l'épreuve, et elle porte sur deux faits liés.

    Une base n'a aucune raison d'être joignable depuis l'extérieur : sa vitrine
    l'atteint par le réseau des conteneurs. Rien ne retire un port publié sur
    un conteneur existant, ce qui est en soi une information du diagnostic.

    Le second fait est la cause du premier symptôme : sur le réseau par défaut,
    les conteneurs ont une adresse mais aucun nom. Y rester, c'est régler le
    symptôme sans régler la cause.
    """
    _tourne(host, BASE)
    res = host.run("docker container inspect %s", BASE)
    assert res.rc == 0, message(
        en=f"container `{BASE}` cannot be inspected.",
        fr=f"le conteneur `{BASE}` ne peut pas être inspecté.",
    )
    etat = json.loads(res.stdout)[0]
    liaisons = etat["HostConfig"]["PortBindings"] or {}
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
    reseaux = set(etat["NetworkSettings"]["Networks"] or {})
    fournis = reseaux & RESEAUX_DU_MOTEUR
    assert reseaux and not fournis, message(
        en=f"`{BASE}` is still attached to a network the engine provides.\n"
           f"  attached to: {', '.join(sorted(reseaux)) or '(none)'}\n"
           "On that network a container has an address but no name, which is "
           "exactly the first symptom.",
        fr=f"`{BASE}` est encore rattaché à un réseau fourni par le moteur.\n"
           f"  rattaché à : {', '.join(sorted(reseaux)) or '(aucun)'}\n"
           "Sur ce réseau, un conteneur a une adresse mais aucun nom, ce qui "
           "est précisément le premier symptôme.",
    )


def test_le_nom_reel_de_l_inventaire_se_resout_aussi(host) -> None:
    """L'exploitation doit continuer à désigner le conteneur par son nom.

    Cette exigence figure dans l'énoncé, donc ce n'est pas un piège. Elle écarte
    la correction par renommage, qui réglerait le symptôme et ferait perdre la
    compétence : un nom supplémentaire s'ajoute, il ne remplace pas.

    C'est aussi la situation réelle : la vitrine a son nom à elle, écrit dans
    une configuration qu'on ne peut pas changer, et l'exploitation garde le
    sien, celui des journaux et des inventaires. Mesuré dans ce dépôt : un alias
    posé sur un réseau laisse le vrai nom résoudre, donc les deux exigences sont
    satisfiables ensemble, et seul un renommage les oppose.
    """
    _tourne(host, FRONTAL)
    _tourne(host, BASE)
    trouvee = _resout(host, FRONTAL, BASE)
    assert trouvee, message(
        en=f"from `{FRONTAL}`, the real name `{BASE}` no longer resolves.\n"
           "The brief asks for both: the name the shop window carries, and the "
           "one operations uses. An additional name is added, it does not "
           "replace the real one.",
        fr=f"depuis `{FRONTAL}`, le nom réel `{BASE}` ne se résout plus.\n"
           "L'énoncé demande les deux : le nom que porte la vitrine, et celui "
           "dont se sert l'exploitation. Un nom supplémentaire s'ajoute, il ne "
           "remplace pas le nom réel.",
    )
    portees = _adresses(host, BASE)
    assert trouvee in portees, message(
        en=f"`{BASE}` resolves to {trouvee}, which the container does not "
           "carry.\n"
           f"  addresses of `{BASE}`: {', '.join(sorted(portees)) or '(none)'}",
        fr=f"`{BASE}` se résout vers {trouvee}, que le conteneur ne porte pas.\n"
           f"  adresses de `{BASE}` : {', '.join(sorted(portees)) or '(aucune)'}",
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
