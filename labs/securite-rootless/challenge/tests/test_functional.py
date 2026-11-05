"""Prouve qu'un second moteur Docker tourne vraiment sans privileges.

HUIT CONTROLES, un par propriete prouvee, et le decoupage est le sujet de cette
reecriture. Le fichier precedent n'en portait que DEUX pour les memes faits : le
second en portait NEUF a lui seul, du chargement d'image jusqu'au refus d'un
pair sans reseau. Trois consequences, toutes mesurees :

  - le bareme mentait. Neuf exigences valaient un point sur deux, donc l'echec
    d'une seule coutait la moitie du lab ;
  - l'arret au premier echec masquait les huit autres. Un `network create` qui
    rate, et plus rien n'est dit de la persistance, du loopback, des pairs ;
  - les `assert` du bloc `finally` MASQUAIENT l'echec reel. Mesure le
    2026-11-05 : une AssertionError levee dans un `finally` remplace celle du
    `try`, et l'apprenant lisait « le nettoyage a echoue » la ou son vrai defaut
    etait « le pair sans reseau n'a pas ete refuse ». Le lab accusait le mauvais
    geste.

CE QUE L'APPRENANT LIVRE, ET CE QUE LES CONTROLES PROUVENT. Le `setup.yaml` pose
le compte dedie, sa plage de sous-identifiants, son service utilisateur, son
lingering et l'image epinglee. Il laisse UN seul geste, et sa tache le dit :
« Reload systemd without starting the learner's daemon ».

L'apprenant demarre donc le service utilisateur du compte dedie. C'est un geste
et un seul, mais c'est le geste difficile du rootless : un compte systeme sans
session n'a ni `XDG_RUNTIME_DIR` ni bus DBus, et `systemctl --user` echoue sans
eux. Tout le reste de ce fichier, le reseau, le volume, le serveur HTTP et ses
deux pairs, est fabrique PAR LES CONTROLES pour prouver que le moteur ainsi
demarre fonctionne reellement, et non qu'il repond seulement a `info`.

L'enonce annoncait ce decor comme des livrables. C'etait le defaut inverse de
celui corrige partout ailleurs dans ce catalogue : non pas une exigence mesuree
sans etre annoncee, mais une exigence ANNONCEE SANS ETRE DEMANDEE. Un apprenant
lisant « son moteur distinct doit executer un vrai service HTTP » montait un
serveur pour rien, puis voyait passer un `check` auquel il n'avait pas touche.
Les deux enonces sont remis en accord avec ce fichier.
"""

from __future__ import annotations

import json
import shlex
import time
import uuid
import warnings

import pytest

from conftest import lab_host, message

IMAGE = "python:3.14.10-slim-trixie@sha256:3cabfd7d7aaf394e6040e79fa1eec6ca1c52b74ed9188650472695d9a9326999"

# Le serveur met un instant a ecouter apres le `run`. On reessaie plutot que
# d'attendre une duree fixe, qui serait soit trop courte sur une VM chargee,
# soit du temps perdu a chaque passage.
TENTATIVES_HTTP = 30
DELAI_ENTRE_TENTATIVES = 0.2


def _systemctl_utilisateur(host, uid, *args):
    """Joue `systemctl --user` pour le compte dedie, qui n'a pas de session.

    Les deux variables sont le piege reel du rootless : sans elles, la commande
    echoue avec « Failed to connect to bus », et c'est precisement ce que
    l'apprenant doit decouvrir pour demarrer son service.
    """
    return host.run(shlex.join([
        "sudo", "-n", "-u", "dsoxlab-rootless", "env",
        f"XDG_RUNTIME_DIR=/run/user/{uid}",
        f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus",
        "systemctl", "--user", *args,
    ]))


@pytest.fixture(scope="module")
def host():
    return lab_host("docker.lab")


