"""Tests fonctionnels du lab donnees-volumes-et-montages : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'il y a trois façons de donner un espace de fichiers à
un conteneur, qu'elles ne servent pas au même usage, et qu'aucune des trois
n'est la couche du conteneur, où tout finit par défaut.

| Montage | Ce qu'il donne | Pour quoi |
| volume nommé | un espace géré par le moteur, qui survit au conteneur | les données |
| bind mount | un répertoire de l'hôte, tel quel | une configuration fournie |
| tmpfs | de la mémoire, qui ne persiste rien | un espace de travail |

UNE MESURE A CHANGÉ L'ÉCRITURE DE CE FICHIER, et elle vaut d'être écrite : un
tmpfs **n'apparaît pas** dans `.Mounts`. Il vit dans `.HostConfig.Tmpfs`.
Relevé sur docker.lab le 2026-10-30. Un test qui l'aurait cherché dans
`.Mounts` aurait échoué quoi que fasse l'apprenant, et aurait accusé un
apprenant irréprochable.

LE CONTRÔLE QUI PORTE LA LEÇON. Le quatrième. `historique.log` a été écrit par
le setup dans la COUCHE du conteneur, avec un contenu tiré au hasard : il
n'existe nulle part ailleurs. Le faire passer dans le volume suppose de l'avoir
sorti AVANT de détruire le conteneur, et c'est exactement le geste qui sauve ou
perd des données en production.

POURQUOI UNE EMPREINTE ET PAS LE CONTENU. Le test compare le SHA256 du fichier
arrivé dans le volume à celui que le setup a relevé. Garder le contenu sur
l'hôte donnerait la réponse ; garder l'empreinte permet de vérifier sans rien
révéler, et l'apprenant peut s'en servir pour se contrôler lui-même. Un contrôle
qu'on peut vérifier soi-même enseigne ; un contrôle opaque fait deviner.

CHAQUE MONTAGE EST MESURÉ DEUX FOIS : ce que l'inspection déclare, et ce que le
conteneur peut réellement faire. Les deux peuvent diverger, et le cas le plus
net est le bind en lecture seule, qui se déclare et dont le refus s'éprouve.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, message

CONTENEUR = "archive"
VOLUME = "coffre-donnees"
# L'image que le setup a posée. Le quatrième contrôle en a besoin pour monter
# le volume dans un conteneur jetable, seule façon de lire un volume sans
# dépendre du conteneur qu'on est en train de noter.
IMAGE = "lab-volumes:1.0"
ATELIER = "/opt/lab-volumes"
EMPREINTE = f"{ATELIER}/historique.sha256"
REFERENCE_SUR_L_HOTE = f"{ATELIER}/reference"
CHEMIN_DONNEES = "/var/lib/donnees"
CHEMIN_REFERENCE = "/etc/reference"
CHEMIN_TRAVAIL = "/var/cache/travail"
MARQUE_DU_VOLUME = "coffre=ce-volume-est-le-bon"

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


def _tourne(host) -> None:
    """Le préalable des quatre contrôles.

    Ce lab fait RECRÉER le conteneur, puisqu'un montage ne s'ajoute pas à un
    conteneur existant : un nom manquant veut presque toujours dire qu'il a été
    détruit et pas relancé.
    """
    res = host.run(
        "docker container inspect %s --format %s", CONTENEUR, "{{.State.Status}}"
    )
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{CONTENEUR}` does not exist. This lab requires "
               "recreating it, because a mount cannot be added to an existing "
               "container: it has to be relaunched under the SAME name.",
            fr=f"le conteneur `{CONTENEUR}` n'existe pas. Ce lab demande de le "
               "recréer, puisqu'un montage ne s'ajoute pas à un conteneur "
               "existant : il faut le relancer sous le MÊME nom.",
        ))
    etat = res.stdout.strip()
    if etat != "running":
        pytest.fail(message(
            en=f"container `{CONTENEUR}` is in state `{etat}`, not `running`. "
               "Its mounts cannot be tested while it is not running.",
            fr=f"le conteneur `{CONTENEUR}` est dans l'état `{etat}`, pas "
               "`running`. Ses montages ne peuvent pas être éprouvés tant qu'il "
               "ne tourne pas.",
        ))


def _montages(host) -> list[dict]:
    """Les montages que l'inspection déclare, sauf le tmpfs.

    `.Mounts` porte les volumes et les binds. Le tmpfs n'y figure PAS : mesuré
    le 2026-10-30, il vit dans `.HostConfig.Tmpfs`, et c'est le contrôle 3 qui
    va le chercher là.
    """
    res = host.run("docker container inspect %s --format %s",
                   CONTENEUR, "{{json .Mounts}}")
    if res.rc != 0 or not res.stdout.strip():
        return []
    try:
        return json.loads(res.stdout.strip()) or []
    except json.JSONDecodeError:
        return []


def _montage_sur(host, destination: str) -> dict | None:
    """Le montage déclaré pour un chemin donné, s'il existe."""
    for montage in _montages(host):
        if montage.get("Destination") == destination:
            return montage
    return None


