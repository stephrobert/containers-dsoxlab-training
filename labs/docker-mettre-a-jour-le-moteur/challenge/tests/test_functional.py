"""Tests fonctionnels du lab docker-mettre-a-jour-le-moteur : cinq contrôles de poids égal.

CE QUE CE LAB NOTE : la MONTÉE, et seulement elle. Le retour arrière reste
enseigné par la leçon, il n'est pas noté. Les contrôles lisent l'ÉTAT FINAL de
l'hôte : le moteur, ses paquets, sa configuration, et un service témoin posé
par le setup. Aucun ne regarde quelles commandes ont été tapées.

L'ÉTAT DE DÉPART EST CELUI D'UN HÔTE RÉEL. Le moteur est en 29.8.2, ses six
paquets sont retenus, le `daemon.json` règle la rotation des journaux sans
`live-restore`, et un service témoin écrit un battement par seconde dans un
volume à côté d'une donnée. Le setup relève ce départ dans un fichier de
référence que les contrôles lisent : processus et heure de démarrage du témoin,
empreinte de sa donnée, options d'origine du démon. Rien de cela n'est écrit
en dur ici.

DEUX CONTRÔLES NE VALENT QU'APRÈS LA MONTÉE. Le témoin n'a pas été relancé, et
sa donnée est intacte : ces deux faits sont vrais AVANT tout travail, puisque le
setup vient de poser le témoin. Un contrôle vrai avant le travail ne mesure rien,
il mesure l'état de départ. Ils exigent donc d'abord que le moteur soit en
29.9.2 : sans cela, « le témoin n'a pas bougé » serait un constat sur un moteur
que personne n'a touché, et le contrôle le dit au lieu de le créditer.

CE QUI NE SE NOTE PAS. Que l'apprenant sauvegarde `/etc/docker` ou qu'il valide
sa configuration avant de la recharger : la leçon l'enseigne, mais l'état final
ne le prouve pas, et un contrôle qui exigerait une trace de ces gestes noterait
des commandes. La leçon ne garantit pas non plus la survie des conteneurs à une
montée de version mineure : ce lab mesure ce qui a été observé sur cette
combinaison, 29.8.2 vers 29.9.2, avec ce témoin.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, message

REFERENCE = "/var/lib/dsoxlab-docker-mettre-a-jour-le-moteur/reference.json"

# Les six paquets que l'installation du catalogue retient. Les trois du moteur
# changent de version à la montée, les trois autres ne doivent pas bouger.
PAQUETS_MOTEUR = ("docker-ce", "docker-ce-cli", "docker-ce-rootless-extras")
PAQUETS_AUTRES = ("containerd.io", "docker-buildx-plugin", "docker-compose-plugin")

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
def ref(host) -> dict:
    """Les valeurs relevées par le setup, au moment où le témoin a été posé."""
    fichier = host.file(REFERENCE)
    if not fichier.exists:
        pytest.fail(message(
            en=f"{REFERENCE} is missing: the setup did not run, or the lab was "
               "cleaned. Run `dsoxlab run` again.",
            fr=f"{REFERENCE} est absent : le setup n'a pas été joué, ou le lab "
               "a été nettoyé. Relancez `dsoxlab run`.",
        ))
    return json.loads(fichier.content_string)


def _version_paquet(host, nom: str) -> str:
    res = host.run("dpkg-query -W -f='${Version}' %s", nom)
    return res.stdout.strip() if res.rc == 0 else ""


def _version_moteur(host) -> str:
    res = host.run("docker version --format '{{.Server.Version}}'")
    return res.stdout.strip() if res.rc == 0 else ""


def _exiger_montee(host, ref: dict) -> None:
    """Les contrôles du témoin ne valent qu'une fois le moteur monté."""
    cible = ref["cible"].split(":")[-1].split("-")[0]
    version = _version_moteur(host)
    if version != cible:
        pytest.fail(message(
            en=f"the engine is in {version or 'an unreadable version'}, not "
               f"{cible} yet.\nThis check compares the witness service with "
               "its starting state, and that comparison only means something "
               "once the engine has been moved: before that, nothing has "
               "touched it. Do the climb first.",
            fr=f"le moteur est en {version or 'une version illisible'}, pas "
               f"encore en {cible}.\nCe contrôle compare le service témoin à "
               "son état de départ, et cette comparaison n'a de sens qu'une "
               "fois le moteur monté : avant, rien n'y a touché. Faites "
               "d'abord la montée.",
        ))


