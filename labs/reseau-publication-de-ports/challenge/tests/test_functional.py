"""Tests fonctionnels du lab reseau-publication-de-ports : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que publier un port est un choix à trois branches, et que
son défaut est le plus ouvert des trois. `-p 8080:80` publie sur TOUTES les
interfaces, parce que l'adresse de publication est optionnelle : c'est le geste
le plus banal de Docker, et celui qui expose un service sans qu'on l'ait décidé.

LES TROIS POSTURES, MESURÉES AVANT D'ÊTRE ÉCRITES, sur docker.lab le
2026-10-30 :

| Publication | depuis 127.0.0.1 | depuis l'adresse routable |
| `-p 127.0.0.1:P:80` | joint | NE JOINT PAS |
| `-p <routable>:P:80` | NE JOINT PAS | joint |
| aucune | ne joint pas | ne joint pas |

LE PIÈGE QUI INVALIDERAIT TOUS CES CONTRÔLES, et il est déjà documenté dans le
contrat dsoxlab : le proxy de Docker accepte une connexion AVANT que quoi que ce
soit écoute. Vérifié ici le 2026-10-30, sur un `-p 127.0.0.1:18099:1234` dont le
conteneur n'écoutait nulle part : la connexion aboutissait. Ces contrôles lisent
donc la RÉPONSE, jamais la seule connexion. Un test qui se contenterait d'un
`connect()` réussi déclarerait joignable un service absent.

AUCUNE ADRESSE N'EST ÉCRITE DANS CE FICHIER. L'adresse routable est déduite de
la route par défaut, au moment de la notation. Un test qui porterait
`10.10.120.11` serait faux sur une machine adressée autrement, et le lab
mourrait au premier changement de réseau.

CE QUE LE LAB IMPOSE SANS LE DIRE : recréer les conteneurs. `-p` ne se modifie
pas à chaud. C'est une leçon, et c'est aussi pourquoi l'image porte son écouteur
en `CMD` : l'apprenant relance un conteneur sans avoir à réécrire une commande
qu'il n'a jamais vue.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

VITRINE = "vitrine"
ANNEXE = "annexe"
INTERNE = "interne"
PORT_VITRINE = 18080
PORT_ANNEXE = 18081
LOOPBACK = "127.0.0.1"

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
def routable(host) -> str:
    """L'adresse routable de la machine, déduite de sa route par défaut.

    Jamais écrite en dur : le lab doit survivre à un changement de plan
    d'adressage, et une adresse figée dans un test est une panne différée.
    """
    res = host.run(
        "ip -o -4 route get 1.1.1.1 "
        "| awk '{for (i = 1; i <= NF; i++) if ($i == \"src\") print $(i + 1)}'"
    )
    adresse = res.stdout.strip()
    if not adresse:
        pytest.skip(message(
            en="the machine has no routable address: nothing can be measured "
               "about publication",
            fr="la machine n'a aucune adresse routable : rien ne peut être "
               "mesuré sur la publication",
        ))
    return adresse


def _tourne(host, nom: str) -> None:
    """Le préalable de chaque contrôle, dit clairement.

    Ce lab fait RECRÉER les conteneurs : un nom manquant veut presque toujours
    dire qu'un conteneur a été détruit et pas relancé, et le message le dit
    plutôt que de laisser conclure à une faute de publication.
    """
    res = host.run(
        "docker container inspect %s --format %s", nom, "{{.State.Status}}"
    )
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{nom}` does not exist. This lab requires "
               "recreating the containers, because `-p` cannot be changed on a "
               "running one: it has to be relaunched under the SAME name, from "
               "the image the setup built.",
            fr=f"le conteneur `{nom}` n'existe pas. Ce lab demande de recréer "
               "les conteneurs, puisque `-p` ne se modifie pas à chaud : il "
               "faut le relancer sous le MÊME nom, depuis l'image que le setup "
               "a construite.",
        ))
    etat = res.stdout.strip()
    if etat != "running":
        pytest.fail(message(
            en=f"container `{nom}` is in state `{etat}`, not `running`. A "
               "stopped container publishes nothing and answers nothing.",
            fr=f"le conteneur `{nom}` est dans l'état `{etat}`, pas `running`. "
               "Un conteneur arrêté ne publie rien et ne répond rien.",
        ))


def _publication(host, nom: str) -> list[str]:
    """Ce que le moteur déclare publier pour le port 80 d'un conteneur.

    `docker port` ÉCHOUE sur un conteneur qui ne publie rien, et ne rend pas
    une sortie vide : vérifié le 2026-10-30, il écrit « No public port '80/tcp'
    published ». Le code de retour est donc la vraie information, et la liste
    vide en est la traduction.
    """
    res = host.run("docker port %s 80/tcp", nom)
    if res.rc != 0:
        return []
    return [ligne.strip() for ligne in res.stdout.splitlines() if ligne.strip()]


def _repond(host, adresse: str, port: int) -> bool:
    """Vrai si un service RÉPOND à cette adresse et ce port.

    La réponse est lue, jamais la seule connexion : le proxy de Docker accepte
    avant que quoi que ce soit écoute, donc un `connect()` réussi ne prouve
    rien. Plusieurs tentatives, parce que l'écouteur est relancé après chaque
    connexion.
    """
    for _ in range(4):
        res = host.run("nc -w 3 %s %s", adresse, str(port))
        if "jeton=" in res.stdout:
            return True
    return False


def test_la_vitrine_est_publiee_sur_le_loopback_seulement(host) -> None:
    """Publier sur une adresse précise, et pas sur toutes par défaut.

    C'est le contrôle central du lab. `-p 18080:80` publie sur toutes les
    interfaces, parce que l'adresse est optionnelle et que son défaut est le
    plus ouvert. La corriger demande de recréer le conteneur en nommant
    l'adresse.

    Deux assertions : l'adresse déclarée, puis le fait que le service répond
    encore. La seconde n'est pas une redite : un conteneur recréé sans son
    écouteur satisferait la première et ne servirait plus rien.
    """
    _tourne(host, VITRINE)
    publications = _publication(host, VITRINE)
    assert publications, message(
        en=f"`{VITRINE}` publishes nothing any more. It must stay published, "
           f"on {LOOPBACK} and port {PORT_VITRINE} of the host.",
        fr=f"`{VITRINE}` ne publie plus rien. Elle doit rester publiée, sur "
           f"{LOOPBACK} et le port {PORT_VITRINE} de l'hôte.",
    )
    ouvertes = [p for p in publications if not p.startswith(f"{LOOPBACK}:")]
    assert not ouvertes, message(
        en=f"`{VITRINE}` is published outside {LOOPBACK}:\n"
           f"  {', '.join(ouvertes)}\n"
           "`-p 18080:80` publishes on ALL interfaces: the publication address "
           "is optional, and its default is the most open one. Name it.",
        fr=f"`{VITRINE}` est publiée en dehors de {LOOPBACK} :\n"
           f"  {', '.join(ouvertes)}\n"
           "`-p 18080:80` publie sur TOUTES les interfaces : l'adresse de "
           "publication est optionnelle, et son défaut est le plus ouvert. "
           "Nommez-la.",
    )
    assert any(p == f"{LOOPBACK}:{PORT_VITRINE}" for p in publications), message(
        en=f"`{VITRINE}` is published on {LOOPBACK}, but not on port "
           f"{PORT_VITRINE}:\n  {', '.join(publications)}",
        fr=f"`{VITRINE}` est publiée sur {LOOPBACK}, mais pas sur le port "
           f"{PORT_VITRINE} :\n  {', '.join(publications)}",
    )
    assert _repond(host, LOOPBACK, PORT_VITRINE), message(
        en=f"`{VITRINE}` is published on {LOOPBACK}:{PORT_VITRINE} but answers "
           "nothing there.\n"
           "Publishing is not serving: a container recreated without its "
           "listener publishes a port that leads nowhere. Relaunch it from the "
           "image the setup built, which carries the listener.",
        fr=f"`{VITRINE}` est publiée sur {LOOPBACK}:{PORT_VITRINE} mais n'y "
           "répond rien.\n"
           "Publier n'est pas servir : un conteneur recréé sans son écouteur "
           "publie un port qui ne mène nulle part. Relancez-le depuis l'image "
           "que le setup a construite, qui porte l'écouteur.",
    )


def test_la_vitrine_n_est_plus_joignable_depuis_le_reseau(host, routable) -> None:
    """La conséquence observable, et la seule qui compte vraiment.

    Le contrôle précédent lit ce que le moteur DÉCLARE ; celui-ci éprouve ce
    que la machine FAIT. Les deux peuvent diverger, et c'est ce qui rend ce
    contrôle utile : une règle de pare-feu ou un second conteneur publié sur le
    même port changerait le résultat sans changer la déclaration.
    """
    _tourne(host, VITRINE)
    assert not _repond(host, routable, PORT_VITRINE), message(
        en=f"`{VITRINE}` still answers on {routable}:{PORT_VITRINE}, which is "
           "the machine's routable address.\n"
           "Anything able to reach this machine reaches the service. That is "
           "exactly what publishing on the loopback alone prevents.",
        fr=f"`{VITRINE}` répond encore sur {routable}:{PORT_VITRINE}, qui est "
           "l'adresse routable de la machine.\n"
           "Tout ce qui atteint cette machine atteint le service. C'est "
           "précisément ce qu'une publication sur le seul loopback empêche.",
    )


def test_l_annexe_est_publiee_sur_la_seule_adresse_routable(host, routable) -> None:
    """La troisième posture : publier sur UNE interface, ni toutes ni aucune.

    C'est le cas réel qu'on oublie : un service d'administration qu'on veut
    joindre depuis le réseau, mais pas depuis tout ce qui tourne sur la
    machine. Il se mesure dans les deux sens, parce qu'une publication sur
    toutes les interfaces satisferait le premier sens seul.
    """
    _tourne(host, ANNEXE)
    publications = _publication(host, ANNEXE)
    assert publications, message(
        en=f"`{ANNEXE}` publishes nothing. It must be published on {routable} "
           f"and port {PORT_ANNEXE}, and only there.",
        fr=f"`{ANNEXE}` ne publie rien. Elle doit être publiée sur {routable} "
           f"et le port {PORT_ANNEXE}, et là seulement.",
    )
    assert any(p == f"{routable}:{PORT_ANNEXE}" for p in publications), message(
        en=f"`{ANNEXE}` is not published on {routable}:{PORT_ANNEXE}:\n"
           f"  {', '.join(publications)}",
        fr=f"`{ANNEXE}` n'est pas publiée sur {routable}:{PORT_ANNEXE} :\n"
           f"  {', '.join(publications)}",
    )
    assert _repond(host, routable, PORT_ANNEXE), message(
        en=f"`{ANNEXE}` is published on {routable}:{PORT_ANNEXE} but answers "
           "nothing there. Relaunch it from the image the setup built, which "
           "carries the listener.",
        fr=f"`{ANNEXE}` est publiée sur {routable}:{PORT_ANNEXE} mais n'y "
           "répond rien. Relancez-la depuis l'image que le setup a construite, "
           "qui porte l'écouteur.",
    )
    assert not _repond(host, LOOPBACK, PORT_ANNEXE), message(
        en=f"`{ANNEXE}` also answers on {LOOPBACK}:{PORT_ANNEXE}, so it is "
           "published on all interfaces rather than on the routable one alone.\n"
           "Naming the address restricts the publication to it: that is the "
           "whole point of naming it.",
        fr=f"`{ANNEXE}` répond aussi sur {LOOPBACK}:{PORT_ANNEXE} : elle est "
           "donc publiée sur toutes les interfaces, et non sur la seule adresse "
           "routable.\n"
           "Nommer l'adresse restreint la publication à celle-ci : c'est tout "
           "l'intérêt de la nommer.",
    )


def test_le_service_interne_ne_publie_rien_et_reste_joignable(host) -> None:
    """La posture qu'on oublie : ne rien publier du tout.

    Un service que seuls les autres conteneurs doivent joindre n'a aucune
    raison d'être publié. Publier est le réflexe, et c'est ce réflexe qui
    expose les bases de données.

    Les deux assertions sont indissociables : ne rien publier est trivial en
    détruisant le conteneur, et la seconde vérifie qu'il sert toujours ceux
    qui en ont besoin. C'est pourquoi elles ne font qu'un contrôle.
    """
    _tourne(host, INTERNE)
    _tourne(host, VITRINE)
    publications = _publication(host, INTERNE)
    assert not publications, message(
        en=f"`{INTERNE}` still publishes a port:\n  {', '.join(publications)}\n"
           "A service only other containers need has no reason to be published. "
           "Publishing is the reflex, and that reflex is what exposes "
           "databases.",
        fr=f"`{INTERNE}` publie encore un port :\n  {', '.join(publications)}\n"
           "Un service que seuls les autres conteneurs doivent joindre n'a "
           "aucune raison d'être publié. Publier est le réflexe, et c'est ce "
           "réflexe qui expose les bases de données.",
    )

    res = host.run(
        "docker container inspect %s --format %s",
        INTERNE, "{{.NetworkSettings.IPAddress}}",
    )
    adresse = res.stdout.strip()
    assert adresse, message(
        en=f"`{INTERNE}` has no address on the network: it cannot be reached by "
           "the other containers either.",
        fr=f"`{INTERNE}` n'a aucune adresse sur le réseau : il n'est pas non "
           "plus joignable par les autres conteneurs.",
    )

    joint = False
    for _ in range(4):
        essai = host.run("docker exec %s nc -w 3 %s 80", VITRINE, adresse)
        if "jeton=" in essai.stdout:
            joint = True
            break
    assert joint, message(
        en=f"`{INTERNE}` publishes nothing, but `{VITRINE}` cannot reach it at "
           f"{adresse}:80 either.\n"
           "Not publishing is not the same as not serving: containers of the "
           "same network reach each other without any published port. Check "
           f"that `{INTERNE}` is still running its listener.",
        fr=f"`{INTERNE}` ne publie rien, mais `{VITRINE}` ne le joint pas non "
           f"plus en {adresse}:80.\n"
           "Ne pas publier n'est pas ne plus servir : les conteneurs d'un même "
           "réseau se joignent sans aucun port publié. Vérifiez que "
           f"`{INTERNE}` fait toujours tourner son écouteur.",
    )
