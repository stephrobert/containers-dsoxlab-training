"""Tests fonctionnels du lab images-optimiser-la-taille : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'une couche garde ce qu'une couche suivante supprime, et
que le conteneur, lui, ne montre rien de ce poids : le cache n'y est pas
visible, les artefacts utiles y sont. Le défaut ne se voit qu'à la pesée.

MESURÉ SUR docker.lab LE 2026-10-30, le même travail sous deux écritures :

| Écriture | Taille | Couches | Plus grosse couche |
| nettoyage dans l'instruction SUIVANTE | 52,3 Mo | 5 | **44 Mo** |
| nettoyage dans la MÊME instruction | 14,6 Mo | 4 | 6,3 Mo |

ET UNE TROISIÈME MESURE, qui a décidé du quatrième contrôle. Aplatir l'image
(`docker export | docker import`) donne 14,6 Mo elle aussi, en UNE couche, et
elle ne partage plus aucune couche avec son socle. Un contrôle qui ne pèserait
que le total récompenserait donc ce geste, qui fait stocker et transférer
l'image entière pour chaque variante.

AUCUN SEUIL N'EST ÉCRIT DANS CE FICHIER. Les contrôles pèsent le socle et les
artefacts utiles au moment de la notation, et en dérivent ce qu'ils acceptent.
Une valeur en dur serait fausse dès que le socle change de version.

LES CONTENEURS D'ESSAI SONT NOMMÉS ET RETIRÉS, et c'est une leçon payée dans un
lab voisin : `docker run --rm` rend la main avant que le moteur ait retiré le
conteneur, et la photo du cycle de validation voyait un conteneur anonyme déjà
condamné. `docker rm -f`, lui, est synchrone.
"""

from __future__ import annotations

import contextlib

import pytest

from conftest import lab_host, message

IMAGE = "appli:legere"
SOCLE = "lab-taille:1.0"
ATELIER = "/opt/lab-taille"
CONTEXTE = f"{ATELIER}/appli"
ATTENDUS = f"{CONTEXTE}/attendus.txt"
CODE = f"{CONTEXTE}/src/main.sh"
UTILE = "/opt/app"
CACHE = "/var/cache/fabrique"
ESSAI = "dsoxlab-essai-taille"

