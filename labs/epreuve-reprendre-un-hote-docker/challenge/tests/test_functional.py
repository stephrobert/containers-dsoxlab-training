"""Tests fonctionnels de l'épreuve de reprise d'hôte : cinq contrôles de poids égal.

C'EST UNE ÉPREUVE D'EXPLOITATION, la plus large du parcours : elle touche le
démon, le disque, les comptes et l'exposition de l'API. Les messages nomment ce
qui manque à l'état final, jamais la commande qui l'apporterait.

L'EXIGENCE CRITIQUE est le contrôle 2 : le volume de l'application supprimé.
C'est le piège, et il est le plus réaliste du catalogue. Pour reprendre de la
place, la commande qui vient à l'esprit est `docker system prune`, et l'une de
ses options emporte les volumes. La donnée part alors avec le ménage, et rien ne
la ramène. Aucun total ne la compense.

CE QUE CES CONTRÔLES MESURENT, ET CE QU'ILS NE MESURENT PAS. Le brief parlait
d'un « espace libre au-dessus du seuil ». Un seuil absolu n'aurait rien voulu
dire sur cette machine, qui a vingt gigaoctets dont quatorze libres : le lab ne
peut pas remplir un disque sans risquer de le remplir pour de bon. Le contrôle
mesure donc ce qui est vraiment en jeu, et qui est vérifiable : les objets
récupérables ont été rendus, images pendantes et cache de build, et le volume
utile est resté. C'est la compétence, et non le chiffre.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, ce qui permet de lire `/etc/docker`, les unités
systemd et les sockets d'écoute.
"""

from __future__ import annotations

import json
import re
import uuid

import pytest

from conftest import lab_host, message

