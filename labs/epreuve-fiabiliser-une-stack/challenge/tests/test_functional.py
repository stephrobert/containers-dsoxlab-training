"""Tests fonctionnels de l'épreuve de fiabilisation : cinq contrôles de poids égal.

C'EST UNE ÉPREUVE, et la stack livrée MARCHE, ou presque. C'est ce qui la rend
réaliste : personne ne laisse en production une stack qui ne démarre jamais, on
laisse celle qui démarre « quand on la relance deux fois ».

LES CINQ DÉFAUTS POSÉS, dits nulle part dans l'énoncé, et un SEUL se voit :
  1. `api` démarre sans attendre que `coffre` soit PRÊT. `depends_on` seul ne
     regarde que le démarrage du conteneur, pas la disponibilité du service.
     C'est le seul défaut qui ait un symptôme, et il se voit mal : « il faut la
     relancer deux fois » ;
  2. le mot de passe est dans `environment`, donc dans `docker inspect`, dans
     `docker compose config`, et dans le fichier versionné ;
  3. aucune limite mémoire ;
  4. aucune politique de redémarrage. Le compose livré ne porte aucun
     `restart:`, et ce défaut-là n'était compté nulle part : l'énoncé en
     annonçait quatre pour cinq contrôles ;
  5. le montage du code source, qui a sa place en développement, est resté dans
     le fichier de déploiement.

L'EXIGENCE CRITIQUE est le contrôle 2. Un secret dans l'environnement se lit
sans privilège particulier, et il suit la stack partout : dans le dépôt, dans
les journaux de celui qui a lancé la commande, dans l'inspection que n'importe
qui peut faire. Aucun total ne le compense.

CHAQUE CONTRÔLE EST INDÉPENDANT, et deux d'entre eux se contrediraient sans
cela : celui du démarrage à froid exige un compteur de redémarrages à zéro, et
celui de la politique de redémarrage FAIT MOURIR un conteneur pour vérifier
qu'il repart. Le premier redémarre donc la stack lui-même, ce que l'énoncé annonce :
il mesure un démarrage à froid, et il se le donne. Les deux ordres d'exécution
rendent alors le même verdict, et aucun ne dépend de la trace de l'autre.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, ce qui permet de lire le relevé du lab dans
`/root` et le cgroup des conteneurs.
"""

from __future__ import annotations

import json
import time

import pytest

from conftest import fuites_dans_l_image, lab_host, message

ATELIER = "/opt/lab-stack-fiable"
PROJET = "stack-fiable"
IMAGE = "lab-stack-fiable:1.0"
ETAT = "/root/.lab-stack-fiable-state.json"
DEPLOIEMENT = f"{ATELIER}/compose.yaml"
DEVELOPPEMENT = f"{ATELIER}/compose.dev.yaml"
PORT_API = 18420
INTERFACE = "127.0.0.1"
SOURCE_MONTEE = "/app/src"
# Le declencheur de panne que le service evalue apres chaque requete.
# Il existe parce que ni `docker kill` ni un `kill -9 1` interne ne font
# mourir un service de facon a declencher sa politique : voir la docstring
# du controle concerne, qui porte les deux mesures.
DECLENCHEUR = "/tmp/panne-provoquee"  # noqa: S108 -- le fichier vit sur la machine du lab, jamais sur un poste partagé

