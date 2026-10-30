"""Tests fonctionnels du lab images-non-root : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que `USER` change l'identité d'exécution et **aucun
droit** : les fichiers déposés avant lui restent à root, et l'application cesse
d'écrire.

MESURÉ SUR docker.lab LE 2026-10-30, la même application sous trois écritures :

| Écriture | uid | Écriture dans /donnees |
| sans `USER` | 0 | ok |
| `USER` seul | 10001 | **REFUSÉE**, « Permission denied » |
| `USER` + propriétaire aligné | 10001 | ok |

DEUX MESURES QUI CONTREDISENT CE QU'ON CROIT, et qui expliquent deux des
contrôles :

`docker run --user 0:0` sur l'image non-root rend **uid=0**. Le `USER` du
Dockerfile est donc une valeur par défaut, pas une garantie : c'est pourquoi le
premier contrôle lance l'image SANS option, pour mesurer ce qu'elle fait quand
personne ne décide à sa place.

Un non-root **écoute sur le port 80** dans un conteneur, mesuré. On lit souvent
qu'il faut être root pour les ports sous 1024 ; le moteur accorde la capacité
par défaut, et l'argument tombe. Aucun contrôle ne porte donc sur les ports :
ce serait mesurer une croyance.

LE QUATRIÈME CONTRÔLE EXIGE UN UID NUMÉRIQUE, et ce n'est pas une préférence.
Un `USER` par nom se résout dans le `/etc/passwd` de l'image ; un orchestrateur
qui refuse les conteneurs root ne lit pas ce fichier, et ne peut donc pas
prouver que ce nom n'est pas root. Un uid numérique se vérifie sans rien ouvrir.

AUCUN UID N'EST ÉCRIT EN DUR ICI. Le contrôle lit l'identité que l'image
déclare et la compare à celle qu'elle prend réellement, et il exige seulement
qu'elle ne soit pas nulle.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

IMAGE = "appli:nonroot"
ATELIER = "/opt/lab-nonroot"
CONTEXTE = f"{ATELIER}/appli"
LANCEUR = f"{CONTEXTE}/lancer.sh"
DONNEES = "/donnees"
ESSAI = "dsoxlab-essai-nonroot"

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


def _image_absente(host) -> bool:
    return host.run("docker image inspect %s", IMAGE).rc != 0


def _lancer(host, gabarit: str, *params):
    """Un conteneur d'essai NOMMÉ, et retiré de façon synchrone.

    `docker run --rm` rend la main avant que le moteur ait retiré le conteneur,
    et la photo du cycle de validation voit alors un conteneur déjà condamné.
    `docker rm -f`, lui, est synchrone. Leçon payée dans un lab voisin.

    AUCUNE OPTION D'IDENTITÉ N'EST POSÉE ICI, et c'est le point : mesuré le
    2026-10-30, `--user 0:0` écrase le `USER` du Dockerfile. On mesure donc ce
    que l'image fait quand personne ne décide à sa place.
    """
    res = host.run(f"docker run --rm --name {ESSAI} " + gabarit, *params)
    host.run("docker rm -f %s", ESSAI)
    return res


def _paires(sortie: str) -> dict[str, str]:
    """Les paires clé=valeur de la sortie, PLUSIEURS PAR LIGNE s'il y en a.

    Un premier jet découpait chaque ligne sur son premier `=` : la ligne
    `uid=10001 gid=10001` rendait alors `uid` valant « 10001 gid=10001 », et le
    troisième contrôle refusait une solution correcte en annonçant un uid
    impossible. Le découpage se fait donc par mots, et chaque mot qui porte un
    `=` donne une paire.
    """
    paires = {}
    for mot in sortie.split():
        if "=" in mot:
            cle, _, valeur = mot.partition("=")
            paires[cle.strip()] = valeur.strip()
    return paires


def _jeton(host) -> str:
    f = host.file(LANCEUR)
    if not f.exists:
        return ""
    for mot in f.content_string.split():
        if mot.startswith("jeton-"):
            return mot
    return ""


def test_l_image_tourne_sous_un_uid_non_nul(host) -> None:
    """L'identité par défaut de l'image, mesurée sans aucune option.

    LE CONTRÔLE NE POSE PAS `--user`, et c'est la seule façon de mesurer ce que
    l'image décide. Avec l'option, toute image passerait : mesuré le
    2026-10-30, `--user 0:0` rend uid=0 sur l'image non-root elle-même.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               f"mission: the context is in {CONTEXTE}.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               f"la mission : le contexte est dans {CONTEXTE}.",
        ))

    jeton = _jeton(host)
    if not jeton:
        pytest.skip(message(
            en=f"{LANCEUR} carries no token: the setup did not finish",
            fr=f"{LANCEUR} ne porte aucun jeton : le setup n'a pas abouti",
        ))

    lance = _lancer(host, "%s", IMAGE)
    assert lance.rc == 0, message(
        en=f"`{IMAGE}` does not run (code {lance.rc}).\n"
           f"  {(lance.stderr or lance.stdout).strip()[:300]}",
        fr=f"`{IMAGE}` ne tourne pas (code {lance.rc}).\n"
           f"  {(lance.stderr or lance.stdout).strip()[:300]}",
    )
    assert jeton in lance.stdout, message(
        en=f"`{IMAGE}` does not print the token its launcher carries.\n"
           f"  printed: {lance.stdout.strip()[:200] or '(nothing)'}",
        fr=f"`{IMAGE}` n'imprime pas le jeton que porte son lanceur.\n"
           f"  imprimé : {lance.stdout.strip()[:200] or '(rien)'}",
    )
    paires = _paires(lance.stdout)
    uid = paires.get("uid", "")
    assert uid and uid != "0", message(
        en=f"`{IMAGE}` runs as uid {uid or '(unknown)'} by default.\n"
           "No option was passed on purpose: an image's identity is what it "
           "takes when nobody decides for it. Measured on this machine, "
           "`--user` overrides the Dockerfile's `USER`, so passing it would "
           "measure the command, not the image.",
        fr=f"`{IMAGE}` tourne sous l'uid {uid or '(inconnu)'} par défaut.\n"
           "Aucune option n'a été passée à dessein : l'identité d'une image "
           "est celle qu'elle prend quand personne ne décide pour elle. "
           "Mesuré sur cette machine, `--user` écrase le `USER` du "
           "Dockerfile : le passer mesurerait la commande, pas l'image.",
    )


