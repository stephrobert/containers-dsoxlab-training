"""Épreuve « remettre une stack en service » : cinq contrôles de poids égal.

CE QUE CETTE ÉPREUVE MESURE, et ce qu'elle ne mesure plus.

Elle est l'épreuve du module Compose, et elle note la composition : un projet
nommé, deux services qui se joignent **par leur nom de service** sur un réseau
de la pile, une seule façade publiée, une donnée qui survit à une recréation,
et une configuration dont les valeurs viennent d'une interpolation.

Elle exigeait auparavant une **sonde de santé** et un
`depends_on: service_completed_successfully`. Les deux s'enseignent au module
SUIVANT, en C28. Une épreuve ne note pas ce qui n'a pas été enseigné, et un
apprenant qui faisait exactement ce que sa leçon montrait échouait sur une
notion dont on ne lui avait jamais parlé.

ELLE N'EN A PLUS BESOIN, et ce n'est pas un renoncement : le frontal fourni
réessaie jusqu'à ce que l'amont réponde, donc l'ordre de démarrage est
indifférent. C'est une façon de se passer d'ordonnancement, et elle se mesure
aussi bien.

L'EXIGENCE CRITIQUE est le contrôle 4 : une donnée écrite avant une recréation
doit être servie après. C'est la seule chose qu'une composition perd pour de
bon, et aucun total ne la compense.

CE QUE LES CONTRÔLES NE MESURENT PAS, délibérément : le nom du réseau, celui du
volume, et la façon dont la composition est écrite. L'épreuve note l'état
final, et deux chemins vers le même état reçoivent la même note.
"""

from __future__ import annotations

import json
import shlex

import pytest

from conftest import lab_host, message

PROJET = "dsoxlab-epreuve-remettre-une-stack-en-service"
ATELIER = "/opt/lab-epreuve-remettre-une-stack-en-service"
COMPOSE = f"{ATELIER}/compose.yaml"
ETAT = f"{ATELIER}/state.json"

#: Les deux services que la composition doit porter.
FRONTAL = "frontal"
DONNEES = "donnees"

#: La façade, telle que le fichier d'environnement fourni la décrit. Les
#: contrôles lisent ces valeurs dans ce fichier et non en dur : c'est lui que
#: la composition doit interpoler, et le lab le tire à chaque passage.
PORT_PAR_DEFAUT = 18092
ADRESSE_PAR_DEFAUT = "127.0.0.1"

TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail."""
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def facade(host) -> tuple[str, int]:
    """L'adresse et le port que le fichier d'environnement fourni déclare."""
    lu = host.run("cat %s", f"{ATELIER}/.env")
    adresse, port = ADRESSE_PAR_DEFAUT, PORT_PAR_DEFAUT
    for ligne in lu.stdout.splitlines():
        if ligne.startswith("FACADE_ADRESSE="):
            adresse = ligne.split("=", 1)[1].strip()
        elif ligne.startswith("FACADE_PORT="):
            port = int(ligne.split("=", 1)[1].strip())
    return adresse, port


# ── aides ─────────────────────────────────────────────────────────────────

def _services(host) -> dict[str, dict]:
    """Les deux conteneurs du projet, par nom de service.

    Échoue en nommant ce qui manque : sur une épreuve, un message dit le
    symptôme et s'arrête là.
    """
    trouves = host.run(
        "docker ps -aq --filter %s",
        f"label=com.docker.compose.project={PROJET}",
    )
    ids = trouves.stdout.split()
    if trouves.rc != 0 or not ids:
        pytest.fail(message(
            en=f"no container belongs to the `{PROJET}` project.\n"
               "The project name is part of the brief: Compose derives it from "
               "the directory unless it is set.",
            fr=f"aucun conteneur n'appartient au projet `{PROJET}`.\n"
               "Le nom du projet fait partie de l'énoncé : Compose le dérive du "
               "répertoire tant qu'on ne le fixe pas.",
        ))
    inspecte = host.run(shlex.join(["docker", "inspect", *ids]))
    if inspecte.rc != 0:
        pytest.fail(message(
            en="the project's containers cannot be inspected.",
            fr="les conteneurs du projet ne peuvent pas être inspectés.",
        ))
    par_service: dict[str, dict] = {}
    for conteneur in json.loads(inspecte.stdout):
        nom = conteneur["Config"]["Labels"].get("com.docker.compose.service")
        if nom:
            par_service[nom] = conteneur
    return par_service


def _lire_la_facade(host, adresse: str, port: int) -> str:
    """Ce que la façade sert, lu depuis l'hôte.

    Plusieurs tentatives : le frontal va chercher sa valeur à l'amont au
    démarrage, et il peut encore être en train de réessayer.
    """
    dernier = ""
    for _ in range(30):
        res = host.run(
            shlex.join([
                "curl", "--noproxy", "*", "-fsS", "--max-time", "3",
                f"http://{adresse}:{port}/release.txt",
            ])
        )
        dernier = res.stdout.strip()
        if res.rc == 0 and dernier and dernier != "amont-injoignable":
            return dernier
        host.run("sleep 1")
    return dernier


def _valeur_attendue(host) -> str:
    """La valeur tirée par le lab à ce passage, lue dans son relevé."""
    lu = host.run("cat %s", ETAT)
    if lu.rc != 0:
        pytest.fail(message(
            en=f"the lab's own record `{ETAT}` is missing. It is written during "
               "`dsoxlab run`: replay it.",
            fr=f"le relevé du lab `{ETAT}` est absent. Il est écrit pendant "
               "`dsoxlab run` : rejouez-le.",
        ))
    return json.loads(lu.stdout)["release"]


# ── les cinq contrôles ────────────────────────────────────────────────────

def test_le_projet_porte_ses_deux_services_et_ils_tournent(host) -> None:
    """Le projet nommé, et ses deux services debout.

    LE NOM DU PROJET fait partie de l'énoncé, parce que c'est lui qui rattache
    conteneurs, réseaux et volumes les uns aux autres : sans lui, Compose le
    dérive du nom du répertoire, et deux personnes obtiennent deux piles
    différentes du même fichier.
    """
    services = _services(host)
    manquants = sorted({FRONTAL, DONNEES} - set(services))
    assert not manquants, message(
        en=f"the project does not carry its two services.\n"
           f"  missing : {', '.join(manquants)}\n"
           f"  present : {', '.join(sorted(services)) or '(none)'}",
        fr=f"le projet ne porte pas ses deux services.\n"
           f"  manquant(s) : {', '.join(manquants)}\n"
           f"  présent(s)  : {', '.join(sorted(services)) or '(aucun)'}",
    )
    en_trop = sorted(set(services) - {FRONTAL, DONNEES})
    assert not en_trop, message(
        en=f"the project carries services the brief does not ask for: "
           f"{', '.join(en_trop)}.",
        fr=f"le projet porte des services que l'énoncé ne demande pas : "
           f"{', '.join(en_trop)}.",
    )
    arretes = sorted(nom for nom, c in services.items()
                     if not c["State"]["Running"])
    assert not arretes, message(
        en=f"these services are not running: {', '.join(arretes)}.\n"
           "Both have to be up: nothing in this brief is a one-shot task.",
        fr=f"ces services ne tournent pas : {', '.join(arretes)}.\n"
           "Les deux doivent être debout : rien dans cet énoncé n'est une tâche "
           "ponctuelle.",
    )


def test_la_requete_metier_joint_les_donnees_par_leur_nom_de_service(
    host, facade,
) -> None:
    """La jonction PAR LE NOM, qui est ce que Compose apporte.

    Le frontal interroge le nom que `CIBLE` lui donne, et ce nom est celui du
    SERVICE : il ne se contourne pas en renommant un conteneur. Le contrôle
    lit donc deux choses, la valeur qui revient de bout en bout, et le fait
    que les deux services partagent un réseau du projet.
    """
    adresse, port = facade
    services = _services(host)
    attendue = _valeur_attendue(host)
    rendue = _lire_la_facade(host, adresse, port)
    assert rendue == attendue, message(
        en=f"the façade does not serve the value the data service holds.\n"
           f"  served  : {rendue or '(nothing)'}\n"
           f"  expected: {attendue}\n"
           "`amont-injoignable` means the front end could not reach the data "
           "service by the name it is given.",
        fr=f"la façade ne sert pas la valeur que détient le service de "
           f"données.\n"
           f"  servi   : {rendue or '(rien)'}\n"
           f"  attendu : {attendue}\n"
           "`amont-injoignable` signifie que le frontal n'a pas joint le "
           "service de données par le nom qu'on lui donne.",
    )
    reseaux = {
        nom: set(services[nom]["NetworkSettings"]["Networks"] or {})
        for nom in (FRONTAL, DONNEES) if nom in services
    }
    partages = set.intersection(*reseaux.values()) if len(reseaux) == 2 else set()
    du_projet = {r for r in partages if r.startswith(PROJET) or r != "bridge"}
    assert du_projet, message(
        en=f"the two services share no network.\n"
           f"  {FRONTAL}: {', '.join(sorted(reseaux.get(FRONTAL, ()))) or '(none)'}\n"
           f"  {DONNEES}: {', '.join(sorted(reseaux.get(DONNEES, ()))) or '(none)'}",
        fr=f"les deux services ne partagent aucun réseau.\n"
           f"  {FRONTAL} : {', '.join(sorted(reseaux.get(FRONTAL, ()))) or '(aucun)'}\n"
           f"  {DONNEES} : {', '.join(sorted(reseaux.get(DONNEES, ()))) or '(aucun)'}",
    )


def test_seul_le_frontal_publie_et_sur_la_boucle_locale(host, facade) -> None:
    """Une pile n'expose qu'une façade, et seulement là où on le demande.

    Le service de données n'a aucune raison d'être joignable du dehors : le
    frontal l'atteint par le réseau de la pile. Et la façade elle-même ne doit
    l'être que depuis la machine, parce qu'un relais la publiera plus tard.
    """
    adresse, port = facade
    services = _services(host)
    liaisons_donnees = (services.get(DONNEES, {})
                        .get("HostConfig", {}).get("PortBindings") or {})
    assert not liaisons_donnees, message(
        en=f"`{DONNEES}` publishes a port: {', '.join(sorted(liaisons_donnees))}.\n"
           "The data service has no reason to be reachable from outside the "
           "stack.",
        fr=f"`{DONNEES}` publie un port : {', '.join(sorted(liaisons_donnees))}.\n"
           "Le service de données n'a aucune raison d'être joignable depuis "
           "l'extérieur de la pile.",
    )
    liaisons_frontal = (services.get(FRONTAL, {})
                        .get("HostConfig", {}).get("PortBindings") or {})
    publies = sorted(liaisons_frontal)
    assert publies == ["8080/tcp"], message(
        en=f"`{FRONTAL}` does not publish exactly one port.\n"
           f"  published: {', '.join(publies) or '(none)'}\n"
           "  expected : 8080/tcp only",
        fr=f"`{FRONTAL}` ne publie pas exactement un port.\n"
           f"  publiés : {', '.join(publies) or '(aucun)'}\n"
           "  attendu : 8080/tcp seul",
    )
    ou = {(ligne.get("HostIp") or "", ligne.get("HostPort") or "")
          for ligne in liaisons_frontal["8080/tcp"] or []}
    assert ou == {(adresse, str(port))}, message(
        en=f"`{FRONTAL}` is published, but not where the brief asks.\n"
           f"  bindings: {sorted(ou)}\n"
           f"  expected: {adresse}:{port}\n"
           "An empty or 0.0.0.0 address means every interface of the host.",
        fr=f"`{FRONTAL}` est publié, mais pas là où l'énoncé le demande.\n"
           f"  liaisons : {sorted(ou)}\n"
           f"  attendu  : {adresse}:{port}\n"
           "Une adresse vide ou 0.0.0.0 désigne toutes les interfaces de "
           "l'hôte.",
    )


def test_une_donnee_ecrite_avant_une_recreation_est_servie_apres(
    host, facade,
) -> None:
    """L'EXIGENCE CRITIQUE : la donnée survit, ou rien ne vaut.

    C'est la seule chose qu'une composition perd pour de bon. Un service se
    relance, un réseau se recrée, un port se republie ; une donnée écrite dans
    la couche d'un conteneur part avec lui et ne revient pas.

    LE CONTRÔLE ÉCRIT UN TÉMOIN, recrée la pile, et relit la façade. Il
    n'impose aucun nom de volume : seul l'effet compte. Un volume anonyme, ou
    pas de volume du tout, perd le témoin et se voit ici.

    Il remet ensuite la valeur d'origine, pour que les contrôles qui suivent
    lisent l'état que l'énoncé décrit, et non celui que celui-ci a fabriqué.
    """
    adresse, port = facade
    services = _services(host)
    assert DONNEES in services, message(
        en=f"service `{DONNEES}` is missing.",
        fr=f"le service `{DONNEES}` est absent.",
    )
    origine = _valeur_attendue(host)
    temoin = f"temoin-{origine}-survivant"
    identifiant = services[DONNEES]["Id"]

    try:
        ecrit = host.run(
            "docker exec %s sh -c %s", identifiant,
            f"printf '%s' '{temoin}' > /data/release.txt",
        )
        assert ecrit.rc == 0, message(
            en=f"cannot write the witness into `{DONNEES}`: "
               f"{(ecrit.stdout + ecrit.stderr).strip()[:200]}",
            fr=f"impossible d'écrire le témoin dans `{DONNEES}` : "
               f"{(ecrit.stdout + ecrit.stderr).strip()[:200]}",
        )
        recree = host.run(
            shlex.join([
                "docker", "compose", "-p", PROJET, "-f", COMPOSE,
                "up", "-d", "--force-recreate", "--no-build", "--pull", "never",
            ])
        )
        assert recree.rc == 0, message(
            en=f"recreating the stack must succeed: {recree.stderr[-400:]}",
            fr=f"la recréation de la pile doit réussir : {recree.stderr[-400:]}",
        )
        apres = _lire_la_facade(host, adresse, port)
        assert apres == temoin, message(
            en=f"the data written before the recreation is gone.\n"
               f"  served  : {apres or '(nothing)'}\n"
               f"  expected: {temoin}\n"
               "A container's writable layer leaves with the container, and an "
               "anonymous volume is not reattached to a recreated service. No "
               "total makes up for lost data.",
            fr=f"la donnée écrite avant la recréation a disparu.\n"
               f"  servi   : {apres or '(rien)'}\n"
               f"  attendu : {temoin}\n"
               "La couche d'écriture d'un conteneur part avec lui, et un volume "
               "anonyme n'est pas rattaché à un service recréé. Aucun total ne "
               "compense une donnée perdue.",
        )
    finally:
        # ON REMET L'ÉTAT QUE L'ÉNONCÉ DÉCRIT. Un contrôle qui laisse sa propre
        # trace fait échouer les suivants sur son travail, et le cycle de
        # validation le verrait comme un moteur non rendu intact.
        courants = _services(host)
        if DONNEES in courants:
            host.run(
                "docker exec %s sh -c %s", courants[DONNEES]["Id"],
                f"printf '%s' '{origine}' > /data/release.txt",
            )
            host.run(
                shlex.join([
                    "docker", "compose", "-p", PROJET, "-f", COMPOSE,
                    "up", "-d", "--force-recreate", "--no-build",
                    "--pull", "never", FRONTAL,
                ])
            )


def test_la_composition_resolue_ne_porte_aucune_variable_en_suspens(
    host, facade,
) -> None:
    """Ce que le moteur COMPREND du fichier, et non ce que le fichier contient.

    `docker compose config` rend la composition résolue : variables
    substituées, superpositions appliquées. C'est elle qui fait foi.

    DEUX FAITS. Aucune variable ne reste en suspens : mesuré le 2026-11-02 sur
    Compose 5.6.1, une variable absente sans valeur par défaut fait émettre un
    avertissement, « Defaulting to a blank string », et la composition est
    tout de même ACCEPTÉE, code 0. La pile démarre donc en écoutant sur un
    port que personne n'attend, et l'avertissement part sur la sortie
    d'erreur, où un script ou une chaîne d'intégration ne le lit pas.

    Et au moins une valeur vient d'une INTERPOLATION : le lab fournit un
    fichier d'environnement, et une composition qui recopie ses valeurs en dur
    ne s'en sert pas.
    """
    adresse, port = facade
    rendu = host.run(
        shlex.join(["docker", "compose", "-p", PROJET, "-f", COMPOSE, "config"])
    )
    assert rendu.rc == 0, message(
        en=f"`docker compose config` fails, so the composition does not even "
           f"resolve:\n{rendu.stderr.strip()[:400]}",
        fr=f"`docker compose config` échoue, donc la composition ne se résout "
           f"même pas :\n{rendu.stderr.strip()[:400]}",
    )
    en_suspens = [ligne.strip() for ligne in rendu.stdout.splitlines() if "${" in ligne]
    assert not en_suspens, message(
        en="the resolved composition still carries unresolved variables:\n"
           + "\n".join(f"  {ligne}" for ligne in en_suspens[:5]) + "\n"
           "An unresolved variable becomes an empty string without Compose "
           "complaining.",
        fr="la composition résolue porte encore des variables non résolues :\n"
           + "\n".join(f"  {ligne}" for ligne in en_suspens[:5]) + "\n"
           "Une variable non résolue devient une chaîne vide sans que Compose "
           "s'en plaigne.",
    )
    brut = host.run("cat %s", COMPOSE)
    assert brut.rc == 0, message(
        en=f"`{COMPOSE}` cannot be read.",
        fr=f"`{COMPOSE}` ne peut pas être lu.",
    )
    assert "${" in brut.stdout, message(
        en="the composition interpolates nothing.\n"
           f"The lab provides `{ATELIER}/.env`, and the brief asks for the "
           "façade's address and port to be read from it rather than written "
           "in by hand.",
        fr="la composition n'interpole rien.\n"
           f"Le lab fournit `{ATELIER}/.env`, et l'énoncé demande que l'adresse "
           "et le port de la façade en soient lus plutôt que recopiés à la "
           "main.",
    )
    assert f"{adresse}:{port}" in rendu.stdout or (
        f'"{port}"' in rendu.stdout and adresse in rendu.stdout
    ), message(
        en=f"the resolved composition does not publish on {adresse}:{port}, "
           "which is what the provided environment file declares.",
        fr=f"la composition résolue ne publie pas sur {adresse}:{port}, qui est "
           "ce que déclare le fichier d'environnement fourni.",
    )
