"""Tests fonctionnels du lab de sauvegarde et restauration : cinq contrôles.

CE QUE CE LAB MESURE, et ce qu'il refuse de mesurer. La leçon C32 enseigne la
sauvegarde logique d'une base dans une stack Compose, l'archivage d'un volume de
fichiers, l'archivage de la configuration, et la restauration sur une cible
VIERGE. Ce lab n'exige rien d'autre.

Le lab qui tenait cette place, `donnees-postgres-sauvegarde`, demandait un
PostgreSQL installé sur la VM, un `sudo -u postgres`, un `CREATE DATABASE`, un
`pg_restore --no-owner --no-privileges` et un `scp` vers un second hôte. La
leçon ne dit rien de tout cela : le lab mesurait donc la débrouille, et pas
l'apprentissage.

LA PREUVE EST UNE EMPREINTE, PAS UN GESTE. On ne vérifie pas qu'un `pg_dump` a
été tapé : on compare ce que la cible SERT à ce que la source servait. Un
contrôle qui cherche une commande dans un historique mesure l'obéissance ; un
contrôle qui compare des données mesure le résultat, et il laisse l'apprenant
libre du chemin.

COMPTER NE SUFFIT PAS, et c'est la raison du md5. Une table remplie de mauvaises
valeurs a le bon nombre de lignes. L'empreinte agrège donc le CONTENU, ordonné
par identifiant, et les planches sont comparées par `sha256sum`.

LE CONTRÔLE DE L'ÉGALITÉ DES DONNÉES EST CELUI POUR LEQUEL CE LAB EXISTE. Une restauration qui rend
des données fausses est pire qu'une restauration qui échoue : personne ne s'en
aperçoit, et l'herbier est perdu le jour où l'on en a besoin.

Ce n'est PAS une exigence bloquante au sens du contrat, et c'est une contrainte
qu'il faut connaître : `exam_blocking_checks` n'est accepté que par un
`lab_type` qui évalue, `challenge` ou `capstone`. Ce lab est le TP d'une leçon,
donc il n'a pas de total, et ses cinq contrôles valent chacun pour eux-mêmes.
"""
from __future__ import annotations

import json

import pytest

from conftest import lab_host, message

ATELIER = "/opt/lab-sauver-restaurer"
SOURCE = f"{ATELIER}/herbier"
SAUVEGARDES = f"{ATELIER}/sauvegardes"
ETAT = "/root/.lab-sauver-restaurer.json"
PROJET_SOURCE = "herbier"
PROJET_CIBLE = "herbier-reprise"
TABLE = "specimens"

# La requête d'empreinte, écrite en entier et non assemblée. Elle est CONSTANTE :
# aucune valeur extérieure n'y entre, et c'est ce qui la distingue d'une
# injection. L'écrire d'un bloc le rend vérifiable d'un coup d'œil, là qu'une
# f-string autour de `{TABLE}` demandait de remonter à sa définition pour en être
# sûr. `order by id` n'est pas un détail : sans lui, deux bases identiques
# rendraient deux empreintes différentes.
REQUETE_EMPREINTE = (
    "select count(*)||' lignes, md5 '||md5(string_agg("
    "nom||'|'||recolte||'|'||jeton, '|' order by id)) from specimens"
)
BASE = "herbier"
UTILISATEUR = "conservateur"
SERVICE_BASE = "depot"
VOLUME_PLANCHES = "planches"

# L'image que la leçon emploie pour manipuler un volume depuis l'extérieur.
ALPINE = (
    "alpine:3.24@sha256:"
    "be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a"
)

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
def releve(host) -> dict:
    """Les empreintes de la SOURCE, prises par le `run` avant tout travail.

    Elles font foi. Les relever au moment du contrôle n'aurait aucun sens : si
    l'apprenant a cassé la source, on comparerait la cible à une source abîmée,
    et deux erreurs se compenseraient.
    """
    lu = host.run("cat %s", ETAT)
    if lu.rc != 0:
        pytest.fail(message(
            en=f"the lab's own measurement is missing from `{ETAT}`. It is "
               "taken during `dsoxlab run`: replay it.",
            fr=f"la mesure que le lab a prise manque dans `{ETAT}`. Elle est "
               "faite pendant `dsoxlab run` : rejouez-le.",
        ))
    return json.loads(lu.stdout)


