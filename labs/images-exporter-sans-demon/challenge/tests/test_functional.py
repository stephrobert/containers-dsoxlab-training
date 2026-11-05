"""Quatre exigences, quatre contrôles, et chacun échoue à l'état initial.

CE QUE CE LAB MESURE, ET POURQUOI DANS CET ORDRE

Le sujet de la leçon est qu'un client de registre copie une image **sans passer
par le démon**. Quatre choses s'en déduisent, indépendantes, et chacune a son
contrôle :

1. l'archive OCI existe, au **format OCI**, et porte l'image attendue ;
2. le **démon ne l'a jamais tirée**, ce qui est le titre même de la leçon ;
3. l'image rechargée porte **son nom** et **ses couches**, et son identifiant
   local change, ce qui est normal et expliqué ;
4. l'archive arm64 porte **bien arm64**, et n'est pas l'amd64 déguisée.

CHAQUE CONTRÔLE ÉCHOUE AVANT TOUT TRAVAIL, et c'est ce qui l'autorise à noter.
Le deuxième demandait une attention particulière : « le démon n'a pas tiré
l'image » est vrai sur une machine neuve, donc vrai avant tout travail. Il est
donc conditionné à l'existence de l'archive : ce que le contrôle mesure est
« l'archive existe ET le démon n'a jamais tiré l'image », et la première moitié
échoue au départ.

CE QUE LA MESURE A IMPOSÉ, le 2026-11-05 sur Skopeo 1.22.3, Docker 29.9.2 et un
store containerd :

- l'identifiant local `.Id` CHANGE à l'aller-retour (`be265606…` devient
  `594f9501…` sur l'image de la leçon), parce qu'avec containerd cet
  identifiant est le digest du manifeste, et la conversion de format reconstruit
  le manifeste. Exiger qu'il survive serait exiger l'impossible ;
- le **digest de configuration** et les **couches**, eux, survivent ;
- les **droits** de l'archive ne sont pas notés : skopeo écrit en 0644 par
  défaut, donc l'exiger ne mesurerait rien. Le fait enseignable est le
  contraste avec `docker save`, qui écrit en 0600, et il est dans la leçon ;
- skopeo **n'exige pas** de nom de destination : une archive sans nom se produit
  sans erreur. La conséquence est au chargement, où `docker load` rend un
  identifiant nu au lieu d'un nom, et c'est là que le contrôle regarde.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, message

LAB = "images-exporter-sans-demon"
TRAVAIL = f"/opt/dsoxlab-{LAB}"
SUJET = "busybox:1.37.0-musl"
NOM_LIVRE = "livraison.test/socle:1.0"
OCI = f"{TRAVAIL}/livraison/socle-oci.tar"
DOCKER_ARCHIVE = f"{TRAVAIL}/livraison/socle-docker.tar"
ARM64 = f"{TRAVAIL}/livraison/socle-arm64.tar"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _skopeo(host, *args: str):
    """Le lanceur fourni par le lab, pour inspecter ce que l'apprenant a produit.

    Le contrôle emploie le MÊME skopeo que l'apprenant, et non celui du paquet
    de la distribution : Debian 13 livre 1.18.0, et mesurer avec une autre
    version que celle du sujet dirait autre chose que ce que l'apprenant a vu.
    """
    return host.run(f"{TRAVAIL}/skopeo " + " ".join(args))


def _archive_existe(host, chemin: str, nom_lisible: str) -> None:
    """Garde-fou commun : sans archive, aucun des contrôles n'observe rien."""
    fichier = host.file(chemin)
    assert fichier.exists and fichier.size > 0, message(
        en=f"{nom_lisible} is missing or empty at {chemin}. Produce it with the "
           f"`skopeo` launcher the lab supplies in {TRAVAIL}.",
        fr=f"{nom_lisible} est absente ou vide à {chemin}. Produisez-la avec le "
           f"lanceur `skopeo` que le lab fournit dans {TRAVAIL}.",
    )