# LA MARGE ACCORDÉE AU-DESSUS DU STRICT NÉCESSAIRE. Deux fois le volume utile :
# assez pour ne pas refuser une écriture correcte qui laisse quelques
# mégaoctets de métadonnées, et très loin des 44 Mo du nettoyage tardif. La
# mesure du 2026-10-30 donne 6,3 Mo pour la bonne écriture contre 44 pour
# l'autre : le seuil ne départage pas des cas limites, il sépare deux mondes.
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
    """Un conteneur d'essai NOMMÉ, et retiré de façon synchrone."""
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
    shell en plusieurs arguments. Mesuré le 2026-10-30, docker recevait alors
    un format tronqué et rendait une sortie vide, ce qui faisait SAUTER ce
    contrôle au lieu de le jouer. Les `%s` de testinfra, eux, sont quotés.
    """
    res = host.run(
        "docker image inspect %s --format %s",
        nom,
        "{{range .RootFS.Layers}}{{println .}}{{end}}",
    )
    return [c.strip() for c in res.stdout.splitlines() if c.strip()]


def _volume_utile(host) -> int:
    """Le poids réel des artefacts, pesé DANS l'image au moment de la notation.

    C'est ce qui remplace un seuil écrit : la mesure suit le socle et les
    artefacts, et elle reste juste quand l'un des deux change.
    """
    res = _lancer(host, "--entrypoint du %s -sk %s", IMAGE, UTILE)
    premier = res.stdout.split()
    try:
        return int(premier[0]) * 1024
    except (IndexError, ValueError):
        return 0


def _tailles_de_couche(host, nom: str) -> list[int]:
    """Les tailles affichées par `docker history`, converties en octets.

    `docker history` ne rend pas d'octets : il affiche « 44MB », « 311B »,
    « 0B ». Le tableau est converti ici, et les unités du moteur sont
    décimales, d'où les puissances de 1000.
    """
    res = host.run("docker history --format {{.Size}} %s", nom)
    facteurs = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}
    tailles = []
    for brute in res.stdout.split():
        texte = brute.strip()
        for unite in ("TB", "GB", "MB", "KB", "B"):
            if texte.endswith(unite):
                with contextlib.suppress(ValueError):
                    tailles.append(int(float(texte[: -len(unite)]) * facteurs[unite]))
                break
    return tailles


def test_l_image_fonctionne_et_porte_ses_artefacts(host) -> None:
    """L'image existe, lance le code courant, et porte ce que le manifeste dit.

    CE CONTRÔLE EXISTE POUR UNE RAISON PRÉCISE : le moyen le plus rapide
    d'alléger une image est de ne plus rien y mettre. L'empreinte prouve en
    outre que la fabrication a bien eu lieu dans CETTE image, et non qu'un
    répertoire a été recopié d'ailleurs.
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
    jetons = [m for m in source.content_string.split() if m.startswith("jeton-")]
    if not jetons:
        pytest.skip(message(
            en=f"{CODE} carries no token: the setup did not finish",
            fr=f"{CODE} ne porte aucun jeton : le setup n'a pas abouti",
        ))

    lance = _lancer(host, "%s", IMAGE)
    assert jetons[0] in lance.stdout, message(
        en=f"`{IMAGE}` does not print the token its source carries.\n"
           f"  printed: {lance.stdout.strip()[:160] or '(nothing)'}\n"
           "So the image does not carry the current code.",
        fr=f"`{IMAGE}` n'imprime pas le jeton que porte son source.\n"
           f"  imprimé : {lance.stdout.strip()[:160] or '(rien)'}\n"
           "L'image ne porte donc pas le code courant.",
    )
    assert "empreinte de fabrication :" in lance.stdout and len(
        lance.stdout.split("empreinte de fabrication :")[-1].strip()
    ) >= 16, message(
        en=f"`{IMAGE}` does not print a fabrication fingerprint.\n"
           f"  printed: {lance.stdout.strip()[:160] or '(nothing)'}\n"
           "So the fabrication did not run in this image: lightening an image "
           "by no longer producing anything is the fastest way, and it is not "
           "a solution.",
        fr=f"`{IMAGE}` n'imprime aucune empreinte de fabrication.\n"
           f"  imprimé : {lance.stdout.strip()[:160] or '(rien)'}\n"
           "La fabrication n'a donc pas eu lieu dans cette image : alléger une "
           "image en ne produisant plus rien est le plus rapide, et ce n'est "
           "pas une solution.",
    )

    manifeste = host.file(ATTENDUS)
    attendus = [
        a.strip() for a in manifeste.content_string.splitlines() if a.strip()
    ] if manifeste.exists else []
    assert attendus, message(
        en=f"{ATTENDUS} is empty or missing: the setup did not finish",
        fr=f"{ATTENDUS} est vide ou absent : le setup n'a pas abouti",
    )
    presents = _lancer(host, "--entrypoint ls %s %s", IMAGE, UTILE).stdout.split()
    manquants = [a for a in attendus if a not in presents]
    assert not manquants, message(
        en=f"`{IMAGE}` does not carry the expected artefacts: "
           f"{', '.join(manquants)}.\n"
           "They are what the application uses, and they stay. What has to go "
           "is the cache that only served to produce them.",
        fr=f"`{IMAGE}` ne porte pas les artefacts attendus : "
           f"{', '.join(manquants)}.\n"
           "Ce sont eux que l'application utilise, et ils restent. Ce qui doit "
           "partir, c'est le cache qui n'a servi qu'à les produire.",
    )


