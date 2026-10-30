"""Tests fonctionnels du lab images-contexte-de-build : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un `COPY` ne peut pas sortir du contexte de
construction, et que le message ne le dit plus.

MESURÉ SUR docker.lab LE 2026-10-30, le même Dockerfile sous les deux
constructeurs :

| Constructeur | Message |
| buildkit (le défaut) | `"/commun/version.txt": not found` |
| classique (`DOCKER_BUILDKIT=0`) | `forbidden path outside the build context` |

LE PREMIER DIT « INTROUVABLE », ET LE FICHIER EXISTE. Le `..` est normalisé
puis écrasé : le moteur ne regarde que dans le contexte, et rend compte de ce
qu'il voit, pas de ce qui est. Le second nommait la cause ; le message s'est
dégradé en changeant de constructeur, et c'est pourquoi tant de réponses
trouvées en ligne parlent d'un fichier manquant.

UNE MESURE QUI CHANGE CE QU'ON CROIT SAVOIR, et qui explique ce que ce lab ne
note PAS. Sous buildkit, un contexte volumineux n'est pas envoyé en entier :
avec 20 Mo d'archives dans le dépôt, `transferring context` a mesuré 2 octets,
et l'image pesait exactement la taille du socle. Le poids du contexte n'est donc
plus l'argument, et un contrôle là-dessus mesurerait une croyance. Ce qui reste
vrai, c'est qu'une copie en bloc fait entrer dans l'image ce qui ne doit pas y
être.

LES CONTRÔLES REJOUENT `construire.sh` DANS UNE COPIE DU DÉPÔT. C'est ce qui
permet de vérifier que le fichier partagé est toujours la source unique, sans
toucher au travail de l'apprenant, et c'est pourquoi le script doit être écrit
en chemins relatifs.

AUCUNE VALEUR N'EST ÉCRITE EN DUR DANS CE FICHIER. Le jeton et la version sont
tirés par le setup, et relus dans les fichiers du dépôt au moment de la
notation.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

IMAGE = "appli:contexte"
# L'étiquette sous laquelle le dernier contrôle met l'image de
# l'apprenant de côté le temps de reconstruire, puis la lui rend.
SAUVEGARDE = "appli:sauvegarde-du-controle"
# Le nom des conteneurs d'essai. Le préfixe du dépôt est la discipline
# du `conftest.py` : rien de ce qu'un test crée ne se confond avec le
# travail de l'apprenant.
ESSAI = "dsoxlab-essai-contexte"
DEPOT = "/opt/lab-contexte/depot"
SCRIPT = f"{DEPOT}/construire.sh"
PARTAGE = f"{DEPOT}/commun/version.txt"
CODE = f"{DEPOT}/appli/src/main.sh"
SECRET_SOURCE = f"{DEPOT}/secrets/jeton-prod.txt"

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


def _image_absente(host, nom: str = IMAGE) -> bool:
    return host.run("docker image inspect %s", nom).rc != 0


def _valeur(host, chemin: str) -> str:
    f = host.file(chemin)
    return f.content_string.strip() if f.exists else ""


def _jeton_du_code(host) -> str:
    source = _valeur(host, CODE)
    for mot in source.split():
        if mot.startswith("jeton-"):
            return mot
    return ""


def _lancer(host, gabarit: str, *params):
    """Un conteneur d'essai NOMMÉ, et retiré de façon synchrone.

    MESURÉ LE 2026-10-30 : `docker run --rm` rend la main dès que le processus
    sort, et le moteur retire le conteneur APRÈS, de façon asynchrone. Le cycle
    de validation a donc rendu ROUGE sur un conteneur anonyme qui avait déjà
    disparu quand je suis allé le chercher.

    `docker rm -f`, lui, est synchrone. Le nom porte le préfixe du dépôt, qui
    est la discipline du `conftest.py` : rien de ce qu'un test crée ne peut se
    confondre avec le travail de l'apprenant.

    Le `--rm` reste posé en plus : si un test s'interrompt avant le retrait
    explicite, le moteur finit le travail.
    """
    res = host.run(f"docker run --rm --name {ESSAI} " + gabarit, *params)
    host.run("docker rm -f %s", ESSAI)
    return res

def test_la_construction_se_rejoue_par_un_script(host) -> None:
    """La construction doit tenir dans un script, et pas dans un terminal.

    CE N'EST PAS UNE COQUETTERIE. Les trois autres contrôles rejouent ce
    script : sans lui, il n'y aurait aucun moyen de vérifier que le fichier
    partagé est toujours la source unique, puisque la commande de construction
    n'existerait nulle part.

    LE SCRIPT EST JOUÉ DANS UNE COPIE DU DÉPÔT, sous un autre nom d'image : le
    travail de l'apprenant n'est pas touché, et le verdict ne porte pas sur un
    état que le test aurait produit.
    """
    script = host.file(SCRIPT)
    assert script.exists, message(
        en=f"{SCRIPT} does not exist. The build has to be replayable from a "
           "script: a command that only lives in a terminal's history is not "
           "reproducible, and the other checks replay this one.",
        fr=f"{SCRIPT} n'existe pas. La construction doit se rejouer par un "
           "script : une commande qui ne vit que dans l'historique d'un "
           "terminal n'est pas reproductible, et les autres contrôles "
           "rejouent celui-ci.",
    )

    bac = host.run("mktemp -d").stdout.strip()
    assert bac, message(
        en="no temporary directory could be created on the machine",
        fr="aucun répertoire temporaire n'a pu être créé sur la machine",
    )
    host.run("cp -a %s/. %s/", DEPOT, bac)
    joue = host.run("sh -c %s", f"cd {bac} && sh ./construire.sh")
    host.run("rm -rf %s", bac)
    assert joue.rc == 0, message(
        en=f"replaying {SCRIPT} in a copy of the repository failed "
           f"(code {joue.rc}).\n"
           f"  {(joue.stderr or joue.stdout).strip()[-400:]}\n"
           "It has to work from any copy of the repository, so in RELATIVE "
           "paths: an absolute path pointing back at the original directory "
           "builds something other than what is being read.",
        fr=f"rejouer {SCRIPT} dans une copie du dépôt a échoué "
           f"(code {joue.rc}).\n"
           f"  {(joue.stderr or joue.stdout).strip()[-400:]}\n"
           "Il doit marcher depuis n'importe quelle copie du dépôt, donc en "
           "chemins RELATIFS : un chemin absolu qui repointe sur le "
           "répertoire d'origine construit autre chose que ce qu'on lit.",
    )


def test_l_image_porte_le_code_et_la_version_partagee(host) -> None:
    """L'image fonctionne, et elle porte le fichier rangé hors de son répertoire.

    LES DEUX VALEURS SONT RELUES dans le dépôt au moment de la notation : le
    jeton dans le code, la version dans le fichier partagé. Aucune n'est écrite
    ici, et le setup les tire au hasard à chaque passage.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               f"mission: the repository is in {DEPOT}.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               f"la mission : le dépôt est dans {DEPOT}.",
        ))

    jeton = _jeton_du_code(host)
    version = _valeur(host, PARTAGE)
    if not jeton or not version:
        pytest.skip(message(
            en="the token or the shared version is missing from the "
               "repository: the setup did not finish",
            fr="le jeton ou la version partagée manque dans le dépôt : le "
               "setup n'a pas abouti",
        ))

    lance = _lancer(host, "%s", IMAGE)
    assert jeton in lance.stdout, message(
        en=f"`{IMAGE}` does not print the token its source carries.\n"
           f"  printed: {lance.stdout.strip()[:160] or '(nothing)'}\n"
           "So the image does not carry the current code.",
        fr=f"`{IMAGE}` n'imprime pas le jeton que porte son source.\n"
           f"  imprimé : {lance.stdout.strip()[:160] or '(rien)'}\n"
           "L'image ne porte donc pas le code courant.",
    )
    assert version in lance.stdout, message(
        en=f"`{IMAGE}` does not print the shared version.\n"
           f"  expected: {version}\n"
           f"  printed: {lance.stdout.strip()[:160] or '(nothing)'}\n"
           "The file it needs is ranged OUTSIDE its directory, and a `COPY` "
           "cannot leave the context. The message says it cannot be found, and "
           "the file does exist: the cause is the context's boundary, not a "
           "missing file.",
        fr=f"`{IMAGE}` n'imprime pas la version partagée.\n"
           f"  attendue : {version}\n"
           f"  imprimé : {lance.stdout.strip()[:160] or '(rien)'}\n"
           "Le fichier dont elle a besoin est rangé HORS de son répertoire, et "
           "un `COPY` ne peut pas sortir du contexte. Le message dit qu'il est "
           "introuvable, et le fichier existe bien : la cause est la frontière "
           "du contexte, pas un fichier manquant.",
    )