def test_l_archive_oci_est_au_format_oci_et_porte_l_image_attendue(host):
    """Le format, et l'image qu'il contient.

    Une archive OCI se reconnaît à sa structure : un `oci-layout`, un
    `index.json`, et des `blobs/sha256/`. Un `docker save` renommé ne la
    satisfait pas, parce qu'il écrit `<id>/layer.tar` et un `manifest.json` à
    plat.

    Le contrôle lit aussi ce que l'archive CONTIENT, et non seulement sa forme :
    une archive OCI d'une autre image passerait le contrôle de format.
    """
    _archive_existe(host, OCI, "L'archive OCI")

    entrees = host.run("tar -tf %s", OCI)
    assert entrees.rc == 0, message(
        en=f"{OCI} cannot be read as a tar archive: {entrees.stderr.strip()[:200]}",
        fr=f"{OCI} n'est pas lisible comme archive tar : {entrees.stderr.strip()[:200]}",
    )
    noms = entrees.stdout.split()
    # CE CONTRÔLE NE PROUVE PAS L'EMPLOI DE SKOPEO, et il ne le prétend pas.
    #
    # Mesuré le 2026-11-05 : sur ce moteur, dont le store est containerd,
    # `docker save` produit LUI AUSSI un `oci-layout` et un `index.json`. Une
    # archive de `docker save` passerait donc ce contrôle de format. C'est le
    # contrôle suivant qui l'attrape, en regardant si le démon a tiré l'image,
    # et c'est précisément pourquoi ils sont deux.
    #
    # Un premier message affirmait ici qu'un `docker save` écrit
    # `<id>/layer.tar` : c'est faux sur ce moteur, et la triche l'a montré.
    assert any(n.rstrip("/") == "oci-layout" for n in noms), message(
        en="The archive carries no `oci-layout`, so it is not an OCI archive. "
           "Use `oci-archive:` as the destination transport.",
        fr="L'archive ne porte pas de `oci-layout` : ce n'est donc pas une "
           "archive OCI. Employez le transport de destination `oci-archive:`.",
    )
    assert any(n.rstrip("/") == "index.json" for n in noms), message(
        en="The OCI archive carries no `index.json`, which is what names the "
           "manifests it holds.",
        fr="L'archive OCI ne porte pas d'`index.json`, qui est ce qui nomme les "
           "manifestes qu'elle contient.",
    )
    assert any(n.startswith("blobs/sha256/") for n in noms), message(
        en="The OCI archive carries no `blobs/sha256/` entry: its content is "
           "addressed by digest, and that directory is where it lives.",
        fr="L'archive OCI ne porte aucune entrée `blobs/sha256/` : son contenu "
           "est adressé par digest, et c'est là qu'il vit.",
    )

    lu = _skopeo(host, "inspect", "oci-archive:livraison/socle-oci.tar")
    assert lu.rc == 0, message(
        en=f"skopeo cannot inspect the archive: {lu.stderr.strip()[-300:]}",
        fr=f"skopeo ne peut pas inspecter l'archive : {lu.stderr.strip()[-300:]}",
    )
    decrit = json.loads(lu.stdout)
    # CE QU ON COMPARE EST LES COUCHES, et c est le seul invariant du transport.
    #
    # Mesure du 2026-11-05 : `skopeo inspect docker://` rend sous `Digest` le
    # digest de l INDEX multi-architecture, et `skopeo inspect oci-archive:`
    # celui du MANIFESTE DE PLATEFORME. Comparer les deux n a aucun sens, et
    # c est ce que ce controle faisait. Les couches compressees, elles, sont
    # identiques de part et d autre du transport.
    attendu = _couches_du_registre(host)
    assert decrit.get("Layers") == attendu, message(
        en=f"The archive holds layers {decrit.get('Layers')}, and the image to "
           f"deliver has {attendu}. The archive is well formed but holds "
           "another image.",
        fr=f"L'archive porte les couches {decrit.get('Layers')}, et l'image à "
           f"livrer a {attendu}. L'archive est bien formée mais contient une "
           "autre image.",
    )