@pytest.fixture(scope="module")
def socle(host):
    """Releve l'etat du demon dedie SANS rien exiger.

    Cette fixture ne leve jamais : elle rend les faits, et chaque controle juge
    celui qui le concerne. C'est ce qui permet a un lab non commence de rendre
    huit echecs qui disent chacun quoi faire, au lieu de huit erreurs de
    fixture qui ne disent qu'une chose, une fois.
    """
    faits = {
        "etat_present": False, "uid": None, "socket": None,
        "service_actif": False, "service_sortie": "",
        "info_rc": None, "info_stderr": "", "options": None,
        "main_pid": None, "uid_compte": None, "uid_processus": None,
    }

    fichier = host.file("/opt/dsoxlab-securite-rootless/state.json")
    if not fichier.exists:
        return faits
    faits["etat_present"] = True
    etat = json.loads(fichier.content_string)
    faits["uid"] = etat["uid"]
    faits["socket"] = etat["socket"]

    service = _systemctl_utilisateur(host, etat["uid"], "is-active", "dsoxlab-rootless.service")
    faits["service_sortie"] = (service.stdout or service.stderr).strip()
    faits["service_actif"] = service.rc == 0 and service.stdout.strip() == "active"
    if not faits["service_actif"]:
        return faits

    info = host.run("docker -H unix://%s info --format '{{json .SecurityOptions}}'", etat["socket"])
    faits["info_rc"] = info.rc
    faits["info_stderr"] = info.stderr[-500:]
    if info.rc == 0:
        faits["options"] = json.loads(info.stdout)

    montre = _systemctl_utilisateur(
        host, etat["uid"], "show", "dsoxlab-rootless.service", "--property", "MainPID", "--value",
    )
    compte = host.run("id -u dsoxlab-rootless")
    if montre.rc == 0 and compte.rc == 0:
        faits["main_pid"] = montre.stdout.strip()
        faits["uid_compte"] = compte.stdout.strip()
        proprietaire = host.run("ps -o uid= -p %s", faits["main_pid"])
        if proprietaire.rc == 0:
            faits["uid_processus"] = proprietaire.stdout.strip()
    return faits