def test_l_application_ecrit_toujours_son_journal(host) -> None:
    """Le piège du lab, et il tombe sur tout le monde une fois.

    `USER` CHANGE L'IDENTITÉ ET AUCUN DROIT. Les répertoires créés avant lui
    appartiennent à root, et l'application non-root n'y écrit plus. Mesuré le
    2026-10-30 : « can't create /donnees/journal.txt: Permission denied ».

    LE CONTRÔLE MESURE L'EFFET, une écriture réelle, et non la présence d'une
    instruction dans le Dockerfile.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))
    lance = _lancer(host, "%s", IMAGE)
    paires = _paires(lance.stdout)
    assert lance.rc == 0 and paires.get("lignes"), message(
        en=f"`{IMAGE}` does not write its journal.\n"
           f"  {(lance.stderr or lance.stdout).strip()[:300]}\n"
           "`USER` changes the running identity and NO right: the directories "
           "created before it belong to root, and a non-root application no "
           "longer writes in them. Align the owner, do not go back to root.",
        fr=f"`{IMAGE}` n'écrit pas son journal.\n"
           f"  {(lance.stderr or lance.stdout).strip()[:300]}\n"
           "`USER` change l'identité d'exécution et AUCUN droit : les "
           "répertoires créés avant lui appartiennent à root, et une "
           "application non-root n'y écrit plus. Alignez le propriétaire, ne "
           "repassez pas en root.",
    )


def test_le_repertoire_appartient_a_l_application_sans_etre_ouvert_a_tous(host) -> None:
    """Le MOYEN est noté, et pas seulement l'effet.

    DEUX RÉPONSES FONT ÉCRIRE L'APPLICATION : donner le répertoire à son
    utilisateur, ou l'ouvrir à tout le monde. La seconde marche, et elle est
    refusée ici : rendre un répertoire inscriptible par n'importe qui pour
    qu'un processus non privilégié y écrive défait exactement ce que le passage
    en non-root cherchait à obtenir.

    C'est la même structure que `troubleshoot-permission-refusee`, où repasser
    en root est refusé bien que cela marche.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))
    uid = _paires(_lancer(host, "%s", IMAGE).stdout).get("uid", "")
    if not uid:
        pytest.skip(message(
            en="the image's uid could not be read: the first check says why",
            fr="l'uid de l'image n'a pas pu être lu : le premier contrôle dit "
               "pourquoi",
        ))

    # L'inspection se fait DANS l'image, avec l'identité qu'elle déclare : le
    # propriétaire et le mode sont ceux que le Dockerfile a posés.
    details = _lancer(
        host, "--entrypoint stat %s -c %s %s", IMAGE, "%u:%g:%a", DONNEES
    ).stdout.strip()
    assert details, message(
        en=f"{DONNEES} could not be inspected inside the image.\n"
           "The application writes there: it has to exist.",
        fr=f"{DONNEES} n'a pas pu être inspecté dans l'image.\n"
           "L'application y écrit : il doit exister.",
    )
    proprietaire, _, reste = details.partition(":")
    groupe, _, mode = reste.partition(":")
    assert proprietaire == uid or groupe == uid, message(
        en=f"{DONNEES} belongs to {proprietaire}:{groupe}, and the application "
           f"runs as {uid}.\n"
           "It writes there all the same, so the right comes from elsewhere: "
           "most likely from a mode open to everyone. Give the directory to "
           "the application's user or group.",
        fr=f"{DONNEES} appartient à {proprietaire}:{groupe}, et l'application "
           f"tourne sous {uid}.\n"
           "Elle y écrit pourtant, donc le droit vient d'ailleurs : très "
           "probablement d'un mode ouvert à tout le monde. Donnez le "
           "répertoire à l'utilisateur ou au groupe de l'application.",
    )
    assert mode and mode[-1] not in "2367", message(
        en=f"{DONNEES} is writable by everyone (mode {mode}).\n"
           "It does make the application write, and it undoes exactly what "
           "going non-root was meant to achieve: any process in the container, "
           "whatever its identity, can now write there.",
        fr=f"{DONNEES} est inscriptible par tout le monde (mode {mode}).\n"
           "Cela fait bien écrire l'application, et cela défait exactement ce "
           "que le passage en non-root cherchait : n'importe quel processus du "
           "conteneur, quelle que soit son identité, peut désormais y écrire.",
    )


