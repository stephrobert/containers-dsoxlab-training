"""Tests fonctionnels du lab images-healthcheck : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un conteneur « up » ne dit rien du service, et qu'une
sonde qui regarde le PROCESSUS ne dit rien de plus.

MESURÉ SUR docker.lab LE 2026-10-30 :

| Situation | Ce que le moteur déclare |
| aucune sonde | **aucun** état de santé, le champ n'existe pas |
| sonde sur la fraîcheur du pouls, service sain | `healthy` en 2 s |
| le même, service muet et processus vivant | `unhealthy` en 8 s |
| le même, service rétabli | retour à `healthy` en 2 s |
| sonde sur le PROCESSUS, service muet | **`healthy`**, pouls rance |

ET UN CONTENEUR `unhealthy` RESTE EN MARCHE : le moteur ne l'arrête pas, ne le
relance pas et ne prévient personne. Une sonde informe ; elle ne répare rien.
Aucun contrôle n'attend donc un arrêt, ce qui mesurerait une croyance.

LES DÉLAIS D'ATTENTE SONT CALCULÉS, et non écrits : chaque contrôle lit les
bornes que l'image déclare et en dérive le temps qu'il accorde. Une valeur en
dur refuserait une sonde prudente, ou accepterait une sonde qui ne conclut
jamais.

AUCUNE VALEUR N'EST ÉCRITE EN DUR. Le jeton est tiré par le setup, et les
bornes sont celles de l'image.
"""

from __future__ import annotations

import time

import pytest

from conftest import lab_host, message

IMAGE = "appli:surveillee"
CONTENEUR = "service-surveille"
ATELIER = "/opt/lab-sante"
CONTEXTE = f"{ATELIER}/appli"
SERVICE = f"{CONTEXTE}/servir.sh"
MUET = "/tmp/muet"  # noqa: S108  chemin DANS le conteneur, pas sur l'hôte
POULS = "/var/run/pouls"

# Le plafond d'attente par défaut, quand les bornes de l'image sont illisibles.
# Mesuré le 2026-10-30 : 8 s suffisent avec un intervalle de 2 s et deux
# tentatives. Soixante secondes laissent donc place à une sonde bien plus
# prudente, sans faire attendre indéfiniment.
ATTENTE_PLANCHER_S = 60
PAS_S = 2

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


def _champ(host, format_go: str, cible: str = CONTENEUR) -> str:
    res = host.run("docker inspect %s --format %s", cible, format_go)
    return res.stdout.strip() if res.rc == 0 else ""


def _sante(host) -> str:
    """L'état de santé du conteneur, ou une chaîne vide s'il n'en a aucun.

    Le format tolère l'absence du champ : une image sans sonde n'a PAS de
    section de santé, et un format qui la déréférencerait rendrait une erreur
    au lieu d'une réponse.
    """
    return _champ(
        host, "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{end}}"
    )


def _bornes(host) -> dict[str, int]:
    """Les bornes que l'IMAGE déclare, en secondes.

    LES DURÉES SE LISENT PAR `.Seconds`, ET NON PAR LEUR FORME BRUTE. Mesuré le
    2026-10-30 : le moteur rend `5s`, et `1m30s` pour quatre-vingt-dix
    secondes. Un premier jet supposait des nanosecondes entières ; `int("2s")`
    levait, la fonction rendait un dictionnaire vide, et le premier contrôle
    annonçait « aucune sonde déclarée » sur une image qui en portait une. Le
    message accusait donc l'inverse de ce qui était vrai.

    `.Seconds` est la méthode que Go expose sur une durée : il n'y a pas de
    `1m30s` à parser, donc pas de parseur à se tromper.

    Un format par champ évite de dépendre de l'ordre d'un rendu composite, et
    l'absence de sonde rend un dictionnaire vide plutôt qu'une erreur.
    """
    if not _champ(host, "{{if .Config.Healthcheck}}oui{{end}}", IMAGE):
        return {}
    bornes = {}
    for nom, champ in (
        ("interval", "Interval.Seconds"),
        ("timeout", "Timeout.Seconds"),
        ("start", "StartPeriod.Seconds"),
        ("retries", "Retries"),
    ):
        brut = _champ(host, "{{.Config.Healthcheck." + champ + "}}", IMAGE)
        try:
            bornes[nom] = int(float(brut))
        except ValueError:
            continue
    return bornes


def _attente_accordee(host) -> int:
    """Le temps accordé à une sonde pour conclure, DÉRIVÉ de ses bornes.

    Une sonde conclut au pire après sa période de démarrage, puis autant
    d'intervalles que de tentatives, chacun pouvant aller jusqu'à son délai
    d'attente. On ajoute un intervalle de marge, et on ne descend jamais sous
    le plancher : une sonde très rapide ne doit pas être jugée sur un hasard de
    synchronisation.
    """
    b = _bornes(host)
    if not b:
        return ATTENTE_PLANCHER_S
    interval = b.get("interval", 30) or 30
    retries = b.get("retries", 3) or 3
    calcule = b.get("start", 0) + (retries + 1) * (interval + b.get("timeout", 0))
    return max(ATTENTE_PLANCHER_S, calcule)