@pytest.fixture(scope="module")
def banc(host, socle):
    """Monte l'epreuve SUR le demon rootless, collecte les faits, demonte.

    Elle n'exige rien non plus : si le demon n'est pas utilisable, elle rend
    None et les controles qui en dependent le disent chacun a leur maniere.

    Le demontage ne porte AUCUN `assert`, et c'est la correction de fond du
    fichier precedent. Un nettoyage en echec emet un avertissement visible,
    jamais une exception qui remplacerait l'echec que l'apprenant doit lire. Le
    menage du banc, lui, est controle a sa vraie place : la photographie du
    moteur que `valider-labs.py` prend avant et apres le lab refuse tout objet
    laisse derriere. Le bareme note l'apprenant, la photographie note le banc.
    """
    if not socle["service_actif"] or socle["options"] is None:
        yield None
        return

    socket = socle["socket"]

    def docker(*args):
        return host.run(shlex.join(["docker", "-H", f"unix://{socket}", *args]))

    suffixe = uuid.uuid4().hex[:12]
    nom = f"dsoxlab-rootless-check-{suffixe}"
    reseau, volume = nom + "-net", nom + "-data"
    marqueur = uuid.uuid4().hex

    faits = {
        "racine_rootful": "", "racine_rootless": "",
        "image_dans_le_rootful": None,
        "chargement_rc": None, "chargement_stderr": "", "image_id": None,
        "reseau_rc": None, "volume_rc": None, "ecriture_rc": None,
        "cycles": [],
    }

    # LA SEPARATION SE PROUVE PAR LES RACINES, PAS PAR UNE ABSENCE. Premiere
    # ecriture de ce controle : exiger que l'image epinglee soit ABSENTE du
    # moteur rootless avant chargement. Mesure le 2026-11-05, deux defauts :
    #
    #   - le controle n'etait pas REJOUABLE. Le banc charge l'image et ne la
    #     retirait pas, donc un second `check` la trouvait presente et refusait.
    #     Mesure : premier `dsoxlab check` rc=0, second rc=1, sans que rien ne
    #     change entre les deux. Un apprenant qui relance son check voyait son
    #     lab passer au rouge pour l'avoir relance ;
    #   - et il accusait la mauvaise chose. Une image presente peut venir d'un
    #     apprenant curieux qui l'a chargee lui-meme, ce que l'enonce ne lui
    #     interdit pas. Le controle lui aurait repondu « vos deux moteurs ne
    #     tiennent pas des stockages distincts », ce qui est faux.
    #
    # Les racines de donnees, elles, se lisent a l'instant, ne dependent
    # d'aucun etat anterieur et disent la separation directement. Mesure sur
    # docker.lab : `/var/lib/docker` pour le rootful,
    # `/var/lib/dsoxlab-rootless/.local/share/docker` pour le rootless.
    for cle, commande in (
        ("racine_rootful", "docker info --format '{{.DockerRootDir}}'"),
        ("racine_rootless", f"docker -H unix://{socket} info --format '{{{{.DockerRootDir}}}}'"),
    ):
        releve = host.run(commande)
        if releve.rc == 0:
            faits[cle] = releve.stdout.strip()

    # ON IDENTIFIE PAR ID, JAMAIS PAR REFERENCE, et ce n'est pas un detail de
    # style. Mesure le 2026-11-05 sur docker.lab : une image tiree PAR DIGEST
    # puis transferee par `save | load` arrive dans le moteur de destination
    # SANS sa reference. `docker -H <rootless> image ls` la montre en
    # `<none>:<none>`, un `image inspect <reference>` y echoue, et un
    # `image inspect <id>` y reussit. L'ID, lui, est le meme des deux cotes.
    #
    # Le test precedent contournait cela sans le dire : son « identifiez
    # l'image epinglee exacte chargee dans le moteur rootless » lancait un
    # `docker image inspect` SANS `-H`, donc interrogeait le moteur ROOTFUL. Il
    # passait au vert en mesurant l'autre moteur que celui qu'il nommait.
    rootful = host.run("docker image inspect %s --format '{{.Id}}'", IMAGE)
    faits["image_dans_le_rootful"] = rootful.rc == 0
    identifiant = rootful.stdout.strip() if rootful.rc == 0 else ""

    charge = host.run("docker image save %s | docker -H unix://%s image load", IMAGE, socket)
    faits["chargement_rc"] = charge.rc
    faits["chargement_stderr"] = charge.stderr[-500:]
    if identifiant:
        identite = docker("image", "inspect", identifiant, "--format", "{{.Id}}")
        if identite.rc == 0 and identite.stdout.strip().startswith("sha256:"):
            faits["image_id"] = identite.stdout.strip()

    reseau_cree = volume_cree = False
    try:
        if faits["image_id"] is None:
            yield faits
            return

        cree = docker("network", "create", reseau)
        faits["reseau_rc"] = cree.rc
        reseau_cree = cree.rc == 0
        cree = docker("volume", "create", volume)
        faits["volume_rc"] = cree.rc
        volume_cree = cree.rc == 0
        if not (reseau_cree and volume_cree):
            yield faits
            return

        ecriture = docker(
            "run", "--rm", "--network", "none", "-v", f"{volume}:/data", faits["image_id"],
            "python", "-c",
            f"from pathlib import Path; Path('/data/value').write_text({marqueur!r})",
        )
        faits["ecriture_rc"] = ecriture.rc
        if ecriture.rc != 0:
            yield faits
            return

        # DEUX recreations, parce qu'une seule ne distingue pas un volume nomme
        # d'un stockage de conteneur qui survit a un simple redemarrage.
        for _ in range(2):
            cycle = {
                "demarrage_rc": None, "port": "", "port_rc": None,
                "http_rc": None, "http_corps": "", "pair_rc": None,
                "pair_corps": "", "sans_reseau_rc": None, "retrait_rc": None,
            }
            faits["cycles"].append(cycle)

            demarrage = docker(
                "run", "-d", "--name", nom, "--network", reseau,
                "--network-alias", "rootless-server", "-p", "127.0.0.1::8080",
                "-v", f"{volume}:/data:ro", faits["image_id"], "python", "-m",
                "http.server", "8080", "--bind", "0.0.0.0",  # noqa: S104 -- dans le conteneur ; la publication de la VM reste sur loopback.
                "--directory", "/data",
            )
            cycle["demarrage_rc"] = demarrage.rc
            if demarrage.rc != 0:
                break

            port = docker("port", nom, "8080/tcp")
            cycle["port_rc"] = port.rc
            cycle["port"] = port.stdout.strip()
            if port.rc != 0 or not cycle["port"]:
                break

            requete = (
                "import urllib.request;"
                f"print(urllib.request.urlopen('http://{cycle['port']}/value',timeout=2).read().decode())"
            )
            for _essai in range(TENTATIVES_HTTP):
                reponse = host.run(shlex.join(["python3", "-c", requete]))
                if reponse.rc == 0:
                    break
                time.sleep(DELAI_ENTRE_TENTATIVES)
            cycle["http_rc"] = reponse.rc
            cycle["http_corps"] = reponse.stdout.strip()

            programme = (
                "import urllib.request;"
                "print(urllib.request.urlopen('http://rootless-server:8080/value',timeout=3).read().decode())"
            )
            pair = docker("run", "--rm", "--network", reseau, faits["image_id"], "python", "-c", programme)
            cycle["pair_rc"] = pair.rc
            cycle["pair_corps"] = pair.stdout.strip()
            sans_reseau = docker("run", "--rm", "--network", "none", faits["image_id"], "python", "-c", programme)
            cycle["sans_reseau_rc"] = sans_reseau.rc

            retrait = docker("rm", "-f", nom)
            cycle["retrait_rc"] = retrait.rc
            if retrait.rc != 0:
                break

        faits["marqueur"] = marqueur
        yield faits
    finally:
        # AUCUN `assert` ici : voir la docstring. Les echecs de menage
        # s'annoncent, ils n'effacent pas le diagnostic de l'apprenant.
        restes = []
        if docker("container", "inspect", nom).rc == 0 and docker("rm", "-f", nom).rc != 0:
            restes.append(f"conteneur {nom}")
        for genre, objet, cree in (("volume", volume, volume_cree), ("network", reseau, reseau_cree)):
            if cree and docker(genre, "rm", objet).rc != 0:
                restes.append(f"{genre} {objet}")
        # L'IMAGE CHARGEE PART AUSSI, et c'est ce qui rend le controle
        # rejouable. Sans ce retrait, le banc laissait derriere lui l'etat
        # qu'il venait de produire : mesure le 2026-11-05, un premier
        # `dsoxlab check` sortait en 0 et le second en 1, le lab passant au
        # rouge pour la seule raison qu'on l'avait relance. Un controle qui ne
        # se rejoue pas ne mesure que son premier passage.
        if faits["image_id"] and docker("image", "rm", "-f", faits["image_id"]).rc != 0:
            restes.append(f"image {faits['image_id'][:19]}")
        if restes:
            warnings.warn(
                "Le banc n'a pas pu retirer : " + ", ".join(restes)
                + ". La photographie du moteur le refusera, et c'est sa place.",
                stacklevel=1,
            )


