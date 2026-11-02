"""Tests fonctionnels de l'épreuve des trois pannes : cinq contrôles de poids égal.

C'EST UNE ÉPREUVE : les messages nomment le SYMPTÔME et s'arrêtent là. Aucun ne
dit « passez la variable » ni « relancez sans le shell ». Les indices sont là
pour ça, et ils coûtent des points.

LES TROIS PANNES POSÉES, dites nulle part dans l'énoncé :
  1. `collecteur` est sorti en 78 : la variable `DESTINATION` manque ;
  2. `expediteur` boucle : son mode est inconnu, il sort en 64, et sa politique
     `--restart always` le relance ;
  3. `scribe` est lancé derrière un `sh` : son PID 1 n'est pas le programme, le
     `SIGTERM` de `docker stop` ne lui parvient pas, et le `SIGKILL` du délai de
     grâce le coupe en pleine écriture.

L'EXIGENCE CRITIQUE est le rapport tronqué. Les deux premières pannes coûtent du
temps, celle-là coûte une donnée, et aucun total ne la compense.

CHAQUE CONTRÔLE RESTAURE CE QU'IL A CHANGÉ, et c'est une correction payée par
la mesure. Le contrôle de l'arrêt propre doit ARRÊTER le scribe : c'est la seule
façon de mesurer une durée d'arrêt et un code de sortie, et aucune lecture après
coup ne la remplace. Il laissait donc un conteneur arrêté, et le contrôle de
propreté, qui exige le contraire, échouait sur la trace du test voisin.

Un premier essai avait ordonné les contrôles pour que le second passe avant le
premier. C'était fragile et c'était faux : l'ordre d'exécution ne fait pas
partie du contrat de pytest, et deux mesures du même lab ont donné deux ordres
différents, lues dans `docker events`. La seule construction solide est
l'INDÉPENDANCE : le contrôle de l'arrêt relance le scribe dans un `finally`, et
plus aucun contrôle ne dépend de ce qu'un autre a fait.

LES CONTRÔLES LISENT LA RÉPONSE, jamais la seule connexion : le proxy de Docker
accepte dès le `run`, avant que quoi que ce soit écoute.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé.
"""

from __future__ import annotations

import json
import time

import pytest

from conftest import lab_host, message

COLLECTEUR = "collecteur"
EXPEDITEUR = "expediteur"
SCRIBE = "scribe"
IMAGE = "lab-trois-pannes:1.0"
ATELIER = "/opt/lab-trois-pannes"
DIAGNOSTIC = f"{ATELIER}/diagnostic.txt"
RAPPORT = "/var/log/scribe.txt"

# Les deux lignes qui font un rapport complet. Une seule des deux, et le rapport
# est tronqué : c'est toute la différence que l'épreuve mesure.
DEBUT = "debut du rapport"
FIN = "fin du rapport"

# Le délai de grâce de `docker stop` est de dix secondes. Un arrêt qui les
# consomme est un arrêt que le programme n'a pas vu venir.
DELAI_DE_GRACE = 10
POLITIQUES_ACCEPTEES = {"always", "unless-stopped"}
CODES_ACCEPTES = {0, 143}

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


def test_le_collecteur_tourne_avec_l_image_fournie(host) -> None:
    """La première panne, et elle se diagnostique par un code de sortie.

    Le conteneur était sorti et ne redémarrait pas : rien ne le relançait, donc
    rien ne masquait la cause. Son code de sortie la disait, et personne ne
    l'avait lu.

    L'image est vérifiée en plus de l'état : reconstruire une image à soi pour
    contourner la panne règle le symptôme et perd la leçon, et l'énoncé fournit
    l'image précisément pour que la question ne se pose pas.
    """
    etat = _inspecte(host, COLLECTEUR)
    statut = etat["State"]["Status"]
    assert statut == "running", message(
        en=f"`{COLLECTEUR}` is `{statut}`, not `running`.\n"
           f"  its exit code: {etat['State']['ExitCode']}\n"
           "Nothing was restarting it, so nothing was hiding the cause: the "
           "exit code and the logs say it.",
        fr=f"`{COLLECTEUR}` est `{statut}`, et non `running`.\n"
           f"  son code de sortie : {etat['State']['ExitCode']}\n"
           "Rien ne le relançait, donc rien ne masquait la cause : son code de "
           "sortie et ses journaux la disent.",
    )
    assert IMAGE in etat["Config"]["Image"], message(
        en=f"`{COLLECTEUR}` does not come from `{IMAGE}`.\n"
           f"  its image: {etat['Config']['Image']}\n"
           "The image is provided: it is not to be rebuilt.",
        fr=f"`{COLLECTEUR}` n'est pas issu de `{IMAGE}`.\n"
           f"  son image : {etat['Config']['Image']}\n"
           "L'image est fournie : elle n'est pas à reconstruire.",
    )


