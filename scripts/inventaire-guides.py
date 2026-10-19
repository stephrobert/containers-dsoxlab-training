#!/usr/bin/env python3
"""Inventaire des guides conteneurs du blog, avec leurs sections.

POURQUOI CE SCRIPT

Le brief exige qu'aucun lab ne soit créé sans savoir à quel guide il
correspond, et les guides sont concentrés : 1095 lignes de Swarm, 798 de
Compose. Un `doc_url` ancré sur une SECTION est donc la seule façon de jumeler
vingt labs à un guide sans que le lien cesse d'apprendre quelque chose.

Ce script sort, pour chaque guide du périmètre, son titre et ses sections de
niveau 2 avec l'ancre que l'astro slugifie. Le résultat alimente COVERAGE.md.

CE QU'IL N'EST PAS

Il ne décide pas du jumelage : il donne la matière pour le décider. Un humain
lit, et rapproche d'une compétence.
"""

from __future__ import annotations

import json
import os
import pathlib
import re

RACINE = pathlib.Path(
    os.environ.get(
        "BLOG_CONTENU",
        "/home/bob/Projets/test-astro-5/src/content/docs/docs/conteneurs",
    )
)

# Le périmètre, décidé par le brief : Docker, les images, la distribution, les
# outils qui servent une compétence, Compose et Swarm. Kubernetes, Incus et
# Podman sont exclus (§27 et §28).
PERIMETRE = (
    "moteurs-conteneurs/docker",
    "moteurs-conteneurs/containerd",
    "images-conteneurs",
    "registres",
    "outils",
    "orchestrateurs/docker-compose.mdx",
    "orchestrateurs/docker-swarm.mdx",
)

HORS = ("kubernetes", "incus", "podman", "helm", "castai", "k3s", "k3d", "kind", "minikube")


def slug(titre: str) -> str:
    """L'ancre qu'Astro Starlight fabrique d'un titre, règle de `github-slugger`.

    MESURÉ, PAS DÉDUIT. Une première version retirait les accents et
    remplaçait l'apostrophe par un tiret : elle tombait juste 26 fois sur 68.
    Confrontée aux ancres réellement publiées, la règle est tout autre :

        'Prérequis'                      -> 'prérequis'        accents GARDÉS
        "Initialisation d'un cluster"    -> '...dun-cluster'   apostrophe SUPPRIMÉE
        'Qu'est-ce que Docker Swarm ?'   -> 'quest-ce-...-swarm-'  le ? laisse un tiret
        'Exemple : workers uniquement'   -> 'exemple--workers-...'  le : laisse DEUX tirets
        'Préférences (soft placement)'   -> 'préférences-soft-placement'
        'Fichiers stack.yml vs ...'      -> 'fichiers-stackyml-vs-...'

    L'algorithme qui rend tout cela : minuscules, puis suppression de tout ce
    qui n'est ni lettre, ni chiffre, ni espace, ni tiret — la ponctuation part
    SANS laisser de séparateur, ce qui explique `dun` et le double tiret après
    un deux-points, qui était suivi d'un espace. Enfin, espaces en tirets.

    Écrire 70 `doc_url` sur l'ancienne règle aurait produit 70 liens qui
    tombent au milieu de la page, sans que rien ne le signale : `--check-urls`
    ne contrôle que le code HTTP de la page, pas l'ancre.
    """
    sans_balise = re.sub(r"`|\*\*|\*|\[|\]\([^)]*\)", "", titre)
    garde = "".join(
        c
        for c in sans_balise.lower()
        if c.isalnum() or c in " -"
    )
    # `lstrip` et non `strip` : un titre qui finit par « ? » ou « ! » laisse
    # un espace final, donc un TIRET final dans l'ancre. Cinq ancres sur 78
    # tombaient là-dessus, et c'est le dernier écart qui restait.
    return garde.lstrip().replace(" ", "-")


def entete(texte: str, cle: str) -> str:
    """Un champ du frontmatter, sans dépendre d'un parseur YAML tolérant."""
    motif = re.compile(rf'^{cle}:\s*["\']?(.+?)["\']?\s*$', re.MULTILINE)
    trouve = motif.search(texte.split("---", 2)[1] if texte.startswith("---") else texte)
    return trouve.group(1).strip() if trouve else ""


def sections(texte: str) -> list[tuple[str, str]]:
    """Les sections de niveau 2, en (titre, ancre). Les blocs de code sont écartés."""
    hors_code = re.sub(r"```.*?```", "", texte, flags=re.DOTALL)
    titres = re.findall(r"^##\s+(.+?)\s*$", hors_code, re.MULTILINE)
    return [(t, slug(t)) for t in titres]


def dans_le_perimetre(chemin: pathlib.Path) -> bool:
    relatif = str(chemin.relative_to(RACINE))
    if any(exclu in relatif for exclu in HORS):
        return False
    return any(relatif.startswith(p) or relatif == p for p in PERIMETRE)


guides = []
for fichier in sorted(RACINE.rglob("*.mdx")):
    if not dans_le_perimetre(fichier):
        continue
    texte = fichier.read_text(encoding="utf-8")
    relatif = str(fichier.relative_to(RACINE))
    guides.append(
        {
            "fichier": relatif,
            "url": "https://www.stephane-robert.info/docs/conteneurs/"
            + relatif.removesuffix(".mdx").removesuffix("/index")
            + "/",
            "titre": entete(texte, "title"),
            "lignes": len(texte.splitlines()),
            "sections": sections(texte),
        }
    )

# Le blog vit à côté, pas dans ce dépôt : son chemin se surcharge par
# l'environnement pour qui l'a cloné ailleurs.
sortie = pathlib.Path(
    os.environ.get("INVENTAIRE_SORTIE", pathlib.Path(__file__).resolve().parent.parent / "guides.json")
)
sortie.write_text(json.dumps(guides, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"{len(guides)} guides dans le périmètre, "
      f"{sum(len(g['sections']) for g in guides)} sections au total\n")
for g in guides:
    print(f"{g['lignes']:>5}  {g['fichier']:<52} {len(g['sections']):>3} sections")