# ───────────────────────────── les huit contrôles ────────────────────────────


def test_le_service_dedie_est_actif(socle):
    """Le seul geste demandé à l'apprenant, et le plus difficile du lab."""
    assert socle["etat_present"], message(
        en="The prepared rootless daemon state is missing; the lab is not set up.",
        fr="L'état préparé du démon rootless est absent : le lab n'est pas monté.",
    )
    assert socle["service_actif"], message(
        en="Start the dedicated dsoxlab-rootless user service. `systemctl --user` on a "
           f"session-less system account needs XDG_RUNTIME_DIR and DBUS_SESSION_BUS_ADDRESS. "
           f"Reported: {socle['service_sortie'] or 'nothing'}.",
        fr="Démarrez le service utilisateur dédié dsoxlab-rootless. `systemctl --user` sur un "
           f"compte système sans session exige XDG_RUNTIME_DIR et DBUS_SESSION_BUS_ADDRESS. "
           f"Rapporté : {socle['service_sortie'] or 'rien'}.",
    )


def test_le_demon_dedie_annonce_le_mode_rootless(socle):
    """Un démon qui répond n'est pas un démon sans privilèges."""
    assert socle["service_actif"], message(
        en="Start the dedicated rootless user service first: nothing else can be measured.",
        fr="Démarrez d'abord le service utilisateur rootless dédié : rien d'autre n'est mesurable.",
    )
    assert socle["info_rc"] == 0, message(
        en=f"The rootless Docker socket is not responding: {socle['info_stderr']}",
        fr=f"Le socket Docker rootless ne répond pas : {socle['info_stderr']}",
    )
    assert socle["options"] is not None and any(
        "rootless" in option.lower() for option in socle["options"]
    ), message(
        en=f"The dedicated daemon must report rootless mode. Reported: {socle['options']}.",
        fr=f"Le démon dédié doit indiquer le mode rootless. Rapporté : {socle['options']}.",
    )


