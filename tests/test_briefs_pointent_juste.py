"""Un énoncé ne doit pas envoyer l'apprenant là où rien ne l'attend.

D'OÙ VIENT CE CONTRÔLE

De l'issue #237 de dsoxlab, corrigée en 0.1.90 : `dsoxlab challenge` annonçait
`<lab>/challenge` en dur, alors que le travail se fait ailleurs. Un apprenant a
suivi cette ligne à la lettre et perdu une demi-heure sur son premier lab.
Mesuré côté moteur : les mêmes trois fichiers valaient **0/100** à la racine et
**100/100** au bon endroit. La ligne n'était pas imprécise, elle désignait un
endroit où rien n'est lu.

CE QU'IL CONTRÔLE ICI, ET POURQUOI CE N'EST PAS LA MÊME CHOSE QU'AILLEURS

Dans un catalogue dont les labs sont en `runtime: shell`, l'énoncé cite des
chemins du répertoire de travail, et c'est là que se joue la méprise. **Ce
catalogue-ci n'a aucun lab `shell`** : ses 71 labs sont en `runtime: vm`, aucun
ne déclare de `workdir` ni de `fixtures`, et mesuré le 2026-10-30, aucun énoncé
ne cite un chemin sous `challenge/`. Porter le contrôle tel quel aurait donné
un module vert qui ne regarde rien.

Ce qu'un énoncé désigne ici, c'est **la machine sur laquelle travailler** :
« sur `docker.lab`, une Debian 13 jetable ». Mesuré le 2026-10-30 : 102
citations d'un hôte, dans les 29 labs écrits, toutes sur le seul hôte que
`meta.yml` déclare. Un énoncé qui citerait `web1.lab` ou `docker-2.lab`
enverrait l'apprenant se connecter à une machine qui n'existe pas, et aucun
test fonctionnel ne le dirait : c'est le même défaut que l'issue #237, par
l'autre bout.

Les deux contrôles sont donc tenus :

1. tout hôte `*.lab` cité dans un texte de lab est déclaré dans
   `meta.yml: infra.hosts[]` ;
2. tout chemin cité sous `challenge/` existe, ou vit sous le `workdir` déclaré.
   Aucun lab n'en cite aujourd'hui ; le contrôle attend le premier lab `shell`
   du catalogue, et son extracteur est éprouvé sur des cas construits pour
   qu'il ne devienne pas un vert muet en attendant.

CE QU'IL NE PEUT PAS FAIRE

Il ne vérifie pas que l'énoncé cite TOUT ce que les tests lisent : un test peut
lire un fichier que l'apprenant produit, dont le nom est justement ce qu'il
doit trouver. Exiger l'inverse reviendrait à donner la réponse dans l'énoncé.

    uv run pytest tests/test_briefs_pointent_juste.py -v
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
LABS = RACINE / "labs"
META = RACINE / "meta.yml"

sys.path.insert(0, str(RACINE / "scripts"))
from lecture_yaml import lire_yaml  # noqa: E402

#: Un nom d'hôte du lab, cité entre accents graves. Le suffixe `.lab` est la
#: convention de tous les catalogues `vm` de la collection.
HOTE_CITE = re.compile(r"`([A-Za-z0-9][A-Za-z0-9_.-]*\.lab)`")

#: Un chemin du répertoire de travail, cité entre accents graves. Le reste du
#: texte parle de commandes et de concepts, pas d'emplacements.
CHEMIN_CITE = re.compile(r"`(challenge/[A-Za-z0-9_./-]+)`")

#: Les textes que l'apprenant lit avant de travailler, dans les deux langues.
TEXTES = (
    "README.md",
    "README.fr.md",
    "scenario.md",
    "scenario.fr.md",
    "challenge/README.md",
    "challenge/README.fr.md",
)

#: Seuil du garde-fou de couverture, et c'est un PLANCHER, pas une cible.
#:
#: Il ne suit pas la taille du catalogue, et c'est volontaire : les 42
#: squelettes n'ont pas de brief du tout, donc une fraction des 71 labs serait
#: fausse. Mesuré le 2026-10-30 : 29 labs citent leur hôte, soit les 29 labs
#: écrits, tous sans exception. Le plancher est posé en dessous pour qu'un lab
#: qui n'aurait pas à nommer sa machine ne rende pas le module rouge, et il ne
#: peut que devenir plus facile à tenir à mesure que les squelettes s'écrivent.
LABS_CITANTS_MINIMUM = 20


def tous_les_labs() -> list[str]:
    return sorted(str(c.parent.relative_to(LABS)) for c in LABS.rglob("lab.yaml"))


def hotes_declares() -> set[str]:
    infra = lire_yaml(META).get("infra") or {}
    return {h["name"] for h in (infra.get("hosts") or []) if h.get("name")}


def workdir_declare(rel: str) -> str:
    runtime = lire_yaml(LABS / rel / "lab.yaml").get("runtime") or {}
    return (runtime.get("workdir") or "").rstrip("/")


def _textes_du_lab(rel: str) -> list[Path]:
    return [LABS / rel / nom for nom in TEXTES if (LABS / rel / nom).is_file()]


def _cites(rel: str, motif: re.Pattern[str]) -> set[str]:
    trouves: set[str] = set()
    for fichier in _textes_du_lab(rel):
        trouves |= set(motif.findall(fichier.read_text(encoding="utf-8")))
    return trouves


TOUS = tous_les_labs()
HOTES = hotes_declares()


def test_le_meta_declare_bien_des_hotes() -> None:
    """Garde-fou : sans hôte déclaré, le contrôle des hôtes serait vert à vide.

    Il refuserait tout, ou ne comparerait rien selon l'ordre des assertions :
    dans les deux cas il ne mesurerait plus le catalogue.
    """
    assert TOUS, "aucun lab.yaml trouvé : le glob est cassé."
    assert HOTES, (
        "meta.yml ne déclare aucun hôte sous infra.hosts : la comparaison "
        "ci-dessous n'aurait plus de référence."
    )


def test_les_enonces_nomment_bien_la_machine() -> None:
    """Garde-fou de couverture, et il mesure quelque chose de réel.

    Un contrôle qui ne trouve plus rien à contrôler est vert, et c'est la forme
    la plus discrète de faux vert.
    """
    citants = [rel for rel in TOUS if _cites(rel, HOTE_CITE)]

    assert len(citants) >= LABS_CITANTS_MINIMUM, (
        f"Seuls {len(citants)} labs sur {len(TOUS)} citent un hôte `*.lab` : "
        "l'expression régulière ne trouve probablement plus rien, ou les "
        "énoncés ont cessé de nommer la machine sur laquelle on travaille."
    )


def test_les_extracteurs_voient_ce_qu_ils_pretendent_voir() -> None:
    """Les deux motifs, éprouvés sur des cas construits.

    Construits plutôt que cherchés dans le dépôt : ce test ne doit pas dépendre
    du contenu du jour, et il doit rester utile le jour où le catalogue
    n'emploie plus la tournure d'aujourd'hui.
    """
    assert HOTE_CITE.findall("Sur `docker.lab`, une Debian jetable.") == ["docker.lab"]
    assert HOTE_CITE.findall("Le conteneur `vitrine` tourne.") == [], (
        "Un nom de conteneur ne doit pas être pris pour un hôte."
    )
    assert HOTE_CITE.findall("le fichier `daemon.json`") == [], (
        "Un nom de fichier ne doit pas être pris pour un hôte."
    )

    assert CHEMIN_CITE.findall("écrivez `challenge/work/compose.yaml`") == [
        "challenge/work/compose.yaml"
    ]
    assert CHEMIN_CITE.findall("lancez `docker ps`") == []


@pytest.mark.parametrize("rel", TOUS)
def test_un_enonce_ne_cite_aucun_hote_inexistant(rel: str) -> None:
    """Un hôte cité doit être une machine que `dsoxlab provision` crée.

    Le FQDN d'un lab `vm` vit dans `meta.yml: infra.hosts[]`, et `lab.yaml` le
    reprend dans `runtime.targets[].host`. Un énoncé qui en cite un autre
    envoie l'apprenant ouvrir une session SSH vers rien.
    """
    egares = sorted(_cites(rel, HOTE_CITE) - HOTES)

    assert not egares, (
        f"{rel} cite des hôtes que meta.yml ne déclare pas : {egares}\n\n"
        f"Hôtes déclarés : {sorted(HOTES)}\n\n"
        "Soit l'énoncé se trompe de nom, soit la machine manque au bloc "
        "`infra.hosts` du meta.yml, et le lab ne se provisionne pas."
    )


@pytest.mark.parametrize("rel", TOUS)
def test_un_enonce_ne_cite_aucun_chemin_inexistant(rel: str) -> None:
    """Un chemin cité doit mener quelque part.

    Trois cas légitimes, et un seul fautif :

      - le répertoire de travail déclaré par le lab, qui n'existe qu'après
        `dsoxlab run` ;
      - un chemin SOUS ce répertoire, donc une fixture qui y sera copiée ;
      - un fichier ou un dossier réellement présent dans le lab.

    Tout le reste envoie l'apprenant à un endroit où rien n'est lu.
    """
    workdir = workdir_declare(rel)
    lab = LABS / rel

    egares = []
    for cite in sorted(_cites(rel, CHEMIN_CITE)):
        propre = cite.rstrip("/")
        if workdir and (propre == workdir or propre.startswith(workdir + "/")):
            continue
        if (lab / propre).exists():
            continue
        egares.append(cite)

    assert not egares, (
        f"{rel} cite des chemins qui n'existent pas : {egares}\n\n"
        f"Répertoire de travail déclaré : `{workdir or 'aucun'}`\n\n"
        "Un énoncé qui désigne un endroit où rien n'est lu coûte une demi-heure "
        "à qui le suit à la lettre : c'est ce que l'issue #237 de dsoxlab a "
        "mesuré, où les mêmes fichiers valaient 0/100 au mauvais endroit et "
        "100/100 au bon."
    )
