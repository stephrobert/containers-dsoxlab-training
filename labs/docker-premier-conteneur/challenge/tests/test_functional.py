"""Tests fonctionnels du lab docker-premier-conteneur : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Les trois verbes dont tout le reste dépend, et l'idée
qu'ils ne recouvrent pas : lancer, arrêter, supprimer. C'est le lab d'entrée du
catalogue, et il se joue en moins d'une minute : rien à construire, aucune
image à tirer pendant le travail.

LE POINT QUI SURPREND, ET QUI EST NOTÉ SÉPARÉMENT. Un conteneur arrêté
**existe encore**. C'est pour cela que le setup en pose deux, dans deux états
différents : un conteneur arrêté se distingue d'un conteneur absent, et un lab
qui ne noterait qu'un seul des deux gestes laisserait passer la confusion
exacte qu'il doit lever.

CE QU'ON NE MESURE PAS, ET POURQUOI. Jamais la commande tapée. `docker stop`,
un signal envoyé au processus, `docker kill` sur un conteneur qui ne gère pas
ses signaux : les trois aboutissent à un conteneur arrêté. De même, un
conteneur peut être lancé de dix façons. On interroge donc le moteur sur
l'ÉTAT, et un apprenant qui y arrive autrement a réussi autant.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true`,
donc tout ce qui suit est déjà élevé : les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

A_LANCER = "premier"
A_ARRETER = "vitrine"
A_SUPPRIMER = "rebut"
LIGNE_ATTENDUE = "premier-est-la"

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui
    les lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier. `pytest --collect-only` l'affiche avec un paramètre `[local]`
    quand l'erreur est commise.
    """
    return lab_host(TARGET_HOST)


def _etats(host) -> dict[str, str]:
    """Les conteneurs de la machine et leur état, par nom.

    Un seul appel au moteur pour les quatre contrôles : interroger un conteneur
    à la fois multiplierait les connexions sans rien apprendre de plus.
    """
    res = host.run("docker ps -a --format '{{.Names}} {{.State}}'")
    if res.rc != 0:
        pytest.fail(message(
            en=f"the engine does not answer `docker ps`: {res.stderr.strip()}. "
               "This lab assumes a working engine, which is the subject of "
               "docker-verifier-son-moteur.",
            fr=f"le moteur ne répond pas à `docker ps` : {res.stderr.strip()}. "
               "Ce lab suppose un moteur en état, ce qui est le sujet de "
               "docker-verifier-son-moteur.",
        ))
    etats = {}
    for ligne in res.stdout.splitlines():
        morceaux = ligne.split()
        if len(morceaux) >= 2:
            etats[morceaux[0]] = morceaux[1].lower()
    return etats


def test_un_conteneur_a_ete_lance_et_tourne(host) -> None:
    """Premier geste : lancer, et laisser tourner.

    « Lancé » ne suffit pas : un conteneur qui s'arrête aussitôt a bien été
    lancé, et ne sert à rien. C'est l'état `running` qui est noté.
    """
    etats = _etats(host)
    assert A_LANCER in etats, message(
        en=f"no container named `{A_LANCER}` exists. The image "
           "`lab-base:1.0` is already on the machine: nothing to pull, nothing "
           f"to build.\n  containers present: {', '.join(sorted(etats)) or 'none'}",
        fr=f"aucun conteneur nommé `{A_LANCER}` n'existe. L'image "
           "`lab-base:1.0` est déjà sur la machine : rien à tirer, rien à "
           f"construire.\n  conteneurs présents : {', '.join(sorted(etats)) or 'aucun'}",
    )
    assert etats[A_LANCER] == "running", message(
        en=f"`{A_LANCER}` exists but is not running (state: {etats[A_LANCER]}). "
           "A container whose command finishes stops immediately: give it "
           "something that keeps it alive.",
        fr=f"`{A_LANCER}` existe mais ne tourne pas (état : {etats[A_LANCER]}). "
           "Un conteneur dont la commande se termine s'arrête aussitôt : "
           "donnez-lui de quoi rester en vie.",
    )


