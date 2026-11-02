"""Tests fonctionnels de l'épreuve de première livraison : cinq contrôles de poids égal.

C'EST UNE ÉPREUVE DE CONSTRUCTION, et non de diagnostic : il n'y a pas de panne
à trouver, il y a une image à livrer correctement. Les messages nomment donc ce
qui MANQUE à la livraison, jamais l'instruction de Dockerfile qui l'apporterait.

L'EXIGENCE CRITIQUE est le contrôle 3 : le jeton du dépôt privé présent dans une
couche. Aucun total ne la compense, parce qu'un secret livré dans une image est
un secret publié : l'image part dans un registre, le registre est lu par
d'autres, et le retirer ensuite ne reprend rien.

POURQUOI LE CONTRÔLE 3 LIT L'ARCHIVE DE L'IMAGE, ET NON SON SYSTÈME DE FICHIERS.
Un `RUN rm` qui efface un secret à l'étape suivante laisse la couche qui le
portait intacte : le fichier a disparu de la vue finale, et il voyage toujours
avec l'image. Chercher dans le conteneur ne verrait rien, et déclarerait propre
une image qui ne l'est pas. `docker save` rend TOUTES les couches, et c'est la
seule lecture qui réponde à la question posée.

POURQUOI LE SEUIL DE TAILLE EST LU SUR LA MACHINE. Il a été mesuré par le lab,
sur une construction de référence faite au moment du `run`. Une taille écrite en
dur ici périmerait à la première mise à jour de l'image de base, et le lab se
mettrait à refuser du travail juste.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, ce qui permet de lire le relevé du lab dans
`/root`.
"""

from __future__ import annotations

import json
import re

import pytest

from conftest import fuites_dans_l_image, lab_host, message

