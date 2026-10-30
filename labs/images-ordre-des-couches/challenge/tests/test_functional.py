"""Tests fonctionnels du lab images-ordre-des-couches : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que l'ordre des instructions d'un Dockerfile décide de ce
que le cache peut servir, et que le défaut ne se voit pas : l'image produite est
juste dans les deux cas. Seul son coût de reconstruction change.

MESURÉ SUR docker.lab LE 2026-10-30, sur le même contexte et deux ordres :

| Ordre | code changé | manifeste changé |
| --- | --- | --- |
| `COPY . /app` puis installation | travail **refait** (3 s) | refait |
| manifeste, installation, puis code | travail **servi par le cache** (1 s) | refait |

L'EMPREINTE EST LA PREUVE, et c'est ce qui rend ce lab mesurable. L'outil
d'installation tire seize octets au hasard et les écrit dans l'image : deux
images qui portent la MÊME empreinte n'ont pas rejoué l'instruction, donc la
couche vient du cache. L'identifiant de couche, lui, vaut `<missing>` sous
buildkit, mesuré le même jour : il ne distingue rien, et le premier jet de ces
tests s'y était appuyé.

LES DEUX MOITIÉS SONT NOTÉES, ET C'EST DÉLIBÉRÉ. Le cache doit servir quand le
code change, et il doit CESSER de servir quand le manifeste change. Un
Dockerfile qui copierait le manifeste après l'installation ne réinstallerait
jamais : le cache servirait toujours, l'image serait figée sur d'anciennes
dépendances, et un contrôle qui ne regarderait que la première moitié le
récompenserait.

LE TROISIÈME CONTRÔLE TRAVAILLE DANS UNE COPIE du contexte. Modifier le
répertoire de l'apprenant pour le noter serait doublement fautif : cela
détruirait son travail, et le verdict porterait sur un état que le test a
produit lui-même.

AUCUNE VALEUR N'EST ÉCRITE EN DUR DANS CE FICHIER. Le jeton est tiré par le
setup et relu dans le code source au moment de la notation ; les dépendances
sont relues dans le manifeste.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

IMAGE = "appli:ordonnee"
ATELIER = "/opt/lab-couches"
CONTEXTE = f"{ATELIER}/appli"
MANIFESTE = f"{CONTEXTE}/dependances.txt"
CODE = f"{CONTEXTE}/src/main.sh"
BROUILLON = "notes/brouillon.log"
EMPREINTE = "/opt/deps/.empreinte"

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


def _dans_l_image(host, chemin: str) -> str:
    """Le contenu d'un fichier de l'image, ou une chaîne vide.

    `--entrypoint cat` plutôt que la commande de l'image : le lab ne dit rien
    de ce que l'image lance, et l'interroger ne doit pas dépendre de cela.
    """
    res = host.run(
        "docker run --rm --entrypoint cat %s %s", IMAGE, chemin
    )
    return res.stdout.strip() if res.rc == 0 else ""


def _dependances_declarees(host) -> list[str]:
    f = host.file(MANIFESTE)
    if not f.exists:
        return []
    return [
        ligne.strip() for ligne in f.content_string.splitlines() if ligne.strip()
    ]


def _empreinte_apres_modification(host, fichier: str, ajout: str) -> str:
    """L'empreinte d'une image reconstruite dans une COPIE du contexte.

    La copie est le point : le répertoire de l'apprenant n'est pas touché, et
    le verdict ne porte donc pas sur un état que le test aurait produit.

    Rend une chaîne vide quand la copie ou la construction échoue, et le
    message de l'appelant le dit plutôt que de conclure à une faute.
    """
    bac = host.run("mktemp -d").stdout.strip()
    if not bac:
        return ""
    etiquette = f"lab-couches-essai:{fichier.replace('/', '-')}"
    host.run("cp -a %s/. %s/", CONTEXTE, bac)
    host.run("sh -c %s", f"printf '%s\\n' '{ajout}' >> {bac}/{fichier}")
    construit = host.run(
        "docker build -t %s %s", etiquette, bac
    )
    if construit.rc != 0:
        host.run("rm -rf %s", bac)
        return ""
    lue = host.run(
        "docker run --rm --entrypoint cat %s %s", etiquette, EMPREINTE
    )
    host.run("docker rmi -f %s", etiquette)
    host.run("rm -rf %s", bac)
    return lue.stdout.strip() if lue.rc == 0 else ""


def test_l_image_fonctionne_et_porte_ses_dependances(host) -> None:
    """L'image existe, lance le code courant, et porte ce que le manifeste dit.

    LE JETON EST TIRÉ PAR LE SETUP et relu ici dans le code source : il prouve
    que l'image porte le code COURANT, et non une image d'un passage antérieur
    restée sous le même nom.

    LES DÉPENDANCES SONT RELUES dans le manifeste, et non écrites ici. Sans ce
    contrôle, le moyen le plus rapide de rendre le cache efficace serait de ne
    plus rien installer.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               f"mission: the context is in {CONTEXTE}.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               f"la mission : le contexte est dans {CONTEXTE}.",
        ))

    source = host.file(CODE)
    if not source.exists:
        pytest.skip(message(
            en=f"{CODE} is missing: the setup did not finish",
            fr=f"{CODE} est absent : le setup n'a pas abouti",
        ))
    jetons = [
        mot for ligne in source.content_string.splitlines()
        for mot in ligne.split() if mot.startswith("jeton-")
    ]
    if not jetons:
        pytest.skip(message(
            en=f"{CODE} carries no token: the setup did not finish",
            fr=f"{CODE} ne porte aucun jeton : le setup n'a pas abouti",
        ))
    attendu = jetons[0]

    lance = host.run("docker run --rm %s", IMAGE)
    assert attendu in lance.stdout, message(
        en=f"`{IMAGE}` does not print the token its source carries.\n"
           f"  printed: {lance.stdout.strip()[:120] or '(nothing)'}\n"
           "So the image does not carry the current code: either it was built "
           "from another context, or it does not launch the application.",
        fr=f"`{IMAGE}` n'imprime pas le jeton que porte son source.\n"
           f"  imprimé : {lance.stdout.strip()[:120] or '(rien)'}\n"
           "L'image ne porte donc pas le code courant : soit elle a été "
           "construite depuis un autre contexte, soit elle ne lance pas "
           "l'application.",
    )

    declarees = _dependances_declarees(host)
    assert declarees, message(
        en=f"{MANIFESTE} is empty or missing: the setup did not finish",
        fr=f"{MANIFESTE} est vide ou absent : le setup n'a pas abouti",
    )
    installees = host.run(
        "docker run --rm --entrypoint ls %s /opt/deps", IMAGE
    ).stdout.split()
    manquantes = [d for d in declarees if d not in installees]
    assert not manquantes, message(
        en=f"`{IMAGE}` does not carry the declared dependencies: "
           f"{', '.join(manquantes)}.\n"
           "Making the cache efficient by no longer installing anything would "
           "be the fastest way, and it is not a solution: the image has to "
           "carry what the manifest declares.",
        fr=f"`{IMAGE}` ne porte pas les dépendances déclarées : "
           f"{', '.join(manquantes)}.\n"
           "Rendre le cache efficace en n'installant plus rien serait le plus "
           "rapide, et ce n'est pas une solution : l'image doit porter ce que "
           "le manifeste déclare.",
    )