def _projet_debout(host, projet: str) -> list[str]:
    """Les conteneurs en marche de ce projet Compose, par leur service.

    `{{.Label "..."}}` ET NON `{{index .Labels "..."}}`, et c'est une mesure qui
    l'impose. Dans `docker ps --format`, `.Labels` est une CHAÎNE, la liste des
    étiquettes séparées par des virgules, et non une table :

        index .Labels "com.docker.compose.service"
        -> failed to execute template: error calling index:
           cannot index slice/array with type string

    Le gabarit échouait donc en silence du point de vue du test, qui lisait une
    sortie vide et concluait qu'aucun service ne tournait. `docker inspect`, lui,
    expose bien une table sous `.Config.Labels` : c'est la confusion entre les
    deux commandes qui m'a trompé.
    """
    lu = host.run(
        "docker ps --filter %s --format %s",
        f"label=com.docker.compose.project={projet}",
        '{{.Label "com.docker.compose.service"}}',
    )
    return sorted(n.strip() for n in lu.stdout.splitlines() if n.strip())


def _empreinte_de_la_base(host, projet: str) -> str:
    """Le compte ET le md5 du contenu de la table, ordonné par identifiant.

    `< /dev/null` est indispensable, et c'est un des pièges de la leçon :
    sans lui, `docker compose exec` lit son entrée standard et avale la suite du
    script appelant, dont les lignes ne s'exécutent alors jamais.
    """
    lu = host.run(
        "docker compose -p %s exec -T %s psql -Atq -U %s -d %s -c %s < /dev/null",
        projet, SERVICE_BASE, UTILISATEUR, BASE, REQUETE_EMPREINTE,
    )
    return lu.stdout.strip() if lu.rc == 0 else ""


def _empreinte_des_planches(host, projet: str) -> str:
    """Le sha256 de chaque planche du volume, trié.

    Lu DANS un conteneur monté sur le volume, parce qu'un volume nommé n'a pas
    de chemin que l'hôte doive connaître : c'est la façon dont la leçon y accède.
    """
    lu = host.run(
        "docker run --rm -v %s -i %s sh -c %s",
        f"{projet}_{VOLUME_PLANCHES}:/src:ro", ALPINE,
        "cd /src && sha256sum * | sort",
    )
    return lu.stdout.strip() if lu.rc == 0 else ""


def _exiger_la_source_intacte(host, releve) -> None:
    """On ne casse pas ce qu'on est venu sauvegarder.

    CE N'EST PAS UN CONTRÔLE À PART, et c'est une correction de conception. Il
    en était un, et il PASSAIT AVANT TOUT TRAVAIL : le setup vient de poser la
    source, donc elle tourne et son empreinte est la bonne. Le cycle de
    validation rendait alors 1 sur 6 au départ, et il exige 0, parce qu'un lab
    dont un contrôle est déjà vert distribue des points pour rien.

    Vérifier que la source est intacte ne mesure pas un acquis, cela mesure que
    le travail n'a rien coûté. C'est une CONDITION, et elle appartient au
    contrôle décisif : comparer l'empreinte de la cible à celle de la source n'a
    de sens que si la source est encore celle qu'on a relevée. Une restauration
    prouvée contre une source détruite ne prouve rien.

    Une sauvegarde prise en arrêtant la base, en la vidant ou en déplaçant son
    volume « marche » et laisse le conservatoire sans son herbier pendant
    l'opération. C'est la faute la plus facile à commettre, parce qu'elle rend
    le reste du travail plus simple.
    """
    services = _projet_debout(host, PROJET_SOURCE)
    assert services == [SERVICE_BASE, "vitrine"], message(
        en=f"the source stack `{PROJET_SOURCE}` no longer runs both its "
           "services.\n"
           f"  running: {services or '(none)'}\n"
           "A backup must not cost the service it protects.",
        fr=f"la stack source `{PROJET_SOURCE}` ne fait plus tourner ses deux "
           "services.\n"
           f"  en marche : {services or '(aucun)'}\n"
           "Une sauvegarde ne doit pas coûter le service qu'elle protège.",
    )
    empreinte = _empreinte_de_la_base(host, PROJET_SOURCE)
    assert empreinte == releve["empreinte_base"], message(
        en="the source's data changed during the operation.\n"
           f"  it was    : {releve['empreinte_base']}\n"
           f"  it is now : {empreinte or '(unreadable)'}\n"
           "The source is read, never modified.",
        fr="les données de la source ont changé pendant l'opération.\n"
           f"  elles étaient : {releve['empreinte_base']}\n"
           f"  elles sont    : {empreinte or '(illisible)'}\n"
           "La source se lit, elle ne se modifie pas.",
    )