def test_aucune_couche_ne_porte_le_cache(host) -> None:
    """Le cœur du lab, et la mesure qui le rend visible.

    LE CONTENEUR NE MONTRE RIEN. Le cache n'est pas visible dans l'image
    assemblée, puisqu'une couche ultérieure le supprime. Il est pourtant là,
    dans une couche, et il est téléchargé avec elle.

    LA PESÉE COUCHE PAR COUCHE est donc la seule façon de le voir, et c'est la
    compétence du lab : mesuré le 2026-10-30, 44 Mo de couche pour un
    nettoyage joué une instruction trop tard, 6,3 Mo quand il est joué dans la
    même.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))

    # Le cache ne doit pas être visible non plus : s'il l'est, le nettoyage
    # n'a pas eu lieu du tout, et le message doit le dire avant de parler de
    # couches.
    visible = _lancer(host, "--entrypoint test %s -d %s", IMAGE, CACHE)
    assert visible.rc != 0, message(
        en=f"`{IMAGE}` still carries {CACHE}, visibly.\n"
           "It only served to produce the artefacts, and it has no reason to "
           "be shipped with the image.",
        fr=f"`{IMAGE}` porte encore {CACHE}, visiblement.\n"
           "Il n'a servi qu'à produire les artefacts, et il n'a aucune raison "
           "de partir avec l'image.",
    )

    utile = _volume_utile(host)
    assert utile > 0, message(
        en=f"the artefacts in {UTILE} could not be weighed inside the image.\n"
           "They are what the expected size is derived from.",
        fr=f"les artefacts de {UTILE} n'ont pas pu être pesés dans l'image.\n"
           "C'est d'eux que la taille attendue est déduite.",
    )
    plafond = int(utile * MARGE)
    tailles = _tailles_de_couche(host, IMAGE)
    assert tailles, message(
        en=f"the layers of `{IMAGE}` could not be weighed",
        fr=f"les couches de `{IMAGE}` n'ont pas pu être pesées",
    )
    trop_grosses = [t for t in tailles if t > plafond]

    # UNE IMAGE APLATIE FAIT ÉCHOUER CE CONTRÔLE AUSSI, puisque son unique
    # couche porte tout. Mesuré le 2026-10-30 : 14,6 Mo en une seule couche,
    # au-dessus du plafond. Le verdict est juste, mais le message ne doit pas
    # accuser le cache, qui n'y est pas : la cause est ailleurs, et un autre
    # contrôle la nomme.
    couches_socle = _couches(host, SOCLE)
    couches_image = _couches(host, IMAGE)
    aplatie = bool(couches_socle) and couches_image[: len(couches_socle)] != couches_socle
    if trop_grosses and aplatie:
        pytest.fail(message(
            en=f"`{IMAGE}` has {len(couches_image)} layer(s) and shares none "
               f"with its base: everything sits in one of them, which weighs "
               f"{max(tailles) // 10**6} MB.\n"
               "The cache is not what is being seen here: the image was "
               "flattened. The size is won in the instructions, and the next "
               "check says what flattening costs.",
            fr=f"`{IMAGE}` a {len(couches_image)} couche(s) et n'en partage "
               f"aucune avec son socle : tout est dans l'une d'elles, qui pèse "
               f"{max(tailles) // 10**6} Mo.\n"
               "Ce n'est pas le cache qu'on voit ici : l'image a été aplatie. "
               "La taille se gagne dans les instructions, et le contrôle "
               "suivant dit ce que l'aplatissement coûte.",
        ))

    assert not trop_grosses, message(
        en=f"one layer of `{IMAGE}` weighs {max(tailles) // 10**6} MB, for "
           f"{utile // 10**6} MB of useful artefacts.\n"
           "So that layer carries the cache: a layer keeps what a LATER layer "
           "deletes. Deleting it afterwards hides it from the container and "
           "changes nothing to the image, which ships that layer in full.\n"
           "The deletion has to happen in the very instruction that created "
           "the cache.",
        fr=f"une couche de `{IMAGE}` pèse {max(tailles) // 10**6} Mo, pour "
           f"{utile // 10**6} Mo d'artefacts utiles.\n"
           "Cette couche porte donc le cache : une couche garde ce qu'une "
           "couche ULTÉRIEURE supprime. Le supprimer après le cache du "
           "conteneur et ne change rien à l'image, qui emporte cette couche en "
           "entier.\n"
           "La suppression doit avoir lieu dans l'instruction même qui a créé "
           "le cache.",
    )


def test_la_taille_totale_reste_proche_du_necessaire(host) -> None:
    """La pesée d'ensemble, qui attrape ce qu'une couche seule laisserait passer.

    DEUX MESURES PLUTÔT QU'UNE, et elles ne disent pas la même chose. Une
    couche peut rester sous le plafond pendant que plusieurs, ensemble, pèsent
    le double du nécessaire : un cache écrit en deux fois, ou un second
    téléchargement, se répartit sans jamais faire une grosse couche.

    LE SEUIL EST CALCULÉ : le socle est pesé, les artefacts aussi, et la marge
    est la même que pour les couches.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))
    socle = _octets(host, SOCLE)
    if not socle:
        pytest.skip(message(
            en=f"the base `{SOCLE}` could not be weighed: the setup did not "
               "finish",
            fr=f"le socle `{SOCLE}` n'a pas pu être pesé : le setup n'a pas "
               "abouti",
        ))
    utile = _volume_utile(host)
    totale = _octets(host, IMAGE)
    plafond = socle + int(utile * MARGE)
    assert 0 < totale <= plafond, message(
        en=f"`{IMAGE}` weighs {totale // 10**6} MB, where the base "
           f"({socle // 10**6} MB) and the artefacts ({utile // 10**6} MB) "
           f"account for a ceiling of {plafond // 10**6} MB.\n"
           "The difference is being shipped on every pull, by everyone, for "
           "ever. It lives in a layer, and deleting it later does not take it "
           "out of that layer.",
        fr=f"`{IMAGE}` pèse {totale // 10**6} Mo, là où le socle "
           f"({socle // 10**6} Mo) et les artefacts ({utile // 10**6} Mo) "
           f"donnent un plafond de {plafond // 10**6} Mo.\n"
           "La différence part à chaque téléchargement, chez tout le monde, "
           "pour toujours. Elle vit dans une couche, et la supprimer plus tard "
           "ne la sort pas de cette couche.",
    )


