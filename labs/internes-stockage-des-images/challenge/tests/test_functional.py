"""Tests fonctionnels du lab internes-stockage-des-images : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que ce qu'un conteneur écrit n'est pas nulle part : c'est
sur le disque de l'hôte, dans un répertoire ordinaire qu'on peut ouvrir. Les
deux labs précédents montraient ce qu'un conteneur voit et ce qu'il peut
consommer ; celui-ci montre où ses fichiers atterrissent.

MESURÉ SUR docker.lab LE 2026-10-30, et ces faits sont le lab :

| Fait | Valeur |
| pilote de stockage | `overlayfs` sur une installation neuve de 29, `overlay2` apres une mise a niveau ; racine `/var/lib/docker` |
| couche d'écriture d'un conteneur | `GraphDriver.Data.UpperDir` en overlay2, `/var/lib/docker/rootfs/overlayfs/<id>` en containerd |
| fichier écrit dans le conteneur | lisible immédiatement à ce chemin, depuis l'hôte |
| contenu de la couche après une écriture | ce fichier SEUL, rien d'autre |

C'est le dernier point qui rend la notion claire : la couche d'écriture ne
contient pas une copie du système de fichiers, elle ne contient que les
DIFFÉRENCES. Et c'est aussi ce qui explique le lab `troubleshoot-disque-plein`
plus loin dans la section : ces différences s'accumulent sur le disque de la
machine.

UN PIÈGE ÉVITÉ À L'ÉCRITURE, et il vaut d'être su. Pour démontrer qu'une
écriture atterrit dans la couche, la première idée était de faire modifier
`/etc/hostname`. Mesuré : la modification n'apparaît PAS dans la couche, parce
que ce fichier est un montage que Docker pose depuis le répertoire du conteneur,
et non un fichier de l'image. Les contrôles portent donc sur des fichiers créés
à la racine, qui n'ont pas ce statut particulier.

LE PRÉALABLE QUI ÉVITE D'ACCUSER L'APPRENANT. Un moteur réglé sur un autre
pilote ne porte pas `UpperDir`, et deux contrôles échoueraient en parlant de
couches. Un garde-fou vérifie donc le pilote avant toute mesure, et le dit.

AUCUN CHEMIN N'EST ÉCRIT EN DUR. La couche est demandée au moteur, qui la
connaît, et son chemin dépend d'un identifiant tiré à chaque création.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
indispensable ici, puisque `/var/lib/docker` n'est pas lisible par un compte
ordinaire. Une mesure sans élévation rendrait des réponses vides, et le premier
essai de conception de ce lab s'y est fait prendre.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

CONTENEUR = "entrepot"
ATELIER = "/opt/lab-stockage"
REPONSES = f"{ATELIER}/reponses.txt"
TRACE = "/trace-ecriture.txt"
CHARGE = "/charge.bin"
MARQUE_ATTENDUE = "ceci-a-ete-ecrit-dans-le-conteneur"
MEGAOCTETS_ATTENDUS = 5

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui
    les lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier.
    """
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def pilote(host) -> str:
    """Le pilote de stockage du moteur, tel qu'il est, et non tel qu'on l'attend.

    DEUX MAGASINS, ET LE DEFAUT A CHANGE. Mesuré le 2026-11-01 sur deux VM
    reprovisionnées à neuf : une installation neuve de docker-ce 29.9.2 emploie
    le magasin containerd et rend `overlayfs` ; une machine mise à niveau depuis
    une version antérieure garde ses graph drivers et rend `overlay2`. Les deux
    sont légitimes, et l'apprenant obtient le premier.

    Ce lab mesurait l'ancien et SKIPPAIT sur le nouveau, donc chez tout apprenant
    qui installe Docker aujourd'hui. Il accepte désormais les deux : seuls les
    chemins diffèrent, pas la leçon.
    """
    res = host.run("docker info --format %s", "{{.Driver}}")
    nom = res.stdout.strip()
    if nom not in ("overlay2", "overlayfs"):
        pytest.skip(message(
            en=f"the engine uses the `{nom}` driver, which this lab does not "
               "know how to locate: it measures the write layer of overlay2 "
               "(graph driver) and of overlayfs (containerd snapshotter)",
            fr=f"le moteur emploie le pilote `{nom}`, que ce lab ne sait pas "
               "situer : il mesure la couche d'écriture d'overlay2 (graph "
               "driver) et celle d'overlayfs (snapshotter containerd)",
        ))
    return nom


