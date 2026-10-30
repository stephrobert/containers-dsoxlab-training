"""Tests fonctionnels du lab images-migrer-vers-alpine : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que changer de socle n'est pas changer une ligne : une
application dépend de ce que son socle lui donne, et le message qui le lui
rappelle ne nomme pas la cause.

MESURÉ SUR docker.lab LE 2026-10-30 :

| Socle | Taille |
| `debian:13-slim` | 78,9 Mo |
| `alpine:3.22` | 8,3 Mo, soit 9,5 fois moins |

Le MÊME script en entrypoint sur Alpine rend « exec /src/traiter.sh: no such
file or directory » ; lancé par `sh`, « not found », code **127**. Et le
fichier est là, exécutable, 205 octets.

LE MESSAGE NOMME LE SCRIPT, et ce n'est pas lui qui manque : c'est
l'interpréteur de son shebang. Même code que `troubleshoot-exit-127`, même
famille de message trompeur que `images-contexte-de-build`.

L'ÉQUIVALENT POSIX REND LE MÊME RÉSULTAT sur les deux socles, mesuré :
`somme=26 max=11` de part et d'autre.

LES QUATRE CONTRÔLES NE SE RECOUVRENT PAS. Le premier éprouve le résultat sur
les données du dépôt, le deuxième la base réellement utilisée, le troisième le
poids, et le quatrième donne à l'image des données QU'ELLE N'A JAMAIS VUES :
une application qui réciterait un résultat figé passerait les trois premiers.

AUCUNE VALEUR N'EST ÉCRITE EN DUR. Les données sont tirées par le setup, le
résultat est recalculé ici, et le seuil de taille est dérivé de l'image de
référence.
"""

from __future__ import annotations

import contextlib

import pytest

from conftest import lab_host, message

LEGERE = "appli:legere"
LOURDE = "appli:lourde"
SOCLE_LEGER = "lab-socle-leger:1.0"
ATELIER = "/opt/lab-migration"
CONTEXTE = f"{ATELIER}/appli"
DONNEES = f"{CONTEXTE}/donnees/valeurs.txt"
CODE = f"{CONTEXTE}/src/traiter.sh"
ESSAI = "dsoxlab-essai-migration"

# LA FRACTION ATTENDUE. Mesuré le 2026-10-30, le socle léger pèse 8,3 Mo contre
# 78,9 pour le lourd, soit 9,5 fois moins : exiger le tiers laisse une marge
# très large tout en refusant sans appel une image restée sur le socle lourd.
FRACTION = 3.0

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


def _image_absente(host, nom: str = LEGERE) -> bool:
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


def _valeurs(host) -> list[int]:
    f = host.file(DONNEES)
    if not f.exists:
        return []
    valeurs = []
    for ligne in f.content_string.split():
        with contextlib.suppress(ValueError):
            valeurs.append(int(ligne))
    return valeurs


def _jeton(host) -> str:
    f = host.file(CODE)
    if not f.exists:
        return ""
    for mot in f.content_string.split():
        if mot.startswith("jeton-"):
            return mot
    return ""


def _resultat(sortie: str) -> dict[str, str]:
    """Les paires clé=valeur de la sortie de l'application."""
    paires = {}
    for ligne in sortie.splitlines():
        if "=" in ligne:
            cle, _, valeur = ligne.partition("=")
            paires[cle.strip()] = valeur.strip()
    return paires