def test_l_image_ne_porte_que_ce_qui_lui_sert(host) -> None:
    """Ce qu'un `COPY . /app` fait entrer sans qu'on le demande.

    C'est la seconde moitié du lab, et elle se mesure aussi bien que la
    première : le contexte porte un brouillon et le Dockerfile lui-même, et
    aucun des deux n'a de raison d'être dans l'image.

    LE CONTRÔLE NE DIT PAS COMMENT LES EXCLURE. Un `.dockerignore` et un `COPY`
    ciblé donnent le même état, et c'est l'état qui est noté.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))

    intrus = []
    for chemin in (f"/app/{BROUILLON}", "/app/Dockerfile"):
        present = host.run(
            "docker run --rm --entrypoint test %s -e %s", IMAGE, chemin
        )
        if present.rc == 0:
            intrus.append(chemin)
    assert not intrus, message(
        en=f"`{IMAGE}` carries what has no reason to be there: "
           f"{', '.join(intrus)}.\n"
           "A copy of the whole context does not copy \"the code\", it copies "
           "EVERYTHING: the Dockerfile and the drafts included. They swell the "
           "image, and above all every one of them invalidates the cache when "
           "it changes.",
        fr=f"`{IMAGE}` porte ce qui n'a aucune raison d'y être : "
           f"{', '.join(intrus)}.\n"
           "Une copie du contexte entier ne copie pas « le code », elle copie "
           "TOUT, le Dockerfile et les brouillons compris. Ils grossissent "
           "l'image, et surtout chacun d'eux invalide le cache quand il "
           "change.",
    )


def test_un_changement_de_code_ne_refait_pas_l_installation(host) -> None:
    """Le cœur du lab, mesuré sur une copie du contexte.

    L'EMPREINTE TRANCHE : identique entre l'image de l'apprenant et celle
    reconstruite après une modification du code, l'instruction n'a pas été
    rejouée. C'est exactement ce que l'ordre des instructions décide.

    LA MODIFICATION EST UN AJOUT EN FIN DE FICHIER, dans une copie : le code
    reste exécutable, l'image reste construisible, et le travail de l'apprenant
    n'est pas touché.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))
    reference = _dans_l_image(host, EMPREINTE)
    assert reference, message(
        en=f"`{IMAGE}` carries no installation fingerprint at {EMPREINTE}.\n"
           "So the installation tool never ran in it: the image does not come "
           "from the lab's context, or its installation step was removed.",
        fr=f"`{IMAGE}` ne porte aucune empreinte d'installation à "
           f"{EMPREINTE}.\n"
           "L'outil d'installation n'y a donc jamais tourné : l'image ne vient "
           "pas du contexte du lab, ou son étape d'installation a été retirée.",
    )

    apres = _empreinte_apres_modification(host, "src/main.sh", "# une ligne de plus")
    assert apres, message(
        en="rebuilding after a code change failed, or produced no "
           "fingerprint.\n"
           "The Dockerfile has to stay buildable from the context as it "
           "stands: a copy of it was used, with one comment line appended to "
           "the source.",
        fr="la reconstruction après un changement de code a échoué, ou n'a "
           "produit aucune empreinte.\n"
           "Le Dockerfile doit rester construisible depuis le contexte tel "
           "qu'il est : une copie en a été utilisée, avec une ligne de "
           "commentaire ajoutée au source.",
    )
    assert apres == reference, message(
        en="changing one line of code redid the whole installation.\n"
           "The step costs a second per dependency, and nothing in the "
           "manifest changed. The order of the instructions is what decides: "
           "everything that changes often has to come AFTER the expensive "
           "work, and what that work depends on has to come before it, alone.",
        fr="changer une ligne de code a refait toute l'installation.\n"
           "L'étape coûte une seconde par dépendance, et rien n'a changé dans "
           "le manifeste. C'est l'ordre des instructions qui en décide : tout "
           "ce qui change souvent doit venir APRÈS le travail coûteux, et ce "
           "dont ce travail dépend doit venir avant lui, seul.",
    )