TAG = "premiere-livraison:1.0"
DEPOT = "/opt/lab-premiere-livraison"
ETAT = "/root/.lab-premiere-livraison-state.json"
DIGEST_CONSIGNE = f"{DEPOT}/digest.txt"
REGISTRE = "127.0.0.1:5000"
DEPOT_DANS_IMAGE = "/opt/app/donnees"

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui les
    lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier.
    """
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def releve(host) -> dict:
    """Ce que le lab a mesuré au moment du `run` : le seuil, et les deux tirages.

    Il vit dans `/root`, en 0600. Les contrôles le lisent parce qu'ils sont
    élevés ; l'apprenant, lui, n'a pas à le lire pour réussir, et l'énoncé ne le
    lui demande pas.
    """
    lu = host.run("cat %s", ETAT)
    if lu.rc != 0:
        pytest.fail(message(
            en=f"the lab's own measurement is missing from `{ETAT}`. It is "
               "taken during `dsoxlab run`: replay it.",
            fr=f"la mesure que le lab a prise manque dans `{ETAT}`. Elle est "
               "faite pendant `dsoxlab run` : rejouez-le.",
        ))
    return json.loads(lu.stdout)


def test_l_image_repond_sans_option_d_identite(host, releve) -> None:
    """La livraison doit fonctionner telle quelle, et c'est le premier devoir.

    SANS OPTION D'IDENTITÉ, parce qu'une image qui n'est exécutable qu'avec un
    `--user` choisi par l'appelant n'est pas livrable : celui qui la reçoit ne
    connaît pas ce détail, et une image qui exige une option pour fonctionner
    est une image qui ne fonctionne pas.

    La réponse doit porter la donnée de la dépendance, ce qui prouve que la
    dépendance est bien entrée dans l'image. Une image qui démarre mais ne
    trouve pas ses données répond son propre code d'erreur, pas la valeur.
    """
    _image_existe(host)
    res = host.run("docker run --rm %s", TAG)
    attendu = f"inventaire={releve['metier']}"
    assert attendu in res.stdout, message(
        en=f"`docker run --rm {TAG}` does not serve the business value.\n"
           f"  what came back: {(res.stdout + res.stderr).strip()[:300] or '(nothing)'}\n"
           f"  expected      : {attendu}\n"
           "The image is run with no identity option, as whoever receives it "
           "would run it.",
        fr=f"`docker run --rm {TAG}` ne rend pas la valeur métier.\n"
           f"  ce qui revient : {(res.stdout + res.stderr).strip()[:300] or '(rien)'}\n"
           f"  attendu        : {attendu}\n"
           "L'image est lancée sans option d'identité, comme la lancerait celui "
           "qui la reçoit.",
    )


def test_l_image_tourne_sous_un_uid_non_nul_proprietaire_de_ses_donnees(
    host,
) -> None:
    """Deux faits liés : qui exécute, et à qui appartiennent les données.

    UN UID NUMÉRIQUE, et non un nom. Un nom d'utilisateur n'a de sens que pour
    l'image qui le définit : il se résout dans son `/etc/passwd`, qui n'existe
    pas pour l'orchestrateur ni pour un contrôle d'admission. L'UID numérique
    est la seule forme qu'un tiers peut vérifier, et c'est celle qu'exigent les
    politiques de sécurité qui refusent `runAsUser: 0`.

    ET LES DONNÉES DOIVENT LUI APPARTENIR, sans être inscriptibles par tous.
    Déclarer un utilisateur non root et lui laisser un répertoire qu'il ne peut
    pas écrire livre une image qui échoue à la première écriture ; le rendre
    inscriptible par tous règle le symptôme en annulant le bénéfice.
    """
    _image_existe(host)
    res = host.run("docker image inspect %s --format %s", TAG, "{{.Config.User}}")
    declare = res.stdout.strip()
    assert declare, message(
        en=f"`{TAG}` declares no user: it therefore runs as root.\n"
           "An image that runs as root is refused by any admission policy worth "
           "the name.",
        fr=f"`{TAG}` ne déclare aucun utilisateur : elle tourne donc en root.\n"
           "Une image qui tourne en root est refusée par toute politique "
           "d'admission digne de ce nom.",
    )
    uid = declare.split(":")[0]
    assert uid.isdigit(), message(
        en=f"`{TAG}` declares the user `{declare}`, which is not a numeric "
           "UID.\n"
           "A user name only means something to the image that defines it: it "
           "resolves in its own `/etc/passwd`, which an orchestrator does not "
           "read.",
        fr=f"`{TAG}` déclare l'utilisateur `{declare}`, qui n'est pas un UID "
           "numérique.\n"
           "Un nom d'utilisateur n'a de sens que pour l'image qui le définit : "
           "il se résout dans son propre `/etc/passwd`, qu'un orchestrateur ne "
           "lit pas.",
    )
    assert int(uid) != 0, message(
        en=f"`{TAG}` declares UID 0, which is root.",
        fr=f"`{TAG}` déclare l'UID 0, c'est-à-dire root.",
    )

    # Les droits sont lus DANS l'image, en écrasant l'entrée pour obtenir un
    # shell : c'est le seul endroit où la question a un sens.
    lu = host.run(
        "docker run --rm --entrypoint sh --user 0 %s -c %s",
        TAG,
        f"stat -c '%u %a' {DEPOT_DANS_IMAGE}",
    )
    assert lu.rc == 0 and lu.stdout.split(), message(
        en=f"the `{DEPOT_DANS_IMAGE}` directory cannot be read in the image.\n"
           f"  {(lu.stdout + lu.stderr).strip()[:200]}\n"
           "The dependency is expected there: that is where the application "
           "reads it.",
        fr=f"le répertoire `{DEPOT_DANS_IMAGE}` ne peut pas être lu dans "
           f"l'image.\n  {(lu.stdout + lu.stderr).strip()[:200]}\n"
           "La dépendance y est attendue : c'est là que l'application la lit.",
    )
    proprietaire, droits = lu.stdout.split()[:2]
    assert proprietaire == uid, message(
        en=f"`{DEPOT_DANS_IMAGE}` belongs to UID {proprietaire}, not to "
           f"{uid}, the one the image declares.\n"
           "Declaring a non-root user and leaving them a directory they do not "
           "own delivers an image that fails on its first write.",
        fr=f"`{DEPOT_DANS_IMAGE}` appartient à l'UID {proprietaire}, et non à "
           f"{uid}, celui que l'image déclare.\n"
           "Déclarer un utilisateur non root et lui laisser un répertoire qui "
           "ne lui appartient pas livre une image qui échoue à sa première "
           "écriture.",
    )
    assert not int(droits, 8) & 0o002, message(
        en=f"`{DEPOT_DANS_IMAGE}` is world-writable (mode {droits}).\n"
           "Making it writable by everyone fixes the symptom by cancelling the "
           "benefit of a non-root user.",
        fr=f"`{DEPOT_DANS_IMAGE}` est inscriptible par tous (mode {droits}).\n"
           "Le rendre inscriptible par tous règle le symptôme en annulant le "
           "bénéfice d'un utilisateur non root.",
    )


def test_ni_le_jeton_ni_le_travail_ne_survivent_dans_une_couche(
    host, releve
) -> None:
    """L'EXIGENCE CRITIQUE, et elle se mesure dans l'archive, pas dans la vue.

    Un `RUN rm` qui efface un secret à l'étape suivante laisse intacte la couche
    qui le portait : le fichier a disparu de la vue finale, et il voyage
    toujours avec l'image. Chercher dans le conteneur ne verrait rien, et
    déclarerait propre une image qui ne l'est pas.

    ON NE PEUT PAS SE CONTENTER D'UN `grep` SUR LE FLUX, et c'est une mesure
    qui le dit, pas une préférence. Le 2026-11-02, sur Docker 29.9.2 avec le
    magasin containerd, `docker save` écrit une disposition OCI dont les
    couches sont des blobs GZIP : un `docker save | grep -a -c <jeton>` rend
    **0** sur une image portant le jeton en clair dans une couche. Ce contrôle
    était donc aveugle, et il n'avait jamais échoué pour la bonne raison.
    `fuites_dans_l_image` ouvre et décompresse chaque couche.

    On y cherche la VALEUR du jeton, et non le nom du fichier : renommer le
    fichier ne change rien au fait que le secret voyage.

    Le répertoire de travail est cherché par le nom de ses fichiers, qui est
    propre au lab : il n'a aucune raison d'apparaître dans une image, et sa
    présence dit qu'on a livré son répertoire de travail.
    """
    _image_existe(host)
    jeton = releve["jeton"]
    assert jeton, message(
        en="the lab's own measurement carries no token. It is taken during `dsoxlab run`: replay it.",
        fr="la mesure prise par le lab ne porte pas de jeton. Elle est faite pendant `dsoxlab run` : rejouez-le.",
    )

    # PAS un `docker save | grep`, qui est AVEUGLE : les couches sont des blobs
    # GZIP et le texte n'y est pas lisible. Mesuré, ce contrôle rendait 0 sur
    # une image portant le jeton en clair. Voir `fuites_dans_l_image`.
    surfaces = fuites_dans_l_image(host, TAG, jeton)
    assert not surfaces, message(
        en="the private repository token is present in the image, which "
           "`docker save | grep` could never see:\n"
           + "\n".join(f"  {s}" for s in surfaces) + "\n"
           "A `RUN rm` at a later step does not remove it: the layer that "
           "carried it travels with the image. A secret delivered in an image "
           "is a published secret, and no total makes up for it.",
        fr="le jeton du dépôt privé est présent dans l'image, là où un "
           "`docker save | grep` ne pouvait pas le voir :\n"
           + "\n".join(f"  {s}" for s in surfaces) + "\n"
           "Un `RUN rm` à une étape ultérieure ne l'enlève pas : la couche qui "
           "le portait voyage avec l'image. Un secret livré dans une image est "
           "un secret publié, et aucun total ne le compense.",
    )

    livres = fuites_dans_l_image(host, TAG, "extrait-1.bin")
    assert not livres, message(
        en="the working directory was delivered in the image:\n"
           + "\n".join(f"  {s}" for s in livres) + "\n"
           "Work files have no reason to be in an image: they make it heavier "
           "for everyone who pulls it, forever.",
        fr="le répertoire de travail a été livré dans l'image :\n"
           + "\n".join(f"  {s}" for s in livres) + "\n"
           "Des fichiers de travail n'ont aucune raison d'être dans une image : "
           "ils l'alourdissent pour tous ceux qui la tirent, définitivement.",
    )


def test_la_taille_reste_sous_le_seuil_mesure_par_le_lab(host, releve) -> None:
    """Le seuil vient d'une construction de référence faite sur CETTE machine.

    Il n'est pas écrit dans ce test, et c'est une décision : une taille en dur
    périme à la première mise à jour de l'image de base, et le lab se mettrait
    alors à refuser du travail juste. Le `run` construit une référence, relève
    sa taille réelle, et consigne le seuil.

    La marge est large à dessein. L'épreuve mesure « n'a pas livré ce qui n'a
    rien à faire dans une image », et non « a optimisé au mégaoctet », qui est
    le sujet d'une autre épreuve du parcours.
    """
    _image_existe(host)
    res = host.run("docker image inspect %s --format %s", TAG, "{{.Size}}")
    taille = int(res.stdout.strip())
    seuil = int(releve["seuil_octets"])
    reference = int(releve["reference_octets"])
    assert taille <= seuil, message(
        en=f"the image is above the threshold this lab measured on this "
           f"machine.\n"
           f"  your image: {taille / 1e6:.1f} MB\n"
           f"  threshold : {seuil / 1e6:.1f} MB\n"
           f"  reference : {reference / 1e6:.1f} MB for the same application\n"
           "The gap is not about optimisation: it is the size of what was "
           "delivered and had no reason to be.",
        fr=f"l'image dépasse le seuil que ce lab a mesuré sur cette machine.\n"
           f"  votre image : {taille / 1e6:.1f} Mo\n"
           f"  seuil       : {seuil / 1e6:.1f} Mo\n"
           f"  référence   : {reference / 1e6:.1f} Mo pour la même application\n"
           "L'écart n'est pas une affaire d'optimisation : c'est la taille de "
           "ce qui a été livré sans avoir de raison de l'être.",
    )


def test_l_image_est_publiee_et_son_digest_consigne_est_celui_servi(
    host, releve,
) -> None:
    """Publier n'est pas construire, et un digest se vérifie contre le registre.

    LE DIGEST EST DEMANDÉ AU REGISTRE, et comparé à celui que l'apprenant a
    consigné. C'est ce qui distingue une livraison d'une construction : le
    digest est l'identité que le registre sert, la seule qu'un tiers puisse
    exiger, et la seule qui ne mente pas sur ce qu'il recevra.

    Un tag, lui, se réécrit : deux `push` du même tag servent deux images
    différentes, et c'est précisément ce que le digest empêche.
    """
    lu = host.run("cat %s", DIGEST_CONSIGNE)
    assert lu.rc == 0, message(
        en=f"the file `{DIGEST_CONSIGNE}` does not exist. The brief asks for "
           "the digest the registry serves to be recorded there, on one line.",
        fr=f"le fichier `{DIGEST_CONSIGNE}` n'existe pas. L'énoncé demande d'y "
           "consigner, sur une ligne, le digest que le registre sert.",
    )
    consigne = lu.stdout.strip()
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", consigne), message(
        en=f"what is recorded is not a digest.\n  read: {consigne[:120] or '(empty)'}\n"
           "A digest is written `sha256:` followed by sixty-four hexadecimal "
           "characters.",
        fr=f"ce qui est consigné n'est pas un digest.\n"
           f"  lu : {consigne[:120] or '(vide)'}\n"
           "Un digest s'écrit `sha256:` suivi de soixante-quatre caractères "
           "hexadécimaux.",
    )

    # Le digest que le registre SERT, demandé à son API. L'entête
    # `Docker-Content-Digest` est la réponse faisant foi, et les deux types de
    # manifeste sont acceptés : une image peut être poussée seule ou dans un
    # index.
    accept = (
        "application/vnd.oci.image.index.v1+json,"
        "application/vnd.oci.image.manifest.v1+json,"
        "application/vnd.docker.distribution.manifest.list.v2+json,"
        "application/vnd.docker.distribution.manifest.v2+json"
    )
    nom, version = TAG.split(":")
    tete = host.run(
        "curl -sS -I -H %s %s",
        f"Accept: {accept}",
        f"http://{REGISTRE}/v2/{nom}/manifests/{version}",
    )
    servi = ""
    for ligne in (tete.stdout + tete.stderr).splitlines():
        trouve = re.search(r"Docker-Content-Digest:\s*(sha256:[0-9a-f]{64})",
                           ligne, re.IGNORECASE)
        if trouve:
            servi = trouve.group(1)
            break
    assert servi, message(
        en=f"the lab's registry does not serve `{TAG}`.\n"
           f"  {(tete.stdout + tete.stderr).strip()[:300] or '(no answer)'}\n"
           "Building is not publishing: the image has to be tagged for the "
           "registry and pushed to it.",
        fr=f"le registre du lab ne sert pas `{TAG}`.\n"
           f"  {(tete.stdout + tete.stderr).strip()[:300] or '(aucune réponse)'}\n"
           "Construire n'est pas publier : l'image doit être étiquetée pour le "
           "registre, puis poussée.",
    )
    assert consigne == servi, message(
        en=f"the recorded digest is not the one the registry serves.\n"
           f"  recorded: {consigne}\n"
           f"  served  : {servi}\n"
           "A tag can be rewritten; a digest cannot. Recording the wrong one "
           "means whoever pulls it gets something other than what was "
           "announced.",
        fr=f"le digest consigné n'est pas celui que le registre sert.\n"
           f"  consigné : {consigne}\n"
           f"  servi    : {servi}\n"
           "Un tag se réécrit, un digest non. En consigner un autre, c'est "
           "livrer à qui le tire autre chose que ce qui a été annoncé.",
    )

    # ET LE DIGEST SE TIRE, parce qu'un tiers ne compare pas des chaînes.
    #
    # Comparer le digest consigné à celui que le registre sert prouve que
    # l'apprenant a recopié le bon, et rien de plus. La fiche promet autre
    # chose : que le digest soit « la seule identité qu'un tiers puisse
    # exiger ». On joue donc le geste du destinataire, pour de vrai : tirer par
    # le digest, lancer sans option d'identité, et attendre la valeur métier.
    #
    # LE MÉNAGE EST DANS UN `finally` : ce tirage crée une référence locale de
    # plus, et le cycle de validation vérifie que le moteur est rendu intact.
    # Un contrôle qui laisserait son image derrière lui ferait échouer le lab
    # sur sa propre trace.
    par_digest = f"{REGISTRE}/{TAG.split(':')[0]}@{consigne}"
    try:
        tire = host.run("docker pull %s", par_digest)
        assert tire.rc == 0, message(
            en=f"the image cannot be pulled by its digest.\n"
               f"  reference: {par_digest}\n"
               f"  {(tire.stdout + tire.stderr).strip()[:300] or '(no answer)'}\n"
               "A digest that resolves to nothing is not an identity.",
            fr=f"l'image ne se tire pas par son digest.\n"
               f"  référence : {par_digest}\n"
               f"  {(tire.stdout + tire.stderr).strip()[:300] or '(aucune réponse)'}\n"
               "Un digest qui ne ramène rien n'est pas une identité.",
        )
        rendu = host.run("docker run --rm %s", par_digest)
        attendu = f"inventaire={releve['metier']}"
        assert attendu in rendu.stdout, message(
            en=f"the image pulled by digest does not serve the business value.\n"
               f"  what came back: {(rendu.stdout + rendu.stderr).strip()[:300] or '(nothing)'}\n"
               f"  expected      : {attendu}\n"
               "This is what whoever receives the delivery does: pull by "
               "digest, run with no option. What they get is what counts.",
            fr=f"l'image tirée par son digest ne rend pas la valeur métier.\n"
               f"  ce qui revient : {(rendu.stdout + rendu.stderr).strip()[:300] or '(rien)'}\n"
               f"  attendu        : {attendu}\n"
               "C'est le geste de celui qui reçoit la livraison : tirer par le "
               "digest, lancer sans option. Ce qu'il obtient est ce qui compte.",
        )
    finally:
        host.run("docker image rm -f %s", par_digest)


def _image_existe(host) -> None:
    """Le préalable de chaque contrôle : l'image demandée a bien été construite.

    Le message nomme le tag attendu, parce que c'est une information d'état et
    non un indice de résolution : l'énoncé le donne déjà.
    """
    res = host.run("docker image inspect %s", TAG)
    if res.rc != 0:
        pytest.fail(message(
            en=f"no image named `{TAG}` exists. The brief names the tag to "
               "produce, and the checks look for it by name.",
            fr=f"aucune image nommée `{TAG}` n'existe. L'énoncé nomme le tag à "
               "produire, et les contrôles le cherchent nommément.",
        ))