def test_ni_le_secret_ni_les_archives_n_entrent_dans_l_image(host) -> None:
    """Ce qu'une copie en bloc fait entrer, et ce que ce lab ne note pas.

    LE POIDS DU CONTEXTE N'EST PAS LE SUJET, et c'est une mesure qui l'a
    décidé : sous buildkit, 20 Mo d'archives dans le dépôt donnent
    `transferring context: 2B` et une image de la taille exacte du socle. Un
    contrôle sur le temps de transfert mesurerait une croyance.

    CE QUI RESTE VRAI est ici : élargir le contexte pour atteindre un fichier
    voisin met tout le dépôt à portée d'un `COPY .`, secret compris. Le
    contrôle cherche le CONTENU du secret, et pas seulement son chemin : le
    copier ailleurs dans l'image ne doit pas suffire à passer.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))

    secret = _valeur(host, SECRET_SOURCE)
    if not secret:
        pytest.skip(message(
            en="the repository's secret is missing: the setup did not finish",
            fr="le secret du dépôt est absent : le setup n'a pas abouti",
        ))

    trouve = _lancer(
        host,
        "--entrypoint grep %s -rl %s / --exclude-dir=proc "
        "--exclude-dir=sys --exclude-dir=dev",
        IMAGE,
        secret.splitlines()[0],
    )
    assert trouve.rc != 0, message(
        en=f"`{IMAGE}` carries the repository's secret, at: "
           f"{trouve.stdout.strip()[:200]}\n"
           "Widening the context to reach a neighbouring file puts the whole "
           "repository within reach of a `COPY .`. An image is handed around, "
           "and whatever enters it leaves with it.",
        fr=f"`{IMAGE}` porte le secret du dépôt, à : "
           f"{trouve.stdout.strip()[:200]}\n"
           "Élargir le contexte pour atteindre un fichier voisin met tout le "
           "dépôt à portée d'un `COPY .`. Une image se transmet, et ce qui y "
           "entre en repart avec elle.",
    )

    archives = _lancer(
        host,
        "--entrypoint sh %s -c %s",
        IMAGE,
        "find / -name dump.bin -not -path '/proc/*' 2>/dev/null | head -3",
    )
    assert not archives.stdout.strip(), message(
        en=f"`{IMAGE}` carries the repository's archives, at: "
           f"{archives.stdout.strip()[:200]}\n"
           "Nobody needs them in the image, and they would be shipped with it "
           "on every pull.",
        fr=f"`{IMAGE}` porte les archives du dépôt, à : "
           f"{archives.stdout.strip()[:200]}\n"
           "Personne n'en a besoin dans l'image, et elles partiraient avec "
           "elle à chaque téléchargement.",
    )


def test_le_fichier_partage_reste_la_source_unique(host) -> None:
    """La contrainte du rangement, et la seule réponse qui la respecte.

    RECOPIER LE FICHIER DANS LE RÉPERTOIRE DE L'APPLICATION réglerait la
    construction en une commande, et créerait la divergence que ce rangement
    existe pour éviter : deux copies d'une même vérité, dont une sera oubliée.

    LE CONTRÔLE LE MESURE PAR L'EFFET. Il copie le dépôt, change la version
    dans `commun/`, rejoue `construire.sh`, et l'image reconstruite doit porter
    la NOUVELLE valeur. Une copie figée dans `appli/` porterait l'ancienne, et
    aucune lecture du Dockerfile n'était nécessaire pour le dire.
    """
    script = host.file(SCRIPT)
    if not script.exists:
        pytest.fail(message(
            en=f"{SCRIPT} does not exist: this check replays it.",
            fr=f"{SCRIPT} n'existe pas : ce contrôle le rejoue.",
        ))

    bac = host.run("mktemp -d").stdout.strip()
    assert bac, message(
        en="no temporary directory could be created on the machine",
        fr="aucun répertoire temporaire n'a pu être créé sur la machine",
    )
    nouvelle = "v-change-par-le-controle"

    # L'ÉTIQUETTE DE L'APPRENANT EST MISE DE CÔTÉ, PUIS RENDUE. Le script
    # reconstruit sous le nom attendu, donc il écrase son image : sans cette
    # sauvegarde, le `check` suivant trouverait une image portant la version du
    # contrôle, et le deuxième contrôle refuserait un travail correct.
    host.run("docker tag %s %s", IMAGE, SAUVEGARDE)
    host.run("cp -a %s/. %s/", DEPOT, bac)
    host.run("sh -c %s", f"printf '%s\\n' '{nouvelle}' > {bac}/commun/version.txt")
    joue = host.run("sh -c %s", f"cd {bac} && sh ./construire.sh")
    sortie = _lancer(host, "%s", IMAGE).stdout
    host.run("docker rmi -f %s", IMAGE)
    host.run("docker tag %s %s", SAUVEGARDE, IMAGE)
    host.run("docker rmi -f %s", SAUVEGARDE)
    host.run("rm -rf %s", bac)

    assert joue.rc == 0, message(
        en=f"replaying {SCRIPT} after changing the shared file failed "
           f"(code {joue.rc}).\n"
           f"  {(joue.stderr or joue.stdout).strip()[-400:]}",
        fr=f"rejouer {SCRIPT} après un changement du fichier partagé a échoué "
           f"(code {joue.rc}).\n"
           f"  {(joue.stderr or joue.stdout).strip()[-400:]}",
    )
    assert nouvelle in sortie, message(
        en="changing the shared file did not change the rebuilt image.\n"
           f"  printed: {sortie.strip()[:200] or '(nothing)'}\n"
           "So the image does not read `commun/version.txt` any more: a copy "
           "of it was most likely made inside the application's directory. "
           "That fixes the build and creates the divergence this layout exists "
           "to prevent, two copies of one truth, one of which will be "
           "forgotten.",
        fr="changer le fichier partagé n'a pas changé l'image reconstruite.\n"
           f"  imprimé : {sortie.strip()[:200] or '(rien)'}\n"
           "L'image ne lit donc plus `commun/version.txt` : une copie en a "
           "très probablement été faite dans le répertoire de l'application. "
           "Cela règle la construction et crée la divergence que ce rangement "
           "existe pour éviter, deux copies d'une même vérité dont une sera "
           "oubliée.",
    )
