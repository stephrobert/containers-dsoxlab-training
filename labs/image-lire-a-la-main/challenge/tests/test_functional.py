"""test_functional.py : image-lire-a-la-main

Une image lue à la main se reconnaît à trois choses : un layout OCI copié par
digest, dont chaque blob porte l'empreinte de son nom ; le digest du manifeste
linux/amd64 lu dans la chaîne ; et le blob altéré d'un layout suspect, trouvé
en recalculant les empreintes. Les tests lisent le disque d'oci.lab, jamais
l'historique.

Aucun n'est vrai avant le travail : au départ, /srv/etal n'existe pas et
/srv/reponses est vide.

Le blob altéré est tiré au hasard par le setup, à chaque passage. Le test le
compare au nom noté par le setup dans un fichier que seul root lit : deviner
parmi six blobs ne suffit pas d'une fois sur l'autre.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_target_host, message

ETAL = "/srv/etal"
REPONSES = "/srv/reponses"
MARQUE = "/var/lib/dsoxlab-image-lire-a-la-main.altere"
#: Mesurés le 2026-11-26 sur l'index busybox 1.37.0
#: (sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec).
MANIFESTE_AMD64 = "66a6306db78bf2dbf3487f293aa8d6990d8e506fdffab9cc43fe422becf886e4"
CONFIG_AMD64 = "30ecbe1509090b38ef3260f3609d64d8261230464eaa4d235901db496e9647fb"
COUCHE_AMD64 = "68fe9bff2ad4ad46da3e58db03faa64eb73c0ff16d546b0c42539eaa9854cb7f"
TAG = "1.37.0"


@pytest.fixture(scope="module")
def host():
    return lab_host(lab_target_host("oci.lab"))


def _lire(host, fichier: str) -> str:
    return host.run(f"sudo cat {fichier} 2>/dev/null").stdout.strip()


def _empreinte(reponse: str) -> str:
    """Une réponse s'écrit avec ou sans le préfixe sha256: ; on compare l'empreinte seule."""
    return reponse.strip().removeprefix("sha256:")


def test_etal_est_un_layout_oci_qui_nomme_le_tag(host):
    version = _lire(host, f"{ETAL}/oci-layout")
    index = _lire(host, f"{ETAL}/index.json")
    assert '"imageLayoutVersion"' in version and index, message(
        en=f"{ETAL} is not an OCI layout: it needs an oci-layout file and an "
        "index.json. skopeo writes both when the destination starts with oci:.",
        fr=f"{ETAL} n'est pas un layout OCI : il lui faut un fichier oci-layout "
        "et un index.json. skopeo écrit les deux quand la destination commence "
        "par oci:.",
    )
    noms = [
        m.get("annotations", {}).get("org.opencontainers.image.ref.name")
        for m in json.loads(index).get("manifests", [])
    ]
    assert TAG in noms, message(
        en=f"index.json of {ETAL} names {noms or 'nothing'}, not {TAG}. The tag "
        "goes on the destination side: oci:/srv/etal:1.37.0.",
        fr=f"L'index.json de {ETAL} nomme {noms or 'rien'}, pas {TAG}. Le tag se "
        "pose du côté de la destination : oci:/srv/etal:1.37.0.",
    )


def test_etal_porte_l_image_amd64_intacte(host):
    index = _lire(host, f"{ETAL}/index.json")
    digests = [m.get("digest", "") for m in json.loads(index or "{}").get("manifests", [])]
    assert f"sha256:{MANIFESTE_AMD64}" in digests, message(
        en=f"{ETAL} does not hold the linux/amd64 manifest of busybox 1.37.0 "
        f"(it holds {digests or 'nothing'}). Copy by the index digest given in "
        "the mission, and choose the platform with --override-arch amd64.",
        fr=f"{ETAL} ne porte pas le manifeste linux/amd64 de busybox 1.37.0 (il "
        f"porte {digests or 'rien'}). Copiez par le digest de l'index donné dans "
        "la mission, et choisissez la plateforme avec --override-arch amd64.",
    )
    res = host.run(
        f"sudo sh -c 'cd {ETAL}/blobs/sha256 && for f in *; do "
        "echo \"$f $(sha256sum \"$f\" | cut -c1-64)\"; done'"
    )
    paires = [ligne.split() for ligne in res.stdout.splitlines() if ligne.strip()]
    faux = [nom for nom, calcul in paires if nom != calcul]
    assert not faux, message(
        en=f"These blobs of {ETAL} no longer carry the hash of their name: {faux}. "
        "A blob is named by the sha256 of its content: copy the image again "
        "rather than repair it.",
        fr=f"Ces blobs de {ETAL} ne portent plus l'empreinte de leur nom : {faux}. "
        "Un blob est nommé par le sha256 de son contenu : recopiez l'image "
        "plutôt que de la réparer.",
    )
    attendus = {MANIFESTE_AMD64, CONFIG_AMD64, COUCHE_AMD64}
    presents = {nom for nom, _ in paires}
    assert attendus <= presents, message(
        en=f"{ETAL}/blobs/sha256 misses {sorted(attendus - presents)}: the "
        "manifest, its config and its layer must all be there.",
        fr=f"{ETAL}/blobs/sha256 n'a pas {sorted(attendus - presents)} : le "
        "manifeste, sa configuration et sa couche doivent tous y être.",
    )


def test_le_digest_du_manifeste_amd64_est_note(host):
    reponse = _lire(host, f"{REPONSES}/manifeste-amd64")
    assert _empreinte(reponse) == MANIFESTE_AMD64, message(
        en=f"{REPONSES}/manifeste-amd64 reads \"{reponse or 'nothing'}\". Expected "
        "the digest of the linux/amd64 manifest of busybox 1.37.0: it is in the "
        "index served by the registry, and in the index.json of your layout.",
        fr=f"{REPONSES}/manifeste-amd64 contient « {reponse or 'rien'} ». Attendu : "
        "le digest du manifeste linux/amd64 de busybox 1.37.0. Il est dans "
        "l'index que sert le registre, et dans l'index.json de votre layout.",
    )


def test_le_blob_altere_est_designe(host):
    altere = _lire(host, MARQUE)
    assert altere, message(
        en=f"The setup mark {MARQUE} is missing: replay the lab with dsoxlab "
        "reset, the altered blob is drawn again.",
        fr=f"La marque du setup {MARQUE} est absente : rejouez le lab avec "
        "dsoxlab reset, le blob altéré est tiré de nouveau.",
    )
    reponse = _lire(host, f"{REPONSES}/blob-altere")
    assert _empreinte(reponse) == altere, message(
        en=f"{REPONSES}/blob-altere reads \"{reponse or 'nothing'}\", which is not "
        "the altered blob of /srv/suspect. Recompute the sha256 of each blob and "
        "compare it to its NAME: the answer is the name of the one that no "
        "longer matches.",
        fr=f"{REPONSES}/blob-altere contient « {reponse or 'rien'} », qui n'est "
        "pas le blob altéré de /srv/suspect. Recalculez le sha256 de chaque blob "
        "et comparez-le à son NOM : la réponse est le nom de celui qui ne "
        "correspond plus.",
    )