def test_les_journaux_du_conteneur_portent_la_ligne_demandee(host) -> None:
    """Le conteneur a reçu une commande, et on le lit dans ses journaux.

    C'est ce qui distingue « j'ai lancé une image » de « j'ai lancé une image
    EN LUI DISANT quoi faire ». Les journaux sont la sortie du processus
    principal : rien d'autre ne les remplit.
    """
    etats = _etats(host)
    if A_LANCER not in etats:
        pytest.skip(message(
            en=f"`{A_LANCER}` does not exist yet: the previous check says so",
            fr=f"`{A_LANCER}` n'existe pas encore : le contrôle précédent le dit",
        ))
    res = host.run("docker logs %s", A_LANCER)
    assert res.rc == 0, message(
        en=f"cannot read the logs of `{A_LANCER}`: {res.stderr.strip()}",
        fr=f"impossible de lire les journaux de `{A_LANCER}` : {res.stderr.strip()}",
    )
    sortie = res.stdout + res.stderr
    assert LIGNE_ATTENDUE in sortie, message(
        en=f"the logs of `{A_LANCER}` do not carry the line `{LIGNE_ATTENDUE}`.\n"
           f"  what they carry: {sortie.strip()[:200] or '(nothing)'}\n"
           "The logs are the output of the container's main process: what you "
           "ask it to print ends up there.",
        fr=f"les journaux de `{A_LANCER}` ne portent pas la ligne "
           f"`{LIGNE_ATTENDUE}`.\n"
           f"  ce qu'ils portent : {sortie.strip()[:200] or '(rien)'}\n"
           "Les journaux sont la sortie du processus principal du conteneur : "
           "ce que vous lui demandez d'afficher s'y retrouve.",
    )


def test_le_conteneur_en_service_a_ete_arrete(host) -> None:
    """Deuxième geste : arrêter, ce qui n'est pas supprimer.

    Le message distingue les deux fautes possibles, parce qu'elles appellent
    des gestes opposés : un conteneur encore en marche n'a pas été arrêté, un
    conteneur disparu a été supprimé par excès de zèle.
    """
    etats = _etats(host)
    assert A_ARRETER in etats, message(
        en=f"`{A_ARRETER}` no longer exists: it was asked to be STOPPED, not "
           "removed. A stopped container still exists, and that is the point "
           "of this lab.",
        fr=f"`{A_ARRETER}` n'existe plus : il était demandé de l'ARRÊTER, pas de "
           "le supprimer. Un conteneur arrêté existe encore, et c'est tout le "
           "point de ce lab.",
    )
    assert etats[A_ARRETER] != "running", message(
        en=f"`{A_ARRETER}` is still running. Stopping it ends its process "
           "while keeping the container, with its logs and its name.",
        fr=f"`{A_ARRETER}` tourne toujours. L'arrêter met fin à son processus "
           "tout en conservant le conteneur, ses journaux et son nom.",
    )


def test_le_conteneur_au_rebut_a_ete_supprime(host) -> None:
    """Troisième geste : supprimer, ce qui fait disparaître le nom.

    Le nom libéré est la conséquence observable, et c'est aussi pourquoi un
    conteneur arrêté gêne : il garde son nom, et un second conteneur ne peut
    pas le reprendre.
    """
    etats = _etats(host)
    assert A_SUPPRIMER not in etats, message(
        en=f"`{A_SUPPRIMER}` still exists (state: {etats[A_SUPPRIMER]}). "
           "Stopping a container does not remove it: as long as it exists, it "
           "keeps its name, and no other container can take it.",
        fr=f"`{A_SUPPRIMER}` existe toujours (état : {etats[A_SUPPRIMER]}). "
           "Arrêter un conteneur ne le supprime pas : tant qu'il existe, il "
           "garde son nom, et aucun autre conteneur ne peut le reprendre.",
    )
