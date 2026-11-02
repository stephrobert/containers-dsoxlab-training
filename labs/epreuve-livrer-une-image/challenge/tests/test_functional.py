"""Tests fonctionnels de l'épreuve epreuve-livrer-une-image : quatre contrôles de poids égal.

CE QUE CETTE ÉPREUVE PROUVE. Qu'une image livrée est utilisable par un client qui
n'a ni le contexte, ni le cache, ni le droit d'écrire, et que le secret ayant
servi à la construire n'a survécu nulle part.

LE SEUIL EST À 75 %, soit trois contrôles sur quatre. C'est délibéré pour une
épreuve : un candidat qui livre une image utilisable, par digest, depuis un
client nu, a démontré l'essentiel même s'il a laissé filer une couche.

LES DEUX HÔTES SONT INTERROGÉS SÉPARÉMENT. Le troisième contrôle regarde
`docker-client.lab`, et c'est tout son intérêt : une image qui ne tourne que sur
la machine qui l'a construite n'est pas livrée, elle est seulement construite.

LE SECRET EST TIRÉ AU HASARD À CHAQUE PASSAGE, et les tests le lisent dans le
relevé privé du banc. Une valeur en dur se recopierait d'un passage sur l'autre,
et le contrôle ne prouverait plus que le secret de CE passage a été employé.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, message

ATELIER = "/opt/lab-livraison"
# Le répertoire qui ne porte QUE la CA. `skopeo --cert-dir` lit tout le
# répertoire et apparie `*.key` avec `*.cert` : pointé sur `certs/`, qui
# porte des clés sans certificat en face, il refuse AVANT de se connecter
# (« missing client certificate ca.cert for key ca.key », mesuré le
# 2026-11-02), et son message ne parle alors ni du registre ni des
# identifiants.
CONFIANCE = "/opt/lab-livraison/confiance"
RELEVE = "/root/.lab-livraison.json"
LIVRAISON = f"{ATELIER}/livraison.txt"
REGISTRE = "livraison.lab.test:15401"
DEPOT = f"{REGISTRE}/livraison/appli"
CONTENEUR = "dsoxlab-livraison-client"

PUBLICATION = "docker.lab"
CLIENT = "docker-client.lab"


@pytest.fixture(scope="module")
def host():
    """L'hôte de publication : celui qui construit et qui pousse."""
    return lab_host(PUBLICATION)


@pytest.fixture(scope="module")
def client():
    """Le client NU, et c'est une machine différente.

    Sans cette fixture, le troisième contrôle regarderait l'hôte de
    publication, où tout est déjà en cache : il passerait sans rien prouver.
    """
    return lab_host(CLIENT)


def _releve(host) -> dict:
    """Le secret tiré au hasard, son empreinte attendue, et les deux comptes."""
    res = host.run("cat %s", RELEVE)
    if res.rc != 0:
        pytest.fail(message(
            en=f"{RELEVE} is missing: the setup did not finish",
            fr=f"{RELEVE} est absent : le setup n'a pas abouti",
        ))
    return json.loads(res.stdout)


