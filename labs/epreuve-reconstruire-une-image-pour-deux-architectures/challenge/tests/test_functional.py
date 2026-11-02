"""Tests fonctionnels de l'épreuve d'enchaînement : cinq contrôles de poids égal.

C'EST L'ÉPREUVE D'ENCHAÎNEMENT du parcours des images, et c'est ce qui la
justifie malgré un recouvrement assumé avec quatre labs d'entraînement. Chacun
de ces quatre mesure un geste ; aucun ne mesure qu'une SEULE image les réunit
tous. Or une image légère dont le secret a fui ne vaut rien, et une image propre
qui ne sert qu'une architecture ne se déploie pas.

L'EXIGENCE CRITIQUE est le contrôle 3 : le jeton dans l'historique. Un
`--build-arg` l'y laisse, et quiconque tire l'image le relit. Mesuré sur le banc
de cette épreuve : deux occurrences avec `--build-arg`, zéro avec
`--mount=type=secret`, dans l'historique comme dans les couches.

LES CONTRÔLES PORTENT SUR L'IMAGE TIRÉE DU REGISTRE, et non sur une image
locale. C'est une décision : `buildx` avec une sortie de type registre ne laisse
RIEN en local, donc exiger une image locale punirait la façon normale de
publier. Et c'est plus juste : on mesure ce qui est livré, pas ce qui est resté
sur le poste.

UN FAIT MESURÉ SUR L'INDEX. Il porte quatre manifestes et non deux : `buildx` y
ajoute ses attestations de provenance, qui se présentent comme des plateformes
`unknown`. Le contrôle cherche donc amd64 et arm64 PARMI les manifestes, au lieu
d'en exiger exactement deux. Un contrôle qui compterait les entrées refuserait
le résultat normal de l'outil.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, ce qui permet de lire le relevé dans `/root`.
"""

from __future__ import annotations

import json
import re
import uuid

import pytest

from conftest import lab_host, message

DEPOT = "deux-arch"
VERSION = "1.0"
REGISTRE = "127.0.0.1:15002"
REFERENCE = f"{REGISTRE}/{DEPOT}:{VERSION}"
ATELIER = "/opt/lab-deux-arch"
ETAT = "/root/.lab-deux-arch-state.json"
DIGEST_CONSIGNE = f"{ATELIER}/digest.txt"

# Les deux architectures que l'index doit porter, et qui doivent s'exécuter.
ARCHITECTURES = ("amd64", "arm64")

