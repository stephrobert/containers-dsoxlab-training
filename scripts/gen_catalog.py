#!/usr/bin/env python3
"""Génère la table des labs (id, titre, niveau, certif, runtime, guide) dans les README.

Source de vérité : l'ordre des sections de `meta.yml` plus chaque
`labs/**/lab.yaml` (et `lab.fr.yaml` pour le titre français). La table s'écrit
entre les marqueurs `<!-- LABS:START -->` et `<!-- LABS:END -->` de `README.md`
et `README.fr.md`.

Repris du catalogue Linux, avec trois différences que CE dépôt impose :

1. **Une cellule vide s'écrit `-`, jamais `—`.** La règle de style du dépôt
   interdit le tiret cadratin dans ce que l'apprenant lit, et la table du README
   en fait partie. Le générateur d'origine posait un cadratin.

2. **La colonne `Runtime` dit ce qu'il faut pour jouer.** Depuis la décision du
   2026-10-28, tous les labs sont en `runtime: vm` : on ne force pas Docker sur
   le poste de l'apprenant. La colonne affiche donc le nombre d'hôtes que le lab
   demande, plus le service déclaré quand il en démarre un. Elle n'est pas muette
   pour autant, et c'est ce qui compte : un lab à deux hôtes coûte deux
   provisionnements, et l'apprenant le lit avant `dsoxlab run`.

   La forme `shell + Docker` reste gérée pour un lab `shell` qui réapparaîtrait,
   mais ce catalogue n'en a plus.

3. **Le titre français vient de `lab.fr.yaml`.** Les répertoires sont nommés en
   anglais et les sections aussi ; seule la colonne des titres bascule.

Usage :
    python3 scripts/gen_catalog.py            # régénère les README
    python3 scripts/gen_catalog.py --check    # échoue (exit 1) si un README est périmé
"""

from __future__ import annotations

import sys
from pathlib import Path

# Un seul chemin de lecture pour tout le catalogue : voir scripts/lecture_yaml.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lecture_yaml import YamlIllisible, lire_yaml

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "meta.yml"
START, END = "<!-- LABS:START -->", "<!-- LABS:END -->"

# Une cellule sans valeur. Pas de tiret cadratin : la règle de style du dépôt
# l'interdit dans ce que l'apprenant lit.
VIDE = "-"

HEAD = {
    "en": ("Lab (id)", "Title", "Level", "Certif", "Runtime", "Companion guide"),
    "fr": ("Lab (id)", "Titre", "Niveau", "Certif", "Runtime", "Guide compagnon"),
}

# Ce catalogue n'a pas de lab exigeant un compte distant : son prérequis est
# local et unique, un moteur Docker qui répond. La colonne le dit une fois pour
# tous les labs `shell`, plutôt que de rester muette.
MENTION_DOCKER = {"en": "shell + Docker", "fr": "shell + Docker"}
MENTION_VM = {"en": "1 VM", "fr": "1 VM"}
MENTION_VM_N = {"en": "{n} VMs", "fr": "{n} VM"}


def _titres_fr() -> dict[str, str]:
    """Titres français des sections, appariés par `id` et non par position.

    C'est le mécanisme du contrat dsoxlab (0.1.54) : `meta.yml` porte
    l'anglais, `meta.fr.yml` la surcharge. Son absence n'est pas une erreur,
    c'est le cas de la langue par défaut.
    """
    fichier = ROOT / "meta.fr.yml"
    if not fichier.exists():
        return {}
    try:
        traduit = lire_yaml(fichier)
    except YamlIllisible as exc:
        print(f"  titres français ignorés : {exc}", file=sys.stderr)
        return {}
    return {
        str(s.get("id", "")): str(s.get("title", ""))
        for s in (traduit.get("sections") or [])
        if s.get("title")
    }


def _runtime_label(lab: dict, lang: str) -> str:
    """Ce qu'il faut avoir sous la main pour jouer ce lab.

    Pour un lab `vm`, ce n'est plus le runtime qui informe (ils le sont tous)
    mais le NOMBRE d'hôtes : un lab à deux hôtes coûte deux provisionnements,
    et c'est la seule chose que l'apprenant ait besoin de savoir d'avance.
    """
    runtime = lab.get("runtime") or {}
    base = str(runtime.get("type", "vm"))

    services = sorted(n for n in (s.get("name", "") for s in (runtime.get("services") or [])) if n)
    if base == "vm":
        hotes = {c.get("host") for c in (runtime.get("targets") or []) if c.get("host")}
        etiquette = MENTION_VM[lang] if len(hotes) <= 1 else MENTION_VM_N[lang].format(n=len(hotes))
        return f"{etiquette} + " + ", ".join(services) if services else etiquette
    if services:
        return f"{base} + " + ", ".join(services)
    if base == "shell":
        # Un lab `shell` parlerait au moteur de l'apprenant : la colonne serait
        # muette à n'afficher que « shell ». Ce catalogue n'en a plus.
        return MENTION_DOCKER[lang]
    return base