def test_la_sauvegarde_de_la_base_est_logique_et_relisible(host) -> None:
    """Une copie à chaud du volume n'est pas une sauvegarde.

    C'est le piège central de la leçon, et il ne se voit pas : copier
    `/var/lib/postgresql` pendant que le moteur écrit donne une archive qui
    SEMBLE complète. Elle porte un état intermédiaire, et elle se restaure sans
    erreur jusqu'au jour où elle ne se restaure pas.

    LE CONTRÔLE NE REGARDE PAS COMMENT L'ARCHIVE A ÉTÉ FAITE, il regarde ce
    qu'elle EST : un `pg_restore --list` la lit, ou elle n'est pas une
    sauvegarde logique. C'est la même distinction que partout ailleurs dans ce
    catalogue, on mesure l'état et non le geste.
    """
    trouves = host.run(
        "find %s -maxdepth 2 -type f -size +1k", SAUVEGARDES
    ).stdout.split()
    assert trouves, message(
        en=f"no backup file was found under `{SAUVEGARDES}`.",
        fr=f"aucun fichier de sauvegarde n'a été trouvé sous `{SAUVEGARDES}`.",
    )
    lisibles = []
    for chemin in trouves:
        lu = host.run(
            "docker compose -p %s exec -T %s pg_restore --list < %s",
            PROJET_SOURCE, SERVICE_BASE, chemin,
        )
        if lu.rc == 0 and TABLE in lu.stdout:
            lisibles.append(chemin)
    assert lisibles, message(
        en="none of the backup files is a logical dump that `pg_restore "
           "--list` can read and that mentions the table.\n"
           f"  files seen: {' '.join(trouves)}\n"
           "A copy of the database volume taken while the engine writes is not "
           "a backup: it holds an intermediate state, and it restores without "
           "an error until the day it does not.",
        fr="aucun fichier de sauvegarde n'est un dump logique que "
           "`pg_restore --list` sait relire et qui mentionne la table.\n"
           f"  fichiers vus : {' '.join(trouves)}\n"
           "Une copie du volume de la base prise pendant que le moteur écrit "
           "n'est pas une sauvegarde : elle porte un état intermédiaire, et "
           "elle se restaure sans erreur jusqu'au jour où elle ne se restaure "
           "pas.",
    )


def test_les_planches_et_la_configuration_sont_archivees(host) -> None:
    """Une base restaurée sans ses fichiers rend un herbier sans ses planches.

    Deux archives distinctes, et deux raisons distinctes. Le volume de fichiers
    ne vit pas dans la base : aucun `pg_dump` ne l'emporte. Et la
    configuration, `compose.yaml`, `.env` et les secrets, est ce qui permet de
    RECONSTRUIRE la stack : sans elle, on a des données et rien pour les servir.
    """
    archives = host.run(
        "find %s -maxdepth 2 -type f -name %s", SAUVEGARDES, "*.tar.gz"
    ).stdout.split()
    assert archives, message(
        en=f"no `.tar.gz` archive was found under `{SAUVEGARDES}`: neither the "
           "files volume nor the configuration was archived.",
        fr=f"aucune archive `.tar.gz` n'a été trouvée sous `{SAUVEGARDES}` : ni "
           "le volume de fichiers ni la configuration n'est sauvegardé.",
    )
    porte_planches = porte_config = None
    for chemin in archives:
        contenu = host.run("tar tzf %s", chemin).stdout
        if "planche-" in contenu:
            porte_planches = chemin
        if "compose.yaml" in contenu and ".env" in contenu:
            porte_config = chemin
    assert porte_planches, message(
        en="no archive carries the plates of the files volume.\n"
           f"  archives seen: {' '.join(archives)}\n"
           "No `pg_dump` takes a files volume along: it is archived on its own.",
        fr="aucune archive ne porte les planches du volume de fichiers.\n"
           f"  archives vues : {' '.join(archives)}\n"
           "Aucun `pg_dump` n'emporte un volume de fichiers : il s'archive à "
           "part.",
    )
    assert porte_config, message(
        en="no archive carries the configuration, `compose.yaml` and `.env` "
           "together.\n"
           f"  archives seen: {' '.join(archives)}\n"
           "Without it you hold data and nothing to serve it with.",
        fr="aucune archive ne porte la configuration, `compose.yaml` et `.env` "
           "ensemble.\n"
           f"  archives vues : {' '.join(archives)}\n"
           "Sans elle, on détient des données et rien pour les servir.",
    )


