"""Tests fonctionnels du lab container-ulimits-et-shm : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que deux réglages qu'on ne regarde jamais décident du
sort d'un conteneur, et qu'ils ne sont pas de la même famille. Les cgroups
plafonnent depuis l'extérieur ; les ulimits sont un mécanisme POSIX, antérieur,
que le processus porte lui-même. Les chercher au même endroit est l'erreur que
ce lab lève.

MESURÉ SUR docker.lab LE 2026-10-30 :

| Fait | Valeur |
| `/dev/shm` par défaut | 64 Mo, et c'est un tmpfs |
| `ulimit -n` par défaut | **1073741816** |
| `--shm-size 64m` | `.HostConfig.ShmSize` = 67108864 |
| `--ulimit nofile=256:256` | `ulimit -n` = 256 dans le conteneur |

LA DEUXIÈME LIGNE SURPREND, et c'est pour cela qu'elle est demandée : la limite
de descripteurs n'est pas le problème des conteneurs modernes, c'est son
RÉGLAGE À LA BAISSE qui en crée un. Un apprenant qui lit ce nombre et croit
s'être trompé a appris quelque chose de plus utile qu'une valeur.

LA LEÇON MAJEURE EST LE QUATRIÈME CONTRÔLE. Le tmpfs de `/dev/shm` compte dans
`memory.current` du cgroup : écrire 128 Mo dedans fait monter la mémoire du
conteneur de 128 Mo. Une limite mémoire doit donc tenir compte de la taille de
`/dev/shm`, sans quoi le conteneur se fait tuer pour une mémoire qu'il croyait
« à part ». C'est une cause réelle de mort inexpliquée, et elle ne se lit dans
aucune documentation d'application.

AUCUNE VALEUR PAR DÉFAUT N'EST ÉCRITE EN DUR. Les deux premières réponses sont
vérifiées en lançant un conteneur neuf au moment de la notation : le jour où
Docker changera ses défauts, ces contrôles suivront au lieu de devenir faux.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
indispensable pour lire `/sys/fs/cgroup`.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

ETROIT = "etroit"
TAG = "lab-ulimits:1.0"
ATELIER = "/opt/lab-ulimits"
REPONSES = f"{ATELIER}/reponses.txt"
SHM_DEMANDE_MO = 256
NOFILE_DEMANDE = 1024
A_ECRIRE_MO = 128

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
def defauts(host) -> dict[str, str]:
    """Les deux valeurs par défaut, mesurées sur un conteneur neuf.

    Mesurées et non écrites : le jour où Docker changera ses défauts, les deux
    premiers contrôles suivront au lieu de devenir faux. Un seul conteneur
    jetable répond aux deux questions.
    """
    res = host.run(
        "docker run --rm %s sh -c %s",
        TAG, "df -m /dev/shm | tail -1 | awk '{print $2}'; ulimit -n",
    )
    lignes = [ligne.strip() for ligne in res.stdout.splitlines() if ligne.strip()]
    if res.rc != 0 or len(lignes) < 2:
        pytest.skip(message(
            en=f"cannot measure the defaults with image {TAG}: "
               f"{res.stderr.strip()}",
            fr=f"impossible de mesurer les défauts avec l'image {TAG} : "
               f"{res.stderr.strip()}",
        ))
    return {"shm": lignes[0], "nofile": lignes[1]}


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
               "shm_defaut_mo= and nofile_defaut=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire deux "
               "lignes : shm_defaut_mo= et nofile_defaut=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def test_la_reponse_dit_la_taille_par_defaut_de_la_memoire_partagee(
    host, defauts
) -> None:
    """Soixante-quatre mégaoctets, et personne ne le sait avant d'en manquer.

    C'est une valeur qui suffit à presque tout et qui ne suffit pas à une base
    de données, laquelle s'en sert pour ses tampons. Le symptôme est alors un
    message d'erreur sur la mémoire partagée, sans aucun rapport apparent avec
    un conteneur.
    """
    annonce = _lire_reponses(host).get("shm_defaut_mo", "")
    assert annonce, message(
        en="the `shm_defaut_mo=` line is empty. Start a container with no "
           "option and ask it how big its /dev/shm is.",
        fr="la ligne `shm_defaut_mo=` est vide. Lancez un conteneur sans aucune "
           "option et demandez-lui la taille de son /dev/shm.",
    )
    chiffres = "".join(c for c in annonce if c.isdigit())
    assert chiffres == defauts["shm"], message(
        en=f"the announced size is not the default one.\n"
           f"  you wrote : {annonce}\n"
           "The answer is expected in megabytes, without a unit, as the "
           "measurement gives it.",
        fr=f"la taille annoncée n'est pas celle du défaut.\n"
           f"  vous avez écrit : {annonce}\n"
           "La réponse est attendue en mégaoctets, sans unité, telle que la "
           "mesure la donne.",
    )


def test_la_reponse_dit_la_limite_de_descripteurs_par_defaut(host, defauts) -> None:
    """Le nombre qui surprend, et c'est pour cela qu'il est demandé.

    La limite de descripteurs n'est pas le problème des conteneurs modernes :
    elle est énorme par défaut. C'est son réglage À LA BAISSE qui en crée un, et
    savoir d'où l'on part est ce qui permet de reconnaître un réglage hérité
    d'un autre temps.
    """
    annonce = _lire_reponses(host).get("nofile_defaut", "")
    assert annonce, message(
        en="the `nofile_defaut=` line is empty. The same container answers it, "
           "and the value is surprising: it is not a reading error.",
        fr="la ligne `nofile_defaut=` est vide. Le même conteneur y répond, et "
           "la valeur surprend : ce n'est pas une erreur de lecture.",
    )
    assert annonce.replace(" ", "") == defauts["nofile"], message(
        en=f"the announced limit is not the default one.\n"
           f"  you wrote : {annonce}\n"
           "The value is surprising by its size, and that is the point: the "
           "descriptor limit is not modern containers' problem, lowering it is.",
        fr=f"la limite annoncée n'est pas celle du défaut.\n"
           f"  vous avez écrit : {annonce}\n"
           "La valeur surprend par sa taille, et c'est le but : la limite de "
           "descripteurs n'est pas le problème des conteneurs modernes, c'est "
           "son abaissement qui en est un.",
    )


def test_le_conteneur_porte_les_deux_reglages(host) -> None:
    """Deux réglages, deux familles, et ils se lisent à deux endroits.

    La taille de la mémoire partagée est un montage, que l'inspection déclare
    et que le conteneur voit comme un système de fichiers. La limite de
    descripteurs est un ulimit, que le processus porte et que seul le conteneur
    peut dire.

    Les contrôler tous les deux DANS le conteneur est délibéré : c'est le seul
    endroit où les deux sont vrais en même temps, et c'est ce qui fait sentir
    qu'ils ne sont pas de la même nature.
    """
    etat = host.run(
        "docker container inspect %s --format %s", ETROIT, "{{.State.Status}}"
    )
    assert etat.rc == 0, message(
        en=f"no container named `{ETROIT}` exists. It has to be started with "
           f"both settings: a /dev/shm of {SHM_DEMANDE_MO} Mo and a limit of "
           f"{NOFILE_DEMANDE} file descriptors.",
        fr=f"aucun conteneur nommé `{ETROIT}` n'existe. Il faut le lancer avec "
           f"les deux réglages : un /dev/shm de {SHM_DEMANDE_MO} Mo et une "
           f"limite de {NOFILE_DEMANDE} descripteurs de fichiers.",
    )
    assert etat.stdout.strip() == "running", message(
        en=f"`{ETROIT}` is in state `{etat.stdout.strip()}`, not `running`: a "
           "stopped container answers nothing.",
        fr=f"`{ETROIT}` est dans l'état `{etat.stdout.strip()}`, pas "
           "`running` : un conteneur arrêté ne répond rien.",
    )

    taille = host.run(
        "docker exec %s sh -c %s",
        ETROIT, "df -m /dev/shm | tail -1 | awk '{print $2}'",
    )
    assert taille.stdout.strip() == str(SHM_DEMANDE_MO), message(
        en=f"`{ETROIT}`'s /dev/shm is {taille.stdout.strip() or '?'} Mo, "
           f"expected {SHM_DEMANDE_MO}.\n"
           "Its size is set at the container's creation, like a mount: it "
           "cannot be changed afterwards.",
        fr=f"le /dev/shm de `{ETROIT}` fait {taille.stdout.strip() or '?'} Mo, "
           f"attendu {SHM_DEMANDE_MO}.\n"
           "Sa taille se fixe à la création du conteneur, comme un montage : "
           "elle ne se change pas après coup.",
    )

    nofile = host.run("docker exec %s sh -c %s", ETROIT, "ulimit -n")
    assert nofile.stdout.strip() == str(NOFILE_DEMANDE), message(
        en=f"`{ETROIT}` declares {nofile.stdout.strip() or '?'} descriptors, "
           f"expected {NOFILE_DEMANDE}.\n"
           "That one is not a cgroup: it is a POSIX limit the process carries "
           "itself, which is why only the container can state it.",
        fr=f"`{ETROIT}` déclare {nofile.stdout.strip() or '?'} descripteurs, "
           f"attendu {NOFILE_DEMANDE}.\n"
           "Celle-là n'est pas un cgroup : c'est une limite POSIX que le "
           "processus porte lui-même, et c'est pourquoi seul le conteneur peut "
           "la dire.",
    )


def test_la_memoire_partagee_compte_dans_la_memoire_du_conteneur(host) -> None:
    """La leçon majeure du lab, et elle se pèse.

    `/dev/shm` est un tmpfs, donc de la mémoire, et cette mémoire est comptée
    dans le cgroup du conteneur. Écrire dedans fait monter `memory.current`
    d'autant.

    Conséquence : une limite mémoire doit tenir compte de la taille de
    `/dev/shm`, sans quoi le conteneur se fait tuer pour une mémoire qu'il
    croyait « à part ». C'est une cause réelle de mort inexpliquée, et elle ne
    se lit dans aucune documentation d'application.
    """
    occupe = host.run(
        "docker exec %s sh -c %s",
        ETROIT, "df -m /dev/shm | tail -1 | awk '{print $3}'",
    )
    try:
        ecrits = int(occupe.stdout.strip())
    except ValueError:
        pytest.fail(message(
            en=f"cannot read how much of `{ETROIT}`'s /dev/shm is used: "
               f"{occupe.stderr.strip()}",
            fr=f"impossible de lire l'occupation du /dev/shm de `{ETROIT}` : "
               f"{occupe.stderr.strip()}",
        ))
    assert ecrits >= A_ECRIRE_MO, message(
        en=f"`{ETROIT}`'s /dev/shm holds {ecrits} Mo, expected at least "
           f"{A_ECRIRE_MO}.\n"
           "The point of the lab is to see what writing there does to the "
           "container's memory, and that needs something written.",
        fr=f"le /dev/shm de `{ETROIT}` porte {ecrits} Mo, attendu au moins "
           f"{A_ECRIRE_MO}.\n"
           "Tout l'intérêt du lab est de voir ce qu'une écriture là-dedans fait "
           "à la mémoire du conteneur, et cela demande d'y avoir écrit.",
    )

    res = host.run("docker container inspect %s --format %s", ETROIT, "{{.Id}}")
    cgroup = f"/sys/fs/cgroup/system.slice/docker-{res.stdout.strip()}.scope"
    courante = host.run("cat %s/memory.current", cgroup)
    try:
        megaoctets = int(courante.stdout.strip()) // (1024 * 1024)
    except ValueError:
        pytest.skip(message(
            en=f"{cgroup}/memory.current is unreadable",
            fr=f"{cgroup}/memory.current est illisible",
        ))
    assert megaoctets >= A_ECRIRE_MO, message(
        en=f"`{ETROIT}`'s cgroup declares {megaoctets} Mo of memory in use, "
           f"while {ecrits} Mo were written into its /dev/shm.\n"
           "That is the lesson, and it is measured here: shared memory is NOT "
           "a separate space. It counts in the container's memory, and a memory "
           "limit must take the size of /dev/shm into account.",
        fr=f"le cgroup de `{ETROIT}` déclare {megaoctets} Mo de mémoire en "
           f"usage, alors que {ecrits} Mo ont été écrits dans son /dev/shm.\n"
           "C'est la leçon, et elle se mesure ici : la mémoire partagée n'est "
           "PAS un espace à part. Elle compte dans la mémoire du conteneur, et "
           "une limite mémoire doit tenir compte de la taille de /dev/shm.",
    )