def test_le_processus_du_service_appartient_au_compte_non_privilegie(socle):
    """La preuve que `info` ne donne pas : qui possède réellement le processus."""
    assert socle["service_actif"], message(
        en="Start the dedicated rootless user service first: nothing else can be measured.",
        fr="Démarrez d'abord le service utilisateur rootless dédié : rien d'autre n'est mesurable.",
    )
    assert socle["main_pid"] not in (None, "", "0"), message(
        en="The dedicated service reports no running main process.",
        fr="Le service dédié ne rapporte aucun processus principal en cours.",
    )
    assert socle["uid_processus"] is not None and socle["uid_compte"] is not None, message(
        en="Could not read the owner of the service process.",
        fr="Impossible de lire le propriétaire du processus du service.",
    )
    assert socle["uid_processus"] != "0", message(
        en="The service process runs as root: this is not a rootless daemon.",
        fr="Le processus du service tourne en root : ce n'est pas un démon rootless.",
    )
    assert socle["uid_processus"] == socle["uid_compte"], message(
        en=f"The service process must belong to the dedicated account "
           f"(uid {socle['uid_compte']}), not to uid {socle['uid_processus']}.",
        fr=f"Le processus du service doit appartenir au compte dédié "
           f"(uid {socle['uid_compte']}), pas à l'uid {socle['uid_processus']}.",
    )


def test_le_stockage_d_images_du_demon_rootless_est_distinct(banc):
    """Une propriété que le lab annonçait et ne mesurait pas.

    Le scénario demande d'« expliquer le stockage d'images distinct », et rien
    ne le prouvait : l'ancien contrôle chargeait l'image et constatait qu'elle
    était là, ce que le moteur rootful aurait aussi bien rendu vrai.
    """
    assert banc is not None, message(
        en="Start the dedicated rootless user service first: nothing else can be measured.",
        fr="Démarrez d'abord le service utilisateur rootless dédié : rien d'autre n'est mesurable.",
    )
    assert banc["image_dans_le_rootful"], message(
        en="The pinned image is missing from the VM's rootful engine; setup did not run.",
        fr="L'image épinglée manque au moteur rootful de la VM : le setup n'a pas tourné.",
    )
    assert banc["racine_rootful"], message(
        en="Could not read the rootful engine's data root.",
        fr="Impossible de lire la racine de données du moteur rootful.",
    )
    assert banc["racine_rootless"], message(
        en="Could not read the rootless engine's data root.",
        fr="Impossible de lire la racine de données du moteur rootless.",
    )
    assert banc["racine_rootless"] != banc["racine_rootful"], message(
        en=f"Both engines share the same data root ({banc['racine_rootful']}): the rootless "
           f"daemon is not holding its own image store.",
        fr=f"Les deux moteurs partagent la même racine de données ({banc['racine_rootful']}) : "
           f"le démon rootless ne tient pas son propre stockage d'images.",
    )
    assert banc["chargement_rc"] == 0, message(
        en=f"Loading the pinned workload into the rootless store failed: {banc['chargement_stderr']}",
        fr=f"Le chargement du workload épinglé dans le stockage rootless a échoué : {banc['chargement_stderr']}",
    )
    assert banc["image_id"] is not None, message(
        en="The pinned image is not identifiable in the rootless engine after loading.",
        fr="L'image épinglée n'est pas identifiable dans le moteur rootless après chargement.",
    )


def test_le_demon_rootless_cree_son_reseau_et_son_volume(banc):
    """Sans privilèges, créer un réseau passe par un espace de noms délégué."""
    assert banc is not None, message(
        en="Start the dedicated rootless user service first: nothing else can be measured.",
        fr="Démarrez d'abord le service utilisateur rootless dédié : rien d'autre n'est mesurable.",
    )
    assert banc["image_id"] is not None, message(
        en="The workload image is not available in the rootless engine.",
        fr="L'image du workload n'est pas disponible dans le moteur rootless.",
    )
    assert banc["reseau_rc"] == 0, message(
        en="The rootless daemon must create its own network.",
        fr="Le démon rootless doit créer son propre réseau.",
    )
    assert banc["volume_rc"] == 0, message(
        en="The rootless daemon must create its own named volume.",
        fr="Le démon rootless doit créer son propre volume nommé.",
    )