def test_l_image_derive_toujours_du_socle(host) -> None:
    """La fausse bonne idée, et la raison pour laquelle elle est refusée.

    APLATIR L'IMAGE DONNE LA BONNE TAILLE. Mesuré le 2026-10-30 :
    `docker export | docker import` rend 14,6 Mo en UNE couche, exactement le
    poids de la bonne écriture. Les deux contrôles de pesée seraient verts.

    ET ELLE NE PARTAGE PLUS RIEN avec son socle. Les couches communes sont ce
    qui fait qu'un dépôt ne stocke le socle qu'une fois, et qu'un poste qui l'a
    déjà ne télécharge que la différence. Une image aplatie est stockée et
    transférée en entier, pour chaque variante : le gain affiché est rendu au
    centuple.

    LE CONTRÔLE COMPARE DONC LES COUCHES : celles du socle doivent être le
    PRÉFIXE de celles de l'image.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{IMAGE}` does not exist. Building it is part of the "
               "mission.",
            fr=f"l'image `{IMAGE}` n'existe pas. La construire fait partie de "
               "la mission.",
        ))
    couches_socle = _couches(host, SOCLE)
    if not couches_socle:
        pytest.skip(message(
            en=f"the layers of `{SOCLE}` could not be read: the setup did not "
               "finish",
            fr=f"les couches de `{SOCLE}` n'ont pas pu être lues : le setup "
               "n'a pas abouti",
        ))
    couches_image = _couches(host, IMAGE)
    assert couches_image[: len(couches_socle)] == couches_socle, message(
        en=f"`{IMAGE}` no longer shares any layer with its base `{SOCLE}`.\n"
           f"  base: {len(couches_socle)} layers, image: "
           f"{len(couches_image)} layers\n"
           "Flattening an image does give the right size, and it takes away "
           "what makes a registry store the base only once, and a host that "
           "already has it download only the difference. A flattened image is "
           "stored and transferred in full, for every variant.\n"
           "The size is won in the instructions, not after the fact.",
        fr=f"`{IMAGE}` ne partage plus aucune couche avec son socle "
           f"`{SOCLE}`.\n"
           f"  socle : {len(couches_socle)} couches, image : "
           f"{len(couches_image)} couches\n"
           "Aplatir une image donne bien la bonne taille, et retire ce qui "
           "fait qu'un dépôt ne stocke le socle qu'une fois, et qu'un poste "
           "qui l'a déjà ne télécharge que la différence. Une image aplatie "
           "est stockée et transférée en entier, pour chaque variante.\n"
           "La taille se gagne dans les instructions, pas après coup.",
    )