def test_le_volume_nomme_est_monte_sur_le_chemin_des_donnees(host) -> None:
    """Un espace géré par le moteur, et qui survit au conteneur.

    Deux assertions, et la seconde n'est pas une redite : l'inspection dit
    quel volume est monté, et la marque prouve que c'est le BON, au BON
    endroit. Un apprenant qui monterait un volume anonyme, ou le bon volume sur
    un autre chemin, satisferait la première et pas la seconde.
    """
    _tourne(host)
    montage = _montage_sur(host, CHEMIN_DONNEES)
    assert montage is not None, message(
        en=f"nothing is mounted on {CHEMIN_DONNEES}.\n"
           f"The data must live on the named volume `{VOLUME}`, not in the "
           "container's layer, which disappears with it.",
        fr=f"rien n'est monté sur {CHEMIN_DONNEES}.\n"
           f"Les données doivent vivre sur le volume nommé `{VOLUME}`, et non "
           "dans la couche du conteneur, qui disparaît avec lui.",
    )
    assert montage.get("Type") == "volume", message(
        en=f"{CHEMIN_DONNEES} is mounted, but its type is "
           f"`{montage.get('Type')}` and not `volume`.\n"
           "A named volume is managed by the engine, which is what makes it "
           "survive the container and be backed up as a unit.",
        fr=f"{CHEMIN_DONNEES} est monté, mais son type est "
           f"`{montage.get('Type')}` et non `volume`.\n"
           "Un volume nommé est géré par le moteur, et c'est ce qui le fait "
           "survivre au conteneur et se sauvegarder d'un bloc.",
    )
    assert montage.get("Name") == VOLUME, message(
        en=f"the volume mounted on {CHEMIN_DONNEES} is "
           f"`{montage.get('Name')}`, not `{VOLUME}`.\n"
           "An anonymous volume would also survive the container, but nobody "
           "would ever find it again: naming it is the point.",
        fr=f"le volume monté sur {CHEMIN_DONNEES} est "
           f"`{montage.get('Name')}`, pas `{VOLUME}`.\n"
           "Un volume anonyme survivrait aussi au conteneur, mais personne ne "
           "le retrouverait jamais : le nommer est tout l'intérêt.",
    )

    res = host.run("docker exec %s cat %s/marque.txt", CONTENEUR, CHEMIN_DONNEES)
    assert MARQUE_DU_VOLUME in res.stdout, message(
        en=f"the container does not see the volume's mark on {CHEMIN_DONNEES}.\n"
           f"  read: {res.stdout.strip()[:120] or '(nothing)'}\n"
           "The volume already carried a `marque.txt` before you arrived. Not "
           "seeing it means the mount does not land where it is expected.",
        fr=f"le conteneur ne voit pas la marque du volume sur "
           f"{CHEMIN_DONNEES}.\n"
           f"  lu : {res.stdout.strip()[:120] or '(rien)'}\n"
           "Le volume portait déjà un `marque.txt` avant votre arrivée. Ne pas "
           "la voir signifie que le montage n'atterrit pas où on l'attend.",
    )


