"""Tests fonctionnels du lab internes-cgroups-v2 : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que l'isolation a deux moitiés qui n'ont rien à voir. Un
namespace restreint une VUE ; un cgroup COMPTE et PLAFONNE. Le lab qui précède
montrait la première, celui-ci montre la seconde.

MESURÉ SUR docker.lab LE 2026-10-30, et ces valeurs sont le lab :

| Fait | Valeur |
| système de fichiers de /sys/fs/cgroup | `cgroup2fs`, pilote `systemd` |
| cgroup d'un conteneur | `/sys/fs/cgroup/system.slice/docker-<id>.scope` |
| `--memory 256m` donne `memory.max` | `268435456`, soit la valeur en OCTETS |
| conteneur SANS limite, `memory.max` | **`max`**, et non 0 ni un grand nombre |

LA TROISIÈME QUESTION EST CELLE QUI SURPREND, et c'est pour cela qu'elle est
posée : on cherche spontanément un nombre, et la réponse n'en est pas un.
L'absence de limite n'est pas une limite très haute, c'est l'absence de la
notion, et c'est ce qui explique qu'un conteneur sans `--memory` puisse prendre
toute la mémoire de la machine.

AUCUNE VALEUR N'EST ÉCRITE EN DUR DANS CE FICHIER. Le chemin est construit
depuis l'identifiant que le moteur donne, et la limite attendue est lue dans le
cgroup lui-même, pas recopiée de l'énoncé. Un test qui aurait porté
`268435456` serait faux le jour où le setup changerait de limite, et le lab
mourrait d'une modification sans rapport.

LE PRÉALABLE QUI ÉVITE D'ACCUSER L'APPRENANT. Sur une machine en cgroup v1, les
chemins et les noms de fichiers diffèrent, et les quatre contrôles échoueraient
en parlant de limites. Un garde-fou vérifie donc la version avant toute mesure,
et le dit.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
indispensable ici, puisque les contrôles lisent `/sys/fs/cgroup`, dont les
fichiers d'un conteneur ne sont pas lisibles par un compte ordinaire.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

AVEC_LIMITE = "mesure"
SANS_LIMITE = "libre"
BRIDE = "bride"
ATELIER = "/opt/lab-cgroups"
REPONSES = f"{ATELIER}/reponses.txt"
MEMOIRE_A_POSER = 128 * 1024 * 1024
PIDS_A_POSER = 64

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


@pytest.fixture(scope="module", autouse=True)
def cgroup_v2(host) -> None:
    """Le préalable de tout le fichier, et il évite d'accuser l'apprenant.

    Sur une machine en cgroup v1, les chemins et les noms de fichiers diffèrent.
    Les quatre contrôles échoueraient alors en parlant de limites, alors que la
    cause serait la version du mécanisme.
    """
    res = host.run("stat -fc %T /sys/fs/cgroup")
    if res.stdout.strip() != "cgroup2fs":
        pytest.skip(message(
            en=f"/sys/fs/cgroup is `{res.stdout.strip()}` and not `cgroup2fs`: "
               "this machine is not on unified cgroup v2, and this lab measures "
               "v2 paths",
            fr=f"/sys/fs/cgroup est en `{res.stdout.strip()}` et non "
               "`cgroup2fs` : cette machine n'est pas en cgroup v2 unifié, et "
               "ce lab mesure des chemins de v2",
        ))


def _cgroup(host, nom: str) -> str:
    """Le chemin du cgroup d'un conteneur, construit depuis son identifiant.

    Construit, et non cherché : le moteur donne l'identifiant complet, et le
    pilote `systemd` en dérive un chemin prévisible. Un `find` dans
    `/sys/fs/cgroup` marcherait aussi et serait plus lent et moins sûr, puisque
    deux conteneurs peuvent porter un préfixe commun.
    """
    res = host.run("docker container inspect %s --format %s", nom, "{{.Id}}")
    identifiant = res.stdout.strip()
    if res.rc != 0 or not identifiant:
        pytest.fail(message(
            en=f"container `{nom}` does not exist. The containers' names are "
               "part of the brief, and the checks look for them by name.",
            fr=f"le conteneur `{nom}` n'existe pas. Les noms des conteneurs "
               "font partie de l'énoncé, et les contrôles les cherchent "
               "nommément.",
        ))
    return f"/sys/fs/cgroup/system.slice/docker-{identifiant}.scope"


def _valeur(host, chemin: str, fichier: str) -> str:
    """Le contenu d'un fichier du cgroup, ou une chaîne vide."""
    res = host.run("cat %s/%s", chemin, fichier)
    return res.stdout.strip() if res.rc == 0 else ""