def test_une_donnee_nouvelle_survit_a_deux_recreations_du_conteneur(banc):
    """Deux recréations, parce qu'une seule ne prouve pas le volume nommé."""
    assert banc is not None, message(
        en="Start the dedicated rootless user service first: nothing else can be measured.",
        fr="Démarrez d'abord le service utilisateur rootless dédié : rien d'autre n'est mesurable.",
    )
    assert banc["ecriture_rc"] == 0, message(
        en="Writing a fresh value through a rootless container failed.",
        fr="L'écriture d'une valeur nouvelle par un conteneur rootless a échoué.",
    )
    assert len(banc["cycles"]) == 2, message(
        en=f"Only {len(banc['cycles'])} of the 2 recreations could run.",
        fr=f"Seulement {len(banc['cycles'])} des 2 recréations ont pu être jouées.",
    )
    for rang, cycle in enumerate(banc["cycles"], start=1):
        assert cycle["demarrage_rc"] == 0, message(
            en=f"Recreation {rang}: the rootless workload did not start.",
            fr=f"Recréation {rang} : le workload rootless n'a pas démarré.",
        )
        assert cycle["http_rc"] == 0, message(
            en=f"Recreation {rang}: loopback HTTP never answered after "
               f"{TENTATIVES_HTTP} attempts.",
            fr=f"Recréation {rang} : HTTP sur la boucle locale n'a jamais répondu "
               f"après {TENTATIVES_HTTP} tentatives.",
        )
        assert cycle["http_corps"] == banc["marqueur"], message(
            en=f"Recreation {rang}: the named volume did not keep the fresh value.",
            fr=f"Recréation {rang} : le volume nommé n'a pas conservé la valeur nouvelle.",
        )
        assert cycle["retrait_rc"] == 0, message(
            en=f"Recreation {rang}: removing only the trial container failed.",
            fr=f"Recréation {rang} : le retrait du seul conteneur d'essai a échoué.",
        )


def test_la_publication_reste_sur_un_port_loopback_non_privilegie(banc):
    """Sans privilèges, aucun port sous 1024, et rien hors de la boucle locale."""
    assert banc is not None, message(
        en="Start the dedicated rootless user service first: nothing else can be measured.",
        fr="Démarrez d'abord le service utilisateur rootless dédié : rien d'autre n'est mesurable.",
    )
    assert banc["cycles"], message(
        en="No recreation ran, so publication could not be observed.",
        fr="Aucune recréation n'a été jouée : la publication n'a pas pu être observée.",
    )
    for rang, cycle in enumerate(banc["cycles"], start=1):
        assert cycle["port_rc"] == 0 and cycle["port"], message(
            en=f"Recreation {rang}: the rootless daemon published no port.",
            fr=f"Recréation {rang} : le démon rootless n'a publié aucun port.",
        )
        assert cycle["port"].startswith("127.0.0.1:"), message(
            en=f"Recreation {rang}: rootless publication must stay on loopback, "
               f"got {cycle['port']}.",
            fr=f"Recréation {rang} : la publication rootless doit rester sur la boucle "
               f"locale, obtenu {cycle['port']}.",
        )
        numero = int(cycle["port"].rsplit(":", 1)[1])
        assert numero >= 1024, message(
            en=f"Recreation {rang}: a rootless daemon cannot hold privileged port {numero}.",
            fr=f"Recréation {rang} : un démon rootless ne peut pas tenir le port privilégié {numero}.",
        )


def test_un_pair_du_reseau_joint_le_service_et_un_pair_sans_reseau_est_refuse(banc):
    """Les deux sens comptent : sans le refus, le contrôle ne prouve rien."""
    assert banc is not None, message(
        en="Start the dedicated rootless user service first: nothing else can be measured.",
        fr="Démarrez d'abord le service utilisateur rootless dédié : rien d'autre n'est mesurable.",
    )
    assert banc["cycles"], message(
        en="No recreation ran, so network peers could not be observed.",
        fr="Aucune recréation n'a été jouée : les pairs réseau n'ont pas pu être observés.",
    )
    for rang, cycle in enumerate(banc["cycles"], start=1):
        assert cycle["pair_rc"] == 0, message(
            en=f"Recreation {rang}: an authorized peer of the rootless network was refused.",
            fr=f"Recréation {rang} : un pair autorisé du réseau rootless a été refusé.",
        )
        assert cycle["pair_corps"] == banc["marqueur"], message(
            en=f"Recreation {rang}: the authorized peer did not read the expected value.",
            fr=f"Recréation {rang} : le pair autorisé n'a pas lu la valeur attendue.",
        )
        assert cycle["sans_reseau_rc"] != 0, message(
            en=f"Recreation {rang}: a networkless peer REACHED the service. The rootless "
               f"network does not isolate, and the whole point of the previous "
               f"assertion collapses with it.",
            fr=f"Recréation {rang} : un pair sans réseau a ATTEINT le service. Le réseau "
               f"rootless n'isole pas, et l'assertion précédente perd tout son sens "
               f"avec lui.",
        )