def test_l_expediteur_ne_redemarre_plus_et_garde_sa_politique(host) -> None:
    """La deuxième panne, et la politique n'en est PAS la cause.

    Elle est ce qui rend la panne visible : sans elle, le conteneur serait sorti
    une fois et se serait tu. La retirer ferait disparaître le symptôme sans
    régler quoi que ce soit, et c'est la fausse correction que ce contrôle
    écarte en exigeant qu'elle soit conservée.

    LA STABILITÉ SE MESURE DANS LE TEMPS. Un `RestartCount` lu une seule fois
    ne dit rien : il vaut zéro sur un conteneur qui vient d'être recréé, qu'il
    soit réparé ou qu'il s'apprête à boucler. Deux lectures espacées sont la
    seule preuve que la boucle est finie.
    """
    etat = _inspecte(host, EXPEDITEUR)
    statut = etat["State"]["Status"]
    assert statut == "running", message(
        en=f"`{EXPEDITEUR}` is `{statut}`, not `running`.",
        fr=f"`{EXPEDITEUR}` est `{statut}`, et non `running`.",
    )
    politique = (etat["HostConfig"]["RestartPolicy"] or {}).get("Name") or "no"
    assert politique in POLITIQUES_ACCEPTEES, message(
        en=f"`{EXPEDITEUR}` no longer carries a restart policy.\n"
           f"  its policy: {politique}\n"
           "The policy is not the failure: it is what made the failure visible. "
           "Removing it hides the symptom without fixing anything, and the "
           "brief asks for it to be kept.",
        fr=f"`{EXPEDITEUR}` ne porte plus de politique de redémarrage.\n"
           f"  sa politique : {politique}\n"
           "La politique n'est pas la panne : elle est ce qui la rendait "
           "visible. La retirer masque le symptôme sans rien régler, et "
           "l'énoncé demande de la conserver.",
    )
    avant = etat["RestartCount"]
    time.sleep(12)
    apres = _inspecte(host, EXPEDITEUR)["RestartCount"]
    assert apres == avant, message(
        en=f"`{EXPEDITEUR}` is still restarting.\n"
           f"  restarts: {avant} then {apres}, twelve seconds apart\n"
           "Its logs say, at each attempt, what it refuses.",
        fr=f"`{EXPEDITEUR}` redémarre encore.\n"
           f"  redémarrages : {avant} puis {apres}, à douze secondes "
           "d'intervalle\n"
           "Ses journaux disent, à chaque tentative, ce qu'il refuse.",
    )


def test_le_rapport_complet_est_copie_sur_l_hote(host) -> None:
    """L'EXIGENCE CRITIQUE : le rapport, et il doit être entier.

    Le contrôle porte sur la copie posée sur l'hôte, parce que c'est elle qui
    survit au conteneur. Un rapport tronqué copié reste un rapport tronqué :
    c'est bien la donnée qui est perdue, pas le fichier.

    Un rapport est complet quand il porte sa ligne de début ET sa ligne de fin.
    La ligne de fin n'est écrite que par le gestionnaire de fin du programme,
    donc elle n'existe que si le programme a reçu son signal.
    """
    lu = host.run("cat %s", DIAGNOSTIC)
    assert lu.rc == 0, message(
        en=f"the file `{DIAGNOSTIC}` does not exist on the host.\n"
           "The report lives inside the container, and a container does not "
           "survive its own removal: the brief asks for the report to be copied "
           "out. No total makes up for a lost report.",
        fr=f"le fichier `{DIAGNOSTIC}` n'existe pas sur l'hôte.\n"
           "Le rapport vit dans le conteneur, et un conteneur ne survit pas à "
           "sa propre suppression : l'énoncé demande que le rapport soit copié "
           "au-dehors. Aucun total ne compense un rapport perdu.",
    )
    contenu = lu.stdout
    manquantes = [l for l in (DEBUT, FIN) if l not in contenu]
    assert not manquantes, message(
        en=f"the copied report is truncated.\n"
           f"  missing: {', '.join(manquantes)}\n"
           f"  content: {contenu.strip()[:200] or '(empty)'}\n"
           "The closing line is written only by the program's shutdown "
           "handler. Its absence means the program never ran it, and a copy of "
           "a truncated report is still a truncated report.",
        fr=f"le rapport copié est tronqué.\n"
           f"  il manque : {', '.join(manquantes)}\n"
           f"  son contenu : {contenu.strip()[:200] or '(vide)'}\n"
           "La ligne de fin n'est écrite que par le gestionnaire de fin du "
           "programme. Son absence signifie qu'il ne l'a jamais exécuté, et la "
           "copie d'un rapport tronqué reste un rapport tronqué.",
    )