def _lire_reponses(host) -> dict[str, str]:
    """Le formulaire, réduit à ses paires clé=valeur.

    Tolérant sur la forme (espaces, lignes vides, commentaires, casse de la
    clé), strict sur le fond : c'est le contenu qui est noté, pas la mise en
    page.
    """
    f = host.file(REPONSES)
    if not f.exists:
        pytest.fail(message(
            en=f"{REPONSES} is missing. The mission asks for three lines in "
               "it: chemin=, memoire_max= and sans_limite=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire trois "
               "lignes : chemin=, memoire_max= et sans_limite=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def test_la_reponse_nomme_le_cgroup_du_conteneur(host) -> None:
    """Où vit le cgroup, et c'est sur l'hôte qu'il vit.

    Le chemin dérive de l'identifiant complet du conteneur, pas de son nom :
    c'est ce qui le rend unique, et ce qui oblige à passer par le moteur pour
    le construire. Un apprenant qui répondrait un chemin plausible mais inexact
    ne l'a pas trouvé.
    """
    attendu = _cgroup(host, AVEC_LIMITE)
    if not _valeur(host, attendu, "memory.max"):
        pytest.skip(message(
            en=f"{attendu}/memory.max is unreadable: the setup did not finish",
            fr=f"{attendu}/memory.max est illisible : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("chemin", "")
    assert annonce, message(
        en="the `chemin=` line is empty. A container's cgroup lives on the "
           "HOST, under /sys/fs/cgroup, at a path derived from the container's "
           "full identifier.",
        fr="la ligne `chemin=` est vide. Le cgroup d'un conteneur vit sur "
           "L'HÔTE, sous /sys/fs/cgroup, à un chemin dérivé de l'identifiant "
           "complet du conteneur.",
    )
    assert annonce.rstrip("/") == attendu, message(
        en=f"the announced path is not `{AVEC_LIMITE}`'s cgroup.\n"
           f"  you wrote : {annonce}\n"
           "The path derives from the container's FULL identifier, not from its "
           "name nor from its short identifier. The engine gives that "
           "identifier.",
        fr=f"le chemin annoncé n'est pas le cgroup de `{AVEC_LIMITE}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "Le chemin dérive de l'identifiant COMPLET du conteneur, pas de son "
           "nom ni de son identifiant court. Le moteur donne cet identifiant.",
    )


def test_la_reponse_nomme_la_limite_memoire_du_cgroup(host) -> None:
    """La limite, telle que le noyau la porte : en octets, et sans unité.

    `--memory 256m` ne laisse aucune trace de « 256m » : le noyau ne connaît
    que des octets. C'est ce qui explique qu'une limite se relise mal quand on
    l'a posée dans une unité et qu'on la lit dans une autre.
    """
    chemin = _cgroup(host, AVEC_LIMITE)
    attendue = _valeur(host, chemin, "memory.max")
    if not attendue:
        pytest.skip(message(
            en=f"{chemin}/memory.max is unreadable: the setup did not finish",
            fr=f"{chemin}/memory.max est illisible : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("memoire_max", "")
    assert annonce, message(
        en="the `memoire_max=` line is empty. The limit is in the cgroup, in "
           "the file that bears its name.",
        fr="la ligne `memoire_max=` est vide. La limite est dans le cgroup, "
           "dans le fichier qui porte son nom.",
    )
    assert annonce == attendue, message(
        en=f"the announced limit is not the one the cgroup declares.\n"
           f"  you wrote : {annonce}\n"
           "The kernel only knows bytes: the unit used when setting the limit "
           "leaves no trace. The expected answer is the file's content, as it "
           "is.",
        fr=f"la limite annoncée n'est pas celle que le cgroup déclare.\n"
           f"  vous avez écrit : {annonce}\n"
           "Le noyau ne connaît que des octets : l'unité employée pour poser la "
           "limite ne laisse aucune trace. La réponse attendue est le contenu "
           "du fichier, tel quel.",
    )


def test_la_reponse_dit_ce_qu_un_conteneur_sans_limite_porte(host) -> None:
    """La question qui surprend, et c'est pour cela qu'elle est posée.

    On cherche spontanément un nombre, et la réponse n'en est pas un. L'absence
    de limite n'est pas une limite très haute : c'est l'absence de la notion, et
    c'est ce qui explique qu'un conteneur sans limite puisse prendre toute la
    mémoire de la machine.
    """
    chemin = _cgroup(host, SANS_LIMITE)
    attendue = _valeur(host, chemin, "memory.max")
    if not attendue:
        pytest.skip(message(
            en=f"{chemin}/memory.max is unreadable: the setup did not finish",
            fr=f"{chemin}/memory.max est illisible : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("sans_limite", "")
    assert annonce, message(
        en="the `sans_limite=` line is empty. Read the SAME file for "
           f"`{SANS_LIMITE}`, which was started without any limit.",
        fr="la ligne `sans_limite=` est vide. Lisez le MÊME fichier pour "
           f"`{SANS_LIMITE}`, qui a été lancé sans aucune limite.",
    )
    assert annonce == attendue, message(
        en=f"`{SANS_LIMITE}` does not declare `{annonce}`.\n"
           "Looking for a number here is the natural reflex, and there is none: "
           "the absence of a limit is not a very high limit, it is the absence "
           "of the notion. That is what explains how a container without a "
           "limit can take all the machine's memory.",
        fr=f"`{SANS_LIMITE}` ne déclare pas `{annonce}`.\n"
           "Chercher un nombre ici est le réflexe naturel, et il n'y en a pas : "
           "l'absence de limite n'est pas une limite très haute, c'est "
           "l'absence de la notion. C'est ce qui explique qu'un conteneur sans "
           "limite puisse prendre toute la mémoire de la machine.",
    )


def test_le_conteneur_bride_porte_les_deux_plafonds(host) -> None:
    """Deux limites d'un seul geste, et toutes deux lues dans le cgroup.

    Deux plafonds plutôt qu'un, parce qu'un seul laisserait croire que la
    mémoire est le sujet. Elle n'est qu'un exemple : un cgroup plafonne la
    mémoire, le temps processeur, le nombre de processus, les entrées-sorties.
    Le nombre de processus est le second parce qu'il protège d'une panne
    différente, celle qui remplit la table des processus de la machine.

    Les deux sont vérifiées DANS le cgroup et non dans `.HostConfig` : ce que
    l'option a demandé n'est pas ce que le noyau applique, et c'est le noyau qui
    décide.
    """
    chemin = _cgroup(host, BRIDE)
    memoire = _valeur(host, chemin, "memory.max")
    assert memoire, message(
        en=f"`{BRIDE}`'s cgroup does not exist or is unreadable.\n"
           "The container has to be running for the kernel to hold its cgroup.",
        fr=f"le cgroup de `{BRIDE}` n'existe pas ou est illisible.\n"
           "Le conteneur doit tourner pour que le noyau tienne son cgroup.",
    )
    assert memoire == str(MEMOIRE_A_POSER), message(
        en=f"`{BRIDE}` declares a memory limit of `{memoire}`, expected "
           f"{MEMOIRE_A_POSER}.\n"
           "That is 128 Mo in bytes: the kernel knows no units. The limit is "
           "read in the cgroup, not in the option that was asked for.",
        fr=f"`{BRIDE}` déclare une limite mémoire de `{memoire}`, attendu "
           f"{MEMOIRE_A_POSER}.\n"
           "C'est 128 Mo en octets : le noyau ne connaît pas les unités. La "
           "limite se lit dans le cgroup, pas dans l'option qui l'a demandée.",
    )

    pids = _valeur(host, chemin, "pids.max")
    assert pids == str(PIDS_A_POSER), message(
        en=f"`{BRIDE}` declares a process limit of `{pids}`, expected "
           f"{PIDS_A_POSER}.\n"
           "A cgroup caps more than memory. The number of processes protects "
           "against a different failure: the one that fills the machine's "
           "process table, where a memory limit would change nothing.",
        fr=f"`{BRIDE}` déclare une limite de processus de `{pids}`, attendu "
           f"{PIDS_A_POSER}.\n"
           "Un cgroup plafonne autre chose que la mémoire. Le nombre de "
           "processus protège d'une panne différente : celle qui remplit la "
           "table des processus de la machine, où une limite mémoire ne "
           "changerait rien.",
    )
