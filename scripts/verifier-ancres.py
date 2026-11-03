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

## Ce qu'il ne peut PAS juger, et qu'il ne faut pas lui demander

Il interroge la **production**. Or la vérité d'un `doc_url` est dans la
**source** du site, à laquelle la CI de ce dépôt n'a pas accès. Une ancre peut
donc être signalée fausse ici alors qu'elle est juste, simplement pas encore
servie, et le même déploiement ressuscite une ancre morte en tuant une ancre
vivante. **Avant de corriger un `doc_url` sur la foi de ce contrôle, le
confronter à la source** : le 2026-11-03, deux liens justes ont failli être
cassés ainsi.

## Trois issues, et une liste d'attente

Mesure du 2026-11-03, croisée lien par lien avec la source de `origin/main` du
site, sur les 91 `doc_url` des labs : 41 verts, 50 rouges, dont 44 **justes à la
source** et 6 visant des pages en brouillon. Soit **zéro dette réelle du
catalogue sur 50 rouges**, et pourtant la CI rouge en permanence, les PR
fusionnées par-dessus. Un contrôle qu'on fusionne par-dessus ne contrôle plus
rien. D'où :

- une **page injoignable** ne conclut plus au rouge : c'est `unknown` au sens de
  `dsoxlab doctor`, affiché, et `--strict` lui rend son propre code (`10`) ;
- une **ancre juste à la source mais pas déployée** se déclare dans
  `scripts/ancres-en-attente.yml`, nommée, datée et motivée.

Le garde-fou de la seconde est ce qui l'empêche de devenir un dépotoir : le
contrôle **échoue** sur une entrée qui n'a plus d'objet, soit parce que l'ancre
résout désormais, soit parce qu'aucun `doc_url` ne la porte plus.
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
EN_ATTENTE = RACINE / "scripts" / "ancres-en-attente.yml"
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


def attentes() -> dict[tuple[str, str], dict[str, str]]:
    """Les ancres declarees justes a la source, mais pas encore deployees.

    Clé : `(identifiant du lab, ancre)`. Le fichier absent n'est pas une faute,
    c'est l'état d'un catalogue dont toutes les leçons sont déployées.
    """
    if not EN_ATTENTE.is_file():
        return {}
    donnees = yaml.safe_load(EN_ATTENTE.read_text(encoding="utf-8")) or {}
    listees = {}
    for entree in donnees.get("ancres") or []:
        lab = str(entree.get("lab") or "").strip()
        ancre_attendue = str(entree.get("ancre") or "").strip()
        if lab and ancre_attendue:
            listees[(lab, ancre_attendue)] = entree
    return listees


