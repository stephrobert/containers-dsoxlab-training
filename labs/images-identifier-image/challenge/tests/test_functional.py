"""Tests fonctionnels du lab images-identifier-image : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Le contrat `conteneurs-11` du pilotage demande
d'« identifier exactement l'image exécutée et sa plateforme », avec trois
points : le résultat, un CAS NÉGATIF représentatif qu'une correction de surface
ne doit pas suffire à passer, et une explication qui relève d'une revue humaine.
Les deux premiers se mesurent ici ; le troisième ne se teste pas et reste hors
de ce fichier, comme le contrat le prévoit.

CE QU'ON NE MESURE PAS, ET POURQUOI. On ne vérifie jamais QUELLE commande
l'apprenant a tapée. `docker inspect`, `skopeo inspect`, une lecture du
répertoire de `containerd` : tous ces chemins mènent au même état, et un lab
qui noterait la commande noterait un style, pas une compétence. On lit donc
`/opt/lab-images/reponse.txt`, et on confronte CE QU'IL AFFIRME à ce que la
machine porte réellement.

LE PIÈGE EST CONSTRUIT, PAS SUPPOSÉ. Le setup construit deux images
différentes sous le même tag `inventaire:1.0`. Un apprenant qui recopie le
digest de la PREMIÈRE construction, encore visible dans l'historique du
terminal ou dans `digest-v1.txt`, est refusé par le test du cas négatif : c'est
la réponse de surface que le contrat demande explicitement de rejeter.

POURQUOI CHAQUE MESSAGE PASSE PAR `message()`. Ce que ce fichier affiche quand
un contrôle refuse est la seule consigne que l'apprenant reçoit à cet instant :
c'est de l'interface, et le catalogue existe dans deux langues. Le contrat
dsoxlab imposant un nom de fichier unique, il n'y a pas de version anglaise
possible par duplication, d'où le helper du `conftest.py`, qui choisit sur
`DSOXLAB_LANG`. `tests/test_assertions_bilingues.py` tient la règle.
"""

from __future__ import annotations

import json
import re

import pytest

from conftest import lab_host, message