def _sections() -> list[tuple[str, str, list[dict]]]:
    """[(id de section, titre, [lab, ...]), ...] dans l'ordre de meta.yml."""
    try:
        meta = lire_yaml(META)
    except YamlIllisible as erreur:
        # Sans meta.yml il n'y a pas de catalogue du tout : on s'arrête en
        # DISANT quoi, pas sur une trace d'appels.
        sys.exit(f"catalogue ingénérable - {erreur}")

    trouvees: list[tuple[str, str, list[dict]]] = []
    for section in meta.get("sections", []):
        labs: list[dict] = []
        for rel in section.get("labs") or []:
            dossier = ROOT / "labs" / rel
            contrat = dossier / "lab.yaml"
            if not contrat.exists():
                continue
            try:
                lab = lire_yaml(contrat)
            except YamlIllisible as erreur:
                print(f"  lab écarté du catalogue - {rel}/{erreur}", file=sys.stderr)
                continue

            lab["_titre_fr"] = lab.get("title", "")
            contrat_fr = dossier / "lab.fr.yaml"
            if contrat_fr.exists():
                try:
                    fr = lire_yaml(contrat_fr)
                except YamlIllisible as erreur:
                    print(f"  {rel}/{erreur}", file=sys.stderr)
                    fr = {}
                lab["_titre_fr"] = fr.get("title", lab.get("title", ""))
            labs.append(lab)

        if labs:
            trouvees.append((
                section.get("id", ""),
                {
                    "en": section.get("title", ""),
                    "fr": _titres_fr().get(str(section.get("id", "")))
                    or section.get("title", ""),
                },
                labs,
            ))
    return trouvees


def _certif(lab: dict) -> str:
    """Les certifications visées, ex. « TF-ASSOCIATE »."""
    tags = lab.get("certification_tags") or []
    if not tags:
        return VIDE
    return " · ".join(str(t).upper() for t in tags)


def _guide(lab: dict) -> str:
    url = lab.get("doc_url", "")
    return f"[guide]({url})" if url else VIDE


def _echapper(texte: str) -> str:
    """Un titre peut porter un `|`, qui couperait la cellule en deux."""
    return str(texte).replace("|", "\\|")


def _table(lang: str) -> str:
    entetes = HEAD[lang]
    lignes: list[str] = []
    sections = _sections()

    for _id, titres, labs in sections:
        lignes.append(f"### {titres[lang]}")
        lignes.append("")
        lignes.append("| " + " | ".join(entetes) + " |")
        lignes.append("|" + "|".join(["---"] * len(entetes)) + "|")
        for lab in labs:
            titre_lab = lab["_titre_fr"] if lang == "fr" else lab.get("title", "")
            lignes.append(
                "| `{id}` | {titre} | {niveau} | {certif} | {rt} | {guide} |".format(
                    id=lab.get("id", ""),
                    titre=_echapper(titre_lab),
                    niveau=lab.get("level", VIDE),
                    certif=_certif(lab),
                    rt=_runtime_label(lab, lang),
                    guide=_guide(lab),
                )
            )
        lignes.append("")

    total = sum(len(labs) for _i, _t, labs in sections)
    # Vrai pluriel, jamais « lab(s) » ni « 1 labs ». Le catalogue n'en compte
    # qu'un aujourd'hui, et la légende l'écrivait « 1 labs ».
    mot = "lab" if total == 1 else "labs"  # le mot est le même dans les deux langues
    legende = (
        f"_{total} {mot}, table generated by `scripts/gen_catalog.py`._"
        if lang == "en"
        else f"_{total} {mot}, table générée par `scripts/gen_catalog.py`._"
    )
    lignes.append(legende)
    return "\n".join(lignes)


def _rendu(chemin: Path, bloc: str) -> str:
    texte = chemin.read_text(encoding="utf-8")
    if START not in texte or END not in texte:
        raise SystemExit(f"marqueurs absents dans {chemin}")
    avant = texte.split(START)[0]
    apres = texte.split(END)[1]
    return f"{avant}{START}\n{bloc}\n{END}{apres}"


CIBLES = {"README.md": "en", "README.fr.md": "fr"}


def _verifier() -> int:
    perimes = []
    for nom, lang in CIBLES.items():
        chemin = ROOT / nom
        if chemin.read_text(encoding="utf-8") != _rendu(chemin, _table(lang)):
            perimes.append(nom)
    if perimes:
        print(
            "Catalogue périmé dans : "
            + ", ".join(perimes)
            + "\nLancez `python3 scripts/gen_catalog.py` puis recommitez.",
            file=sys.stderr,
        )
        return 1
    print("catalogue à jour")
    return 0


def _ecrire() -> None:
    for nom, lang in CIBLES.items():
        chemin = ROOT / nom
        chemin.write_text(_rendu(chemin, _table(lang)), encoding="utf-8")
    print("catalogue régénéré dans README.md et README.fr.md")


def main() -> None:
    if "--check" in sys.argv[1:]:
        raise SystemExit(_verifier())
    _ecrire()


if __name__ == "__main__":
    main()