def test_l_image_legere_rend_le_bon_resultat(host) -> None:
    """L'image migrée imprime le jeton, la somme et le maximum attendus.

    LE RÉSULTAT EST RECALCULÉ ICI depuis les données du dépôt, et les données
    sont tirées par le setup à chaque passage : rien n'est écrit en dur, et
    comparer à l'image de référence ne suffirait pas, puisqu'elle pourrait être
    fausse elle aussi.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{LEGERE}` does not exist. Building it on the light "
               f"base is the mission: the context is in {CONTEXTE}.",
            fr=f"l'image `{LEGERE}` n'existe pas. La construire sur le socle "
               f"léger est la mission : le contexte est dans {CONTEXTE}.",
        ))

    valeurs = _valeurs(host)
    jeton = _jeton(host)
    if not valeurs or not jeton:
        pytest.skip(message(
            en="the data or the token is missing from the repository: the "
               "setup did not finish",
            fr="les données ou le jeton manquent dans le dépôt : le setup n'a "
               "pas abouti",
        ))

    lance = _lancer(host, "%s", LEGERE)
    assert lance.rc == 0, message(
        en=f"`{LEGERE}` does not run (code {lance.rc}).\n"
           f"  {(lance.stderr or lance.stdout).strip()[:300]}\n"
           "If the message names the script and says it cannot be found, go "
           "and check: it is there. What is missing is the interpreter of its "
           "shebang, which the previous base provided.",
        fr=f"`{LEGERE}` ne tourne pas (code {lance.rc}).\n"
           f"  {(lance.stderr or lance.stdout).strip()[:300]}\n"
           "Si le message nomme le script et dit qu'il est introuvable, allez "
           "vérifier : il est là. Ce qui manque est l'interpréteur de son "
           "shebang, que le socle précédent fournissait.",
    )
    assert jeton in lance.stdout, message(
        en=f"`{LEGERE}` does not print the token its source carries.\n"
           f"  printed: {lance.stdout.strip()[:160] or '(nothing)'}",
        fr=f"`{LEGERE}` n'imprime pas le jeton que porte son source.\n"
           f"  imprimé : {lance.stdout.strip()[:160] or '(rien)'}",
    )
    obtenu = _resultat(lance.stdout)
    attendu = {"somme": str(sum(valeurs)), "max": str(max(valeurs))}
    assert obtenu.get("somme") == attendu["somme"] and obtenu.get("max") == attendu["max"], message(
        en=f"`{LEGERE}` does not give the expected result.\n"
           f"  expected: somme={attendu['somme']} max={attendu['max']}\n"
           f"  obtained: somme={obtenu.get('somme', '(absent)')} "
           f"max={obtenu.get('max', '(absent)')}\n"
           "The data is in the repository, and the values are drawn on every "
           "pass. Migrating means keeping the result, not only getting the "
           "container to start.",
        fr=f"`{LEGERE}` ne rend pas le résultat attendu.\n"
           f"  attendu : somme={attendu['somme']} max={attendu['max']}\n"
           f"  obtenu : somme={obtenu.get('somme', '(absent)')} "
           f"max={obtenu.get('max', '(absent)')}\n"
           "Les données sont dans le dépôt, et les valeurs sont tirées à "
           "chaque passage. Migrer, c'est garder le résultat, pas seulement "
           "faire démarrer le conteneur.",
    )


def test_l_image_legere_est_bien_construite_sur_le_socle_leger(host) -> None:
    """La base a réellement changé, et ce n'est pas l'ancienne renommée.

    LE CONTRÔLE COMPARE LES COUCHES, et non un fichier de version : les couches
    du socle léger doivent être le PRÉFIXE de celles de l'image. C'est la
    mesure la plus directe de « construite sur ce socle », et elle ne dépend
    d'aucune convention de distribution.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{LEGERE}` does not exist. Building it on the light "
               "base is the mission.",
            fr=f"l'image `{LEGERE}` n'existe pas. La construire sur le socle "
               "léger est la mission.",
        ))
    couches_socle = _couches(host, SOCLE_LEGER)
    if not couches_socle:
        pytest.skip(message(
            en=f"the layers of `{SOCLE_LEGER}` could not be read: the setup "
               "did not finish",
            fr=f"les couches de `{SOCLE_LEGER}` n'ont pas pu être lues : le "
               "setup n'a pas abouti",
        ))
    couches_image = _couches(host, LEGERE)
    assert couches_image[: len(couches_socle)] == couches_socle, message(
        en=f"`{LEGERE}` is not built on `{SOCLE_LEGER}`.\n"
           f"  base: {len(couches_socle)} layers, image: "
           f"{len(couches_image)} layers, none in common\n"
           "The image may well work and weigh the right amount: the mission is "
           "to migrate the base, and that is read in the layers.",
        fr=f"`{LEGERE}` n'est pas construite sur `{SOCLE_LEGER}`.\n"
           f"  socle : {len(couches_socle)} couches, image : "
           f"{len(couches_image)} couches, aucune en commun\n"
           "L'image peut très bien marcher et peser le bon poids : la mission "
           "est de migrer le socle, et cela se lit dans les couches.",
    )