@pytest.fixture(scope="module")
def couche(host, pilote) -> str:
    """Le chemin de la couche d'écriture, là où le magasin présent la met.

    Avec un graph driver (`overlay2`), l'inspection le donne dans
    `GraphDriver.Data.UpperDir`.

    Avec le snapshotter containerd (`overlayfs`), défaut d'une installation neuve
    de Docker 29, `GraphDriver` vaut `null` et le moteur ne dit pas la couche.
    Elle est l'`upperdir` du montage overlay du conteneur, sous
    `/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/<n>/fs`,
    et c'est le noyau qui la rend. Mesuré le 2026-11-01 sur une VM neuve : ce
    répertoire porte le seul fichier écrit, là où le point de montage
    `/var/lib/docker/rootfs/overlayfs/<id>` porte les 18 entrées du rootfs
    complet. Confondre les deux ferait échouer la pesée, qui est la quatrième
    mesure du lab.
    """
    if pilote == "overlay2":
        res = host.run(
            "docker container inspect %s --format %s",
            CONTENEUR, "{{.GraphDriver.Data.UpperDir}}",
        )
    else:
        # En magasin containerd, le moteur ne dit pas la couche : `GraphDriver`
        # vaut `null`. Elle est l'`upperdir` du montage overlay du conteneur, que
        # le noyau rend. Le point de montage, lui, est la vue FUSIONNEE : s'y
        # fier donnerait le rootfs entier et non les differences.
        res = host.run(
            "findmnt -no OPTIONS /var/lib/docker/rootfs/overlayfs/"
            "$(docker container inspect %s --format %s)"
            " | tr , '\n' | sed -n %s",
            CONTENEUR, "{{.Id}}", "s/^upperdir=//p",
        )
    chemin = res.stdout.strip()
    if res.rc != 0 or not chemin:
        pytest.fail(message(
            en=f"container `{CONTENEUR}` has no write layer: it does not exist "
               "or is not running. Replay the lab with `dsoxlab reset`.",
            fr=f"le conteneur `{CONTENEUR}` n'a aucune couche d'écriture : il "
               "n'existe pas ou ne tourne pas. Rejouez le lab avec "
               "`dsoxlab reset`.",
        ))
    return chemin


