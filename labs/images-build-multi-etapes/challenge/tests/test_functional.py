"""Tests fonctionnels du lab images-build-multi-etapes : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un outillage venu du SOCLE ne se retire pas. Il n'a
pas été installé par une instruction, donc aucune instruction ne peut le
désinstaller, et le cacher au conteneur ne retire pas un octet à l'image.

C'EST CE QUI LE DISTINGUE DE `images-optimiser-la-taille`. Là, le nettoyage
existait et était au mauvais endroit. Ici, il n'y a rien à nettoyer : il faut
que l'image finale ne parte pas du même socle.

MESURÉ SUR docker.lab LE 2026-10-30 :

| Image | Taille | Outillage présent |
| socle d'exécution | 8,3 Mo | sans objet |
| socle d'atelier | 39,8 Mo | oui |
| une seule étape | 39,8 Mo | **OUI** |
| deux étapes | 8,3 Mo | **NON** |

L'EMPREINTE EST LA PREUVE QU'UNE FABRICATION A EU LIEU. Mesuré le même jour :
elle change quand la source change, et reste stable quand la source ne change
pas. Un produit recopié depuis l'hôte n'en porterait aucune, et c'est ce que le
quatrième contrôle éprouve.

L'OUTIL DE FABRICATION REFUSE DE TOURNER SANS SON OUTILLAGE, et cela ferme la
fausse voie : on ne peut pas fabriquer sur le socle d'exécution. La seconde
étape n'est pas une élégance, c'est la seule issue.

AUCUNE VALEUR N'EST ÉCRITE EN DUR. Le jeton et la source sont tirés par le
setup, l'empreinte par la fabrication, et le seuil de poids est dérivé des deux
socles.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

IMAGE = "appli:finale"
ATELIER_TAG = "lab-atelier:1.0"
EXECUTION_TAG = "lab-execution:1.0"
ATELIER = "/opt/lab-multietapes"
CONTEXTE = f"{ATELIER}/appli"
SOURCE = f"{CONTEXTE}/source/version.txt"
LANCEUR = f"{CONTEXTE}/lancer.sh"
OUTILLAGE = "/usr/lib/atelier"
OUTIL = "/usr/local/bin/fabriquer"
ESSAI = "dsoxlab-essai-multietapes"

# LA MARGE AU-DESSUS DU SOCLE D'EXÉCUTION. Mesuré le 2026-10-30, l'image à deux
# étapes pèse 8 302 259 octets contre 8 302 174 pour le socle : 85 octets de
# plus. Accorder le double du socle laisse donc une marge énorme, et refuse
# sans appel les 39,8 Mo de l'image à une seule étape.
MARGE = 2.0

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


def _lancer(host, gabarit: str, *params):
    """Un conteneur d'essai NOMMÉ, et retiré de façon synchrone.

    `docker run --rm` rend la main avant que le moteur ait retiré le conteneur,
    et la photo du cycle de validation voit alors un conteneur déjà condamné.
    `docker rm -f`, lui, est synchrone. Leçon payée dans un lab voisin.
    """
    res = host.run(f"docker run --rm --name {ESSAI} " + gabarit, *params)
    host.run("docker rm -f %s", ESSAI)
    return res


def _octets(host, nom: str) -> int:
    res = host.run("docker image inspect %s --format {{.Size}}", nom)
    try:
        return int(res.stdout.strip())
    except ValueError:
        return 0


def _couches(host, nom: str) -> list[str]:
    """Les couches d'une image, dans l'ordre.

    LE FORMAT PASSE PAR UN PARAMÈTRE, ET C'EST OBLIGATOIRE : il contient des
    espaces, et une commande qui le porterait en clair serait découpée par le
    shell. Mesuré dans un lab voisin, docker recevait alors un format tronqué
    et rendait une sortie vide, ce qui faisait SAUTER le contrôle.
    """
    res = host.run(
        "docker image inspect %s --format %s",
        nom,
        "{{range .RootFS.Layers}}{{println .}}{{end}}",
    )
    return [c.strip() for c in res.stdout.splitlines() if c.strip()]


def _valeur(host, chemin: str) -> str:
    f = host.file(chemin)
    return f.content_string.strip() if f.exists else ""


def _jeton(host) -> str:
    for mot in _valeur(host, LANCEUR).split():
        if mot.startswith("jeton-"):
            return mot
    return ""


def _paires(sortie: str) -> dict[str, str]:
    paires = {}
    for ligne in sortie.splitlines():
        if "=" in ligne:
            cle, _, valeur = ligne.partition("=")
            paires[cle.strip()] = valeur.strip()
    return paires


def test_l_image_fonctionne_et_porte_son_produit(host) -> None:
    """L'image lance l'application, et le produit porte la source du dépôt.

    CE CONTRÔLE EXISTE POUR UNE RAISON PRÉCISE : la façon la plus rapide de
    retirer un outillage d'une image est de ne plus rien fabriquer. Le produit
    doit être là, et sa source doit être celle du dépôt, tirée au hasard à
    chaque passage.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               f"mission: the context is in {CONTEXTE}.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               f"la mission : le contexte est dans {CONTEXTE}.",
        ))

    jeton = _jeton(host)
    version = _valeur(host, SOURCE)
    if not jeton or not version:
        pytest.skip(message(
            en="the token or the source is missing from the repository: the "
               "setup did not finish",
            fr="le jeton ou la source manque dans le dépôt : le setup n'a pas "
               "abouti",
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
    assert paires.get("source") == version, message(
        en=f"the product does not carry the repository's source.\n"
           f"  expected: source={version}\n"
           f"  obtained: source={paires.get('source', '(absent)')}\n"
           "Removing the tooling by no longer building anything would be the "
           "fastest way, and it is not a solution.",
        fr=f"le produit ne porte pas la source du dépôt.\n"
           f"  attendu : source={version}\n"
           f"  obtenu : source={paires.get('source', '(absent)')}\n"
           "Retirer l'outillage en ne fabriquant plus rien serait le plus "
           "rapide, et ce n'est pas une solution.",
    )
    assert paires.get("empreinte"), message(
        en="the product carries no fabrication fingerprint.\n"
           "It is drawn when the fabrication runs: a product without one was "
           "not built here.",
        fr="le produit ne porte aucune empreinte de fabrication.\n"
           "Elle est tirée au moment où la fabrication tourne : un produit qui "
           "n'en porte pas n'a pas été fabriqué ici.",
    )


def test_l_image_ne_porte_plus_l_outillage(host) -> None:
    """Le cœur du lab : ce qui vient du socle ne se retire pas.

    DEUX MESURES, ET ELLES SONT COMPLÉMENTAIRES. L'absence des fichiers dit que
    le conteneur ne les voit plus ; le poids dit qu'ils ne sont plus dans
    l'image. Un `rm -rf` dans une instruction suivante donnerait la première
    sans la seconde, et c'est exactement la faute que
    `images-optimiser-la-taille` a enseigné à reconnaître.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))

    presents = []
    for chemin, drapeau in ((OUTILLAGE, "-d"), (OUTIL, "-e")):
        if _lancer(host, "--entrypoint test %s %s %s", IMAGE, drapeau, chemin).rc == 0:
            presents.append(chemin)
    assert not presents, message(
        en=f"`{IMAGE}` still carries the tooling: {', '.join(presents)}.\n"
           "The fabrication is over, and nobody needs it at runtime. It does "
           "not come from an instruction of this Dockerfile, it comes from the "
           "BASE: so it is the base of the final image that has to change.",
        fr=f"`{IMAGE}` porte encore l'outillage : {', '.join(presents)}.\n"
           "La fabrication est terminée, et personne n'en a besoin à "
           "l'exécution. Il ne vient pas d'une instruction de ce Dockerfile, "
           "il vient du SOCLE : c'est donc le socle de l'image finale qu'il "
           "faut changer.",
    )

    socle = _octets(host, EXECUTION_TAG)
    if not socle:
        pytest.skip(message(
            en=f"the execution base `{EXECUTION_TAG}` could not be weighed: "
               "the setup did not finish",
            fr=f"le socle d'exécution `{EXECUTION_TAG}` n'a pas pu être pesé : "
               "le setup n'a pas abouti",
        ))
    totale = _octets(host, IMAGE)
    plafond = int(socle * MARGE)
    assert 0 < totale <= plafond, message(
        en=f"`{IMAGE}` weighs {totale // 10**6} MB, where the execution base "
           f"weighs {socle // 10**6} MB.\n"
           "The files may well be gone from the container: a deletion played "
           "in a later instruction hides them without removing one byte from "
           "the image. Measured on this machine, two stages give 85 bytes more "
           "than the base.",
        fr=f"`{IMAGE}` pèse {totale // 10**6} Mo, là où le socle d'exécution "
           f"pèse {socle // 10**6} Mo.\n"
           "Les fichiers ont peut-être disparu du conteneur : une suppression "
           "jouée dans une instruction suivante les cache sans retirer un "
           "octet à l'image. Mesuré sur cette machine, deux étapes donnent "
           "85 octets de plus que le socle.",
    )


def test_l_image_est_construite_sur_le_socle_d_execution(host) -> None:
    """La base de l'image finale a réellement changé.

    LE CONTRÔLE COMPARE LES COUCHES : celles du socle d'exécution doivent être
    le préfixe des siennes, et celles de l'atelier ne doivent PAS l'être. La
    seconde moitié compte autant : une image pourrait être légère et dériver
    encore de l'atelier si l'outillage avait été retiré autrement.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))
    couches_exec = _couches(host, EXECUTION_TAG)
    couches_atelier = _couches(host, ATELIER_TAG)
    if not couches_exec or not couches_atelier:
        pytest.skip(message(
            en="the bases' layers could not be read: the setup did not finish",
            fr="les couches des socles n'ont pas pu être lues : le setup n'a "
               "pas abouti",
        ))
    couches_image = _couches(host, IMAGE)
    assert couches_image[: len(couches_exec)] == couches_exec, message(
        en=f"`{IMAGE}` is not built on `{EXECUTION_TAG}`.\n"
           f"  execution base: {len(couches_exec)} layers, image: "
           f"{len(couches_image)} layers\n"
           "The mission is that the final image does not start from the "
           "workshop, and that is read in the layers.",
        fr=f"`{IMAGE}` n'est pas construite sur `{EXECUTION_TAG}`.\n"
           f"  socle d'exécution : {len(couches_exec)} couches, image : "
           f"{len(couches_image)} couches\n"
           "La mission est que l'image finale ne parte pas de l'atelier, et "
           "cela se lit dans les couches.",
    )
    assert couches_image[: len(couches_atelier)] != couches_atelier, message(
        en=f"`{IMAGE}` still derives from `{ATELIER_TAG}`.\n"
           "Even light, an image that starts from the workshop carries its "
           "layers: a registry stores and transfers them with it.",
        fr=f"`{IMAGE}` dérive encore de `{ATELIER_TAG}`.\n"
           "Même légère, une image qui part de l'atelier porte ses couches : "
           "un dépôt les stocke et les transfère avec elle.",
    )