def test_l_image_legere_pese_une_fraction_de_la_lourde(host) -> None:
    """Le gain, mesuré contre la référence et non contre un chiffre écrit.

    LE SEUIL EST DÉRIVÉ de l'image de départ, que le setup construit. Une
    valeur en dur serait fausse au premier changement de socle, et le lab
    refuserait alors un travail correct.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{LEGERE}` does not exist. Building it on the light "
               "base is the mission.",
            fr=f"l'image `{LEGERE}` n'existe pas. La construire sur le socle "
               "léger est la mission.",
        ))
    lourde = _octets(host, LOURDE)
    if not lourde:
        pytest.skip(message(
            en=f"the reference image `{LOURDE}` could not be weighed: the "
               "setup did not finish",
            fr=f"l'image de référence `{LOURDE}` n'a pas pu être pesée : le "
               "setup n'a pas abouti",
        ))
    legere = _octets(host, LEGERE)
    plafond = int(lourde / FRACTION)
    assert 0 < legere <= plafond, message(
        en=f"`{LEGERE}` weighs {legere // 10**6} MB, where `{LOURDE}` weighs "
           f"{lourde // 10**6} MB: a third of it is {plafond // 10**6} MB.\n"
           "The light base weighs 8 MB against 79, measured on this machine. "
           "An image that stays this heavy has not changed base, or carries "
           "along what the base already provides.",
        fr=f"`{LEGERE}` pèse {legere // 10**6} Mo, là où `{LOURDE}` pèse "
           f"{lourde // 10**6} Mo : le tiers fait {plafond // 10**6} Mo.\n"
           "Le socle léger pèse 8 Mo contre 79, mesuré sur cette machine. Une "
           "image qui reste aussi lourde n'a pas changé de socle, ou emporte "
           "avec elle ce que le socle fournit déjà.",
    )


def test_l_image_legere_calcule_et_ne_recite_pas(host) -> None:
    """Des données qu'elle n'a jamais vues, et le résultat attendu.

    LES TROIS PREMIERS CONTRÔLES PASSERAIENT sur une application qui imprime un
    résultat figé : les données du dépôt ne changent pas pendant une session.
    Celui-ci lui en donne d'autres, par un montage, et recalcule ce qu'elle doit
    rendre.

    LE MONTAGE PLUTÔT QU'UNE RECONSTRUCTION : on éprouve l'image telle qu'elle
    est, sans toucher au contexte de l'apprenant ni reconstruire quoi que ce
    soit. Le lab impose d'ailleurs que les données vivent dans `/donnees`, et
    l'image de départ les y range déjà.
    """
    if _image_absente(host):
        pytest.fail(message(
            en=f"image `{LEGERE}` does not exist. Building it on the light "
               "base is the mission.",
            fr=f"l'image `{LEGERE}` n'existe pas. La construire sur le socle "
               "léger est la mission.",
        ))

    autres = [13, 41, 7, 29, 2]
    bac = host.run("mktemp -d").stdout.strip()
    assert bac, message(
        en="no temporary directory could be created on the machine",
        fr="aucun répertoire temporaire n'a pu être créé sur la machine",
    )
    host.run(
        "sh -c %s",
        f"printf '%s\\n' {' '.join(str(v) for v in autres)} > {bac}/valeurs.txt",
    )
    lance = _lancer(host, "-v %s:/donnees:ro %s", bac, LEGERE)
    host.run("rm -rf %s", bac)

    obtenu = _resultat(lance.stdout)
    attendu = {"somme": str(sum(autres)), "max": str(max(autres))}
    assert obtenu.get("somme") == attendu["somme"] and obtenu.get("max") == attendu["max"], message(
        en=f"given data it has never seen, `{LEGERE}` does not give the right "
           "result.\n"
           f"  data: {' '.join(str(v) for v in autres)}\n"
           f"  expected: somme={attendu['somme']} max={attendu['max']}\n"
           f"  obtained: somme={obtenu.get('somme', '(absent)')} "
           f"max={obtenu.get('max', '(absent)')}\n"
           f"  {(lance.stderr or '').strip()[:200]}\n"
           "So it does not read /donnees/valeurs.txt any more, or it prints a "
           "frozen result. The three other checks would pass on such an image: "
           "this one is why they are not enough.",
        fr=f"sur des données qu'elle n'a jamais vues, `{LEGERE}` ne rend pas "
           "le bon résultat.\n"
           f"  données : {' '.join(str(v) for v in autres)}\n"
           f"  attendu : somme={attendu['somme']} max={attendu['max']}\n"
           f"  obtenu : somme={obtenu.get('somme', '(absent)')} "
           f"max={obtenu.get('max', '(absent)')}\n"
           f"  {(lance.stderr or '').strip()[:200]}\n"
           "Elle ne lit donc plus /donnees/valeurs.txt, ou elle imprime un "
           "résultat figé. Les trois autres contrôles passeraient sur une "
           "telle image : celui-ci est la raison pour laquelle ils ne "
           "suffisent pas.",
    )


def _couches(host, nom: str) -> list[str]:
    """Les couches d'une image, dans l'ordre.

    LE FORMAT PASSE PAR UN PARAMÈTRE, ET C'EST OBLIGATOIRE : il contient des
    espaces, et une commande qui le porterait en clair serait découpée par le
    shell. Mesuré dans un lab voisin, docker recevait alors un format tronqué
    et rendait une sortie vide, ce qui faisait SAUTER le contrôle au lieu de le
    jouer.
    """
    res = host.run(
        "docker image inspect %s --format %s",
        nom,
        "{{range .RootFS.Layers}}{{println .}}{{end}}",
    )
    return [c.strip() for c in res.stdout.splitlines() if c.strip()]