REPONSE = "/opt/lab-images/reponse.txt"
TAG = "inventaire:1.0"

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tournaient alors sur la machine de celui
    qui les lance, ce que `pytest --collect-only` affichait en clair avec le
    paramètre `[local]`. Un lab qui noterait le poste au lieu de sa VM rendrait
    un verdict sur le mauvais système, et pourrait le modifier.
    """
    return lab_host(TARGET_HOST)


def _lire_reponse(host) -> dict[str, str]:
    """Le fichier de réponse, réduit à ses paires clé=valeur.

    Tolérant sur la forme (espaces, lignes vides, commentaires), strict sur le
    fond : c'est le contenu qui est noté, pas la mise en page.
    """
    f = host.file(REPONSE)
    if not f.exists:
        pytest.fail(message(
            en=f"{REPONSE} is missing. The mission asks for three lines in it: "
               "digest=, base= and plateforme=.",
            fr=f"{REPONSE} est absent. La mission demande d'y écrire trois lignes : "
               "digest=, base= et plateforme=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def _digest_reel(host, reference: str) -> str:
    """Le digest que la machine donne à une image, lu par le démon lui-même."""
    res = host.run("docker image inspect %s --format '{{json .Id}}'", reference)
    if res.rc != 0:
        pytest.fail(message(
            en=f"image {reference} cannot be found on the machine: {res.stderr.strip()}",
            fr=f"l'image {reference} est introuvable sur la machine : {res.stderr.strip()}",
        ))
    return json.loads(res.stdout.strip()).strip()


def test_la_reponse_nomme_le_digest_reel_du_tag(host) -> None:
    """Le digest annoncé est celui que le tag désigne MAINTENANT.

    C'est le contrôle central : le tag `inventaire:1.0` a été réécrit, et seule
    la seconde image compte. Un digest correct prouve que l'apprenant a
    interrogé l'image, pas sa propre mémoire.
    """
    paires = _lire_reponse(host)
    annonce = paires.get("digest", "")
    assert annonce, message(
        en=f"the `digest=` line is missing from the answer. It is the identity of "
           f"the image that {TAG} points at today.",
        fr=f"la ligne `digest=` manque dans la réponse. C'est l'identité de l'image "
           f"que {TAG} désigne aujourd'hui.",
    )
    reel = _digest_reel(host, TAG)
    assert annonce == reel, message(
        en=f"the digest you state is not the image {TAG} points at.\n"
           f"  stated : {annonce}\n"
           f"  actual : {reel}\n"
           "The tag was built twice: it no longer points at the first image.",
        fr=f"le digest annoncé ne correspond pas à l'image que {TAG} désigne.\n"
           f"  annoncé : {annonce}\n"
           f"  réel    : {reel}\n"
           "Le tag a été construit deux fois : il ne pointe plus la première image.",
    )


def test_le_digest_de_la_premiere_construction_est_refuse(host) -> None:
    """Le cas négatif exigé par le contrat.

    La première image existe encore dans le cache, et son digest traîne dans
    `digest-v1.txt`. Le recopier est la correction de surface typique : elle
    ressemble à une réponse et ne prouve rien.
    """
    paires = _lire_reponse(host)
    annonce = paires.get("digest", "")
    v1 = host.file("/opt/lab-images/digest-v1.txt")
    if not v1.exists:
        pytest.skip(message(
            en="digest-v1.txt is missing: the setup did not lay the negative case",
            fr="digest-v1.txt absent : le setup n'a pas posé le cas négatif",
        ))
    ancien = v1.content_string.strip()
    assert annonce != ancien, message(
        en="the digest you state is the FIRST build's, the one the tag no longer "
           "points at. That is the trace the setup left behind, not a measurement "
           "of the image in place.",
        fr="le digest annoncé est celui de la PREMIÈRE construction, celle que le "
           "tag ne désigne plus. C'est la trace laissée par le setup, pas une "
           "mesure de l'image en place.",
    )


def test_la_reponse_nomme_le_digest_de_l_image_de_base(host) -> None:
    """L'identité remonte la chaîne : une image hérite de celle dont elle part.

    `debian:13` est le socle imposé par le scénario. Savoir lire SON digest,
    distinct de celui de l'image construite, est ce qui distingue « je connais
    mon image » de « je connais ma commande ».
    """
    paires = _lire_reponse(host)
    annonce = paires.get("base", "")
    assert annonce, message(
        en="the `base=` line is missing: it is the digest of the local debian:13 image.",
        fr="la ligne `base=` manque : c'est le digest de l'image debian:13 locale.",
    )
    reel = _digest_reel(host, "debian:13")
    assert annonce == reel, message(
        en=f"the base digest you state is not debian:13 on this machine.\n"
           f"  stated : {annonce}\n  actual : {reel}",
        fr=f"le digest de base annoncé ne correspond pas à debian:13 sur cette machine.\n"
           f"  annoncé : {annonce}\n  réel    : {reel}",
    )
    construite = _digest_reel(host, TAG)
    assert annonce != construite, message(
        en="the base digest you state is the built image's. An image and the one "
           "it was built from have two distinct identities.",
        fr="le digest de base annoncé est celui de l'image construite. Une image "
           "et son socle ont deux identités distinctes.",
    )


def test_la_plateforme_annoncee_est_celle_de_l_image(host) -> None:
    """La plateforme fait partie de l'identité, et elle ne se devine pas.

    Une même référence peut servir plusieurs plateformes. On vérifie la forme
    `os/architecture` ET sa valeur, telle que le démon la rapporte.
    """
    paires = _lire_reponse(host)
    annonce = paires.get("plateforme", "").lower()
    assert annonce, message(
        en="the `plateforme=` line is missing: it reads `os/architecture`.",
        fr="la ligne `plateforme=` manque : elle s'écrit `os/architecture`.",
    )
    assert re.fullmatch(r"[a-z0-9]+/[a-z0-9]+", annonce), message(
        en=f"`{annonce}` does not have the expected `os/architecture` form, "
           "for instance `linux/amd64`.",
        fr=f"`{annonce}` n'a pas la forme attendue `os/architecture`, "
           "par exemple `linux/amd64`.",
    )
    res = host.run(
        "docker image inspect %s --format '{{.Os}}/{{.Architecture}}'", TAG
    )
    assert res.rc == 0, message(
        en=f"cannot read the platform of {TAG}: {res.stderr.strip()}",
        fr=f"impossible de lire la plateforme de {TAG} : {res.stderr.strip()}",
    )
    reel = res.stdout.strip().lower()
    assert annonce == reel, message(
        en=f"the platform you state ({annonce}) is not the image's ({reel}).",
        fr=f"la plateforme annoncée ({annonce}) n'est pas celle de l'image ({reel}).",
    )