def _attendre(host, attendu: str, limite_s: int) -> str:
    fin = time.monotonic() + limite_s
    etat = _sante(host)
    while etat != attendu and time.monotonic() < fin:
        time.sleep(PAS_S)
        etat = _sante(host)
    return etat


def _conteneur_absent(host) -> bool:
    return host.run("docker inspect %s", CONTENEUR).rc != 0


def _exiger_conteneur(host) -> None:
    if _conteneur_absent(host):
        pytest.fail(message(
            en=f"container `{CONTENEUR}` does not exist. Building the image "
               f"and running it under that name is part of the mission: the "
               f"context is in {CONTEXTE}.",
            fr=f"le conteneur `{CONTENEUR}` n'existe pas. Construire l'image et "
               f"la lancer sous ce nom fait partie de la mission : le contexte "
               f"est dans {CONTEXTE}.",
        ))


def test_le_conteneur_atteint_l_etat_sain(host) -> None:
    """Le service travaille, et le moteur le dit.

    LE PREMIER ÉCART EST L'ABSENCE DE SONDE, et son message est distinct : un
    conteneur sans sonde n'a pas un état de santé « inconnu », il n'a aucun
    champ de santé. Confondre les deux fait chercher une sonde qui marche mal
    là où il n'y en a aucune.
    """
    _exiger_conteneur(host)

    bornes = _bornes(host)
    assert bornes, message(
        en=f"image `{IMAGE}` declares no probe at all.\n"
           "Its inspection carries no health section: the engine knows nothing "
           "about this service, and « up » only means that its process exists.",
        fr=f"l'image `{IMAGE}` ne déclare aucune sonde.\n"
           "Son inspection ne porte aucune section de santé : le moteur ne sait "
           "rien de ce service, et « up » ne veut dire que « son processus "
           "existe ».",
    )

    # Le service doit battre son pouls : sans cela, c'est le service qui est en
    # panne, et la sonde a raison de le dire.
    host.run("docker exec %s rm -f %s", CONTENEUR, MUET)
    etat = _attendre(host, "healthy", _attente_accordee(host))
    assert etat == "healthy", message(
        en=f"`{CONTENEUR}` does not reach the healthy state "
           f"(currently `{etat or 'none'}`), with the probe's own bounds "
           f"granted: {bornes}.\n"
           f"The service refreshes {POULS} every second. A probe that never "
           "concludes healthy on a working service is a probe that measures "
           "something else.",
        fr=f"`{CONTENEUR}` n'atteint pas l'état sain (actuellement "
           f"`{etat or 'aucun'}`), ses propres bornes accordées : {bornes}.\n"
           f"Le service rafraîchit {POULS} chaque seconde. Une sonde qui ne "
           "conclut jamais au sain sur un service qui travaille mesure autre "
           "chose.",
    )


