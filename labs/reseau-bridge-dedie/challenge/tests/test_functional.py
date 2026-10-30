"""Tests fonctionnels du lab reseau-bridge-dedie : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un réseau dédié apporte DEUX choses, et non une : la
résolution des noms entre ses membres, et l'isolation de ceux qui n'en sont pas.
Le lab précédent faisait constater l'absence de DNS sur le réseau par défaut ;
celui-ci fait corriger la situation et mesure les deux effets.

AUCUN FORMULAIRE ICI, ET C'EST VOULU. Les deux labs précédents faisaient écrire
des réponses ; celui-ci fait FABRIQUER. Les quatre contrôles lisent l'état du
moteur, pas un fichier : un réseau existe ou non, un conteneur en est membre ou
non, un nom se résout ou non, une connexion aboutit ou non.

L'ÉTAT DE DÉPART EST JOIGNABLE, ET C'EST LE POINT DÉLICAT. Au départ, les trois
conteneurs sont sur le réseau par défaut, donc `tiers` joint `arriere` : le
contrôle d'isolation est FAUX avant tout travail, ce que `valider-labs.py`
exige. Un setup qui aurait déjà séparé les conteneurs rendrait ce contrôle vrai
sans travail, et ce ne serait plus un test mais une hypothèse du setup.

LE PIÈGE DU LAB, ET IL EST FRÉQUENT EN VRAI. Attacher un conteneur à un réseau
ne le retire pas de l'autre : un conteneur peut être sur DEUX réseaux à la
fois, et il garde alors sa joignabilité depuis le réseau par défaut. Le
deuxième contrôle exige donc les deux gestes, et son message nomme celui qui
manque.

POURQUOI LE TÉMOIN EST PROTÉGÉ. Le quatrième contrôle serait aussi vrai si
`tiers` ou `arriere` disparaissaient. Un préalable commun vérifie donc que les
trois conteneurs tournent, et le troisième contrôle prouve par ailleurs que
`arriere` est vivant et répond. Sans cela, détruire le témoin vaudrait réussir.

MESURÉ AVANT D'ÊTRE ÉCRIT, sur docker.lab le 2026-10-30 : au départ `tiers`
obtient le jeton et `avant` ne résout pas le nom ; après le travail
`nslookup arriere` rend son adresse sur le réseau dédié, la connexion par nom
aboutit, et `tiers` ne joint plus rien.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

CLIENT = "avant"
ECOUTEUR = "arriere"
TEMOIN = "tiers"
PORT = 8080
RESEAU_DEMANDE = "atelier"
SOUS_RESEAU_DEMANDE = "172.28.5.0/24"
RESEAU_PAR_DEFAUT = "bridge"

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


def _les_trois_conteneurs_tournent(host) -> None:
    """Le préalable des quatre contrôles, et la protection du témoin.

    Sans lui, détruire `tiers` ferait passer le contrôle d'isolation : il n'y
    aurait plus personne pour échouer à joindre. Un contrôle qu'on satisfait en
    retirant le sujet ne mesure rien.
    """
    for nom in (ECOUTEUR, CLIENT, TEMOIN):
        res = host.run(
            "docker container inspect %s --format %s", nom, "{{.State.Status}}"
        )
        if res.rc != 0:
            pytest.fail(message(
                en=f"container `{nom}` does not exist any more. All three are "
                   "needed: `tiers` in particular is the isolation witness, and "
                   "removing it would prove nothing. Replay the lab with "
                   "`dsoxlab reset`.",
                fr=f"le conteneur `{nom}` n'existe plus. Les trois sont "
                   "nécessaires : `tiers` est le témoin de l'isolation, et le "
                   "supprimer ne prouverait rien. Rejouez le lab avec "
                   "`dsoxlab reset`.",
            ))
        etat = res.stdout.strip()
        if etat != "running":
            pytest.fail(message(
                en=f"container `{nom}` is in state `{etat}`, not `running`. A "
                   "stopped container has no address and answers nothing.",
                fr=f"le conteneur `{nom}` est dans l'état `{etat}`, pas "
                   "`running`. Un conteneur arrêté n'a plus d'adresse et ne "
                   "répond rien.",
            ))


def _reseaux_du_conteneur(host, nom: str) -> set[str]:
    """Les réseaux dont un conteneur est membre, selon le moteur."""
    res = host.run(
        "docker container inspect %s --format %s",
        nom, "{{range $r, $v := .NetworkSettings.Networks}}{{println $r}}{{end}}",
    )
    if res.rc != 0:
        return set()
    return {ligne.strip() for ligne in res.stdout.splitlines() if ligne.strip()}


def _adresse_sur(host, nom: str, reseau: str) -> str:
    """L'adresse d'un conteneur sur un réseau donné."""
    res = host.run(
        "docker container inspect %s --format %s",
        nom,
        '{{(index .NetworkSettings.Networks "' + reseau + '").IPAddress}}',
    )
    return res.stdout.strip() if res.rc == 0 else ""


def _adresse_courante(host, nom: str) -> str:
    """La première adresse d'un conteneur, quel que soit son réseau.

    Utilisée par le contrôle d'isolation, qui doit joindre `arriere` là où il
    est MAINTENANT : sur le réseau par défaut avant le travail, sur le réseau
    dédié après.
    """
    res = host.run(
        "docker container inspect %s --format %s",
        nom,
        "{{range .NetworkSettings.Networks}}{{println .IPAddress}}{{end}}",
    )
    if res.rc != 0:
        return ""
    for ligne in res.stdout.splitlines():
        if ligne.strip():
            return ligne.strip()
    return ""


def test_le_reseau_demande_existe_avec_son_sous_reseau(host) -> None:
    """Un réseau à soi, et dont on a choisi le plan d'adressage.

    Le sous-réseau est imposé parce que c'est le geste réel : en production, un
    réseau de conteneurs doit cohabiter avec le reste sans collision, et cela
    se décide à la création. Un réseau créé sans `--subnet` reçoit un plan que
    le moteur choisit, ce qui est précisément ce qu'on veut éviter.
    """
    _les_trois_conteneurs_tournent(host)
    res = host.run("docker network inspect %s --format %s",
                   RESEAU_DEMANDE, "{{(index .IPAM.Config 0).Subnet}}")
    assert res.rc == 0, message(
        en=f"no network named `{RESEAU_DEMANDE}` exists: {res.stderr.strip()}\n"
           "It has to be created, with the requested subnet "
           f"{SOUS_RESEAU_DEMANDE}.",
        fr=f"aucun réseau nommé `{RESEAU_DEMANDE}` n'existe : "
           f"{res.stderr.strip()}\n"
           "Il faut le créer, avec le sous-réseau demandé "
           f"{SOUS_RESEAU_DEMANDE}.",
    )
    sous_reseau = res.stdout.strip()
    assert sous_reseau == SOUS_RESEAU_DEMANDE, message(
        en=f"`{RESEAU_DEMANDE}` carries the subnet {sous_reseau}, not "
           f"{SOUS_RESEAU_DEMANDE}.\n"
           "A network created without declaring its subnet gets one the engine "
           "picks. Here the plan is imposed, as it is in production, so that "
           "the network can coexist with the rest without collision.",
        fr=f"`{RESEAU_DEMANDE}` porte le sous-réseau {sous_reseau}, pas "
           f"{SOUS_RESEAU_DEMANDE}.\n"
           "Un réseau créé sans déclarer son sous-réseau en reçoit un que le "
           "moteur choisit. Ici le plan est imposé, comme il l'est en "
           "production, pour que le réseau cohabite avec le reste sans "
           "collision.",
    )


def test_les_deux_conteneurs_ont_change_de_reseau(host) -> None:
    """Attachés au réseau dédié, et retirés du réseau par défaut.

    Les deux gestes, parce qu'ils sont distincts : attacher un conteneur à un
    réseau ne le retire pas de l'autre. Un conteneur sur DEUX réseaux garde sa
    joignabilité depuis le réseau par défaut, et l'isolation visée n'existe
    pas. C'est le piège du lab, et il est fréquent en vrai.
    """
    _les_trois_conteneurs_tournent(host)
    for nom in (CLIENT, ECOUTEUR):
        reseaux = _reseaux_du_conteneur(host, nom)
        assert RESEAU_DEMANDE in reseaux, message(
            en=f"`{nom}` is not attached to `{RESEAU_DEMANDE}`.\n"
               f"  it is on: {', '.join(sorted(reseaux)) or '(nothing)'}",
            fr=f"`{nom}` n'est pas attaché à `{RESEAU_DEMANDE}`.\n"
               f"  il est sur : {', '.join(sorted(reseaux)) or '(rien)'}",
        )
        assert RESEAU_PAR_DEFAUT not in reseaux, message(
            en=f"`{nom}` is attached to `{RESEAU_DEMANDE}` but is STILL on "
               f"`{RESEAU_PAR_DEFAUT}`.\n"
               "Attaching a container to a network does not remove it from the "
               "other one: it is on both, and it stays reachable from the "
               "default network. The two moves are distinct.",
            fr=f"`{nom}` est attaché à `{RESEAU_DEMANDE}` mais il est ENCORE "
               f"sur `{RESEAU_PAR_DEFAUT}`.\n"
               "Attacher un conteneur à un réseau ne le retire pas de l'autre : "
               "il est sur les deux, et il reste joignable depuis le réseau par "
               "défaut. Les deux gestes sont distincts.",
        )


def test_le_nom_se_resout_sur_le_reseau_dedie(host) -> None:
    """La leçon du lab, et ce que le réseau par défaut refusait.

    Un réseau dédié embarque un résolveur qui connaît ses membres par leur nom.
    Le contrôle ne se contente pas d'une résolution qui aboutit : il vérifie
    que le nom rend bien l'adresse du conteneur SUR CE RÉSEAU, ce qui écarte
    une résolution qui pointerait ailleurs.
    """
    _les_trois_conteneurs_tournent(host)
    attendue = _adresse_sur(host, ECOUTEUR, RESEAU_DEMANDE)
    if not attendue:
        pytest.fail(message(
            en=f"`{ECOUTEUR}` has no address on `{RESEAU_DEMANDE}`: it is not "
               "attached to it yet, so nothing can resolve its name there.",
            fr=f"`{ECOUTEUR}` n'a aucune adresse sur `{RESEAU_DEMANDE}` : il "
               "n'y est pas encore attaché, donc rien ne peut y résoudre son "
               "nom.",
        ))

    res = host.run("docker exec %s nslookup %s", CLIENT, ECOUTEUR)
    assert res.rc == 0, message(
        en=f"from `{CLIENT}`, the name `{ECOUTEUR}` does not resolve: "
           f"{(res.stdout + res.stderr).strip()[:200]}\n"
           "A dedicated network carries a resolver that knows its members by "
           "name. Both containers must be on it.",
        fr=f"depuis `{CLIENT}`, le nom `{ECOUTEUR}` ne se résout pas : "
           f"{(res.stdout + res.stderr).strip()[:200]}\n"
           "Un réseau dédié embarque un résolveur qui connaît ses membres par "
           "leur nom. Les deux conteneurs doivent y être.",
    )
    assert attendue in res.stdout, message(
        en=f"the name `{ECOUTEUR}` resolves, but not to the address it carries "
           f"on `{RESEAU_DEMANDE}` ({attendue}).\n"
           f"  answer: {res.stdout.strip()[:200]}",
        fr=f"le nom `{ECOUTEUR}` se résout, mais pas vers l'adresse qu'il porte "
           f"sur `{RESEAU_DEMANDE}` ({attendue}).\n"
           f"  réponse : {res.stdout.strip()[:200]}",
    )

    # La résolution ne prouve pas la joignabilité : un résolveur peut répondre
    # pour une adresse qu'aucune route n'atteint. La connexion le prouve, et
    # elle est faite PAR LE NOM, qui est le geste du lab.
    for _ in range(5):
        joint = host.run("docker exec %s nc -w 3 %s %s", CLIENT, ECOUTEUR, str(PORT))
        if "jeton=" in joint.stdout:
            return
    pytest.fail(message(
        en=f"`{CLIENT}` resolves `{ECOUTEUR}` but cannot reach it by name on "
           f"port {PORT}. Resolving is not reaching: a resolver can answer for "
           "an address no route reaches.",
        fr=f"`{CLIENT}` résout `{ECOUTEUR}` mais ne le joint pas par son nom "
           f"sur le port {PORT}. Résoudre n'est pas joindre : un résolveur peut "
           "répondre pour une adresse qu'aucune route n'atteint.",
    ))


def test_le_temoin_reste_sur_le_reseau_par_defaut_est_isole(host) -> None:
    """L'autre moitié de la leçon : un réseau dédié isole.

    `tiers` n'a pas bougé, et c'est le point : ce n'est pas lui qu'on a
    changé, c'est `arriere` qui a quitté le réseau qu'ils partageaient. Au
    départ il obtenait le jeton, donc ce contrôle était faux : c'est bien le
    travail de l'apprenant qui le rend vrai.
    """
    _les_trois_conteneurs_tournent(host)
    reseaux_temoin = _reseaux_du_conteneur(host, TEMOIN)
    assert reseaux_temoin == {RESEAU_PAR_DEFAUT}, message(
        en=f"`{TEMOIN}` is the isolation witness and must not be touched. It "
           f"should be on `{RESEAU_PAR_DEFAUT}` alone.\n"
           f"  it is on: {', '.join(sorted(reseaux_temoin)) or '(nothing)'}\n"
           "Moving it would make this check pass without proving anything: what "
           f"has to change is `{ECOUTEUR}`'s network, not the witness's.",
        fr=f"`{TEMOIN}` est le témoin de l'isolation et ne doit pas être "
           f"touché. Il doit être sur `{RESEAU_PAR_DEFAUT}` et lui seul.\n"
           f"  il est sur : {', '.join(sorted(reseaux_temoin)) or '(rien)'}\n"
           "Le déplacer ferait passer ce contrôle sans rien prouver : ce qui "
           f"doit changer est le réseau de `{ECOUTEUR}`, pas celui du témoin.",
    )

    adresse = _adresse_courante(host, ECOUTEUR)
    if not adresse:
        pytest.skip(message(
            en=f"the engine reports no address for `{ECOUTEUR}`: nothing to "
               "test reachability against",
            fr=f"le moteur ne donne aucune adresse à `{ECOUTEUR}` : il n'y a "
               "rien contre quoi éprouver la joignabilité",
        ))

    res = host.run("docker exec %s nc -w 3 %s %s", TEMOIN, adresse, str(PORT))
    assert "jeton=" not in res.stdout, message(
        en=f"`{TEMOIN}` still reaches `{ECOUTEUR}` at {adresse}, and gets its "
           "token.\n"
           f"A dedicated network also isolates: as long as `{ECOUTEUR}` stays "
           "on the default network, everything on that network reaches it. "
           "Check that it has really been detached, and not simply attached to "
           "a second network.",
        fr=f"`{TEMOIN}` joint encore `{ECOUTEUR}` en {adresse}, et obtient son "
           "jeton.\n"
           f"Un réseau dédié isole aussi : tant que `{ECOUTEUR}` reste sur le "
           "réseau par défaut, tout ce qui s'y trouve l'atteint. Vérifiez qu'il "
           "en a réellement été détaché, et pas seulement attaché à un second "
           "réseau.",
    )