def _couches_du_registre(host) -> list[str]:
    """Les couches compressées de l'image à livrer, lues depuis le registre.

    LUES ET NON ÉCRITES EN DUR : l'éditeur d'une image peut republier son tag,
    et un digest recopié dans un test finit par désigner autre chose que ce que
    l'apprenant tire. Ce catalogue en a l'expérience, sur l'image de skopeo
    elle-même, dont le digest a changé en deux jours.

    LES COUCHES ET NON UN DIGEST, et c'est le cycle qui l'a imposé. Mesuré le
    2026-11-05 : `skopeo inspect docker://` rend sous `Digest` le digest de
    l'INDEX multi-architecture, tandis qu'une archive rend celui de son
    MANIFESTE DE PLATEFORME. Les deux nombres ne se comparent pas. Les couches,
    elles, traversent le transport sans changer.
    """
    lu = _skopeo(host, "inspect", f"docker://{SUJET}")
    assert lu.rc == 0, message(
        en=f"The registry cannot be read to establish the reference: "
           f"{lu.stderr.strip()[-200:]} Not your fault, report it.",
        fr=f"Le registre est illisible pour établir la référence : "
           f"{lu.stderr.strip()[-200:]} Ce n'est pas votre faute, signalez-le.",
    )
    couches = json.loads(lu.stdout)["Layers"]
    assert couches, message(
        en="The registry returned no layer for the image to deliver. Not your "
           "fault, report it.",
        fr="Le registre n'a rendu aucune couche pour l'image à livrer. Ce n'est "
           "pas votre faute, signalez-le.",
    )
    return couches


def test_le_demon_n_a_jamais_tire_l_image_livree(host):
    """Le titre même de la leçon, et le contrôle qu'on ne peut pas contourner.

    Un `docker pull` suivi d'un `docker save` produit une archive, mais laisse
    l'image dans le store du démon. Mesuré le 2026-11-05 : un
    `skopeo copy docker://… oci-archive:…` laisse ce store à ZÉRO image, avant
    comme après.

    L'ARCHIVE CONDITIONNE CE CONTRÔLE, et c'est nécessaire. « Le démon n'a pas
    tiré l'image » est vrai sur une machine neuve, donc vrai avant tout travail :
    seul, ce contrôle accorderait des points pour rien. Ce qu'il mesure est donc
    « l'archive existe ET le démon ne l'a jamais tirée ».
    """
    _archive_existe(host, OCI, "L'archive OCI")

    present = host.run("docker image inspect %s", SUJET)
    assert present.rc != 0, message(
        en=f"The daemon holds {SUJET} in its local store. The archive may be "
           "correct, but it was produced by pulling the image first, which is "
           "exactly what a host without a daemon cannot do. Copy straight from "
           "the registry with `docker://` as the source transport, and remove "
           "the image the daemon pulled.",
        fr=f"Le démon détient {SUJET} dans son store local. L'archive est "
           "peut-être juste, mais elle a été produite en tirant d'abord "
           "l'image, ce qu'un hôte sans démon ne peut justement pas faire. "
           "Copiez directement depuis le registre avec `docker://` en transport "
           "de source, et retirez l'image que le démon a tirée.",
    )