def test_la_reference_vient_de_l_hote_en_lecture_seule(host) -> None:
    """Un répertoire de l'hôte, exposé tel quel, et qu'on ne doit pas modifier.

    Le bind mount ne copie rien : il expose. C'est ce qui le rend commode pour
    fournir une configuration, et dangereux pour des données, puisque le
    conteneur écrit alors directement sur l'hôte. La lecture seule est la
    réponse, et elle se déclare au montage.

    Deux mesures : ce que l'inspection déclare, et ce que le conteneur peut
    réellement faire. Les deux, parce qu'une déclaration n'est pas une preuve.
    """
    _tourne(host)
    montage = _montage_sur(host, CHEMIN_REFERENCE)
    assert montage is not None, message(
        en=f"nothing is mounted on {CHEMIN_REFERENCE}.\n"
           f"The host's directory {REFERENCE_SUR_L_HOTE} has to be exposed "
           "there.",
        fr=f"rien n'est monté sur {CHEMIN_REFERENCE}.\n"
           f"Le répertoire {REFERENCE_SUR_L_HOTE} de l'hôte doit y être exposé.",
    )
    assert montage.get("Type") == "bind", message(
        en=f"{CHEMIN_REFERENCE} is mounted, but its type is "
           f"`{montage.get('Type')}` and not `bind`.\n"
           "A directory of the host is exposed as it is, which is not the same "
           "as a volume managed by the engine.",
        fr=f"{CHEMIN_REFERENCE} est monté, mais son type est "
           f"`{montage.get('Type')}` et non `bind`.\n"
           "Un répertoire de l'hôte est exposé tel quel, ce qui n'est pas la "
           "même chose qu'un volume géré par le moteur.",
    )
    assert montage.get("Source") == REFERENCE_SUR_L_HOTE, message(
        en=f"{CHEMIN_REFERENCE} comes from `{montage.get('Source')}`, not from "
           f"`{REFERENCE_SUR_L_HOTE}`.",
        fr=f"{CHEMIN_REFERENCE} vient de `{montage.get('Source')}`, et non de "
           f"`{REFERENCE_SUR_L_HOTE}`.",
    )
    assert montage.get("RW") is False, message(
        en=f"{CHEMIN_REFERENCE} is mounted read-write.\n"
           "A bind mount writes directly on the host: a configuration provided "
           "to a container is mounted read-only, so that the container cannot "
           "alter what it was given.",
        fr=f"{CHEMIN_REFERENCE} est monté en lecture-écriture.\n"
           "Un bind mount écrit directement sur l'hôte : une configuration "
           "fournie à un conteneur se monte en lecture seule, pour que le "
           "conteneur ne puisse pas altérer ce qu'on lui donne.",
    )

    vu = host.run("docker exec %s cat %s/politique.txt", CONTENEUR, CHEMIN_REFERENCE)
    assert "politique de conservation" in vu.stdout, message(
        en=f"the container does not see the host's file on {CHEMIN_REFERENCE}.\n"
           f"  read: {vu.stdout.strip()[:120] or '(nothing)'}",
        fr=f"le conteneur ne voit pas le fichier de l'hôte sur "
           f"{CHEMIN_REFERENCE}.\n"
           f"  lu : {vu.stdout.strip()[:120] or '(rien)'}",
    )

    essai = host.run(
        "docker exec %s sh -c %s",
        CONTENEUR, f"echo essai > {CHEMIN_REFERENCE}/essai-de-test",
    )
    assert essai.rc != 0, message(
        en=f"writing into {CHEMIN_REFERENCE} succeeded, so the mount is not "
           "really read-only.\n"
           "The declaration said one thing and the machine does another: that "
           "is why both are measured.",
        fr=f"l'écriture dans {CHEMIN_REFERENCE} a réussi : le montage n'est donc "
           "pas réellement en lecture seule.\n"
           "La déclaration disait une chose et la machine en fait une autre : "
           "c'est pour cela que les deux sont mesurées.",
    )


def test_l_espace_de_travail_est_en_memoire(host) -> None:
    """De la mémoire, qui ne persiste rien, et c'est voulu.

    Un espace de travail n'a pas à survivre : il n'a pas à être sauvegardé, ni
    à remplir le disque, ni à traîner après le conteneur. C'est le montage
    qu'on oublie, et celui qui évite une classe entière de problèmes.

    LE PIÈGE DU TEST, et il a été mesuré : un tmpfs n'apparaît PAS dans
    `.Mounts`. Il faut aller le lire dans `.HostConfig.Tmpfs`.
    """
    _tourne(host)
    res = host.run("docker container inspect %s --format %s",
                   CONTENEUR, "{{json .HostConfig.Tmpfs}}")
    brut = res.stdout.strip()
    declares = {}
    if brut and brut != "null":
        try:
            declares = json.loads(brut) or {}
        except json.JSONDecodeError:
            declares = {}
    assert CHEMIN_TRAVAIL in declares, message(
        en=f"{CHEMIN_TRAVAIL} is not an in-memory space.\n"
           f"  declared in memory: "
           f"{', '.join(sorted(declares)) or '(nothing)'}\n"
           "A working space does not have to survive: not to be backed up, not "
           "to fill the disk, not to linger after the container.",
        fr=f"{CHEMIN_TRAVAIL} n'est pas un espace en mémoire.\n"
           f"  déclarés en mémoire : "
           f"{', '.join(sorted(declares)) or '(rien)'}\n"
           "Un espace de travail n'a pas à survivre : ni à être sauvegardé, ni "
           "à remplir le disque, ni à traîner après le conteneur.",
    )

    essai = host.run(
        "docker exec %s sh -c %s",
        CONTENEUR, f"echo essai > {CHEMIN_TRAVAIL}/essai-de-test",
    )
    assert essai.rc == 0, message(
        en=f"{CHEMIN_TRAVAIL} is declared in memory, but the container cannot "
           f"write there: {essai.stderr.strip()}\n"
           "An unusable working space is not a working space.",
        fr=f"{CHEMIN_TRAVAIL} est déclaré en mémoire, mais le conteneur n'y "
           f"écrit pas : {essai.stderr.strip()}\n"
           "Un espace de travail inutilisable n'est pas un espace de travail.",
    )