def test_la_cible_est_un_projet_distinct_et_debout(host, releve) -> None:
    """Un AUTRE projet, qui tourne EN MÊME TEMPS que la source.

    Restaurer par-dessus la source ne prouve rien : les données y étaient déjà.
    La cible est donc un projet Compose distinct, et les deux cohabitent, ce qui
    oblige à lui donner son propre port publié. C'est le geste que la leçon
    montre, et c'est aussi la situation réelle : on vérifie une sauvegarde
    AVANT d'avoir perdu l'original.
    """
    services = _projet_debout(host, PROJET_CIBLE)
    assert services == [SERVICE_BASE, "vitrine"], message(
        en=f"the target project `{PROJET_CIBLE}` does not run both its "
           "services.\n"
           f"  running: {services or '(none)'}\n"
           "The target is a project of its own, and it runs beside the source.",
        fr=f"le projet cible `{PROJET_CIBLE}` ne fait pas tourner ses deux "
           "services.\n"
           f"  en marche : {services or '(aucun)'}\n"
           "La cible est un projet à elle, et elle tourne à côté de la source.",
    )
    # Les deux ne peuvent pas publier le même port, et le moteur l'aurait
    # refusé : on vérifie donc que la cible publie bien SON port, et non que la
    # source a été arrêtée pour lui laisser le sien.
    publie = host.run(
        "docker ps --filter %s --format %s",
        f"label=com.docker.compose.project={PROJET_CIBLE}", "{{.Ports}}",
    ).stdout
    port_source = str(releve["port_source"])
    assert port_source not in publie, message(
        en=f"the target publishes the source's port, {port_source}.\n"
           "Both stacks run at once, so the target takes a port of its own: "
           "reusing that one means the source was stopped.",
        fr=f"la cible publie le port de la source, {port_source}.\n"
           "Les deux stacks tournent en même temps, donc la cible prend un "
           "port à elle : reprendre celui-là veut dire que la source a été "
           "arrêtée.",
    )