def test_le_produit_est_fabrique_et_non_recopie(host) -> None:
    """Le contrôle anti-triche, et il est le seul à le voir.

    LES TROIS PREMIERS PASSERAIENT sur un produit recopié depuis l'hôte, à une
    condition près : il faudrait y écrire une empreinte à la main. Celui-ci
    ferme la porte autrement : il change la SOURCE dans une copie du contexte,
    reconstruit, et exige que le produit suive.

    MESURÉ LE 2026-10-30 : l'empreinte change quand la source change, et reste
    stable quand elle ne change pas. C'est ce qui rend cette vérification
    fiable sans dépendre du cache.

    L'ÉTIQUETTE DE L'APPRENANT EST MISE DE CÔTÉ, puis rendue : la
    reconstruction se fait sous un nom à elle, pour ne rien écraser.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))
    avant = _paires(_lancer(host, "%s", IMAGE).stdout)
    if not avant.get("empreinte"):
        pytest.fail(message(
            en="the product carries no fingerprint: it was not built by the "
               "lab's fabrication tool.",
            fr="le produit ne porte aucune empreinte : il n'a pas été fabriqué "
               "par l'outil du lab.",
        ))

    bac = host.run("mktemp -d").stdout.strip()
    assert bac, message(
        en="no temporary directory could be created on the machine",
        fr="aucun répertoire temporaire n'a pu être créé sur la machine",
    )
    nouvelle = "v-change-par-le-controle"
    essai_tag = "appli:controle-multietapes"
    host.run("cp -a %s/. %s/", CONTEXTE, bac)
    host.run("sh -c %s", f"printf '%s\\n' '{nouvelle}' > {bac}/source/version.txt")
    construit = host.run("docker build -t %s %s", essai_tag, bac)
    apres = _paires(
        host.run("docker run --rm --name %s %s", f"{ESSAI}-ctrl", essai_tag).stdout
    )
    host.run("docker rm -f %s", f"{ESSAI}-ctrl")
    host.run("docker rmi -f %s", essai_tag)
    host.run("rm -rf %s", bac)

    assert construit.rc == 0, message(
        en=f"rebuilding in a copy of the context failed (code "
           f"{construit.rc}).\n"
           f"  {(construit.stderr or construit.stdout).strip()[-400:]}\n"
           "The Dockerfile has to stay buildable from the context as it "
           "stands, with one line changed in the source.",
        fr=f"la reconstruction dans une copie du contexte a échoué (code "
           f"{construit.rc}).\n"
           f"  {(construit.stderr or construit.stdout).strip()[-400:]}\n"
           "Le Dockerfile doit rester construisible depuis le contexte tel "
           "qu'il est, avec une ligne changée dans la source.",
    )
    assert apres.get("source") == nouvelle, message(
        en="changing the source did not change the product.\n"
           f"  expected: source={nouvelle}\n"
           f"  obtained: source={apres.get('source', '(absent)')}\n"
           "So the product does not come from a fabrication played during the "
           "build: it was most likely copied from the host, and it will stay "
           "frozen on the day the source changes for real.",
        fr="changer la source n'a pas changé le produit.\n"
           f"  attendu : source={nouvelle}\n"
           f"  obtenu : source={apres.get('source', '(absent)')}\n"
           "Le produit ne vient donc pas d'une fabrication jouée pendant la "
           "construction : il a très probablement été recopié depuis l'hôte, "
           "et il restera figé le jour où la source changera pour de vrai.",
    )
    assert apres.get("empreinte") and apres["empreinte"] != avant["empreinte"], message(
        en="the fingerprint did not change although the source did.\n"
           "It is drawn when the fabrication runs: an unchanged fingerprint "
           "means the fabrication was not replayed, so the product does not "
           "depend on the source.",
        fr="l'empreinte n'a pas changé alors que la source, oui.\n"
           "Elle est tirée au moment où la fabrication tourne : une empreinte "
           "inchangée veut dire que la fabrication n'a pas été rejouée, donc "
           "que le produit ne dépend pas de la source.",
    )