def _lire_reponses(host) -> dict[str, str]:
    """Le formulaire, réduit à ses paires clé=valeur.

    Tolérant sur la forme (espaces, lignes vides, commentaires, casse de la
    clé), strict sur le fond : c'est le contenu qui est noté, pas la mise en
    page.
    """
    f = host.file(REPONSES)
    if not f.exists:
        pytest.fail(message(
            en=f"{REPONSES} is missing. The mission asks for two lines in it: "
               "pilote= and ecriture=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire deux "
               "lignes : pilote= et ecriture=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def test_la_reponse_nomme_le_pilote_de_stockage(host, pilote) -> None:
    """Le pilote, qui décide de tout le reste.

    Il n'y a pas une seule façon d'empiler des couches : le moteur en connaît
    plusieurs, et le choix change les chemins, les performances et jusqu'aux
    systèmes de fichiers acceptables sous `/var/lib/docker`. Savoir lequel est
    en place est la première question d'un diagnostic de stockage.
    """
    annonce = _lire_reponses(host).get("pilote", "").lower()
    assert annonce, message(
        en="the `pilote=` line is empty. The engine declares its storage "
           "driver, and that choice decides where everything else lives.",
        fr="la ligne `pilote=` est vide. Le moteur déclare son pilote de "
           "stockage, et ce choix décide de l'emplacement de tout le reste.",
    )
    assert annonce == pilote, message(
        en=f"the announced driver is not the one the engine declares.\n"
           f"  you wrote : {annonce}\n"
           "The engine states it in its general information, next to the "
           "directory where it keeps everything.",
        fr=f"le pilote annoncé n'est pas celui que le moteur déclare.\n"
           f"  vous avez écrit : {annonce}\n"
           "Le moteur l'indique dans ses informations générales, à côté du "
           "répertoire où il garde tout.",
    )


def test_la_reponse_nomme_la_couche_d_ecriture(host, couche) -> None:
    """Le chemin de la couche, qui est un répertoire réel de l'hôte.

    C'est le point que le lab existe pour faire constater : la couche
    d'écriture n'est pas une abstraction du moteur, c'est un répertoire qu'on
    peut ouvrir, et dont le chemin est donné par l'inspection du conteneur.
    """
    annonce = _lire_reponses(host).get("ecriture", "")
    # LE MESSAGE NE PROMET PLUS QUATRE CHEMINS. Il décrivait l'inspection du
    # magasin CLASSIQUE, où `GraphDriver.Data` en déclare quatre. Sur le
    # magasin containerd, mesuré le 2026-11-02, `GraphDriver` vaut `null` : la
    # couche se trouve par le point de montage, et un message qui annonce un
    # état impossible envoie chercher ce qui n'existe pas.
    assert annonce, message(
        en="the `ecriture=` line is empty. Find where this container's writes "
           "land: what the engine declares depends on its image store, so look "
           "at what it declares before looking for a path.",
        fr="la ligne `ecriture=` est vide. Trouvez où atterrissent les "
           "écritures de ce conteneur : ce que le moteur déclare dépend de son "
           "magasin d'images, donc regardez ce qu'il déclare avant de chercher "
           "un chemin.",
    )
    assert annonce.rstrip("/") == couche.rstrip("/"), message(
        en=f"the announced path is not `{CONTENEUR}`'s write layer.\n"
           f"  you wrote : {annonce}\n"
           "The path depends on the image store. With the classic store the "
           "inspection declares several, and only the one that receives the "
           "writes is asked for; with the containerd store it declares none, "
           "and the layer is found through the mount.",
        fr=f"le chemin annoncé n'est pas la couche d'écriture de "
           f"`{CONTENEUR}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "Le chemin dépend du magasin d'images. Avec le magasin classique "
           "l'inspection en déclare plusieurs, et seul celui qui reçoit les "
           "écritures est demandé ; avec le magasin containerd elle n'en "
           "déclare aucun, et la couche se trouve par le point de montage.",
    )


def test_le_fichier_ecrit_dans_le_conteneur_est_sur_le_disque_de_l_hote(
    host, couche
) -> None:
    """Le contrôle qui rend la notion concrète.

    Le fichier est écrit DANS le conteneur et lu DEPUIS l'hôte, sans export ni
    commande particulière. C'est ce qui montre qu'un conteneur n'écrit pas dans
    un ailleurs : il écrit sur le disque de la machine, à un endroit précis.

    Le contrôle porte sur un fichier créé à la racine, et pas sur un fichier de
    configuration : mesuré le 2026-10-30, une modification de `/etc/hostname`
    n'apparaît pas dans la couche, parce que Docker y pose un montage depuis le
    répertoire du conteneur.
    """
    dans_le_conteneur = host.run("docker exec %s cat %s", CONTENEUR, TRACE)
    assert dans_le_conteneur.rc == 0, message(
        en=f"{TRACE} does not exist inside `{CONTENEUR}`: "
           f"{dans_le_conteneur.stderr.strip()}\n"
           "It has to be written FROM the container, which is the whole point: "
           "the lab then shows where that write landed.",
        fr=f"{TRACE} n'existe pas dans `{CONTENEUR}` : "
           f"{dans_le_conteneur.stderr.strip()}\n"
           "Il faut l'écrire DEPUIS le conteneur, et c'est tout l'intérêt : le "
           "lab montre ensuite où cette écriture a atterri.",
    )
    assert MARQUE_ATTENDUE in dans_le_conteneur.stdout, message(
        en=f"{TRACE} exists but does not carry the expected line.\n"
           f"  read: {dans_le_conteneur.stdout.strip()[:120] or '(empty)'}",
        fr=f"{TRACE} existe mais ne porte pas la ligne attendue.\n"
           f"  lu : {dans_le_conteneur.stdout.strip()[:120] or '(vide)'}",
    )

    sur_l_hote = host.run("cat %s%s", couche, TRACE)
    assert sur_l_hote.rc == 0, message(
        en=f"the file exists in the container but not at {couche}{TRACE} on the "
           "host.\n"
           "Either the announced layer is not the right one, or the file was "
           "written somewhere the container does not keep in its own layer, "
           "such as a mount.",
        fr=f"le fichier existe dans le conteneur mais pas en {couche}{TRACE} "
           "sur l'hôte.\n"
           "Soit la couche annoncée n'est pas la bonne, soit le fichier a été "
           "écrit à un endroit que le conteneur ne garde pas dans sa propre "
           "couche, comme un montage.",
    )
    assert MARQUE_ATTENDUE in sur_l_hote.stdout, message(
        en=f"{couche}{TRACE} exists on the host but does not carry the expected "
           "line.\n"
           f"  read: {sur_l_hote.stdout.strip()[:120] or '(empty)'}",
        fr=f"{couche}{TRACE} existe sur l'hôte mais ne porte pas la ligne "
           "attendue.\n"
           f"  lu : {sur_l_hote.stdout.strip()[:120] or '(vide)'}",
    )


def test_la_couche_d_ecriture_pese_ce_que_le_conteneur_y_a_mis(host, couche) -> None:
    """Ce que le conteneur écrit occupe le disque de l'hôte, et cela se pèse.

    C'est la conséquence qui compte en exploitation, et celle qu'on découvre
    trop tard : la couche d'écriture n'est pas gratuite. Elle explique le lab
    `troubleshoot-disque-plein` de cette même section, où une machine se remplit
    sans qu'aucun volume soit en cause.

    La taille est mesurée sur l'HÔTE, dans la couche, et non dans le conteneur :
    c'est le disque de la machine qui se remplit, pas un espace à part.
    """
    dedans = host.run("docker exec %s ls -l %s", CONTENEUR, CHARGE)
    assert dedans.rc == 0, message(
        en=f"{CHARGE} does not exist inside `{CONTENEUR}`: "
           f"{dedans.stderr.strip()}\n"
           f"A file of about {MEGAOCTETS_ATTENDUS} Mo has to be created from "
           "the container.",
        fr=f"{CHARGE} n'existe pas dans `{CONTENEUR}` : "
           f"{dedans.stderr.strip()}\n"
           f"Il faut créer depuis le conteneur un fichier d'environ "
           f"{MEGAOCTETS_ATTENDUS} Mo.",
    )

    res = host.run("du -sm %s", couche)
    try:
        megaoctets = int(res.stdout.split()[0])
    except (ValueError, IndexError):
        pytest.fail(message(
            en=f"cannot measure the size of {couche}: {res.stderr.strip()}",
            fr=f"impossible de mesurer la taille de {couche} : "
               f"{res.stderr.strip()}",
        ))
    assert megaoctets >= MEGAOCTETS_ATTENDUS, message(
        en=f"the write layer weighs {megaoctets} Mo on the host, expected at "
           f"least {MEGAOCTETS_ATTENDUS}.\n"
           "What a container writes is not free: it occupies the machine's "
           "disk, in that very directory. A file created in a volume or in "
           "memory would not appear here, which is precisely the difference.",
        fr=f"la couche d'écriture pèse {megaoctets} Mo sur l'hôte, attendu au "
           f"moins {MEGAOCTETS_ATTENDUS}.\n"
           "Ce qu'un conteneur écrit n'est pas gratuit : cela occupe le disque "
           "de la machine, dans ce répertoire même. Un fichier créé dans un "
           "volume ou en mémoire n'apparaîtrait pas ici, et c'est précisément "
           "la différence.",
    )