APPLICATION = "application"
OUTIL = "inventaire-outil"
IMAGE_SERVICE = "lab-reprise:1.0"
IMAGE_PROXY = "lab-reprise-proxy:1.0"
VOLUME = "dsoxlab-reprise-donnees"
VOLUME_SAUVEGARDES = "dsoxlab-reprise-sauvegardes"
ATELIER = "/opt/lab-reprise"
ETAT = "/root/.lab-reprise-state.json"
DAEMON_JSON = "/etc/docker/daemon.json"
STAGIAIRE = "stagiaire-parti"
EXPLOITANT = "exploitant"
SOCKET_DEMON = "/var/run/docker.sock"

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
    """Ce que le lab a relevé avant de salir la machine.

    Il porte la donnée de référence du volume, et les membres du groupe `docker`
    tels qu'ils étaient. Les deux servent à distinguer « c'est propre » de
    « c'est propre parce qu'on a tout emporté ».
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


def test_le_demon_tourne_avec_une_rotation_des_journaux(host) -> None:
    """La rotation, et elle se mesure sur un conteneur créé APRÈS.

    `daemon.json` ne suffit pas : un fichier écrit et jamais relu ne change
    rien, et le démon ne le relit qu'au redémarrage. Lire le fichier ne dirait
    donc que l'intention.

    LE CONTRÔLE CRÉE UN CONTENEUR JETABLE et lit sa configuration de
    journalisation. C'est le seul endroit où la rotation est un fait : elle
    s'applique aux conteneurs créés ensuite, et jamais rétroactivement à ceux
    qui existent déjà. C'est aussi ce que dit l'énoncé.

    ET L'APPLICATION DOIT TOURNER. Redémarrer le démon arrête les conteneurs
    sans politique de redémarrage et ne les relance pas : une reprise d'hôte
    qui laisse l'application à terre n'est pas une reprise.
    """
    valide = host.run("cat %s", DAEMON_JSON)
    assert valide.rc == 0, message(
        en=f"`{DAEMON_JSON}` does not exist. Without it the engine runs on its "
           "defaults, and the default has no log rotation at all.",
        fr=f"`{DAEMON_JSON}` n'existe pas. Sans lui le moteur tourne sur ses "
           "défauts, et le défaut n'a aucune rotation des journaux.",
    )
    try:
        json.loads(valide.stdout)
    except json.JSONDecodeError as erreur:
        pytest.fail(message(
            en=f"`{DAEMON_JSON}` is not valid JSON: {erreur}\n"
               "An invalid file stops the daemon from starting at all, which is "
               "worse than no file.",
            fr=f"`{DAEMON_JSON}` n'est pas du JSON valide : {erreur}\n"
               "Un fichier invalide empêche le démon de démarrer, ce qui est "
               "pire qu'un fichier absent.",
        ))

    jetable = f"temoin-rotation-{uuid.uuid4().hex[:8]}"
    try:
        cree = host.run(
            "docker create --name %s --entrypoint sh %s -c %s",
            jetable, IMAGE_SERVICE, "true",
        )
        assert cree.rc == 0, message(
            en=f"the lab could not create a witness container to read the "
               f"rotation from:\n  {cree.stderr.strip()[:200]}",
            fr=f"le lab n'a pas pu créer le conteneur témoin qui sert à lire la "
               f"rotation :\n  {cree.stderr.strip()[:200]}",
        )
        lu = host.run(
            "docker container inspect %s --format %s",
            jetable,
            "{{json .HostConfig.LogConfig}}",
        )
        config = json.loads(lu.stdout) if lu.rc == 0 else {}
    finally:
        host.run("docker rm -f %s", jetable)

    options = config.get("Config") or {}
    assert options.get("max-size"), message(
        en=f"a container created now carries no log size limit.\n"
           f"  its log configuration: {json.dumps(config)}\n"
           "The daemon only rereads its configuration when it restarts, and the "
           "rotation applies to containers created afterwards.",
        fr=f"un conteneur créé maintenant ne porte aucune limite de taille de "
           f"journal.\n  sa configuration de journalisation : "
           f"{json.dumps(config)}\n"
           "Le démon ne relit sa configuration qu'au redémarrage, et la "
           "rotation s'applique aux conteneurs créés ensuite.",
    )

    etat = host.run(
        "docker container inspect %s --format %s", APPLICATION, "{{.State.Status}}"
    )
    assert etat.rc == 0 and etat.stdout.strip() == "running", message(
        en=f"`{APPLICATION}` is not running.\n"
           f"  its state: {etat.stdout.strip() or '(absent)'}\n"
           "Restarting the daemon stops containers with no restart policy and "
           "does not bring them back. A host recovery that leaves the "
           "application down is not a recovery.",
        fr=f"`{APPLICATION}` ne tourne pas.\n"
           f"  son état : {etat.stdout.strip() or '(absent)'}\n"
           "Redémarrer le démon arrête les conteneurs sans politique de "
           "redémarrage et ne les relance pas. Une reprise d'hôte qui laisse "
           "l'application à terre n'est pas une reprise.",
    )


def test_la_place_est_rendue_et_le_volume_utile_est_intact(host, releve) -> None:
    """L'EXIGENCE CRITIQUE, et elle a deux faces inséparables.

    LA PREMIÈRE : la place occupée pour rien est rendue. Les images pendantes et
    le cache de build sont ce qu'un hôte non suivi accumule, et ils ne servent à
    personne.

    LA SECONDE, et c'est elle qui fait l'épreuve : le volume de l'application est
    resté, avec sa donnée. Pour reprendre de la place, la commande qui vient à
    l'esprit est `docker system prune`, et l'une de ses options emporte les
    volumes. La donnée part alors avec le ménage, et rien ne la ramène.

    LE CONTRÔLE COMPARE LA DONNÉE, pas la seule existence du volume : un volume
    recréé vide porte le bon nom et ne vaut rien.
    """
    attendue = releve.get("donnee")
    assert attendue, message(
        en="the lab's own measurement carries no reference value. It is taken during `dsoxlab run`: replay it.",
        fr="la mesure prise par le lab ne porte pas la donnée de référence. Elle est faite pendant `dsoxlab run` : rejouez-le.",
    )

    # LES DEUX VOLUMES NOMMÉS, et le second est le piège.
    #
    # Celui de l'application est MONTÉ : un `prune` l'épargne, donc il ne risque
    # presque rien. Celui des sauvegardes n'est monté par PERSONNE, parce qu'on
    # ne monte un volume de sauvegarde que pour sauvegarder : c'est lui que
    # `docker system prune --volumes` emporte, et c'est la perte qu'on voit en
    # production.
    existe = host.run("docker volume inspect %s", VOLUME)
    assert existe.rc == 0, message(
        en=f"the `{VOLUME}` volume no longer exists.\n"
           "`docker system prune` has options that take volumes away.",
        fr=f"le volume `{VOLUME}` n'existe plus.\n"
           "`docker system prune` a des options qui emportent les volumes.",
    )
    servie = host.run("docker exec %s cat %s", APPLICATION, "/donnees/reference")
    assert servie.rc == 0 and servie.stdout.strip() == attendue, message(
        en=f"the volume is there, and its value is not.\n"
           f"  read    : {servie.stdout.strip() or '(nothing)'}\n"
           f"  expected: {attendue}\n"
           "A volume recreated empty carries the right name and is worth "
           "nothing.",
        fr=f"le volume est là, et sa donnée n'y est pas.\n"
           f"  lu      : {servie.stdout.strip() or '(rien)'}\n"
           f"  attendu : {attendue}\n"
           "Un volume recréé vide porte le bon nom et ne vaut rien.",
    )

    empreintes = releve.get("sauvegardes") or {}
    assert empreintes, message(
        en="the lab's own measurement carries no backup digest. It is taken during `dsoxlab run`: replay it.",
        fr="la mesure prise par le lab ne porte aucune empreinte de sauvegarde. Elle est faite pendant `dsoxlab run` : rejouez-le.",
    )
    presence = host.run("docker volume inspect %s", VOLUME_SAUVEGARDES)
    assert presence.rc == 0, message(
        en=f"the `{VOLUME_SAUVEGARDES}` volume no longer exists, and it held the "
           "backups.\n"
           "It was mounted by nobody, because a backup volume is only mounted "
           "when backing up. That is exactly what `prune --volumes` takes away: "
           "A VOLUME THAT IS NOT MOUNTED IS NOT A USELESS VOLUME. No total "
           "makes up for that loss.",
        fr=f"le volume `{VOLUME_SAUVEGARDES}` n'existe plus, et il portait les "
           "sauvegardes.\n"
           "Il n'était monté par personne, parce qu'un volume de sauvegarde ne "
           "se monte que pour sauvegarder. C'est précisément ce que "
           "`prune --volumes` emporte : UN VOLUME NON MONTÉ N'EST PAS UN VOLUME "
           "INUTILE. Aucun total ne compense cette perte.",
    )
    lu = host.run(
        "docker run --rm --entrypoint sh -v %s %s -c %s",
        f"{VOLUME_SAUVEGARDES}:/sauvegardes",
        IMAGE_SERVICE,
        "cd /sauvegardes && sha256sum sauvegarde-*.txt 2>/dev/null | sort",
    )
    trouvees = {}
    for ligne in lu.stdout.splitlines():
        morceaux = ligne.split()
        if len(morceaux) == 2:
            trouvees[morceaux[1]] = morceaux[0]
    perdues = sorted(n for n, e in empreintes.items() if trouvees.get(n) != e)
    assert not perdues, message(
        en=f"backups are missing or altered:\n"
           + "\n".join(f"  {n}" for n in perdues) + "\n"
           "The volume is there and its contents are not what they were.",
        fr=f"des sauvegardes manquent ou sont altérées :\n"
           + "\n".join(f"  {n}" for n in perdues) + "\n"
           "Le volume est là et son contenu n'est pas celui qu'il était.",
    )

    # ET LE REBUT EST PARTI. Pas d'images pendantes ici : mesuré sur le magasin
    # containerd de cette version, une image dont la référence disparaît est
    # ramassée aussitôt, et la notion n'a plus d'objet. Ce qui occupe vraiment
    # la place d'un hôte non suivi, ce sont des conteneurs arrêtés et des
    # volumes anonymes dont plus personne ne sait l'usage.
    arretes = host.run(
        "docker ps -a --filter %s --format %s",
        "label=dsoxlab.lab=epreuve-reprendre-un-hote-docker",
        "{{.Names}} {{.State}}",
    )
    traine = [
        l.strip() for l in arretes.stdout.splitlines()
        if l.strip() and l.split()[-1] in {"exited", "created", "dead"}
    ]
    assert not traine, message(
        en=f"stopped containers are still taking up room:\n"
           + "\n".join(f"  {l}" for l in traine) + "\n"
           "A stopped container keeps its name, its configuration and its "
           "writable layer.",
        fr=f"des conteneurs arrêtés occupent encore la place :\n"
           + "\n".join(f"  {l}" for l in traine) + "\n"
           "Un conteneur arrêté garde son nom, sa configuration et sa couche "
           "d'écriture.",
    )

    # LE CONTRÔLE NE REGARDE QUE LES ORPHELINS QUE CE LAB A POSÉS, et c'est une
    # correction payée par la mesure. Un premier jet cherchait TOUT volume
    # anonyme, c'est-à-dire tout nom de 64 caractères sans préfixe `dsoxlab` :
    # sur une machine qui en portait un, étranger au lab, le contrôle exigeait
    # sa suppression et la solution l'emportait.
    #
    # Deux fautes en une : reprocher un volume qu'on n'a pas créé, et le faire
    # détruire. Un volume anonyme peut porter la donnée de quelqu'un d'autre, et
    # rien ne la ramène. Le défaut ne se voyait pas sur une machine propre, ce
    # qui est la pire espèce : il attendait qu'un volume traîne.
    poses = set(releve.get("volumes_orphelins") or [])
    presents = {v.strip() for v in host.run("docker volume ls -q").stdout.splitlines()
                if v.strip()}
    orphelins = sorted(poses & presents)
    assert not orphelins, message(
        en=f"{len(orphelins)} anonymous volume(s) this host accumulated are "
           "still there, with nobody knowing what they were for:\n"
           + "\n".join(f"  {v[:19]}..." for v in orphelins) + "\n"
           "They are what a `docker rm` without `-v`, repeated for months, "
           "leaves behind.",
        fr=f"{len(orphelins)} volume(s) anonyme(s) accumulés par cet hôte "
           "subsistent, sans que personne sache à quoi ils servaient :\n"
           + "\n".join(f"  {v[:19]}..." for v in orphelins) + "\n"
           "Ils sont ce qu'un `docker rm` sans `-v`, répété pendant des mois, "
           "laisse derrière lui.",
    )

    cache = host.run("docker system df --format %s", "{{.Type}}|{{.Reclaimable}}")
    recuperable = ""
    for ligne in cache.stdout.splitlines():
        if ligne.lower().startswith("build cache"):
            recuperable = ligne.split("|", 1)[1] if "|" in ligne else ""
    chiffre = re.match(r"([0-9.]+)\s*([KMGT]?)B", recuperable.strip())
    octets = 0.0
    if chiffre:
        echelle = {"": 1, "K": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}
        octets = float(chiffre.group(1)) * echelle[chiffre.group(2)]
    assert octets < 1e6, message(
        en=f"the build cache has not been purged.\n"
           f"  reclaimable: {recuperable.strip() or '(unreadable)'}\n"
           "A cache rebuilds itself: keeping it on a host that is running out "
           "of disk is keeping the wrong thing.",
        fr=f"le cache de build n'a pas été purgé.\n"
           f"  récupérable : {recuperable.strip() or '(illisible)'}\n"
           "Un cache se reconstruit : le garder sur un hôte qui manque de "
           "disque, c'est garder ce qu'il ne faut pas.",
    )


def test_le_groupe_docker_ne_porte_que_ceux_qui_doivent_y_etre(
    host, releve
) -> None:
    """Trois faits, et le troisième est celui qu'on oublie.

    Le stagiaire parti doit sortir. L'exploitant doit rester. ET PERSONNE
    D'AUTRE NE DOIT AVOIR BOUGÉ : ni ajouté, ni retiré.

    Le troisième fait est le vrai contrôle. Un `gpasswd -d` appliqué trop large,
    ou un groupe réécrit à la main, retire aussi le compte qui administre la
    machine. Le travail a l'air fait, et l'hôte devient inaccessible à qui en a
    besoin : c'est la panne qu'on ne découvre qu'au prochain déploiement.
    """
    avant = set(releve.get("docker_group") or [])
    lu = host.run("getent group docker")
    assert lu.rc == 0, message(
        en="the `docker` group no longer exists. Removing it does not remove "
           "the problem, it removes the engine's access control.",
        fr="le groupe `docker` n'existe plus. Le supprimer ne supprime pas le "
           "problème, cela supprime le contrôle d'accès du moteur.",
    )
    membres = {m for m in lu.stdout.strip().split(":")[-1].split(",") if m}

    assert STAGIAIRE not in membres, message(
        en=f"`{STAGIAIRE}` is still in the `docker` group.\n"
           f"  members: {', '.join(sorted(membres)) or '(none)'}\n"
           "Being in that group means being able to do anything on the host, "
           "through the engine.",
        fr=f"`{STAGIAIRE}` est encore dans le groupe `docker`.\n"
           f"  membres : {', '.join(sorted(membres)) or '(aucun)'}\n"
           "Être dans ce groupe, c'est pouvoir tout faire sur l'hôte, par le "
           "moteur.",
    )
    assert EXPLOITANT in membres, message(
        en=f"`{EXPLOITANT}` is no longer in the `docker` group.\n"
           f"  members: {', '.join(sorted(membres)) or '(none)'}\n"
           "That account has to keep working: the brief says so.",
        fr=f"`{EXPLOITANT}` n'est plus dans le groupe `docker`.\n"
           f"  membres : {', '.join(sorted(membres)) or '(aucun)'}\n"
           "Ce compte doit continuer de fonctionner : l'énoncé le demande.",
    )

    # LE TROISIÈME FAIT. Les comptes du socle, relevés avant que le lab touche à
    # quoi que ce soit, doivent tous être encore là. Et aucun compte inconnu ne
    # doit avoir été ajouté.
    perdus = sorted(avant - membres - {STAGIAIRE})
    assert not perdus, message(
        en=f"accounts that were in the group before have been removed:\n"
           + "\n".join(f"  {c}" for c in perdus) + "\n"
           "A removal applied too broadly also takes out the account that "
           "administers the machine. The work looks done, and the host becomes "
           "unreachable to whoever needs it.",
        fr=f"des comptes qui étaient dans le groupe avant ont été retirés :\n"
           + "\n".join(f"  {c}" for c in perdus) + "\n"
           "Un retrait appliqué trop large emporte aussi le compte qui "
           "administre la machine. Le travail a l'air fait, et l'hôte devient "
           "inaccessible à qui en a besoin.",
    )
    ajoutes = sorted(membres - avant - {EXPLOITANT})
    assert not ajoutes, message(
        en=f"accounts have been added to the group:\n"
           + "\n".join(f"  {c}" for c in ajoutes) + "\n"
           "The brief asks for one removal, not for a new distribution of "
           "rights.",
        fr=f"des comptes ont été ajoutés au groupe :\n"
           + "\n".join(f"  {c}" for c in ajoutes) + "\n"
           "L'énoncé demande un retrait, pas une nouvelle distribution des "
           "droits.",
    )


def test_l_outil_passe_par_un_proxy_de_lecture_seule(host) -> None:
    """Le socket du démon, et pourquoi le monter en lecture seule ne protège pas.

    UN SOCKET N'EST PAS UN FICHIER. Un montage `:ro` porte sur l'inode, pas sur
    ce qui circule : tout ce qui parle au socket peut créer, arrêter et
    supprimer, donc faire sur l'hôte tout ce que le démon peut faire. C'est la
    confusion la plus coûteuse de ce module, et c'est pour cela que l'épreuve
    exige un intermédiaire qui LISE la requête.

    DEUX FAITS SONT MESURÉS. L'outil ne monte plus le socket, et le proxy refuse
    une requête d'arrêt tout en laissant passer une lecture. Le second est le
    vrai contrôle : un proxy qui laisserait tout passer satisferait le premier
    sans rien protéger.
    """
    etat = host.run("docker container inspect %s", OUTIL)
    assert etat.rc == 0, message(
        en=f"container `{OUTIL}` does not exist. The brief names it, and the "
           "checks look for it by name.",
        fr=f"le conteneur `{OUTIL}` n'existe pas. L'énoncé le nomme, et les "
           "contrôles le cherchent nommément.",
    )
    montages = json.loads(etat.stdout)[0].get("Mounts") or []
    fautifs = [
        m for m in montages
        if SOCKET_DEMON in (m.get("Source") or "")
        or SOCKET_DEMON in (m.get("Destination") or "")
    ]
    assert not fautifs, message(
        en=f"`{OUTIL}` still mounts the daemon's socket.\n"
           f"  mounts: {json.dumps(fautifs)}\n"
           "A socket is not a file: a `:ro` mount protects nothing, because it "
           "applies to the inode and not to what travels through it.",
        fr=f"`{OUTIL}` monte encore le socket du démon.\n"
           f"  montages : {json.dumps(fautifs)}\n"
           "Un socket n'est pas un fichier : un montage `:ro` ne protège rien, "
           "car il porte sur l'inode et non sur ce qui y circule.",
    )

    adresse = _adresse_du_proxy(host)
    lecture = host.run(
        "curl -sS -o /dev/null -w %s %s",
        "%{http_code}",
        f"http://{adresse}/containers/json",
    )
    assert lecture.stdout.strip() == "200", message(
        en=f"a read request does not pass through the proxy.\n"
           f"  HTTP code: {lecture.stdout.strip() or '(no answer)'}\n"
           "A proxy that blocks everything is not a proxy, it is an outage: the "
           "tool has to keep doing its inventory.",
        fr=f"une requête de lecture ne passe pas par le proxy.\n"
           f"  code HTTP : {lecture.stdout.strip() or '(aucune réponse)'}\n"
           "Un proxy qui bloque tout n'est pas un proxy, c'est une panne : "
           "l'outil doit continuer son inventaire.",
    )
    arret = host.run(
        "curl -sS -o /dev/null -w %s -X POST %s",
        "%{http_code}",
        f"http://{adresse}/containers/{APPLICATION}/stop",
    )
    assert arret.stdout.strip() == "403", message(
        en=f"a stop request is not refused by the proxy.\n"
           f"  HTTP code: {arret.stdout.strip() or '(no answer)'}\n"
           "The point of the intermediary is exactly this: reading passes, "
           "acting does not.",
        fr=f"une requête d'arrêt n'est pas refusée par le proxy.\n"
           f"  code HTTP : {arret.stdout.strip() or '(aucune réponse)'}\n"
           "Tout l'intérêt de l'intermédiaire est là : lire passe, agir non.",
    )


def test_le_demon_n_ecoute_aucun_socket_tcp_sans_tls(host) -> None:
    """L'API exposée, et c'est la faute la plus grave de l'hôte livré.

    Une API Docker en TCP sans TLS donne à quiconque l'atteint le pouvoir de
    lancer un conteneur privilégié, donc de devenir root sur la machine. Il n'y
    a pas de demi-mesure à trouver ici : cette écoute doit disparaître.

    LE CONTRÔLE REGARDE LES SOCKETS D'ÉCOUTE, et non la configuration. Un fichier
    corrigé sans redémarrage du démon laisse l'écoute en place, et c'est
    précisément l'erreur à attraper : le travail est écrit, il n'est pas
    appliqué.
    """
    # `dockerd` ET NON `docker` : le processus `docker-proxy` publie les ports
    # des conteneurs, et il ecoute donc en TCP tout a fait legitimement. Un
    # filtre sur « docker » l'attrape, et le controle echouait des que le proxy
    # de l'epreuve publiait son port, c'est-a-dire exactement quand le travail
    # etait bien fait. Mesure le 2026-11-02 : la solution sortait en echec sur
    # son propre controle.
    sockets = host.run("ss -lntpH")
    fautifs = []
    for ligne in sockets.stdout.splitlines():
        if "dockerd" not in ligne:
            continue
        adresse = ligne.split()[3] if len(ligne.split()) > 3 else ""
        fautifs.append(adresse)
    assert not fautifs, message(
        en=f"the daemon is still listening on a TCP socket:\n"
           + "\n".join(f"  {a}" for a in fautifs) + "\n"
           "Whoever reaches that port can start a privileged container, and so "
           "become root on this machine. Note that correcting a file without "
           "restarting the daemon leaves the listener in place.",
        fr=f"le démon écoute encore sur un socket TCP :\n"
           + "\n".join(f"  {a}" for a in fautifs) + "\n"
           "Quiconque atteint ce port peut lancer un conteneur privilégié, donc "
           "devenir root sur cette machine. À noter : corriger un fichier sans "
           "redémarrer le démon laisse l'écoute en place.",
    )

    # ET L'ÉCOUTE N'A PAS SIMPLEMENT ÉTÉ DÉPLACÉE SUR UN AUTRE PORT : on relit
    # la ligne de commande effective du démon, qui est ce qui décide.
    ligne = host.run(
        "systemctl show docker --property=ExecStart --no-pager"
    )
    exposes = re.findall(r"-H\s+tcp://[^\s;]+", ligne.stdout)
    assert not exposes, message(
        en=f"the daemon is still started with a TCP endpoint:\n"
           + "\n".join(f"  {e}" for e in exposes) + "\n"
           "The listener may be closed right now and come back at the next "
           "boot: what starts the daemon is what decides.",
        fr=f"le démon est encore lancé avec un point d'accès TCP :\n"
           + "\n".join(f"  {e}" for e in exposes) + "\n"
           "L'écoute peut être fermée à l'instant et revenir au prochain "
           "démarrage : ce qui lance le démon est ce qui décide.",
    )


def _adresse_du_proxy(host) -> str:
    """L'adresse publiée du proxy, cherchée parmi les conteneurs du lab.

    Cherchée et non imposée : l'épreuve ne dicte ni le nom du conteneur de proxy
    ni le port de l'hôte, parce qu'elle note l'état final. Ce qui est exigé est
    qu'un proxy issu de l'image fournie soit joignable et qu'il filtre.
    """
    liste = host.run(
        "docker ps --filter %s --format %s",
        f"ancestor={IMAGE_PROXY}",
        "{{.ID}}",
    )
    identifiants = [l.strip() for l in liste.stdout.splitlines() if l.strip()]
    if not identifiants:
        pytest.fail(message(
            en=f"no container from the `{IMAGE_PROXY}` image is running. The "
               "lab provides that image: the test is to use it, not to write a "
               "proxy.",
            fr=f"aucun conteneur issu de l'image `{IMAGE_PROXY}` ne tourne. Le "
               "lab fournit cette image : l'épreuve est de s'en servir, pas "
               "d'écrire un proxy.",
        ))
    for identifiant in identifiants:
        ports = host.run("docker port %s", identifiant)
        for ligne in ports.stdout.splitlines():
            trouve = re.search(r"->\s*([0-9.]+):(\d+)", ligne)
            if trouve:
                hote = trouve.group(1)
                if hote == "0.0.0.0":
                    hote = "127.0.0.1"
                return f"{hote}:{trouve.group(2)}"
    pytest.fail(message(
        en="the proxy is running but publishes no port, so nothing can reach "
           "it. The tool has to be able to talk to it.",
        fr="le proxy tourne mais ne publie aucun port, donc rien ne peut "
           "l'atteindre. L'outil doit pouvoir lui parler.",
    ))