def _paires(host, chemin: str, quoi: str) -> dict[str, str]:
    """Un fichier `clé=valeur`, réduit à ses paires.

    Tolérant sur la forme (espaces, lignes vides, commentaires, casse de la
    clé), strict sur le fond : c'est le contenu qui est noté, pas la mise en
    page.
    """
    f = host.file(chemin)
    if not f.exists:
        pytest.fail(message(
            en=f"{chemin} is missing: {quoi}",
            fr=f"{chemin} est absent : {quoi}",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def _livraison(host) -> dict[str, str]:
    return _paires(
        host, LIVRAISON,
        message(
            en="the mission asks for two lines in it: reference_par_digest= "
               "and empreinte_du_secret=",
            fr="la mission demande d'y écrire deux lignes : "
               "reference_par_digest= et empreinte_du_secret=",
        ),
    )


def test_la_livraison_est_publiee_et_designee_par_son_digest(host) -> None:
    """La publication, et la référence qui la désigne sans ambiguïté.

    UN DIGEST, PAS UNE ÉTIQUETTE. Le contrôle demande au registre ce qu'il sert
    pour l'étiquette `1.0`, et exige que la référence consignée porte ce même
    digest. Les deux valeurs sont relevées séparément : les comparer reste une
    mesure.
    """
    releve = _releve(host)
    livraison = _livraison(host)

    reference = livraison.get("reference_par_digest", "")
    assert reference, message(
        en="the `reference_par_digest=` line is empty. It is the reference the "
           "registry serves, by digest.",
        fr="la ligne `reference_par_digest=` est vide. C'est la référence que "
           "le registre sert, par digest.",
    )
    assert reference.startswith(f"{DEPOT}@sha256:"), message(
        en=f"`{reference}` is not a digest reference on {DEPOT}.\n"
           "A tag can be moved without the file that cites it changing.",
        fr=f"`{reference}` n'est pas une référence par digest sur {DEPOT}.\n"
           "Une étiquette peut être déplacée sans que le fichier qui la cite "
           "change.",
    )

    compte = releve["comptes"]
    # LE REPERTOIRE DE CONFIANCE, et non `certs/`. Mesure du
    # 2026-11-02 : `skopeo --cert-dir` lit tout le repertoire et
    # apparie `*.key` avec `*.cert` ; sur `certs/`, qui porte des cles
    # sans certificat en face, il refuse avant de se connecter.
    servi = host.run(
        "skopeo inspect --cert-dir %s --creds %s --format %s %s",
        CONFIANCE, f"publisher:{compte['publisher']}", "{{.Digest}}",
        f"docker://{DEPOT}:1.0",
    )
    assert servi.rc == 0, message(
        en=f"the registry does not serve {DEPOT}:1.0. Push the image with the "
           f"publishing account: {servi.stderr[-300:]}",
        fr=f"le registre ne sert pas {DEPOT}:1.0. Poussez l'image avec le "
           f"compte de publication : {servi.stderr[-300:]}",
    )
    assert reference.split("@", 1)[1] == servi.stdout.strip(), message(
        en=f"the recorded reference does not carry the digest the registry "
           f"serves.\n"
           f"  you wrote : {reference.split('@', 1)[1]}\n"
           f"  served    : {servi.stdout.strip()}",
        fr=f"la référence consignée ne porte pas le digest que le registre "
           f"sert.\n"
           f"  vous avez écrit : {reference.split('@', 1)[1]}\n"
           f"  servi           : {servi.stdout.strip()}",
    )


def test_le_secret_a_servi_et_ne_survit_dans_aucune_couche(host) -> None:
    """Les deux moitiés d'une même exigence, et elles ne se séparent pas.

    LE SECRET A SERVI : l'empreinte consignée est bien celle du secret de CE
    passage, qu'aucune valeur plausible ne peut deviner.

    IL NE SURVIT PAS : le contrôle cherche le secret dans l'historique de
    l'image, puis dans TOUTES ses couches, en exportant l'image et en lisant
    ses fichiers. Chercher dans l'historique seul laisserait passer un `COPY`,
    qui n'y apparaît que par le nom du fichier.
    """
    releve = _releve(host)
    livraison = _livraison(host)

    annonce = livraison.get("empreinte_du_secret", "")
    assert annonce, message(
        en="the `empreinte_du_secret=` line is empty.",
        fr="la ligne `empreinte_du_secret=` est vide.",
    )
    assert annonce == releve["empreinte_attendue"], message(
        en="the recorded digest is not that of this run's build secret.\n"
           f"  you wrote : {annonce}\n"
           "It is drawn at random at every run, and no plausible value can be "
           "guessed.",
        fr="l'empreinte consignée n'est pas celle du secret de construction de "
           "ce passage.\n"
           f"  vous avez écrit : {annonce}\n"
           "Il est tiré au hasard à chaque passage, et aucune valeur plausible "
           "ne se devine.",
    )

    secret = releve["secret"]
    historique = host.run(
        "docker image history --no-trunc --format %s %s",
        "{{.CreatedBy}}{{.Comment}}", f"{DEPOT}:1.0",
    )
    assert historique.rc == 0, message(
        en=f"the image {DEPOT}:1.0 is not on the publishing host.",
        fr=f"l'image {DEPOT}:1.0 n'est pas sur l'hôte de publication.",
    )
    assert secret not in historique.stdout, message(
        en="the build secret is readable in the image's history. A build "
           "argument and an environment variable both land there.",
        fr="le secret de construction se relit dans l'historique de l'image. "
           "Un argument de construction comme une variable d'environnement y "
           "atterrissent.",
    )

    # LES COUCHES ELLES-MEMES, et pas seulement l'historique : un `COPY` n'y
    # laisse que le nom du fichier. On exporte l'image et on cherche dedans.
    fouille = host.run(
        "set -o pipefail; docker image save %s | tar -xO 2>/dev/null | "
        "grep -c -F -- %s || true",
        f"{DEPOT}:1.0", secret,
    )
    trouvailles = (fouille.stdout or "0").strip().splitlines()
    combien = int(trouvailles[-1]) if trouvailles and trouvailles[-1].isdigit() else 0
    assert combien == 0, message(
        en=f"the build secret is present {combien} time(s) in the image's "
           "layers. A secret mounted for the duration of one instruction does "
           "not enter a layer; a copied secret does.",
        fr=f"le secret de construction est présent {combien} fois dans les "
           "couches de l'image. Un secret monté le temps d'une instruction "
           "n'entre pas dans une couche ; un secret copié y entre.",
    )


def test_le_client_nu_tire_par_digest_et_execute(host, client) -> None:
    """La livraison est-elle utilisable ailleurs ? C'est la question de l'épreuve.

    SUR L'AUTRE MACHINE, et par le DIGEST consigné. Le client n'a ni le
    contexte, ni le cache, ni le droit d'écrire : s'il fait tourner l'image et
    qu'elle répond la bonne empreinte, la livraison tient.
    """
    releve = _releve(host)
    reference = _livraison(host).get("reference_par_digest", "")
    assert reference, message(
        en="the `reference_par_digest=` line is empty: the client has nothing "
           "to pull.",
        fr="la ligne `reference_par_digest=` est vide : le client n'a rien à "
           "tirer.",
    )

    etat = client.run(
        "docker container inspect %s --format %s", CONTENEUR,
        "{{.State.Status}} {{.Image}} {{.Config.Image}}",
    )
    assert etat.rc == 0, message(
        en=f"no container named `{CONTENEUR}` on {CLIENT}. The delivery has to "
           "run on the bare client, not only on the host that built it.",
        fr=f"aucun conteneur nommé `{CONTENEUR}` sur {CLIENT}. La livraison "
           "doit tourner sur le client nu, et pas seulement sur l'hôte qui l'a "
           "construite.",
    )
    statut, _, configuree = etat.stdout.split(None, 2)
    assert statut == "running", message(
        en=f"`{CONTENEUR}` is in state `{statut}`, not `running`.",
        fr=f"`{CONTENEUR}` est dans l'état `{statut}`, pas `running`.",
    )
    assert configuree.strip() == reference, message(
        en=f"the container on {CLIENT} does not run the recorded digest "
           "reference.\n"
           f"  it runs  : {configuree.strip()}\n"
           f"  expected : {reference}",
        fr=f"le conteneur sur {CLIENT} ne tourne pas la référence par digest "
           "consignée.\n"
           f"  il tourne : {configuree.strip()}\n"
           f"  attendu   : {reference}",
    )

    rendu = client.run(
        "docker exec %s python -c %s", CONTENEUR,
        "import urllib.request; "
        "print(urllib.request.urlopen('http://127.0.0.1:8080/', timeout=5)"
        ".read().decode().strip())",
    )
    assert rendu.rc == 0 and rendu.stdout.strip() == releve["empreinte_attendue"], message(
        en=f"the delivery does not answer the expected digest on {CLIENT}.\n"
           f"  answered : {rendu.stdout.strip() or rendu.stderr[-200:]}",
        fr=f"la livraison ne répond pas l'empreinte attendue sur {CLIENT}.\n"
           f"  répondu : {rendu.stdout.strip() or rendu.stderr[-200:]}",
    )


def test_le_compte_en_lecture_seule_ne_peut_pas_publier(host, client) -> None:
    """Le droit, mesuré sur ce que le candidat a réellement livré.

    POURQUOI LA SONDE DÉRIVE DE LA LIVRAISON. Un premier passage faisait ce
    contrôle sur le banc seul : il passait AVANT tout travail, puisque le refus
    d'un compte en lecture seule ne dépend pas du candidat. Sur une épreuve à
    75 %, un quart de la note offerte ramène l'exigence à deux contrôles sur
    trois. La sonde part donc de l'image que le candidat a tirée : sans
    livraison sur le client, elle n'existe pas.

    POURQUOI UN CONTENU INÉDIT. Mesuré le 2026-11-02 sur Docker 29.9.2 :
    repousser un contenu que le registre possède déjà sort en 0 sans aucune
    écriture, le client voyant tout en place, et le journal du registre ne
    porte alors ni PUT, ni POST, ni PATCH. Le refus n'aurait aucune occasion de
    se produire, et on mesurerait une optimisation du client au lieu d'un droit.
    Une image dérivée en une ligne rend le manifeste inédit : sa configuration
    doit être téléversée, donc le droit est demandé.
    """
    reference = _livraison(host).get("reference_par_digest", "")
    assert reference, message(
        en="the `reference_par_digest=` line is empty: there is nothing the "
           "client could have pulled, so nothing to derive from.",
        fr="la ligne `reference_par_digest=` est vide : le client n'a rien pu "
           "tirer, donc rien à dériver.",
    )

    sonde = f"{DEPOT}:sonde-lecteur"
    contexte = "/tmp/dsoxlab-livraison-sonde"
    try:
        derive = client.run(
            "mkdir -p %s && printf 'FROM %s\\nLABEL dsoxlab.lab=\"%s\"\\n' > %s "
            "&& docker build --provenance=false -t %s %s",
            contexte, reference, "epreuve-livrer-une-image",
            f"{contexte}/Dockerfile", sonde, contexte,
        )
        assert derive.rc == 0, message(
            en=f"cannot derive an image from the delivery on the client: the "
               f"image has to be there first.\n  {derive.stderr[-300:]}",
            fr=f"impossible de dériver une image de la livraison sur le "
               f"client : l'image doit d'abord y être.\n  "
               f"{derive.stderr[-300:]}",
        )
        refus = client.run("docker push %s", sonde)
        assert refus.rc != 0 and any(
            mot in refus.stderr.lower()
            for mot in ("denied", "unauthorized", "insufficient_scope")
        ), message(
            en=f"the read-only account published content the registry had "
               f"never seen.\n  {(refus.stderr or refus.stdout)[-300:]}\n"
               "A read-only account must not be able to write.",
            fr=f"le compte en lecture seule a publié un contenu que le registre "
               f"n'avait jamais vu.\n  {(refus.stderr or refus.stdout)[-300:]}\n"
               "Un compte en lecture seule ne doit pas pouvoir écrire.",
        )
    finally:
        client.run("docker image rm -f %s", sonde)
        client.run("rm -rf %s", contexte)