def controler(cibles: list[tuple[str, str]], strict: bool = False) -> int:
    """Le verdict, en TROIS issues et non deux.

    Une page qui ne répond pas n'est pas une ancre fausse : c'est une sonde qui
    n'a pas abouti. Les deux appellent des gestes opposés, et les confondre a un
    coût mesuré. Le 2026-11-03, sur les 91 `doc_url` des labs : 41 verts,
    50 rouges, dont **44 justes à la source** de `origin/main` du site et 6
    visant des pages en brouillon. Soit **zéro dette réelle du catalogue sur
    50 rouges** : ce contrôle mesurait l'écart de déploiement du site, pas le
    catalogue. Il était rouge sur `main` en permanence, et les PR étaient
    fusionnées par-dessus. Un contrôle qu'on fusionne par-dessus ne contrôle
    plus rien.

    D'où les trois issues, calquées sur celles de `dsoxlab doctor` :

        juste         la page répond, et l'ancre y est
        FAUSSE        la page répond, et l'ancre n'y est pas : une vraie dette
        INJOIGNABLE   la page ne répond pas : on ne sait pas, et on le dit

    `INJOIGNABLE` reste **affiché**, parce qu'un contrôle qui tait ce qu'il
    ignore est pire qu'absent, mais il ne peint plus en rouge ce qu'il ne peut
    pas juger. Il garde son propre code de sortie sous `--strict` (`10`),
    distinct de l'échec réel (`1`) : une construction automatisée ne peut rien
    conclure d'une mesure qui n'a pas eu lieu, et les deux codes se réparent
    autrement. Le premier se corrige, le second se remesure après déploiement.

    **Ce que ce contrôle ne peut pas faire, et qu'il ne faut pas lui demander.**
    La vérité d'un `doc_url` est dans la SOURCE du site, à laquelle la CI de ce
    dépôt n'a pas accès : elle ne voit que ce qui est déjà déployé. Une ancre
    peut donc être signalée fausse ici alors qu'elle est juste à la source, et
    le même déploiement ressuscite une ancre morte et tue une ancre vivante.
    Avant de corriger un `doc_url` sur la foi de ce contrôle, le confronter à
    la source : le 2026-11-03, deux liens justes ont failli être cassés ainsi.
    """
    listees = attentes()
    vues: set[tuple[str, str]] = set()
    a_retirer: list[tuple[str, str]] = []
    justes = fausses = injoignables = sans_ancre = en_attente = 0
    for origine, url in cibles:
        page, _, fragment = url.partition("#")
        if not fragment:
            sans_ancre += 1
            continue
        identifiant = origine.split(" ", 1)[-1] if " " in origine else origine
        cle = (identifiant, fragment)
        if cle in listees:
            vues.add(cle)
        publiees = ancres(page)
        if publiees is None:
            print(f"  INJOIGNABLE  {origine:<34} {page}")
            injoignables += 1
            continue
        if fragment in publiees:
            justes += 1
            # L'ancre resout : une tolerance encore declaree n'a plus d'objet.
            if cle in listees:
                a_retirer.append(cle)
            continue
        if cle in listees:
            depuis = str(listees[cle].get("depuis") or "?")
            print(f"  EN ATTENTE   {origine:<34} #{fragment}  (déclarée le {depuis})")
            en_attente += 1
            continue
        fausses += 1
        proches = [a for a in sorted(publiees) if fragment[:12] in a or a[:12] in fragment]
        print(f"  FAUSSE       {origine:<34} #{fragment}")
        if proches:
            print(f"               peut-être : {', '.join('#' + p for p in proches[:3])}")

    mortes = sorted(set(listees) - vues)

    print(
        f"\n{justes} ancre(s) juste(s), {fausses} fausse(s), "
        f"{injoignables} page(s) injoignable(s), {en_attente} en attente, "
        f"{sans_ancre} doc_url sans ancre"
    )
    if injoignables:
        print(
            f"\nLes {injoignables} page(s) injoignable(s) ne comptent pas dans le "
            "verdict : une\nsonde qui n'a pas abouti ne conclut pas. Ce sont presque "
            "toujours des leçons\npas encore déployées. `--strict` les rend "
            "bloquantes, en code 10."
        )

    # UNE TOLERANCE QUI N A PLUS D OBJET EST UNE FAUTE, pas un oubli silencieux :
    # c est ce qui empeche `ancres-en-attente.yml` de devenir un depotoir.
    if a_retirer:
        print(f"\n{len(a_retirer)} ancre(s) en attente résolvent désormais en "
              "production.\nRetirer leur entrée de scripts/ancres-en-attente.yml :")
        for lab, frag in sorted(a_retirer):
            print(f"  - lab: {lab}  ancre: {frag}")
    if mortes:
        print(f"\n{len(mortes)} entrée(s) de scripts/ancres-en-attente.yml ne "
              "correspondent plus à\naucun doc_url : le lab a changé de cible ou a "
              "disparu. Les retirer :")
        for lab, frag in mortes:
            print(f"  - lab: {lab}  ancre: {frag}")

    if fausses or a_retirer or mortes:
        return 1
    if strict and injoignables:
        return 10
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labs", action="store_true", help="ne contrôler que les lab.yaml")
    ap.add_argument("--backlog", action="store_true", help="ne contrôler que ROADMAP.md")
    ap.add_argument("--strict", action="store_true",
                    help="une page injoignable échoue aussi, en code 10")
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
    return controler(cibles, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