# Les politiques qui font repartir un conteneur tué. `on-failure` en fait
# partie : un conteneur tué par un signal sort en échec.
POLITIQUES_ACCEPTEES = {"always", "unless-stopped", "on-failure"}

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
    """Le mot de passe attendu et son dérivé, tirés au sort par le `run`.

    Le dérivé sert à prouver que le secret est bien ARRIVÉ au service, et pas
    seulement qu'il a disparu de l'environnement : retirer un secret sans le
    remplacer est une fausse correction, et elle doit être détectée.
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


def test_la_stack_repond_du_premier_coup_apres_un_demarrage_a_froid(
    host, releve
) -> None:
    """Le symptôme de départ, et il ne se mesure qu'à froid.

    LE CONTRÔLE DÉMARRE LA STACK LUI-MÊME, et l'énoncé l'annonce. C'est la seule
    façon de mesurer un démarrage à froid : une stack déjà debout a oublié
    comment elle s'est levée, et la seconde tentative réussit toujours, ce qui
    est précisément le symptôme qu'on vient corriger.

    DEUX FAITS SONT EXIGÉS ENSEMBLE. L'API répond, et aucun service n'a eu
    besoin de redémarrer pour cela. Le second est le vrai contrôle : avec une
    politique de redémarrage et sans attente de la santé du coffre, l'API finit
    par répondre, après deux ou trois morts. Elle marche, et elle est fausse.
    """
    _fichier_existe(host, DEPLOIEMENT)
    bas = host.run(
        "cd %s && docker compose -p %s -f %s down --remove-orphans",
        ATELIER, PROJET, DEPLOIEMENT,
    )
    assert bas.rc == 0, message(
        en=f"`docker compose down` failed:\n  {bas.stderr.strip()[:300]}",
        fr=f"`docker compose down` a échoué :\n  {bas.stderr.strip()[:300]}",
    )
    haut = host.run(
        "cd %s && docker compose -p %s -f %s up -d",
        ATELIER, PROJET, DEPLOIEMENT,
    )
    assert haut.rc == 0, message(
        en=f"`docker compose up -d` failed:\n  {haut.stderr.strip()[:400]}",
        fr=f"`docker compose up -d` a échoué :\n  {haut.stderr.strip()[:400]}",
    )

    attendu = f"api={releve['derive']}"
    recu = _interroge_l_api(host)
    assert attendu in recu, message(
        en=f"after a cold start, the API does not answer on "
           f"{INTERFACE}:{PORT_API}.\n"
           f"  what came back: {recu.strip()[:200] or '(nothing)'}\n"
           f"  expected      : {attendu}\n"
           "The API queries the vault once, as it starts. If the vault is not "
           "yet serving, it exits.",
        fr=f"après un démarrage à froid, l'API ne répond pas sur "
           f"{INTERFACE}:{PORT_API}.\n"
           f"  ce qui revient : {recu.strip()[:200] or '(rien)'}\n"
           f"  attendu        : {attendu}\n"
           "L'API interroge le coffre une seule fois, à son démarrage. Si le "
           "coffre ne sert pas encore, elle sort.",
    )

    for service in ("coffre", "api"):
        compte = _redemarrages(host, service)
        assert compte == 0, message(
            en=f"service `{service}` restarted {compte} time(s) to reach that "
               "state.\n"
               "A stack that works after two or three deaths works by accident. "
               "The brief asks for an answer on the first try.",
            fr=f"le service `{service}` a redémarré {compte} fois pour arriver "
               "là.\n"
               "Une stack qui marche après deux ou trois morts marche par "
               "accident. L'énoncé demande une réponse du premier coup.",
        )


def test_le_mot_de_passe_n_est_ni_dans_l_environnement_ni_dans_l_image(
    host, releve
) -> None:
    """L'EXIGENCE CRITIQUE, et elle a deux faces qu'il faut mesurer ensemble.

    LA PREMIÈRE : le secret ne doit plus être lisible là où il traînait, c'est-à-
    dire dans l'environnement des conteneurs, dans l'image, et dans le fichier
    que `docker compose config` rend.

    LA SECONDE, et c'est elle qui empêche la fausse correction : le coffre doit
    le recevoir QUAND MÊME. Retirer une variable et s'arrêter là donne une stack
    propre et muette, ou qui sert une valeur par défaut. Le contrôle compare
    donc la valeur servie au dérivé que le lab a calculé du vrai mot de passe :
    elle ne peut être juste que si le secret est bien arrivé.
    """
    mdp = releve["mot_de_passe"]
    assert mdp, message(
        en="the lab's own measurement carries no password. It is taken during `dsoxlab run`: replay it.",
        fr="la mesure prise par le lab ne porte pas de mot de passe. Elle est faite pendant `dsoxlab run` : rejouez-le.",
    )

    for service in ("coffre", "api"):
        conteneur = _conteneur(host, service)
        env = host.run(
            "docker container inspect %s --format %s",
            conteneur,
            "{{range .Config.Env}}{{println .}}{{end}}",
        )
        fautives = [
            ligne.strip() for ligne in env.stdout.splitlines() if mdp in ligne
        ]
        assert not fautives, message(
            en=f"the password is readable in `{service}`'s environment:\n"
               + "\n".join(f"  {ligne}" for ligne in fautives) + "\n"
               "An environment variable is read by `docker inspect`, by "
               "`docker compose config`, and by anyone who can talk to the "
               "daemon. No total makes up for it.",
            fr=f"le mot de passe se lit dans l'environnement de `{service}` :\n"
               + "\n".join(f"  {ligne}" for ligne in fautives) + "\n"
               "Une variable d'environnement se lit par `docker inspect`, par "
               "`docker compose config`, et par quiconque parle au démon. "
               "Aucun total ne le compense.",
        )

    # PAS un `docker save | grep` : il est AVEUGLE. Les couches sont des blobs
    # gzip, et le texte n'y est pas lisible. Voir `fuites_dans_l_image`.
    surfaces = fuites_dans_l_image(host, IMAGE, mdp)
    assert not surfaces, message(
        en="the password is present in the image, which `docker save | grep` "
           "could never see:\n"
           + "\n".join(f"  {s}" for s in surfaces) + "\n"
           "Moving a secret from the environment into the image moves it from "
           "something readable to something published.",
        fr="le mot de passe est présent dans l'image, là où un "
           "`docker save | grep` ne pouvait pas le voir :\n"
           + "\n".join(f"  {s}" for s in surfaces) + "\n"
           "Déplacer un secret de l'environnement vers l'image, c'est le faire "
           "passer de lisible à publié.",
    )

    rendu = host.run(
        "cd %s && docker compose -p %s -f %s config", ATELIER, PROJET, DEPLOIEMENT
    )
    assert mdp not in rendu.stdout, message(
        en="the password still appears in what `docker compose config` renders, "
           "which is the file as the engine reads it.",
        fr="le mot de passe apparaît encore dans ce que rend "
           "`docker compose config`, c'est-à-dire le fichier tel que le moteur "
           "le lit.",
    )

    # ET LE SECRET EST BIEN ARRIVÉ : sans ce contrôle, retirer la variable
    # suffirait, et la stack servirait une valeur fausse en silence.
    recu = _interroge_l_api(host)
    attendu = f"api={releve['derive']}"
    assert attendu in recu, message(
        en=f"the password no longer reaches the vault.\n"
           f"  what the API serves: {recu.strip()[:200] or '(nothing)'}\n"
           f"  expected           : {attendu}\n"
           "Removing a secret without replacing it is not a fix: the stack is "
           "clean and wrong.",
        fr=f"le mot de passe n'arrive plus au coffre.\n"
           f"  ce que l'API sert : {recu.strip()[:200] or '(rien)'}\n"
           f"  attendu           : {attendu}\n"
           "Retirer un secret sans le remplacer n'est pas une correction : la "
           "stack est propre et fausse.",
    )


def test_chaque_service_porte_une_limite_memoire_appliquee(host) -> None:
    """Déclarer une limite et l'appliquer sont deux choses, donc on lit les deux.

    `HostConfig.Memory` dit ce que le moteur a RETENU de la déclaration.
    `memory.max` du cgroup dit ce que le NOYAU applique. Les deux peuvent
    différer, et la raison n'est pas celle qu'on croit.

    NEUF FORMES MESURÉES le 2026-11-02 sur Docker 29.9.2 et Compose 5.6.1.
    `mem_limit` au niveau du service et `deploy.resources.limits.memory`
    donnent tous DEUX `HostConfig.Memory` à 67108864 pour 64M : la forme n'est
    pas le piège. Une clé écrite au mauvais niveau n'en est pas un non plus,
    Compose validant son schéma et REFUSANT le fichier avec un message et un
    code d'erreur, ce qui ne laisse donc passer aucune stack.

    LE PIÈGE EST LA RÉSERVATION. `deploy.resources.reservations.memory` passe
    la validation sans un mot, et laisse `HostConfig.Memory` à zéro et
    `memory.max` à `max` : le fichier parle de mémoire, et le conteneur n'a
    aucune limite. C'est ce que la première assertion attrape.

    Le contrôle n'impose aucune valeur : une limite trop basse tuerait le
    service, et le contrôle du démarrage le verrait. Ce qui est mesuré est
    qu'une limite existe et qu'elle soit effective.
    """
    for service in ("coffre", "api"):
        conteneur = _conteneur(host, service)
        lu = host.run(
            "docker container inspect %s --format %s",
            conteneur,
            "{{.HostConfig.Memory}}",
        )
        declaree = int(lu.stdout.strip() or "0")
        assert declaree > 0, message(
            en=f"service `{service}` carries no memory limit the engine "
               "retained.\n"
               "  HostConfig.Memory: 0\n"
               "A limit declared where the engine does not read it leaves this "
               "value at zero, and the service is unlimited.",
            fr=f"le service `{service}` ne porte aucune limite mémoire que le "
               "moteur ait retenue.\n"
               "  HostConfig.Memory : 0\n"
               "Une limite déclarée là où le moteur ne la lit pas laisse cette "
               "valeur à zéro, et le service reste sans limite.",
        )

        applique = host.run(
            "docker exec %s cat /sys/fs/cgroup/memory.max", conteneur
        )
        brut = applique.stdout.strip()
        assert brut and brut != "max", message(
            en=f"the kernel applies no memory limit to `{service}`.\n"
               f"  memory.max: {brut or '(unreadable)'}\n"
               "The engine retained a limit, and the cgroup does not carry it: "
               "the container has to be recreated for a limit to apply.",
            fr=f"le noyau n'applique aucune limite mémoire à `{service}`.\n"
               f"  memory.max : {brut or '(illisible)'}\n"
               "Le moteur a retenu une limite, et le cgroup ne la porte pas : "
               "un conteneur doit être recréé pour qu'une limite s'applique.",
        )
        assert int(brut) == declaree, message(
            en=f"the limit the kernel applies to `{service}` is not the one "
               "declared.\n"
               f"  declared: {declaree}\n"
               f"  applied : {brut}",
            fr=f"la limite que le noyau applique à `{service}` n'est pas celle "
               "qui est déclarée.\n"
               f"  déclarée : {declaree}\n"
               f"  appliquée : {brut}",
        )


def test_un_service_qui_meurt_repart_seul(host) -> None:
    """La politique de redémarrage, et elle ne se mesure qu'en faisant mourir.

    Déclarer `restart:` et le relire dans l'inspection ne prouve rien : la valeur
    peut être lue par Compose et ne jamais s'appliquer, par exemple sur un
    conteneur créé avant le changement. La seule question qui compte est
    « revient-il ? ».

    COMMENT ON FAIT MOURIR LE SERVICE, et pourquoi pas autrement. Deux façons
    évidentes ne marchent pas, mesurées sur 29.9.2 le 2026-11-02 :

      `docker kill <id>`   le moteur traite cela comme un arrêt VOULU. Le
                           conteneur reste `exited` et `unless-stopped` ne le
                           relance pas : dix lectures en trente secondes, le
                           compteur de redémarrages est resté à zéro.
      `docker exec <id> kill -9 1`
                           sans effet : le noyau protège le PID 1 d'un
                           namespace contre les signaux envoyés DEPUIS ce
                           namespace, SIGKILL compris.

    Ce qu'une politique couvre vraiment est un processus qui MEURT DE LUI-MÊME.
    Le service porte donc un déclencheur de panne, que l'énoncé nomme : un
    fichier dont la présence le fait sortir en erreur au tour suivant.

    CE CONTRÔLE LAISSE UN COMPTEUR DE REDÉMARRAGES À UN, et c'est sans
    conséquence : le contrôle du démarrage à froid redémarre la stack lui-même.
    """
    for service in ("coffre", "api"):
        conteneur = _conteneur(host, service)
        lu = host.run(
            "docker container inspect %s --format %s",
            conteneur,
            "{{.HostConfig.RestartPolicy.Name}}",
        )
        politique = lu.stdout.strip() or "no"
        assert politique in POLITIQUES_ACCEPTEES, message(
            en=f"service `{service}` carries no restart policy.\n"
               f"  its policy: {politique}\n"
               "Without one, a container that dies at four in the morning stays "
               "dead until someone notices.",
            fr=f"le service `{service}` ne porte aucune politique de "
               "redémarrage.\n"
               f"  sa politique : {politique}\n"
               "Sans elle, un conteneur qui meurt à quatre heures du matin "
               "reste mort jusqu'à ce que quelqu'un s'en aperçoive.",
        )

    # On fait mourir l'API, et non le coffre : si le coffre meurt, l'API qui ne
    # l'interroge qu'au démarrage ne s'en remet pas, et l'on mesurerait la
    # conception de l'application au lieu de la politique.
    conteneur = _conteneur(host, "api")
    avant = _redemarrages(host, "api")
    pose = host.run("docker exec %s touch %s", conteneur, DECLENCHEUR)
    assert pose.rc == 0, message(
        en=f"the failure trigger could not be placed in `api`:\n"
           f"  {pose.stderr.strip()[:200]}",
        fr=f"le déclencheur de panne n'a pas pu être posé dans l'`api` :\n"
           f"  {pose.stderr.strip()[:200]}",
    )
    # Le service évalue le déclencheur après chaque requête servie : une
    # connexion est donc nécessaire pour qu'il le voie.
    host.run("nc -w 3 %s %s", INTERFACE, str(PORT_API))

    revenu = False
    for _ in range(40):
        time.sleep(1)
        etat = host.run(
            "docker container inspect %s --format %s",
            conteneur,
            "{{.State.Status}}",
        )
        if etat.stdout.strip() == "running" and _redemarrages(host, "api") > avant:
            revenu = True
            break
    apres = _redemarrages(host, "api")
    assert revenu, message(
        en=f"after dying, `api` did not come back on its own within forty "
           "seconds.\n"
           f"  restarts: {avant} then {apres}\n"
           "The policy is declared; it is not applying. A container has to be "
           "recreated for a policy change to take effect.",
        fr=f"après être morte, l'`api` n'est pas revenue d'elle-même en "
           "quarante secondes.\n"
           f"  redémarrages : {avant} puis {apres}\n"
           "La politique est déclarée, elle ne s'applique pas. Un conteneur "
           "doit être recréé pour qu'un changement de politique prenne effet.",
    )


def test_les_deux_variantes_disent_des_choses_differentes(host) -> None:
    """Deux fichiers, deux usages, et la superposition doit être vraie.

    Le montage du code source a sa place en développement : il permet de
    modifier sans reconstruire. Il n'a aucune place en déploiement, où il fait
    dépendre le service du contenu d'un répertoire de la machine, que personne ne
    versionne et que le prochain déploiement ne recréera pas.

    LE CONTRÔLE LIT `docker compose config`, et non les fichiers. C'est la
    composition telle que le moteur la comprend, variables substituées et
    superpositions appliquées : un `volumes:` écrit au mauvais niveau
    d'indentation n'y apparaît pas, alors qu'il est bien dans le fichier.
    """
    _fichier_existe(host, DEPLOIEMENT)
    _fichier_existe(host, DEVELOPPEMENT)

    deploiement = host.run(
        "cd %s && docker compose -p %s -f %s config", ATELIER, PROJET, DEPLOIEMENT
    )
    assert deploiement.rc == 0, message(
        en=f"the deployment variant is not valid:\n"
           f"  {deploiement.stderr.strip()[:300]}",
        fr=f"la variante de déploiement n'est pas valide :\n"
           f"  {deploiement.stderr.strip()[:300]}",
    )
    assert SOURCE_MONTEE not in deploiement.stdout, message(
        en=f"the deployment variant still mounts the source code on "
           f"`{SOURCE_MONTEE}`.\n"
           "In deployment, that makes the service depend on a directory nobody "
           "versions and the next deployment will not recreate.",
        fr=f"la variante de déploiement monte encore le code source sur "
           f"`{SOURCE_MONTEE}`.\n"
           "En déploiement, cela fait dépendre le service d'un répertoire que "
           "personne ne versionne et que le prochain déploiement ne recréera "
           "pas.",
    )

    dev = host.run(
        "cd %s && docker compose -p %s -f %s -f %s config",
        ATELIER, PROJET, DEPLOIEMENT, DEVELOPPEMENT,
    )
    assert dev.rc == 0, message(
        en=f"the two variants do not compose:\n  {dev.stderr.strip()[:300]}",
        fr=f"les deux variantes ne se composent pas :\n"
           f"  {dev.stderr.strip()[:300]}",
    )
    assert SOURCE_MONTEE in dev.stdout, message(
        en=f"the development variant does not mount the source code on "
           f"`{SOURCE_MONTEE}`.\n"
           "That mount is what makes development work without rebuilding, and "
           "it is the reason the two variants exist.",
        fr=f"la variante de développement ne monte pas le code source sur "
           f"`{SOURCE_MONTEE}`.\n"
           "Ce montage est ce qui permet de développer sans reconstruire, et "
           "c'est la raison d'être des deux variantes.",
    )


def _fichier_existe(host, chemin: str) -> None:
    """Un fichier que l'énoncé nomme, et dont l'absence est un échec net."""
    if host.run("test -f %s", chemin).rc != 0:
        pytest.fail(message(
            en=f"the file `{chemin}` does not exist. The brief names it, and "
               "the checks look for it by name.",
            fr=f"le fichier `{chemin}` n'existe pas. L'énoncé le nomme, et les "
               "contrôles le cherchent nommément.",
        ))


def _conteneur(host, service: str) -> str:
    """L'identifiant du conteneur d'un service, demandé à Compose.

    Demandé à Compose et non deviné d'après un nom : le nom d'un conteneur de
    projet dépend de la version du greffon et d'un éventuel `container_name`.
    """
    # `-aq` ET NON `-q` : sans `-a`, Compose ne liste que les conteneurs EN
    # COURS, et rend une chaîne vide pour un service arrêté. Le contrôle de la
    # politique de redémarrage, qui regarde justement un service mort, perdait
    # alors son identifiant et échouait sur « conteneur introuvable » au lieu de
    # mesurer ce qu'il devait mesurer.
    res = host.run(
        "cd %s && docker compose -p %s -f %s ps -aq %s",
        ATELIER, PROJET, DEPLOIEMENT, service,
    )
    identifiant = (res.stdout or "").strip().splitlines()
    if not identifiant or not identifiant[0].strip():
        pytest.fail(message(
            en=f"service `{service}` has no container. The two service names "
               "are part of the brief, and the checks look for them by name.",
            fr=f"le service `{service}` n'a aucun conteneur. Les deux noms de "
               "services font partie de l'énoncé, et les contrôles les "
               "cherchent nommément.",
        ))
    return identifiant[0].strip()


def _redemarrages(host, service: str) -> int:
    """Le compteur de redémarrages d'un service, ou zéro si illisible."""
    conteneur = _conteneur(host, service)
    res = host.run(
        "docker container inspect %s --format %s", conteneur, "{{.RestartCount}}"
    )
    try:
        return int(res.stdout.strip())
    except ValueError:
        return 0


def _interroge_l_api(host) -> str:
    """Ce que l'API répond, lu depuis l'hôte sur l'interface publiée.

    Plusieurs tentatives, pour deux raisons mesurées : l'écouteur est relancé
    après chaque connexion, et un conteneur qui vient d'être recréé peut n'avoir
    pas encore ouvert son port. La réponse est lue, jamais la seule connexion :
    le proxy de Docker accepte dès le `run`.
    """
    dernier = ""
    for _ in range(20):
        res = host.run("nc -w 3 %s %s", INTERFACE, str(PORT_API))
        dernier = res.stdout
        if "api=" in dernier:
            return dernier
        time.sleep(1)
    return dernier