def test_le_moteur_est_en_29_9_2_exactement(host, ref) -> None:
    """La version visée, et non le candidat du dépôt.

    Le dépôt officiel propose 29.9.3 comme candidat : un `apt-get install
    docker-ce` sans version nommée l'installe, et la montée réussit... vers la
    mauvaise version. Le contrôle lit le serveur, le client ET le paquet, et
    exige la version décidée, pas « une version plus récente ».
    """
    cible = ref["cible"]
    court = cible.split(":")[-1].split("-")[0]
    serveur = _version_moteur(host)
    client = host.run("docker version --format '{{.Client.Version}}'").stdout.strip()
    paquet = _version_paquet(host, "docker-ce")

    assert serveur == court and client == court and paquet == cible, message(
        en=f"the target is {court} (package `{cible}`).\n"
           f"  engine (server) : {serveur or 'unreadable'}\n"
           f"  client          : {client or 'unreadable'}\n"
           f"  package         : {paquet or 'absent'}\n"
           "The official repository offers a newer candidate than the target: "
           "name the version, or `apt-get` installs the candidate.",
        fr=f"la cible est {court} (paquet `{cible}`).\n"
           f"  moteur (serveur) : {serveur or 'illisible'}\n"
           f"  client           : {client or 'illisible'}\n"
           f"  paquet           : {paquet or 'absent'}\n"
           "Le dépôt officiel propose un candidat plus récent que la cible : "
           "nommez la version, sinon `apt-get` installe le candidat.",
    )


def test_les_paquets_du_moteur_sont_retenus_a_la_nouvelle_version(host, ref) -> None:
    """Les six paquets restent retenus, et seuls les trois du moteur ont bougé.

    La retenue transforme une montée en geste décidé. Une montée qui la lève
    sans la reposer laisse le prochain `apt upgrade` déplacer le moteur sans
    que personne l'ait voulu. Les trois autres paquets (containerd.io et les
    deux plugins) ne sont pas dans le périmètre de la montée : les monter aussi
    changerait ce que la leçon a mesuré.
    """
    cible = ref["cible"]
    retenus = set(host.run("apt-mark showhold").stdout.split())
    attendus = set(PAQUETS_MOTEUR) | set(PAQUETS_AUTRES)
    manquants = sorted(attendus - retenus)
    versions = {nom: _version_paquet(host, nom) for nom in PAQUETS_MOTEUR}
    en_retard = {nom: v for nom, v in versions.items() if v != cible}

    assert not en_retard, message(
        en=f"the engine packages are not all in `{cible}`: {en_retard}.",
        fr=f"les paquets du moteur ne sont pas tous en `{cible}` : {en_retard}.",
    )
    assert not manquants, message(
        en=f"these packages are no longer held: {manquants}.\nA hold lifted "
           "for the climb must be set again, otherwise the next `apt upgrade` "
           "moves the engine on its own.",
        fr=f"ces paquets ne sont plus retenus : {manquants}.\nUne retenue levée "
           "pour la montée se repose, sinon le prochain `apt upgrade` déplace "
           "le moteur tout seul.",
    )
    autres = {nom: _version_paquet(host, nom) for nom in PAQUETS_AUTRES}
    assert all(autres.values()), message(
        en=f"a package outside the engine is missing: {autres}.",
        fr=f"un paquet hors du moteur est absent : {autres}.",
    )


def test_live_restore_est_actif_et_les_options_de_journal_demeurent(host, ref) -> None:
    """Le réglage est posé ET la configuration d'origine a survécu.

    Les deux moitiés se jugent ensemble : écrire `{"live-restore": true}` à la
    place du fichier active le réglage et efface sans bruit les options de
    journal, et ne rien écrire les conserve toutes. Le contrôle lit le fichier,
    pour les options, et le démon en marche, pour le réglage : un fichier juste
    que le démon n'a pas relu ne protège aucun conteneur.
    """
    fichier = host.file("/etc/docker/daemon.json")
    assert fichier.exists, message(
        en="/etc/docker/daemon.json is missing: the original configuration, "
           "with its log options, is gone.",
        fr="/etc/docker/daemon.json est absent : la configuration d'origine, "
           "avec ses options de journal, a disparu.",
    )
    try:
        config = json.loads(fichier.content_string)
    except ValueError:
        pytest.fail(message(
            en="/etc/docker/daemon.json is not valid JSON: the daemon cannot "
               "read it.",
            fr="/etc/docker/daemon.json n'est pas un JSON valide : le démon ne "
               "peut pas le lire.",
        ))
    origine = ref["options"]

    assert config.get("log-driver") == origine["log-driver"] and config.get(
        "log-opts"
    ) == origine["log-opts"], message(
        en="the original log options are not all kept.\n"
           f"  expected : log-driver={origine['log-driver']}, "
           f"log-opts={origine['log-opts']}\n"
           f"  found    : log-driver={config.get('log-driver')}, "
           f"log-opts={config.get('log-opts')}\n"
           "Merge the setting into the existing file instead of replacing it.",
        fr="les options de journal d'origine ne sont pas toutes conservées.\n"
           f"  attendu : log-driver={origine['log-driver']}, "
           f"log-opts={origine['log-opts']}\n"
           f"  trouvé  : log-driver={config.get('log-driver')}, "
           f"log-opts={config.get('log-opts')}\n"
           "Fusionnez le réglage dans le fichier existant au lieu de le "
           "remplacer.",
    )
    assert config.get("live-restore") is True, message(
        en="`live-restore` is not set to true in /etc/docker/daemon.json.",
        fr="`live-restore` n'est pas à true dans /etc/docker/daemon.json.",
    )
    actif = host.run("docker info --format '{{.LiveRestoreEnabled}}'").stdout.strip()
    assert actif == "true", message(
        en=f"the file carries the setting but the running daemon reports "
           f"`LiveRestoreEnabled={actif or 'unreadable'}`.\nA reload makes "
           "the daemon read it without stopping the containers.",
        fr=f"le fichier porte le réglage mais le démon en marche annonce "
           f"`LiveRestoreEnabled={actif or 'illisible'}`.\nUn rechargement "
           "fait relire le fichier au démon sans arrêter les conteneurs.",
    )