def test_un_changement_de_manifeste_refait_l_installation(host) -> None:
    """La moitié qu'on oublie, et sans laquelle le lab enseignerait un piège.

    UN CACHE QUI SERT TOUJOURS EST UNE FAUTE. Copier le manifeste après
    l'installation, ou l'installer depuis une copie figée dans l'image de base,
    rendrait le premier contrôle vert et l'image serait figée sur d'anciennes
    dépendances : le cache servirait même quand il ne doit plus.

    LE CONTRÔLE VÉRIFIE LES DEUX CHOSES : que le travail est refait, et que la
    nouvelle dépendance est réellement installée. La première sans la seconde
    laisserait passer une image qui refait un travail sans effet.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))
    reference = _dans_l_image(host, EMPREINTE)
    if not reference:
        pytest.fail(message(
            en=f"`{IMAGE}` carries no installation fingerprint at "
               f"{EMPREINTE}: the installation tool never ran in it.",
            fr=f"`{IMAGE}` ne porte aucune empreinte d'installation à "
               f"{EMPREINTE} : l'outil d'installation n'y a jamais tourné.",
        ))

    nouvelle = "delta"
    bac = host.run("mktemp -d").stdout.strip()
    assert bac, message(
        en="no temporary directory could be created on the machine",
        fr="aucun répertoire temporaire n'a pu être créé sur la machine",
    )
    etiquette = "lab-couches-essai:manifeste"
    host.run("cp -a %s/. %s/", CONTEXTE, bac)
    host.run("sh -c %s", f"printf '%s\\n' '{nouvelle}' >> {bac}/dependances.txt")
    construit = host.run("docker build -t %s %s", etiquette, bac)
    if construit.rc != 0:
        host.run("rm -rf %s", bac)
        pytest.fail(message(
            en="rebuilding after a manifest change failed.\n"
               "The Dockerfile has to stay buildable from the context as it "
               "stands, with one dependency appended to the manifest.",
            fr="la reconstruction après un changement du manifeste a échoué.\n"
               "Le Dockerfile doit rester construisible depuis le contexte tel "
               "qu'il est, avec une dépendance ajoutée au manifeste.",
        ))
    apres = host.run(
        "docker run --rm --entrypoint cat %s %s", etiquette, EMPREINTE
    ).stdout.strip()
    installees = host.run(
        "docker run --rm --entrypoint ls %s /opt/deps", etiquette
    ).stdout.split()
    host.run("docker rmi -f %s", etiquette)
    host.run("rm -rf %s", bac)

    assert apres and apres != reference, message(
        en="adding a dependency did not redo the installation.\n"
           "So the cache serves even when it must not, and the image is "
           "frozen on old dependencies. The expensive work has to depend on "
           "the manifest, which means the manifest has to be copied BEFORE "
           "it, not after.",
        fr="ajouter une dépendance n'a pas refait l'installation.\n"
           "Le cache sert donc même quand il ne doit plus, et l'image est "
           "figée sur d'anciennes dépendances. Le travail coûteux doit "
           "dépendre du manifeste, ce qui veut dire que le manifeste doit être "
           "copié AVANT lui, et non après.",
    )
    assert nouvelle in installees, message(
        en=f"the installation was redone, but `{nouvelle}` is not in the "
           "rebuilt image.\n"
           "So the step runs without effect: it does not install what the "
           "manifest of the context declares.",
        fr=f"l'installation a bien été refaite, mais `{nouvelle}` n'est pas "
           "dans l'image reconstruite.\n"
           "L'étape tourne donc sans effet : elle n'installe pas ce que "
           "déclare le manifeste du contexte.",
    )