def test_le_conteneur_passe_malade_quand_le_service_se_tait(host) -> None:
    """Le cœur du lab : le processus vit, le service ne travaille plus.

    MESURÉ LE 2026-10-30 : une sonde sur le processus déclare `healthy` alors
    que le pouls est rance, et le processus ne meurt jamais. C'est la panne la
    plus fréquente des deux, et c'est celle qu'une supervision par processus ne
    voit pas.

    LE CONTRÔLE REMET LE SERVICE EN MARCHE à la fin, quoi qu'il arrive : il ne
    laisse pas derrière lui un conteneur muet que le contrôle suivant prendrait
    pour l'état de l'apprenant.
    """
    _exiger_conteneur(host)
    if not _bornes(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` declares no probe: the first check says so.",
            fr=f"l'image `{IMAGE}` ne déclare aucune sonde : le premier "
               "contrôle le dit.",
        ))

    host.run("docker exec %s touch %s", CONTENEUR, MUET)
    etat = _attendre(host, "unhealthy", _attente_accordee(host))
    vivant = host.run(
        "docker exec %s sh -c %s", CONTENEUR, "pgrep -f servir >/dev/null"
    ).rc == 0
    host.run("docker exec %s rm -f %s", CONTENEUR, MUET)

    assert etat == "unhealthy", message(
        en=f"the service is mute and `{CONTENEUR}` is still `{etat or 'none'}`."
           f"\n  process still alive: {'yes' if vivant else 'no'}\n"
           "A probe that watches the process sees nothing here, measured: it "
           "declares the service healthy while its pulse is stale. The process "
           "never dies. What has to be probed is the WORK, and the pulse in "
           f"{POULS} is its proof: its freshness, not its existence.",
        fr=f"le service est muet et `{CONTENEUR}` est toujours "
           f"`{etat or 'aucun'}`.\n"
           f"  processus toujours vivant : {'oui' if vivant else 'non'}\n"
           "Une sonde qui regarde le processus ne voit rien ici, c'est mesuré : "
           "elle déclare le service sain alors que son pouls est rance. Le "
           "processus ne meurt jamais. Ce qu'il faut sonder, c'est le TRAVAIL, "
           f"et le pouls de {POULS} en est la preuve : sa fraîcheur, pas son "
           "existence.",
    )


def test_le_conteneur_revient_sain_quand_le_service_repart(host) -> None:
    """Une sonde dit l'état courant, et non ce qu'elle a vu une fois.

    SANS CE CONTRÔLE, une sonde qui garde la trace de son premier échec
    passerait les deux précédents : elle conclurait au sain, puis au malade, et
    y resterait pour toujours. Un service qui repart doit être reconnu comme
    reparti, sans quoi la sonde ne sert qu'une fois.
    """
    _exiger_conteneur(host)
    if not _bornes(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` declares no probe: the first check says so.",
            fr=f"l'image `{IMAGE}` ne déclare aucune sonde : le premier "
               "contrôle le dit.",
        ))

    accordee = _attente_accordee(host)
    host.run("docker exec %s touch %s", CONTENEUR, MUET)
    malade = _attendre(host, "unhealthy", accordee)
    host.run("docker exec %s rm -f %s", CONTENEUR, MUET)
    revenu = _attendre(host, "healthy", accordee)

    assert malade == "unhealthy", message(
        en="the service was muted and the probe did not report it: the "
           "previous check says why.",
        fr="le service a été rendu muet et la sonde ne l'a pas dit : le "
           "contrôle précédent dit pourquoi.",
    )
    assert revenu == "healthy", message(
        en=f"the service is working again and `{CONTENEUR}` stays "
           f"`{revenu or 'none'}`.\n"
           "A probe reports the CURRENT state, not what it saw once. One that "
           "keeps a trace of its first failure, in a file or a flag, would pass "
           "the two previous checks and serve only once.",
        fr=f"le service travaille de nouveau et `{CONTENEUR}` reste "
           f"`{revenu or 'aucun'}`.\n"
           "Une sonde dit l'état COURANT, et non ce qu'elle a vu une fois. "
           "Celle qui garde la trace de son premier échec, dans un fichier ou "
           "un drapeau, passerait les deux contrôles précédents et ne servirait "
           "qu'une fois.",
    )


def test_les_bornes_declarees_sont_coherentes(host) -> None:
    """Les quatre bornes, et ce qu'une valeur par défaut coûte.

    TROIS EXIGENCES, chacune pour une raison mesurable :

    le DÉLAI D'ATTENTE sous l'INTERVALLE, sans quoi une sonde lente est encore
    en cours quand la suivante démarre, et le moteur les empile ;

    au moins DEUX TENTATIVES, sans quoi un seul hoquet, une seconde de charge,
    déclare un service malade ;

    une PÉRIODE DE DÉMARRAGE, sans quoi un service qui prend du temps à se
    préparer est déclaré malade avant d'avoir commencé. Mesuré sur ce lab : la
    sonde conclut dès la deuxième seconde, et sans période de démarrage elle
    aurait jugé un service qui n'avait pas encore écrit son premier pouls.
    """
    _exiger_conteneur(host)
    b = _bornes(host)
    assert b, message(
        en=f"image `{IMAGE}` declares no probe: the first check says so.",
        fr=f"l'image `{IMAGE}` ne déclare aucune sonde : le premier contrôle le "
           "dit.",
    )

    interval = b.get("interval", 0)
    timeout = b.get("timeout", 0)
    assert interval > 0 and timeout > 0 and timeout < interval, message(
        en=f"the probe's timeout ({timeout} s) is not below its interval "
           f"({interval} s).\n"
           "A slow probe is then still running when the next one starts, and "
           "the engine stacks them up on a service that is already struggling.",
        fr=f"le délai d'attente de la sonde ({timeout} s) n'est pas inférieur à "
           f"son intervalle ({interval} s).\n"
           "Une sonde lente est alors encore en cours quand la suivante "
           "démarre, et le moteur les empile sur un service qui va déjà mal.",
    )
    assert b.get("retries", 0) >= 2, message(
        en=f"the probe allows {b.get('retries', 0)} attempt(s).\n"
           "A single hiccup, one second of load, then declares a healthy "
           "service sick. Two attempts are the floor.",
        fr=f"la sonde autorise {b.get('retries', 0)} tentative(s).\n"
           "Un seul hoquet, une seconde de charge, déclare alors malade un "
           "service qui va bien. Deux tentatives sont le plancher.",
    )
    assert b.get("start", 0) > 0, message(
        en="the probe declares no start period.\n"
           "A service that takes time to get ready is then judged before it has "
           "begun. Measured on this lab, the probe concludes from the second "
           "second onwards.",
        fr="la sonde ne déclare aucune période de démarrage.\n"
           "Un service qui prend du temps à se préparer est alors jugé avant "
           "d'avoir commencé. Mesuré sur ce lab, la sonde conclut dès la "
           "deuxième seconde.",
    )