def test_aucun_conteneur_du_lab_ne_traine_a_l_arret(host) -> None:
    """La propreté de la machine, et elle fait partie du travail.

    Un conteneur arrêté garde son nom, sa configuration et son espace disque. En
    exploitation, ce sont eux qui remplissent un disque sans que personne ne
    sache d'où ils viennent, et qui font échouer un `docker run` sur un conflit
    de nom des semaines plus tard.

    CE CONTRÔLE NE DÉPEND D'AUCUN AUTRE. Celui de l'arrêt propre arrête le
    scribe pour le mesurer, puis le relance : sans cette restauration, celui-ci
    échouerait ou passerait selon l'ordre d'exécution, qui ne fait pas partie du
    contrat de pytest.
    """
    res = host.run(
        "docker ps -a --filter %s --format %s",
        "label=dsoxlab.lab=epreuve-remettre-trois-conteneurs-en-service",
        "{{.Names}} {{.State}}",
    )
    traine = [
        l.strip() for l in res.stdout.splitlines()
        if l.strip() and l.split()[-1] in {"exited", "created", "dead"}
    ]
    assert not traine, message(
        en=f"containers of this lab are left stopped:\n"
           + "\n".join(f"  {l}" for l in traine) + "\n"
           "A stopped container keeps its name, its configuration and its disk "
           "space. The three containers are expected to be running.",
        fr=f"des conteneurs de ce lab restent à l'arrêt :\n"
           + "\n".join(f"  {l}" for l in traine) + "\n"
           "Un conteneur arrêté garde son nom, sa configuration et son espace "
           "disque. Les trois conteneurs sont attendus en marche.",
    )


def test_le_scribe_s_arrete_proprement_et_son_rapport_est_entier(host) -> None:
    """L'arrêt propre, et il ne se mesure qu'en arrêtant.

    TROIS FAITS, UN SEUL GESTE. `docker stop` envoie `SIGTERM`, attend dix
    secondes, puis `SIGKILL`. Un programme qui reçoit son signal se termine
    aussitôt, écrit sa ligne de fin, et sort en 0. Un programme qui ne le reçoit
    pas consomme tout le délai et se fait couper : l'arrêt dure dix secondes, le
    code vaut 137, et le rapport est tronqué.

    Les trois faits ont donc la même cause, et c'est pour cela qu'ils sont
    mesurés ensemble : séparer la durée, le code et le contenu donnerait trois
    contrôles pour une seule compétence, et pèserait trois fois le même acquis.

    CE CONTRÔLE RELANCE LE SCRIBE EN PARTANT, dans un `finally`, et c'est ce qui
    le rend indépendant : il est le seul à modifier l'état de la machine, donc il
    est le seul à devoir le rendre. Sans cela, le contrôle de propreté passait ou
    échouait selon l'ordre d'exécution, qui ne fait pas partie du contrat de
    pytest.
    """
    etat = _inspecte(host, SCRIBE)
    statut = etat["State"]["Status"]
    assert statut == "running", message(
        en=f"`{SCRIBE}` is `{statut}`, not `running`. The brief asks for it to "
           "be running at the end, and an orderly shutdown can only be measured "
           "on a container that is up.",
        fr=f"`{SCRIBE}` est `{statut}`, et non `running`. L'énoncé le demande "
           "en marche à la fin, et un arrêt propre ne se mesure que sur un "
           "conteneur debout.",
    )

    # TOUT CE QUI SUIT EST SOUS `finally` : ce contrôle arrête le scribe, donc
    # il doit le relancer, qu'il réussisse ou qu'il échoue. Un test qui laisse
    # la machine autrement qu'il l'a trouvée fait échouer ses voisins, et le
    # verdict dépend alors de l'ordre d'exécution plutôt que du travail.
    try:
        _mesurer_l_arret(host)
    finally:
        host.run("docker start %s", SCRIBE)