def test_l_image_rechargee_porte_son_nom_et_ses_couches(host):
    """L'archive est utilisable : elle se charge, sous son nom, et c'est la bonne.

    Le nom prouve que la destination a été nommée. Une archive produite sans
    nom se charge en `Loaded image ID: sha256:…`, et l'image arrive sans nom :
    le site devrait la renommer avant de s'en servir. Mesuré : skopeo
    n'ERREUR PAS sur une destination sans nom, la conséquence n'apparaît qu'ici.

    L'identifiant local n'est pas exigé identique à celui du registre, et il ne
    peut pas l'être : avec un store containerd il vaut le digest du MANIFESTE,
    que la conversion de format reconstruit. Le lab montre donc ce qu'il vaut,
    le manifeste de l'archive chargée, au lieu d'affirmer qu'il change.

    LES COUCHES NE SE COMPARENT PAS DE CE CÔTÉ, et le commentaire plus bas dit
    pourquoi : le démon ne garde que les couches décompressées. Leur comparaison
    a lieu dans le premier contrôle, entre le registre et l'archive.
    """
    _archive_existe(host, OCI, "L'archive OCI")

    charge = host.run("docker load -i %s", OCI)
    assert charge.rc == 0, message(
        en=f"`docker load` refuses the archive: {charge.stderr.strip()[-300:]}",
        fr=f"`docker load` refuse l'archive : {charge.stderr.strip()[-300:]}",
    )
    assert "Loaded image ID:" not in charge.stdout, message(
        en=f"`docker load` answered « {charge.stdout.strip()[:90]} », that is an "
           "identifier and not a name: the archive was produced without a "
           "destination name. Name it, as in "
           f"`oci-archive:chemin.tar:{NOM_LIVRE}`.",
        fr=f"`docker load` a répondu « {charge.stdout.strip()[:90]} », soit un "
           "identifiant et non un nom : l'archive a été produite sans nom de "
           "destination. Nommez-la, comme dans "
           f"`oci-archive:chemin.tar:{NOM_LIVRE}`.",
    )

    decrit = host.run("docker image inspect %s", NOM_LIVRE)
    assert decrit.rc == 0, message(
        en=f"The loaded image does not answer to {NOM_LIVRE}: "
           f"{decrit.stderr.strip()[:200]} That is the destination name the "
           "mission asks for.",
        fr=f"L'image chargée ne répond pas à {NOM_LIVRE} : "
           f"{decrit.stderr.strip()[:200]} C'est le nom de destination que la "
           "mission demande.",
    )

    # LES COUCHES D UNE IMAGE CHARGEE NE SE COMPARENT PAS A CELLES DU REGISTRE,
    # et aucun outil n y change rien. Deux mesures du 2026-11-05 l ont etabli :
    #
    #   registre, par skopeo                c5d667da...   compresse
    #   demon, par docker .RootFS.Layers    694513db...   decompresse
    #   demon, par skopeo docker-daemon:    694513db...   decompresse AUSSI
    #
    # Le demon ne conserve pas les blobs compresses : il stocke les couches
    # decompressees, et skopeo rapporte ce qu il trouve. Passer par le meme
    # outil des deux cotes ne suffit donc pas, c est le TRANSPORT qui change la
    # nature du nombre. Ce controle comparait les deux, et le cycle l a dit deux
    # fois : d abord en comparant docker a skopeo, puis skopeo a skopeo.
    #
    # La comparaison des couches a donc lieu entre le REGISTRE et L ARCHIVE,
    # c est-a-dire dans le premier controle. Ici, ce qui est verifiable est que
    # l image chargee vient bien de l archive livree, et c est ce que son
    # identifiant local etablit.

    # VOICI CE QUE VAUT L IDENTIFIANT LOCAL, plutot que de dire qu il change.
    #
    # Mesure : avec un store containerd, `.Id` vaut le digest du MANIFESTE de
    # l archive chargee, et non celui de la configuration ni celui de l index du
    # registre. Le lab le montre au lieu de l affirmer.
    local = json.loads(decrit.stdout)[0]["Id"]
    archive = _skopeo(host, "inspect", "oci-archive:livraison/socle-oci.tar")
    if archive.rc == 0:
        manifeste = json.loads(archive.stdout).get("Digest")
        assert local == manifeste, message(
            en=f"The loaded image announces {local}, and the archive's manifest "
               f"is {manifeste}. On this engine the local identifier is the "
               "manifest digest: a mismatch means another archive was loaded "
               "than the one delivered.",
            fr=f"L'image chargée annonce {local}, et le manifeste de l'archive "
               f"vaut {manifeste}. Sur ce moteur l'identifiant local est le "
               "digest du manifeste : un écart signifie qu'une autre archive a "
               "été chargée que celle livrée.",
        )


def test_l_archive_arm64_porte_bien_arm64_et_non_l_architecture_de_l_hote(host):
    """Une autre architecture que celle de la machine, et la preuve qu'elle l'est.

    L'index de l'image à livrer porte quinze manifestes : c'est ce qui rend
    l'exercice possible. Sans `--override-arch`, skopeo choisit l'architecture
    de l'hôte, qui est amd64 ici, et l'archive serait juste de format mais
    fausse de contenu.
    """
    _archive_existe(host, ARM64, "L'archive arm64")

    lu = _skopeo(host, "inspect", "oci-archive:livraison/socle-arm64.tar")
    assert lu.rc == 0, message(
        en=f"skopeo cannot inspect the arm64 archive: {lu.stderr.strip()[-300:]}",
        fr=f"skopeo ne peut pas inspecter l'archive arm64 : "
           f"{lu.stderr.strip()[-300:]}",
    )
    decrit = json.loads(lu.stdout)
    assert decrit.get("Architecture") == "arm64", message(
        en=f"The archive holds the « {decrit.get('Architecture')} » "
           "architecture. Without `--override-arch`, skopeo picks the host's, "
           "which is amd64 here: the archive is then well formed and wrong.",
        fr=f"L'archive porte l'architecture « {decrit.get('Architecture')} ». "
           "Sans `--override-arch`, skopeo prend celle de l'hôte, qui est amd64 "
           "ici : l'archive est alors bien formée et fausse.",
    )
    assert decrit.get("Os") == "linux", message(
        en=f"The archive holds the « {decrit.get('Os')} » system instead of "
           "linux.",
        fr=f"L'archive porte le système « {decrit.get('Os')} » au lieu de linux.",
    )

    # ET CE N'EST PAS LA MÊME ARCHIVE QUE L'AUTRE : deux copies de la même
    # architecture passeraient les deux contrôles pris séparément.
    amd = _skopeo(host, "inspect", "oci-archive:livraison/socle-oci.tar")
    if amd.rc == 0:
        autre = json.loads(amd.stdout)
        assert autre.get("Digest") != decrit.get("Digest"), message(
            en="The arm64 archive and the main archive hold the same manifest: "
               "one of the two was produced without selecting its architecture.",
            fr="L'archive arm64 et l'archive principale portent le même "
               "manifeste : l'une des deux a été produite sans choisir son "
               "architecture.",
        )


