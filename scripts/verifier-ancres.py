#!/usr/bin/env python3
"""Chaque `doc_url` ancré pointe-t-il une section qui EXISTE ?

## Pourquoi ce contrôle existe

`dsoxlab validate-structure --check-urls` vérifie le code HTTP de la page, pas
le fragment. Une ancre fausse donne donc un lien qui répond 200 et dépose le
lecteur en haut d'un guide de mille lignes, sans que rien ne le signale.

Ce catalogue ancre ses `doc_url` par nécessité : le guide Swarm porte 20
sections pour 18 labs, celui de Compose 15 pour 11. Sans ancre, vingt labs
pointeraient la même URL et le champ n'apprendrait plus rien. Avec, il faut ce
contrôle.

## Ce qu'il a trouvé la première fois

Écrit le 2026-10-01 pour vérifier le backlog, il a montré que les ancres
rédigées de mémoire étaient majoritairement fausses, alors que celles produites
par l'inventaire du blog étaient justes. C'est la différence entre lire une
source et se souvenir d'elle.

## Ce qu'il lit

Les `doc_url` des `lab.yaml`, et les ancres citées dans `ROADMAP.md`, qui est
le backlog : un lab pas encore écrit a déjà son jumelage, et autant le savoir
faux avant de l'écrire.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
LABS = RACINE / "labs"
ROADMAP = RACINE / "ROADMAP.md"
PREFIXE = "https://www.stephane-robert.info/docs/conteneurs/"

# Le site refuse l'agent par défaut de Python : mesuré le 2026-10-01, il rend
# 404 sur une page qui répond 200 à curl. Sans cet en-tête, le contrôle
# accuserait toutes les pages.
AGENT = "Mozilla/5.0 (verifier-ancres; catalogue dsoxlab)"

_pages: dict[str, set[str] | None] = {}


def ancres(url_page: str) -> set[str] | None:
    """Les ancres de titres réellement publiées. `None` si la page ne répond pas."""
    if url_page in _pages:
        return _pages[url_page]
    requete = urllib.request.Request(url_page, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            html = reponse.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        _pages[url_page] = None
        return None
    _pages[url_page] = set(re.findall(r'<h[1-6][^>]*\sid="([^"]+)"', html))
    return _pages[url_page]


def depuis_les_labs() -> list[tuple[str, str]]:
    """(origine, url) de chaque `doc_url` déclaré par un lab."""
    trouves = []
    for contrat in sorted(LABS.rglob("lab.yaml")):
        donnees = yaml.safe_load(contrat.read_text(encoding="utf-8")) or {}
        url = donnees.get("doc_url")
        if url:
            trouves.append((f"lab {donnees.get('id', contrat.parent.name)}", url))
    return trouves


def depuis_le_backlog() -> list[tuple[str, str]]:
    """(origine, url) de chaque ancre citée dans ROADMAP.md.

    Le backlog écrit ses URL sans le préfixe commun, pour rester lisible : on
    le remet. Une ligne de tableau porte l'identifiant du lab en première
    colonne, ce qui permet de nommer le coupable.
    """
    if not ROADMAP.is_file():
        return []
    trouves = []
    for ligne in ROADMAP.read_text(encoding="utf-8").splitlines():
        if "#" not in ligne or "`" not in ligne:
            continue
        identifiant = ""
        premiere = re.match(r"\|\s*\*{0,2}`([^`]+)`", ligne)
        if premiere:
            identifiant = premiere.group(1)
        for chemin in re.findall(r"`([a-z0-9][^`\s]*/#[^`\s]+)`", ligne):
            trouves.append((f"backlog {identifiant or '?'}", PREFIXE + chemin))
    return trouves


def controler(cibles: list[tuple[str, str]]) -> int:
    justes = fausses = injoignables = sans_ancre = 0
    for origine, url in cibles:
        page, _, fragment = url.partition("#")
        if not fragment:
            sans_ancre += 1
            continue
        publiees = ancres(page)
        if publiees is None:
            print(f"  INJOIGNABLE  {origine:<34} {page}")
            injoignables += 1
            continue
        if fragment in publiees:
            justes += 1
            continue
        fausses += 1
        proches = [a for a in sorted(publiees) if fragment[:12] in a or a[:12] in fragment]
        print(f"  FAUSSE       {origine:<34} #{fragment}")
        if proches:
            print(f"               peut-être : {', '.join('#' + p for p in proches[:3])}")

    print(
        f"\n{justes} ancre(s) juste(s), {fausses} fausse(s), "
        f"{injoignables} page(s) injoignable(s), {sans_ancre} doc_url sans ancre"
    )
    return 1 if (fausses or injoignables) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labs", action="store_true", help="ne contrôler que les lab.yaml")
    ap.add_argument("--backlog", action="store_true", help="ne contrôler que ROADMAP.md")
    args = ap.parse_args()

    cibles: list[tuple[str, str]] = []
    if not args.backlog:
        cibles += depuis_les_labs()
    if not args.labs:
        cibles += depuis_le_backlog()

    if not cibles:
        print("rien à contrôler", file=sys.stderr)
        return 1
    print(f"{len(cibles)} doc_url à contrôler\n")
    return controler(cibles)


if __name__ == "__main__":
    sys.exit(main())