def _mesurer_l_arret(host) -> None:
    """La mesure elle-même, séparée pour que la relance l'encadre toujours."""
    depart = time.monotonic()
    arret = host.run("docker stop %s", SCRIBE)
    duree = time.monotonic() - depart
    assert arret.rc == 0, message(
        en=f"`docker stop {SCRIBE}` failed:\n  {arret.stderr.strip()[:200]}",
        fr=f"`docker stop {SCRIBE}` a échoué :\n  {arret.stderr.strip()[:200]}",
    )
    apres = _inspecte(host, SCRIBE)
    code = apres["State"]["ExitCode"]

    assert duree < DELAI_DE_GRACE, message(
        en=f"stopping `{SCRIBE}` took {duree:.1f} s, which is the whole grace "
           f"period of {DELAI_DE_GRACE} s.\n"
           f"  its exit code: {code}\n"
           "A program that gets its signal stops at once. One that consumes the "
           "grace period never got it.",
        fr=f"arrêter `{SCRIBE}` a pris {duree:.1f} s, soit tout le délai de "
           f"grâce de {DELAI_DE_GRACE} s.\n"
           f"  son code de sortie : {code}\n"
           "Un programme qui reçoit son signal s'arrête aussitôt. Celui qui "
           "consomme le délai de grâce ne l'a jamais reçu.",
    )
    assert code in CODES_ACCEPTES, message(
        en=f"`{SCRIBE}` exited with code {code}.\n"
           f"  expected: {' or '.join(str(c) for c in sorted(CODES_ACCEPTES))}\n"
           "137 means the container was killed after the grace period, which is "
           "what happens when the signal does not reach the program.",
        fr=f"`{SCRIBE}` est sorti avec le code {code}.\n"
           f"  attendu : {' ou '.join(str(c) for c in sorted(CODES_ACCEPTES))}\n"
           "137 signifie que le conteneur a été tué après le délai de grâce, "
           "ce qui arrive quand le signal n'atteint pas le programme.",
    )

    # LE CONTENEUR EST MAINTENANT ARRÊTÉ, donc `docker exec` n'y fonctionne
    # plus : on lit le fichier dans sa couche d'écriture par une COPIE, qui
    # marche sur un conteneur arrêté et ne le modifie pas.
    #
    # La copie va dans un fichier, et non sur la sortie standard : `docker cp`
    # vers `-` écrit une ARCHIVE TAR, où un `in` sur le texte passerait par
    # chance et échouerait dès qu'un nom de fichier ou un entête tomberait au
    # mauvais endroit. Un contrôle qui marche par chance ne mesure rien.
    temporaire = f"/tmp/rapport-verifie-{int(time.monotonic() * 1000)}.txt"
    try:
        copie = host.run("docker cp %s:%s %s", SCRIBE, RAPPORT, temporaire)
        assert copie.rc == 0, message(
            en=f"the report could not be read inside `{SCRIBE}`:\n"
               f"  {copie.stderr.strip()[:200]}",
            fr=f"le rapport n'a pas pu être lu dans `{SCRIBE}` :\n"
               f"  {copie.stderr.strip()[:200]}",
        )
        contenu = host.run("cat %s", temporaire).stdout
    finally:
        host.run("rm -f %s", temporaire)
    manquantes = [l for l in (DEBUT, FIN) if l not in contenu]
    assert not manquantes, message(
        en=f"after an orderly stop, the report inside the container is still "
           f"incomplete.\n  missing: {', '.join(manquantes)}\n"
           "The closing line is written by the program's shutdown handler, so "
           "its absence means the handler never ran.",
        fr=f"après un arrêt propre, le rapport dans le conteneur est encore "
           f"incomplet.\n  il manque : {', '.join(manquantes)}\n"
           "La ligne de fin est écrite par le gestionnaire de fin du programme : "
           "son absence signifie qu'il ne s'est pas exécuté.",
    )


def _inspecte(host, nom: str) -> dict:
    """L'inspection complète d'un conteneur, ou un échec qui nomme l'absence.

    Un nom manquant veut presque toujours dire qu'un conteneur a été détruit et
    pas relancé. Le message le dit, parce que c'est une information d'état et
    non un indice de résolution.
    """
    res = host.run("docker container inspect %s", nom)
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{nom}` does not exist. The three container names "
               "are part of the brief, and the checks look for them by name: if "
               "you recreated it, it has to carry the same name.",
            fr=f"le conteneur `{nom}` n'existe pas. Les trois noms de "
               "conteneurs font partie de l'énoncé, et les contrôles les "
               "cherchent nommément : si vous l'avez recréé, il doit porter le "
               "même nom.",
        ))
    return json.loads(res.stdout)[0]