def test_le_service_temoin_n_a_jamais_ete_relance(host, ref) -> None:
    """Le processus, l'heure de démarrage et le compteur disent la même chose.

    Sans `live-restore`, redémarrer le démon arrête le conteneur puis le relance
    avec un nouveau processus : sa politique de redémarrage le veut. Rien ne
    l'annonce. Trois mesures indépendantes le révèlent : le PID a changé,
    l'heure de démarrage a changé, et le compteur de battements est retombé à 1.
    Le compteur d'un témoin jamais relancé monte de un en un, sans trou, depuis
    la première ligne du fichier.
    """
    _exiger_montee(host, ref)
    nom = ref["temoin"]
    etat = host.run(
        "docker inspect -f '{{.State.StartedAt}}|{{.State.Pid}}|{{.State.Running}}' %s",
        nom,
    )
    assert etat.rc == 0, message(
        en=f"the witness container `{nom}` no longer exists.",
        fr=f"le conteneur témoin `{nom}` n'existe plus.",
    )
    demarre_le, pid, en_marche = etat.stdout.strip().split("|")
    assert en_marche == "true", message(
        en=f"the witness `{nom}` is not running.",
        fr=f"le témoin `{nom}` ne tourne pas.",
    )
    assert demarre_le == ref["demarre_le"] and pid == ref["pid"], message(
        en=f"the witness was restarted.\n  start time : {demarre_le} "
           f"(was {ref['demarre_le']})\n  process    : {pid} (was {ref['pid']})\n"
           "Restarting the daemon stops its containers unless `live-restore` "
           "was set BEFORE the climb.",
        fr=f"le témoin a été relancé.\n  heure de démarrage : {demarre_le} "
           f"(c'était {ref['demarre_le']})\n  processus          : {pid} "
           f"(c'était {ref['pid']})\n"
           "Redémarrer le démon arrête ses conteneurs, sauf si `live-restore` "
           "a été posé AVANT la montée.",
    )

    lignes = host.run("docker exec %s cat /data/pouls", nom).stdout.split("\n")
    numeros = [int(ligne.split()[0]) for ligne in lignes if ligne.strip()]
    saut = next(
        (i for i in range(1, len(numeros)) if numeros[i] != numeros[i - 1] + 1),
        None,
    )
    assert numeros and numeros[0] == 1 and saut is None, message(
        en="the heartbeat counter is not continuous"
           + (f" (it jumps after beat {numeros[saut - 1]})" if saut else "")
           + ".\nA counter that falls back to 1 means the service was "
           "restarted, whatever its container looks like now.",
        fr="le compteur de battements n'est pas continu"
           + (f" (il saute après le battement {numeros[saut - 1]})" if saut else "")
           + ".\nUn compteur qui retombe à 1 dit que le service a été relancé, "
           "quel que soit l'aspect actuel de son conteneur.",
    )


def test_la_donnee_du_temoin_est_intacte(host, ref) -> None:
    """La donnée du volume est celle du départ, octet pour octet.

    Les volumes ne figurent pas dans la sauvegarde de `/etc/docker`, et un
    retour en arrière ne les restaure pas : la montée ne doit pas les toucher.
    L'empreinte relevée par le setup est comparée à celle d'aujourd'hui, lue
    dans le conteneur qui monte le volume.
    """
    _exiger_montee(host, ref)
    nom = ref["temoin"]
    res = host.run("docker exec %s sha256sum /data/abonnes.csv", nom)
    assert res.rc == 0, message(
        en="the witness data file cannot be read: the container or the file "
           "is gone.",
        fr="la donnée du témoin est illisible : le conteneur ou le fichier a "
           "disparu.",
    )
    empreinte = res.stdout.split()[0]
    assert empreinte == ref["empreinte"], message(
        en=f"the data changed.\n  now    : {empreinte}\n  before : "
           f"{ref['empreinte']}",
        fr=f"la donnée a changé.\n  maintenant : {empreinte}\n  avant      : "
           f"{ref['empreinte']}",
    )