def test_l_historique_a_rejoint_le_volume_intact(host) -> None:
    """Le contrôle qui porte la leçon, et le seul qui ne pardonne pas.

    `historique.log` était dans la COUCHE du conteneur, avec un contenu tiré au
    hasard : il n'existait nulle part ailleurs. Le faire passer dans le volume
    suppose de l'avoir sorti AVANT de détruire le conteneur.

    C'est le geste qui sauve ou perd des données en vrai, et c'est pourquoi il
    est noté sur l'EMPREINTE : un fichier recréé à la main aurait le bon nom et
    pas le bon contenu, ce qui est exactement la façon dont on se raconte qu'une
    migration a réussi.
    """
    _tourne(host)
    fichier_empreinte = host.file(EMPREINTE)
    if not fichier_empreinte.exists:
        pytest.skip(message(
            en=f"{EMPREINTE} is missing: the setup did not record the "
               "original fingerprint",
            fr=f"{EMPREINTE} est absent : le setup n'a pas relevé l'empreinte "
               "d'origine",
        ))
    attendue = fichier_empreinte.content_string.strip()

    # LE FICHIER EST LU DANS LE VOLUME, PAR UN CONTENEUR JETABLE, et c'est une
    # correction mesurée. Une première version lisait le chemin
    # `/var/lib/donnees/historique.log` dans `archive` : ce test PASSAIT avant
    # tout travail, puisque la couche du conteneur porte déjà le fichier à ce
    # chemin. Il mesurait la présence du fichier, pas sa migration, et
    # `valider-labs.py` l'a attrapé en rendant 1/4 sur l'état de départ.
    #
    # Monter le volume dans un conteneur à part le mesure, lui, et non ce que
    # `archive` donne à voir. C'est aussi ce qui rend le contrôle indépendant
    # de la configuration de `archive`, déjà mesurée par le premier contrôle.
    res = host.run(
        "docker run --rm -v %s:/cible %s sh -c %s",
        VOLUME, IMAGE, "sha256sum /cible/historique.log | awk '{print $1}'",
    )
    assert res.rc == 0, message(
        en=f"`historique.log` is not on the volume `{VOLUME}`: "
           f"{res.stderr.strip()}\n"
           "Being visible from the container is not enough: as long as the "
           "file is only in its layer, it disappears with it. The check reads "
           "the volume itself, through a throwaway container.\n"
           "Its content was drawn at random and exists nowhere else. If the "
           "container was destroyed before the file was taken out, it is lost "
           "and there is no recovery: replay the lab with `dsoxlab reset`.",
        fr=f"`historique.log` n'est pas sur le volume `{VOLUME}` : "
           f"{res.stderr.strip()}\n"
           "Être visible depuis le conteneur ne suffit pas : tant que le "
           "fichier n'est que dans sa couche, il disparaît avec lui. Le "
           "contrôle lit le volume lui-même, par un conteneur jetable.\n"
           "Son contenu était tiré au hasard et n'existe nulle part ailleurs. "
           "Si le conteneur a été détruit avant que le fichier en soit sorti, "
           "il est perdu et il n'y a pas de rattrapage : rejouez le lab avec "
           "`dsoxlab reset`.",
    )
    obtenue = res.stdout.strip()
    assert obtenue == attendue, message(
        en="`historique.log` is on the volume, but it is not the original "
           "file.\n"
           f"  expected : {attendue[:16]}…\n"
           f"  found    : {obtenue[:16]}…\n"
           "A file recreated by hand has the right name and not the right "
           "content, which is exactly how one tells oneself a migration "
           f"succeeded. The fingerprint is in {EMPREINTE}: you can check your "
           "own copy with it.",
        fr="`historique.log` est sur le volume, mais ce n'est pas le fichier "
           "d'origine.\n"
           f"  attendue : {attendue[:16]}…\n"
           f"  obtenue  : {obtenue[:16]}…\n"
           "Un fichier recréé à la main a le bon nom et pas le bon contenu, ce "
           "qui est exactement la façon dont on se raconte qu'une migration a "
           f"réussi. L'empreinte est dans {EMPREINTE} : vous pouvez vérifier "
           "votre copie avec elle.",
    )
