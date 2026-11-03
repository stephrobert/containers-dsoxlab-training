"""La sonde qui cherche le secret dans le contexte de `buildkit-secret-de-build`.

POURQUOI CE TEST EXISTE

Le scenario du lab exige deux fois que le secret reste hors du contexte de
build, et **aucun test ne le mesurait**. Les trois controles du lab inspectent
l'IMAGE : configuration, historique, couches. Or un fichier present dans le
contexte mais jamais `COPY` n'entre dans aucune couche. Un apprenant pouvait
donc copier `depot.token` dans `appli/`, le passer par
`--secret id=depot,src=./depot.token`, et obtenir 100 : l'exigence etait
invisible, et il la croyait notee.

CE QUE CE TEST MESURE, ET POURQUOI IL NE PASSE PAS PAR LA VM

La sonde est un script Python pur : sa logique ne depend ni de Docker ni de la
VM. L'eprouver sur des repertoires jetables la mesure elle, et non l'etat du
banc du jour. Le lab, lui, est eprouve de bout en bout par la reattestation.

ET IL PROVOQUE LES REFUS, dans les deux sens. Un controle qui refuserait tout
bloquerait chaque apprenant honnete ; un controle qui n'accepterait que le cas
evident laisserait passer ce qu'il doit arreter. Les deux defauts se trouvent
en soumettant les deux familles de cas, jamais en jouant le seul cas nominal.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
SONDE = (RACINE / "labs" / "buildkit-secret-de-build" / "fixtures"
         / "inspect-context.py")

JETON = "jeton-de-banc-7f3a91c4"


def jouer(contexte: Path, chemin_jeton: Path) -> dict:
    resultat = subprocess.run(
        [sys.executable, "-I", str(SONDE), str(contexte), str(chemin_jeton)],
        capture_output=True, text=True, timeout=60,
    )
    assert resultat.returncode == 0, resultat.stderr[-500:]
    return json.loads(resultat.stdout)


@pytest.fixture
def banc(tmp_path: Path):
    """Un contexte honnete, et le jeton RANGE EN DEHORS, comme le lab l'exige."""
    jeton = tmp_path / "depot.token"
    jeton.write_text(JETON + "\n", encoding="utf-8")
    contexte = tmp_path / "appli"
    contexte.mkdir()
    (contexte / "Dockerfile").write_text(
        "FROM alpine:3.22.2\n"
        "RUN --mount=type=secret,id=depot,required=true \\\n"
        '  wget -q -O /produit.txt --header="Authorization: Bearer '
        '$(cat /run/secrets/depot)" "$DEPOT_URL"\n',
        encoding="utf-8",
    )
    return contexte, jeton


def test_un_contexte_honnete_est_accepte(banc) -> None:
    """LE SENS QUI PROTEGE L'APPRENANT. Un Dockerfile qui NOMME le secret par
    son point de montage ne le divulgue pas : `/run/secrets/depot` n'est pas le
    jeton. Un controle trop zele le refuserait, et bloquerait la bonne reponse.
    """
    contexte, jeton = banc
    rapport = jouer(contexte, jeton)
    assert rapport["propre"] is True, rapport["fuites"]
    assert rapport["fuites"] == []
    assert rapport["illisibles"] == []


def test_le_fichier_d_identifiant_recopie_est_refuse(banc) -> None:
    """LA FAUTE VISEE, et elle est refusee sur le NOM, meme vide.

    C'est le geste « j'ai copié le secret dans le contexte » que le scénario
    interdit. Son contenu n'y change rien.
    """
    contexte, jeton = banc
    (contexte / "depot.token").write_text("", encoding="utf-8")
    rapport = jouer(contexte, jeton)
    assert rapport["propre"] is False
    assert rapport["fuites"] == [{"chemin": "depot.token",
                                  "ou": "le nom du fichier"}]


@pytest.mark.parametrize(
    ("libelle", "nom", "contenu"),
    [
        ("le jeton en clair dans un fichier quelconque", "aide.sh",
         f"export DEPOT_SECRET={JETON}\n"),
        ("le jeton en base64", "config.json",
         base64.b64encode(JETON.encode()).decode()),
        ("l'en-tête Bearer construit", "entete.txt",
         f"Authorization: Bearer {JETON}"),
        ("le Bearer encodé en base64", "entete.b64",
         base64.b64encode(("Bearer " + JETON).encode()).decode()),
        ("le jeton dans un sous-répertoire", "sous/dossier.conf",
         f"token = {JETON}\n"),
    ],
)
def test_les_formes_du_secret_sont_refusees(banc, libelle: str,
                                            nom: str, contenu: str) -> None:
    """Un secret recopie ne se presente pas toujours brut.

    Ce sont les formes qu'un apprenant produit sans y penser, en gardant une
    note, un script d'aide ou un fichier de configuration dans le contexte.
    """
    contexte, jeton = banc
    cible = contexte / nom
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(contenu, encoding="utf-8")
    rapport = jouer(contexte, jeton)
    assert rapport["propre"] is False, libelle
    assert any(f["ou"] == "le contenu du fichier" for f in rapport["fuites"]), libelle


def test_un_nom_qui_evoque_un_jeton_ne_suffit_pas(banc) -> None:
    """LE FAUX ROUGE QU'ON EVITE. Un `tokenizer.py` innocent passe.

    Refuser tout nom qui evoque un jeton serait un controle qui crie a tort, et
    un controle qui crie a tort s'apprend a ignorer.
    """
    contexte, jeton = banc
    (contexte / "tokenizer.py").write_text("# rien de secret ici\n", encoding="utf-8")
    (contexte / "token-helper.md").write_text("Comment passer un secret.\n",
                                              encoding="utf-8")
    rapport = jouer(contexte, jeton)
    assert rapport["propre"] is True, rapport["fuites"]


def test_un_dockerignore_ne_rachete_pas_le_secret(banc) -> None:
    """L'exigence porte sur le REPERTOIRE, et c'est delibere.

    Un secret exclu ne part pas au demon, mais il reste sur le disque, dans ce
    qu'on versionne, et une exclusion s'oublie : le jour ou quelqu'un retire la
    ligne, ou ajoute un `COPY . .` avant elle, le secret suit l'arborescence.
    """
    contexte, jeton = banc
    (contexte / "depot.token").write_text(JETON, encoding="utf-8")
    (contexte / ".dockerignore").write_text("depot.token\n", encoding="utf-8")
    rapport = jouer(contexte, jeton)
    assert rapport["propre"] is False


def test_une_surface_illisible_est_dite_et_non_tue(banc) -> None:
    """UNE SURFACE NON LUE N'EST PAS UNE SURFACE PROPRE.

    Le lab leve sur `illisibles` plutot que de noter l'apprenant sur ce qu'il
    n'a pas regarde. Encore faut-il que la sonde les RAPPORTE.
    """
    contexte, jeton = banc
    interdit = contexte / "coffre.bin"
    interdit.write_text("peu importe", encoding="utf-8")
    interdit.chmod(0o000)
    try:
        rapport = jouer(contexte, jeton)
    finally:
        interdit.chmod(0o644)
    if not rapport["illisibles"]:
        pytest.skip("exécuté avec un compte qui lit tout : rien à mesurer ici")
    assert any("coffre.bin" in surface for surface in rapport["illisibles"])