def test_l_image_declare_son_utilisateur_par_un_uid_numerique(host) -> None:
    """La portabilité de la déclaration, et pourquoi elle est notée.

    UN `USER` PAR NOM SE RÉSOUT DANS LE `/etc/passwd` DE L'IMAGE. Un
    orchestrateur qui refuse les conteneurs root ne lit pas ce fichier : il lit
    la déclaration de l'image, et il ne peut pas prouver qu'un nom n'est pas
    root. Il refuse alors de démarrer le conteneur, ou le laisse passer sans
    rien garantir.

    UN UID NUMÉRIQUE SE VÉRIFIE SANS RIEN OUVRIR, et c'est tout l'intérêt. Le
    contrôle accepte `10001` comme `10001:10001`, et refuse `appli`.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))
    declare = host.run(
        "docker image inspect %s --format {{.Config.User}}", IMAGE
    ).stdout.strip()
    assert declare, message(
        en=f"`{IMAGE}` declares no user at all.\n"
           "It may run as non-root because of how it was launched: the image "
           "has to say it itself, otherwise nothing holds once it is handed "
           "over.",
        fr=f"`{IMAGE}` ne déclare aucun utilisateur.\n"
           "Elle tourne peut-être en non-root grâce à la façon dont elle a été "
           "lancée : c'est l'image qui doit le dire, sinon rien ne tient "
           "lorsqu'elle est transmise.",
    )
    morceaux = declare.split(":")
    assert all(m.isdigit() for m in morceaux if m), message(
        en=f"`{IMAGE}` declares its user by name: `{declare}`.\n"
           "A name is resolved in the image's own /etc/passwd. An orchestrator "
           "refusing root containers does not read that file: it reads the "
           "declaration, and it cannot prove a name is not root. A numeric uid "
           "can be checked without opening anything.",
        fr=f"`{IMAGE}` déclare son utilisateur par un nom : `{declare}`.\n"
           "Un nom se résout dans le /etc/passwd de l'image. Un orchestrateur "
           "qui refuse les conteneurs root ne lit pas ce fichier : il lit la "
           "déclaration, et il ne peut pas prouver qu'un nom n'est pas root. "
           "Un uid numérique se vérifie sans rien ouvrir.",
    )
    assert morceaux[0] != "0", message(
        en=f"`{IMAGE}` declares uid 0: `{declare}`.",
        fr=f"`{IMAGE}` déclare l'uid 0 : `{declare}`.",
    )