def test_la_cible_sert_exactement_les_donnees_de_la_source(host, releve) -> None:
    """LE CONTRÔLE POUR LEQUEL CE LAB EXISTE.

    Une restauration qui rend des données FAUSSES est pire qu'une restauration
    qui échoue. Un échec se voit et se reprend ; des données fausses se
    découvrent le jour où l'on en a besoin, et l'herbier est perdu.

    DEUX EMPREINTES, et chacune couvre ce que l'autre ne voit pas. Celle de la
    base agrège le contenu ORDONNÉ de la table : compter les lignes ne suffit
    pas, une table remplie de mauvaises valeurs a le bon compte. Celle des
    planches est un `sha256sum` par fichier : un volume vide a le bon nombre de
    fichiers si on les recrée à la main, et pas les bons octets.

    Les deux témoins tirés au sort par le `run` rendent le résultat
    infalsifiable : on ne peut pas les deviner, et ils n'existent nulle part
    ailleurs que dans la source.
    """
    # LA CONDITION D'ABORD : sans source intacte, la comparaison qui suit ne
    # prouve rien, et son verdict porterait sur deux états abîmés.
    _exiger_la_source_intacte(host, releve)

    empreinte = _empreinte_de_la_base(host, PROJET_CIBLE)
    assert empreinte, message(
        en=f"the target's table `{TABLE}` cannot be read at all. The database "
           "was not restored, or it is not the one the stack serves.",
        fr=f"la table `{TABLE}` de la cible ne se lit pas du tout. La base n'a "
           "pas été restaurée, ou ce n'est pas celle que la stack sert.",
    )
    assert empreinte == releve["empreinte_base"], message(
        en="the data the target serves is not the data the source served.\n"
           f"  source: {releve['empreinte_base']}\n"
           f"  target: {empreinte}\n"
           "The count alone is not enough, which is why the fingerprint "
           "aggregates the ordered content. A restore that serves wrong data "
           "is worse than a restore that fails, because nobody notices.",
        fr="les données servies par la cible ne sont pas celles que servait la "
           "source.\n"
           f"  source : {releve['empreinte_base']}\n"
           f"  cible  : {empreinte}\n"
           "Le compte seul ne suffit pas, et c'est pourquoi l'empreinte agrège "
           "le contenu ordonné. Une restauration qui sert des données fausses "
           "est pire qu'une restauration qui échoue, parce que personne ne s'en "
           "aperçoit.",
    )
    planches = _empreinte_des_planches(host, PROJET_CIBLE)
    assert planches == releve["empreinte_planches"], message(
        en="the plates the target serves are not the ones the source had.\n"
           f"  source:\n{releve['empreinte_planches']}\n"
           f"  target:\n{planches or '(unreadable)'}\n"
           "A files volume lives outside the database: no `pg_dump` brings it "
           "back.",
        fr="les planches servies par la cible ne sont pas celles de la source.\n"
           f"  source :\n{releve['empreinte_planches']}\n"
           f"  cible  :\n{planches or '(illisible)'}\n"
           "Un volume de fichiers vit hors de la base : aucun `pg_dump` ne le "
           "ramène.",
    )


def test_la_cible_sert_ses_planches_par_le_web_et_non_seulement_son_volume(
    host, releve
) -> None:
    """Le volume est rempli, mais la vitrine le sert-elle ?

    Un volume juste et un service qui ne le monte pas donnent une cible qui
    détient les planches sans les servir. Le contrôle précédent lit le volume ;
    celui-ci lit ce qu'un visiteur obtient, par le port que la cible publie.

    C'est la distinction que tout ce catalogue tient : ce qui est DÉCLARÉ et ce
    qui est SERVI sont deux faits, et seul le second intéresse celui qui vient
    consulter l'herbier.
    """
    # L'IDENTIFIANT SE PREND EN DEUX APPELS, et c'est nécessaire : `host.run`
    # QUOTE chacun de ses `%s`, donc un `$(docker ps -q …)` passé en argument
    # part littéralement au lieu d'être substitué par le shell. Le test lançait
    # alors `docker exec '$(docker ps -q …)'`, qui sort en 1 sur un nom de
    # conteneur inexistant, et le message accusait la vitrine de ne pas servir.
    trouve = host.run(
        "docker ps -q --filter %s --filter %s",
        f"label=com.docker.compose.project={PROJET_CIBLE}",
        "label=com.docker.compose.service=vitrine",
    )
    conteneur = trouve.stdout.strip().splitlines()
    assert conteneur, message(
        en=f"the target project `{PROJET_CIBLE}` has no running web service to "
           "ask.",
        fr=f"le projet cible `{PROJET_CIBLE}` n'a aucun service web en marche à "
           "interroger.",
    )
    lu = host.run(
        "docker exec %s wget -qO- %s",
        conteneur[0], "http://127.0.0.1/planche-03.txt",
    )
    assert lu.rc == 0 and releve["jeton_planche"] in lu.stdout, message(
        en="the target's web service does not serve the plates.\n"
           f"  what came back: {lu.stdout.strip()[:200] or '(nothing)'}\n"
           "Holding the volume is not serving it: the service has to mount it.",
        fr="le service web de la cible ne sert pas les planches.\n"
           f"  ce qui revient : {lu.stdout.strip()[:200] or '(rien)'}\n"
           "Détenir le volume n'est pas le servir : encore faut-il que le "
           "service le monte.",
    )
