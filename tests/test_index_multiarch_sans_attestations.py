"""`images-multi-architecture` compte les VARIANTES de l'index, pas ses entrees.

POURQUOI CE TEST EXISTE

Le lab exigeait `len(manifests) == 2` sur l'index publie. Mesure du 2026-11-03
sur Engine 29.9.2 et Buildx 0.38.1, registre local jetable :

    --platform linux/amd64,linux/arm64 --push, provenance par DEFAUT  -> 4 entrees
    la meme poussee avec --provenance=false                            -> 2 entrees

Les deux entrees de trop sont des manifestes d'attestation de provenance, en
plateforme `unknown/unknown`, annotes
`vnd.docker.reference.type=attestation-manifest`.

La solution du lab emploie `--provenance=false`, donc elle passait, et
l'attestation du lab etait VERTE. Mais la lecon enseigne la voie simple, qui
garde la provenance : un apprenant qui la suit lisait « une release exige deux
manifestes distincts » apres en avoir livre deux. **Un test ne doit pas accuser
le travail pour une forme que l'enonce n'a jamais exigee**, et c'est l'ecart
exact que la solution masquait.

CE QUE CE TEST MESURE

Les deux index REELS, tels que le registre les a servis, figes en donnees. Pas
une forme supposee : `annotations` vaut `null` et non `{}` sur une variante
utile, et c'est le genre de detail qu'un index ecrit de memoire aurait manque.

Et il PROVOQUE le refus : un index qui ne porte qu'une seule variante, ou deux
fois la meme, doit etre refuse. Sans ces cas, un filtre qui garderait tout, ou
qui jetterait tout, passerait ce fichier sans broncher.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
MODULE = (RACINE / "labs" / "images-multi-architecture" / "challenge" / "tests"
          / "test_functional.py")

# ── Les deux index reellement servis, le 2026-11-03 ──────────────────────────
VARIANTE_AMD64 = {
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "digest": "sha256:" + "a" * 64,
    "platform": {"architecture": "amd64", "os": "linux"},
    "annotations": None,
}
VARIANTE_ARM64 = {
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "digest": "sha256:" + "b" * 64,
    "platform": {"architecture": "arm64", "os": "linux"},
    "annotations": None,
}


def _attestation(suffixe: str) -> dict:
    return {
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "digest": "sha256:" + suffixe * 64,
        "platform": {"architecture": "unknown", "os": "unknown"},
        "annotations": {"vnd.docker.reference.type": "attestation-manifest"},
    }


PROVENANCE_PAR_DEFAUT = [VARIANTE_AMD64, VARIANTE_ARM64,
                         _attestation("c"), _attestation("d")]
PROVENANCE_DESACTIVEE = [VARIANTE_AMD64, VARIANTE_ARM64]


@pytest.fixture(scope="module")
def variantes():
    """`_image_variants` du lab, chargee sans jouer le lab."""
    spec = importlib.util.spec_from_file_location("lab_multiarch", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._image_variants


def test_les_deux_strategies_donnent_les_memes_deux_variantes(variantes) -> None:
    """LE DEFAUT CORRIGE : les deux voies doivent se valoir.

    C'est tout l'objet du changement. La voie de la lecon et celle de la
    solution produisent des index de taille differente, et pourtant le meme
    travail : deux variantes, Linux AMD64 et Linux ARM64.
    """
    par_defaut = variantes(PROVENANCE_PAR_DEFAUT)
    desactivee = variantes(PROVENANCE_DESACTIVEE)
    assert len(par_defaut) == 2, "la voie que la leçon enseigne doit être acceptée"
    assert len(desactivee) == 2
    assert [e["digest"] for e in par_defaut] == [e["digest"] for e in desactivee]


def test_une_attestation_est_ecartee_par_son_annotation(variantes) -> None:
    """L'annotation dit l'INTENTION, et c'est le critere le plus sûr."""
    annotee = dict(_attestation("e"), platform={"architecture": "amd64", "os": "linux"})
    assert variantes([VARIANTE_AMD64, annotee]) == [VARIANTE_AMD64]


def test_une_plateforme_unknown_est_ecartee_sans_annotation(variantes) -> None:
    """La plateforme dit la FORME, et un futur buildx peut changer l'autre.

    Les deux criteres sont appliques, et non l'un ou l'autre : c'est ce qui
    fait tenir le filtre si l'annotation disparait ou change de nom.
    """
    muette = {"digest": "sha256:" + "f" * 64,
              "platform": {"architecture": "unknown", "os": "unknown"},
              "annotations": None}
    assert variantes([VARIANTE_AMD64, muette]) == [VARIANTE_AMD64]


@pytest.mark.parametrize(
    ("libelle", "index", "attendu"),
    [
        ("une seule variante ne suffit pas", [VARIANTE_AMD64], 1),
        ("un index vide ne rend rien", [], 0),
        ("un index d'attestations seules ne rend rien",
         [_attestation("c"), _attestation("d")], 0),
    ],
)
def test_le_filtre_ne_garde_pas_tout(variantes, libelle: str,
                                     index: list, attendu: int) -> None:
    """LE REFUS PROVOQUE. Un filtre qui garderait tout passerait le reste.

    Le lab exige ensuite DEUX variantes distinctes : ces cas doivent donc rendre
    moins de deux, sinon le compte du lab ne mesurerait plus rien.
    """
    assert len(variantes(index)) == attendu, libelle


def test_les_annotations_nulles_ne_font_pas_lever(variantes) -> None:
    """`annotations` vaut `null` sur une variante utile, pas `{}`.

    Mesure du 2026-11-03 : c'est la forme que le registre sert reellement. Un
    filtre qui ferait `entry["annotations"].get(...)` leverait sur chaque index
    valide, et le lab deviendrait injouable pour tout le monde.
    """
    sans_cle = {"digest": "sha256:" + "0" * 64,
                "platform": {"architecture": "amd64", "os": "linux"}}
    assert variantes([sans_cle]) == [sans_cle]
    assert variantes([VARIANTE_AMD64]) == [VARIANTE_AMD64]