# Ce qui n'a rien à faire dans une image livrée : le compilateur, et le
# gestionnaire de paquets qui a servi à l'installer.
INTRUS = {
    "gcc": "le compilateur",
    "apk": "le gestionnaire de paquets de l'image de base",
}

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
    """Ce que le lab a mesuré au moment du `run` : le seuil, le jeton, la dépendance.

    Le seuil vient d'une construction de référence multi-étapes faite sur CETTE
    machine. Une taille écrite en dur dans ce fichier périmerait à la première
    mise à jour de l'image de base, et le lab se mettrait à refuser du travail
    juste.
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


@pytest.fixture(scope="module")
def index(host) -> dict:
    """L'index que le registre sert, et le digest qu'il annonce.

    Relevé une seule fois pour tout le fichier : chaque contrôle en a besoin, et
    l'interroger cinq fois n'apprendrait rien de plus.
    """
    accept = (
        "application/vnd.oci.image.index.v1+json,"
        "application/vnd.docker.distribution.manifest.list.v2+json,"
        "application/vnd.oci.image.manifest.v1+json,"
        "application/vnd.docker.distribution.manifest.v2+json"
    )
    url = f"http://{REGISTRE}/v2/{DEPOT}/manifests/{VERSION}"
    tete = host.run("curl -sS -I -H %s %s", f"Accept: {accept}", url)
    servi = ""
    for ligne in (tete.stdout + tete.stderr).splitlines():
        trouve = re.search(r"Docker-Content-Digest:\s*(sha256:[0-9a-f]{64})",
                           ligne, re.IGNORECASE)
        if trouve:
            servi = trouve.group(1)
            break
    corps = host.run("curl -sS -H %s %s", f"Accept: {accept}", url)
    try:
        charge = json.loads(corps.stdout)
    except json.JSONDecodeError:
        charge = {}
    if not servi or not charge:
        pytest.fail(message(
            en=f"the lab's registry does not serve `{DEPOT}:{VERSION}`.\n"
               f"  {(corps.stdout + corps.stderr).strip()[:300] or '(no answer)'}\n"
               "Building is not publishing: the image has to be pushed to the "
               "registry, and the brief names it.",
            fr=f"le registre du lab ne sert pas `{DEPOT}:{VERSION}`.\n"
               f"  {(corps.stdout + corps.stderr).strip()[:300] or '(aucune réponse)'}\n"
               "Construire n'est pas publier : l'image doit être poussée dans "
               "le registre, et l'énoncé le nomme.",
        ))
    return {"digest": servi, "contenu": charge}


def test_l_image_livree_ne_porte_plus_le_compilateur(host, releve) -> None:
    """Le multi-étapes, et il se mesure DANS l'image livrée.

    Ni le compilateur ni le gestionnaire de paquets qui l'a installé n'ont leur
    place dans une image qu'on publie : ils ne servent qu'à la construire, et
    ils voyagent ensuite chez tous ceux qui la tirent.

    ET LA CHARGE MÉTIER RÉUSSIT. Retirer le compilateur est facile ; le retirer
    en gardant un binaire qui fonctionne est le geste du multi-étapes. Un
    binaire lié dynamiquement contre des bibliothèques restées dans l'étape de
    construction ne démarre pas, et c'est l'erreur classique.
    """
    _tire(host)
    # LES FICHIERS DE L'IMAGE SONT LISTÉS, et non interrogés par un shell.
    #
    # Un premier jet lançait `command -v gcc` dans l'image : cela exige un
    # shell, donc une image qui en porte un. Or la bonne réponse à cette épreuve
    # est une image sans système du tout, puisque le binaire est statique : il
    # n'y aurait alors ni shell pour répondre, ni rien à chercher.
    #
    # `docker export` rend le système de fichiers de l'image, et le lister ne
    # dépend d'aucun binaire qui s'y trouve.
    fichiers = _fichiers(host)
    for binaire, quoi in INTRUS.items():
        presents = [f for f in fichiers if f.rsplit("/", 1)[-1] == binaire]
        assert not presents, message(
            en=f"`{binaire}` is still in the published image ({quoi}):\n"
               + "\n".join(f"  {f}" for f in presents[:5]) + "\n"
               "It only served to build: it then travels to everyone who pulls "
               "the image.",
            fr=f"`{binaire}` est encore dans l'image publiée ({quoi}) :\n"
               + "\n".join(f"  {f}" for f in presents[:5]) + "\n"
               "Il n'a servi qu'à construire : il voyage ensuite chez tous ceux "
               "qui tirent l'image.",
        )

    rendu = host.run("docker run --rm %s", REFERENCE)
    assert "charge=ok" in rendu.stdout, message(
        en=f"the published image does not run its workload.\n"
           f"  what came back: "
           f"{(rendu.stdout + rendu.stderr).strip()[:300] or '(nothing)'}\n"
           "A binary linked dynamically against libraries left in the build "
           "stage does not start: that is the classic multi-stage mistake.",
        fr=f"l'image publiée n'exécute pas sa charge métier.\n"
           f"  ce qui revient : "
           f"{(rendu.stdout + rendu.stderr).strip()[:300] or '(rien)'}\n"
           "Un binaire lié dynamiquement contre des bibliothèques restées dans "
           "l'étape de construction ne démarre pas : c'est l'erreur classique "
           "du multi-étapes.",
    )


def test_la_taille_reste_sous_le_seuil_mesure(host, releve) -> None:
    """Le seuil vient d'une construction de référence faite sur CETTE machine.

    Il n'est pas écrit dans ce test : une taille en dur périmerait à la première
    mise à jour de l'image de base. Le `run` construit une référence
    multi-étapes, relève sa taille réelle, et consigne le seuil.

    La marge est large. L'épreuve mesure « n'a pas livré son compilateur », et
    non « a optimisé au mégaoctet », qui est le sujet d'un lab d'entraînement.
    """
    _tire(host)
    res = host.run("docker image inspect %s --format %s", REFERENCE, "{{.Size}}")
    taille = int(res.stdout.strip())
    seuil = int(releve["seuil_octets"])
    reference = int(releve["reference_octets"])
    livree = int(releve["livree_octets"])
    assert taille <= seuil, message(
        en=f"the published image is above the threshold this lab measured.\n"
           f"  your image: {taille / 1e6:.1f} MB\n"
           f"  threshold : {seuil / 1e6:.1f} MB\n"
           f"  reference : {reference / 1e6:.1f} MB for the same workload\n"
           f"  delivered : {livree / 1e6:.1f} MB, the one you started from\n"
           "The gap is the size of what was shipped without any reason to be.",
        fr=f"l'image publiée dépasse le seuil que ce lab a mesuré.\n"
           f"  votre image : {taille / 1e6:.1f} Mo\n"
           f"  seuil       : {seuil / 1e6:.1f} Mo\n"
           f"  référence   : {reference / 1e6:.1f} Mo pour la même charge\n"
           f"  livrée      : {livree / 1e6:.1f} Mo, celle dont vous partiez\n"
           "L'écart est la taille de ce qui a été livré sans raison de l'être.",
    )


def test_le_jeton_n_est_ni_dans_l_historique_ni_dans_les_couches(
    host, releve
) -> None:
    """L'EXIGENCE CRITIQUE, et elle se mesure à DEUX endroits distincts.

    L'HISTORIQUE d'abord. Un `--build-arg` y laisse la valeur, et quiconque tire
    l'image la relit avec `docker history --no-trunc`. Mesuré sur le banc de
    cette épreuve : deux occurrences. C'est la fuite la plus discrète du métier,
    parce que l'image elle-même ne contient rien de suspect.

    LES COUCHES ensuite, parce qu'un secret peut aussi avoir été écrit dans un
    fichier puis effacé : la couche qui le portait voyage toujours.

    ET LA DÉPENDANCE DOIT ÊTRE LÀ. Retirer le jeton sans s'en servir donne une
    image propre et inutile : le contrôle compare la dépendance produite à celle
    que le lab attend, et elle ne peut être juste que si le jeton a servi.
    """
    _tire(host)
    jeton = releve["jeton"]
    assert jeton, message(
        en="the lab's own measurement carries no token. It is taken during `dsoxlab run`: replay it.",
        fr="la mesure prise par le lab ne porte pas de jeton. Elle est faite pendant `dsoxlab run` : rejouez-le.",
    )

    historique = host.run(
        "docker history --no-trunc %s | grep -c %s || true", REFERENCE, jeton
    )
    compte = historique.stdout.strip() or "0"
    assert compte == "0", message(
        en=f"the token is readable in the image's history ({compte} "
           "occurrence(s)).\n"
           "A `--build-arg` leaves its value there, and anyone who pulls the "
           "image reads it back with `docker history --no-trunc`. The image "
           "itself looks clean, which is what makes this leak the most discreet "
           "of the trade. No total makes up for it.",
        fr=f"le jeton se lit dans l'historique de l'image ({compte} "
           "occurrence(s)).\n"
           "Un `--build-arg` y laisse sa valeur, et quiconque tire l'image la "
           "relit avec `docker history --no-trunc`. L'image elle-même a l'air "
           "propre, ce qui fait de cette fuite la plus discrète du métier. "
           "Aucun total ne la compense.",
    )

    couches = host.run("docker save %s | grep -a -c %s || true", REFERENCE, jeton)
    dans_couches = couches.stdout.strip() or "0"
    assert dans_couches == "0", message(
        en=f"the token is present in the image's layers ({dans_couches} "
           "occurrence(s)).\n"
           "Writing it to a file then deleting it does not help: the layer that "
           "carried it travels with the image.",
        fr=f"le jeton est présent dans les couches de l'image ({dans_couches} "
           "occurrence(s)).\n"
           "L'écrire dans un fichier puis l'effacer n'y change rien : la couche "
           "qui le portait voyage avec l'image.",
    )

    attendue = releve["dependance_attendue"]
    assert attendue, message(
        en="the lab's own measurement carries no expected dependency. It is taken during `dsoxlab run`: replay it.",
        fr="la mesure prise par le lab ne porte pas la dépendance attendue. Elle est faite pendant `dsoxlab run` : rejouez-le.",
    )
    rendu = host.run("docker run --rm %s", REFERENCE)
    assert f"dependance={attendue}" in rendu.stdout, message(
        en=f"the private dependency is missing or wrong in the image.\n"
           f"  what came back: {rendu.stdout.strip()[:300] or '(nothing)'}\n"
           f"  expected      : dependance={attendue}\n"
           "Removing the token without using it gives a clean, useless image.",
        fr=f"la dépendance privée manque ou est fausse dans l'image.\n"
           f"  ce qui revient : {rendu.stdout.strip()[:300] or '(rien)'}\n"
           f"  attendu        : dependance={attendue}\n"
           "Retirer le jeton sans s'en servir donne une image propre et "
           "inutile.",
    )


def test_l_index_porte_les_deux_architectures_et_chacune_s_execute(
    host, index
) -> None:
    """Publier deux architectures, et prouver que les deux marchent.

    LE CONTRÔLE CHERCHE amd64 ET arm64 PARMI les manifestes, sans en exiger un
    nombre : mesuré sur le banc de cette épreuve, `buildx` ajoute à l'index ses
    attestations de provenance, qui se présentent comme des plateformes
    `unknown`. Un contrôle qui compterait les entrées refuserait le résultat
    normal de l'outil.

    ET CHACUNE S'EXÉCUTE. Un index qui déclare une plateforme sans que l'image
    correspondante démarre est pire qu'un index à une seule entrée : il promet
    un déploiement qui échouera chez celui qui s'y fie. L'émulation est posée par
    le lab, donc l'exécution arm64 est mesurable sur cette machine amd64.
    """
    manifestes = index["contenu"].get("manifests")
    assert manifestes, message(
        en="the registry serves a single-image manifest, not an index.\n"
           f"  media type: {index['contenu'].get('mediaType', '(unknown)')}\n"
           "One image cannot carry two architectures: an index is what points "
           "to one image per platform.",
        fr="le registre sert un manifeste d'image unique, et non un index.\n"
           f"  type de média : "
           f"{index['contenu'].get('mediaType', '(inconnu)')}\n"
           "Une image seule ne peut pas porter deux architectures : c'est un "
           "index qui désigne une image par plateforme.",
    )
    trouvees = {
        (m.get("platform") or {}).get("architecture")
        for m in manifestes
        if (m.get("platform") or {}).get("os") == "linux"
    }
    manquantes = [a for a in ARCHITECTURES if a not in trouvees]
    assert not manquantes, message(
        en=f"the index does not carry every expected architecture.\n"
           f"  missing : {', '.join(manquantes)}\n"
           f"  present : {', '.join(sorted(a for a in trouvees if a)) or '(none)'}",
        fr=f"l'index ne porte pas toutes les architectures attendues.\n"
           f"  il manque : {', '.join(manquantes)}\n"
           f"  présentes : "
           f"{', '.join(sorted(a for a in trouvees if a)) or '(aucune)'}",
    )

    for arch in ARCHITECTURES:
        # LE TIRAGE PAR PLATEFORME EST OBLIGATOIRE, et c'est une mesure qui
        # l'impose : `docker run --platform linux/arm64` n'honore PAS la
        # plateforme demandée si une image locale correspond déjà à la
        # référence. Le moteur annonce « Image is up to date » et exécute celle
        # qu'il a, en rendant `architecture=amd64` pour un `--platform
        # linux/arm64`. Sans ce tirage, le contrôle validerait un index dont
        # une variante n'a jamais été construite.
        tirage = host.run(
            "docker pull -q --platform %s %s", f"linux/{arch}", REFERENCE
        )
        assert tirage.rc == 0, message(
            en=f"the `linux/{arch}` variant cannot be pulled from the "
               f"registry.\n  {tirage.stderr.strip()[:300]}\n"
               "The index declares that platform: the registry must serve its "
               "image.",
            fr=f"la variante `linux/{arch}` ne peut pas être tirée du "
               f"registre.\n  {tirage.stderr.strip()[:300]}\n"
               "L'index déclare cette plateforme : le registre doit en servir "
               "l'image.",
        )
        rendu = host.run(
            "docker run --rm --platform %s %s", f"linux/{arch}", REFERENCE
        )
        sortie = rendu.stdout + rendu.stderr
        assert f"architecture={arch}" in sortie, message(
            en=f"the `linux/{arch}` image does not run, or was not built for "
               f"that architecture.\n"
               f"  what came back: {sortie.strip()[:300] or '(nothing)'}\n"
               "An index that declares a platform whose image does not start is "
               "worse than a single-platform index: it promises a deployment "
               "that will fail for whoever relies on it.",
            fr=f"l'image `linux/{arch}` ne s'exécute pas, ou n'a pas été "
               f"construite pour cette architecture.\n"
               f"  ce qui revient : {sortie.strip()[:300] or '(rien)'}\n"
               "Un index qui déclare une plateforme dont l'image ne démarre pas "
               "est pire qu'un index à une seule entrée : il promet un "
               "déploiement qui échouera chez celui qui s'y fie.",
        )
        assert "charge=ok" in sortie, message(
            en=f"the `linux/{arch}` image starts without running its workload.\n"
               f"  what came back: {sortie.strip()[:300] or '(nothing)'}",
            fr=f"l'image `linux/{arch}` démarre sans exécuter sa charge "
               f"métier.\n"
               f"  ce qui revient : {sortie.strip()[:300] or '(rien)'}",
        )


def test_le_digest_consigne_est_celui_de_l_index(host, index) -> None:
    """Le digest de l'INDEX, et non celui d'une de ses images.

    C'est la distinction que ce contrôle existe pour mesurer. L'index a son
    propre digest, et c'est lui qu'on épingle dans un déploiement : il désigne
    les deux architectures à la fois, et laisse le moteur du destinataire
    choisir la sienne. Le digest d'une des images désigne UNE plateforme, et un
    déploiement épinglé dessus échoue partout ailleurs.

    Le contrôle compare donc le digest consigné à celui que le registre annonce
    pour la référence, qui est celui de l'index.
    """
    lu = host.run("cat %s", DIGEST_CONSIGNE)
    assert lu.rc == 0, message(
        en=f"the file `{DIGEST_CONSIGNE}` does not exist. The brief asks for the "
           "index's digest to be recorded there, on one line.",
        fr=f"le fichier `{DIGEST_CONSIGNE}` n'existe pas. L'énoncé demande d'y "
           "consigner, sur une ligne, le digest de l'index.",
    )
    consigne = lu.stdout.strip()
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", consigne), message(
        en=f"what is recorded is not a digest.\n"
           f"  read: {consigne[:120] or '(empty)'}",
        fr=f"ce qui est consigné n'est pas un digest.\n"
           f"  lu : {consigne[:120] or '(vide)'}",
    )

    servi = index["digest"]
    if consigne != servi:
        # SI C'EST LE DIGEST D'UNE DES IMAGES, le message le dit : c'est l'erreur
        # instructive, et la nommer vaut mieux que d'annoncer une différence.
        par_plateforme = {
            m.get("digest"): (m.get("platform") or {}).get("architecture")
            for m in index["contenu"].get("manifests") or []
        }
        if consigne in par_plateforme:
            pytest.fail(message(
                en=f"the recorded digest is the one of the "
                   f"`{par_plateforme[consigne]}` image, not the index's.\n"
                   f"  recorded : {consigne}\n"
                   f"  the index: {servi}\n"
                   "The index designates both architectures at once and lets "
                   "the receiving engine pick its own. A deployment pinned on "
                   "one platform's digest fails everywhere else.",
                fr=f"le digest consigné est celui de l'image "
                   f"`{par_plateforme[consigne]}`, et non celui de l'index.\n"
                   f"  consigné : {consigne}\n"
                   f"  l'index  : {servi}\n"
                   "L'index désigne les deux architectures à la fois et laisse "
                   "le moteur du destinataire choisir la sienne. Un déploiement "
                   "épinglé sur le digest d'une plateforme échoue partout "
                   "ailleurs.",
            ))
        pytest.fail(message(
            en=f"the recorded digest is not the one the registry serves.\n"
               f"  recorded: {consigne}\n  served  : {servi}",
            fr=f"le digest consigné n'est pas celui que le registre sert.\n"
               f"  consigné : {consigne}\n  servi    : {servi}",
        ))


def _fichiers(host) -> list[str]:
    """Les chemins que l'image publiée contient, sans rien exécuter dedans.

    `docker create` puis `docker export` rendent le système de fichiers de
    l'image, et le lister ne dépend d'aucun binaire présent à l'intérieur. C'est
    la seule lecture qui fonctionne aussi bien sur une image sans système, et la
    bonne réponse à cette épreuve est justement une image sans système.

    Le conteneur est créé sous un nom unique et retiré dans un `finally` : deux
    exécutions ne doivent pas se gêner, et un objet laissé derrière ferait
    échouer la photographie du cycle de validation.
    """
    jetable = f"inventaire-{uuid.uuid4().hex[:8]}"
    try:
        cree = host.run("docker create --name %s %s", jetable, REFERENCE)
        if cree.rc != 0:
            pytest.fail(message(
                en=f"the published image's contents cannot be listed:\n"
                   f"  {cree.stderr.strip()[:200]}",
                fr=f"le contenu de l'image publiée ne peut pas être listé :\n"
                   f"  {cree.stderr.strip()[:200]}",
            ))
        liste = host.run("docker export %s | tar -t", jetable)
    finally:
        host.run("docker rm -f %s", jetable)
    return [l.strip() for l in liste.stdout.splitlines() if l.strip()]


def _fichiers(host) -> list[str]:
    """Les chemins que l'image publiée contient, sans rien exécuter dedans.

    `docker create` puis `docker export` rendent le système de fichiers de
    l'image, et le lister ne dépend d'aucun binaire présent à l'intérieur. C'est
    la seule lecture qui fonctionne aussi bien sur une image sans système, et la
    bonne réponse à cette épreuve est justement une image sans système.

    Le conteneur est créé sous un nom unique et retiré dans un `finally` : deux
    exécutions ne doivent pas se gêner, et un objet laissé derrière ferait
    échouer la photographie du cycle de validation.
    """
    jetable = f"inventaire-{uuid.uuid4().hex[:8]}"
    try:
        cree = host.run("docker create --name %s %s", jetable, REFERENCE)
        if cree.rc != 0:
            pytest.fail(message(
                en=f"the published image's contents cannot be listed:\n"
                   f"  {cree.stderr.strip()[:200]}",
                fr=f"le contenu de l'image publiée ne peut pas être listé :\n"
                   f"  {cree.stderr.strip()[:200]}",
            ))
        liste = host.run("docker export %s | tar -t", jetable)
    finally:
        host.run("docker rm -f %s", jetable)
    return [l.strip() for l in liste.stdout.splitlines() if l.strip()]


def _tire(host) -> None:
    """Tire l'image publiée, pour que les contrôles portent sur ce qui est livré.

    `buildx` avec une sortie de type registre ne laisse RIEN en local : exiger
    une image locale punirait la façon normale de publier. Le tirage est donc
    fait par le contrôle lui-même, et il échoue en nommant l'absence.
    """
    res = host.run("docker pull %s", REFERENCE)
    if res.rc != 0:
        pytest.fail(message(
            en=f"`{REFERENCE}` cannot be pulled from the lab's registry.\n"
               f"  {res.stderr.strip()[:300]}\n"
               "Building is not publishing: the brief names the repository and "
               "the version to push.",
            fr=f"`{REFERENCE}` ne peut pas être tirée du registre du lab.\n"
               f"  {res.stderr.strip()[:300]}\n"
               "Construire n'est pas publier : l'énoncé nomme le dépôt et la "
               "version à pousser.",
        ))