def test_les_deux_formats_sont_livres_et_ne_se_ressemblent_pas(host):
    """Les deux formats, et ce qui les distingue à l'intérieur.

    Le docker-archive n'est pas une variante cosmétique de l'OCI : il écrit
    `<id>/layer.tar` et un `manifest.json` à plat, là où l'OCI adresse son
    contenu par digest. Mesuré sur la même image : 3,98 Mo contre 8,72 Mo pour
    l'alpine de la leçon.

    Le contrôle regarde la STRUCTURE et non la taille : une taille dépend de
    l'image, et un lab qui note un nombre d'octets se périme au premier
    changement de version.
    """
    _archive_existe(host, DOCKER_ARCHIVE, "L'archive docker-archive")

    entrees = host.run("tar -tf %s", DOCKER_ARCHIVE)
    assert entrees.rc == 0, message(
        en=f"{DOCKER_ARCHIVE} is not readable as a tar archive: "
           f"{entrees.stderr.strip()[:200]}",
        fr=f"{DOCKER_ARCHIVE} n'est pas lisible comme archive tar : "
           f"{entrees.stderr.strip()[:200]}",
    )
    noms = entrees.stdout.split()
    assert any(n.rstrip("/") == "manifest.json" for n in noms), message(
        en="The docker-archive carries no flat `manifest.json`, which is what "
           "distinguishes that format: use `docker-archive:` as the destination "
           "transport, not `oci-archive:`.",
        fr="L'archive docker-archive ne porte pas de `manifest.json` à plat, qui "
           "est ce qui distingue ce format : employez `docker-archive:` en "
           "transport de destination, pas `oci-archive:`.",
    )
    assert not any(n.rstrip("/") == "oci-layout" for n in noms), message(
        en="The docker-archive carries an `oci-layout`: it is in fact an OCI "
           "archive under another name, so the two deliveries are the same "
           "format.",
        fr="L'archive docker-archive porte un `oci-layout` : c'est en fait une "
           "archive OCI sous un autre nom, donc les deux livraisons sont du "
           "même format.",
    )

    # LE VRAI DISCRIMINANT DU FORMAT DOCKER, mesuré le 2026-11-05 en comparant
    # les deux producteurs côte à côte :
    #
    #                        docker save    skopeo -> docker-archive
    #   oci-layout           PRÉSENT        absent
    #   index.json           PRÉSENT        absent
    #   manifest.json        présent        présent
    #   repositories         absent         PRÉSENT
    #   <id>/layer.tar       0              1
    #
    # `manifest.json` ne distingue donc rien, puisque les deux l'écrivent. Ce
    # qui appartient au format Docker historique est `repositories` et les
    # `<id>/layer.tar`, et c'est ce qui se vérifie ici.
    assert any(n.endswith("/layer.tar") for n in noms), message(
        en="The docker-archive carries no `<id>/layer.tar`, which is how that "
           "historical format stores its layers. A `manifest.json` alone proves "
           "nothing: `docker save` writes one too, inside an OCI archive.",
        fr="L'archive docker-archive ne porte aucun `<id>/layer.tar`, qui est la "
           "façon dont ce format historique stocke ses couches. Un "
           "`manifest.json` seul ne prouve rien : `docker save` en écrit un "
           "aussi, à l'intérieur d'une archive OCI.",
    )
