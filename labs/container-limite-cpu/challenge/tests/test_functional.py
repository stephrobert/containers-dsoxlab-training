"""Tests fonctionnels du lab container-limite-cpu : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'il y a DEUX façons de limiter le processeur d'un
conteneur, qu'elles n'ont pas le même effet, et que la plus employée ne change
RIEN à ce que le conteneur croit avoir.

MESURÉ SUR docker.lab LE 2026-10-30, sur une machine à 2 CPU :

| Option | `cpu.max` | `cpuset.cpus` | `nproc` DANS le conteneur |
| aucune | `max 100000` | tous | 2 |
| `--cpus 0.5` | `50000 100000` | tous | **2** |
| `--cpuset-cpus 0` | `max 100000` | `0` | **1** |

LE PIÈGE DU SUJET EST SUR LA DEUXIÈME LIGNE. Une limite de TEMPS n'est pas une
restriction de VUE : le conteneur bridé à la moitié d'un CPU en voit toujours
deux. Une application qui dimensionne ses fils d'exécution sur `nproc` en lance
donc deux fois trop, et passe son temps à se faire étrangler. C'est une cause
réelle de lenteur inexpliquée, et elle ne se devine pas.

LE QUATRIÈME CONTRÔLE DEMANDE UNE PREUVE, PAS UNE DÉCLARATION. Le cgroup compte
les étranglements : tant que `nr_throttled` est à zéro, la limite n'a jamais
mordu. Mesuré sous deux boucles infinies : le moteur annonçait 48,97 % et le
compteur 85 étranglements. Une limite qu'on n'a jamais vue mordre est une limite
qu'on croit sur parole.

AUCUNE VALEUR N'EST ÉCRITE EN DUR DANS CE FICHIER. Le quota attendu est lu dans
le cgroup, le nombre de CPU est demandé à la machine, et le lab exige seulement
que le conteneur épinglé en voie MOINS. Un test qui aurait porté `50000 100000`
ou `2` serait faux sur une machine différemment dotée.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
indispensable pour lire `/sys/fs/cgroup`, dont les fichiers d'un conteneur ne
sont pas lisibles par un compte ordinaire.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

BRIDE = "brideur"
EPINGLE = "epingle"
ATELIER = "/opt/lab-cpu"
REPONSES = f"{ATELIER}/reponses.txt"

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

    Sur une machine en cgroup v1, les noms de fichiers diffèrent et les
    contrôles échoueraient en parlant de quotas, alors que la cause serait la
    version du mécanisme.
    """
    res = host.run("stat -fc %T /sys/fs/cgroup")
    if res.stdout.strip() != "cgroup2fs":
        pytest.skip(message(
            en=f"/sys/fs/cgroup is `{res.stdout.strip()}` and not `cgroup2fs`: "
               "this lab measures cgroup v2 files",
            fr=f"/sys/fs/cgroup est en `{res.stdout.strip()}` et non "
               "`cgroup2fs` : ce lab mesure des fichiers de cgroup v2",
        ))


def _cgroup(host, nom: str) -> str:
    """Le chemin du cgroup d'un conteneur, construit depuis son identifiant."""
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
            en=f"{REPONSES} is missing. The mission asks for two lines in it: "
               "quota= and cpu_vus=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire deux "
               "lignes : quota= et cpu_vus=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def test_la_reponse_nomme_le_quota_du_cgroup(host) -> None:
    """Le quota, et il s'écrit en deux nombres, pas en fraction de CPU.

    `--cpus 0.5` ne laisse aucune trace de « 0.5 » : le noyau compte un TEMPS
    par tranche de temps. Le lire explique pourquoi la limite s'exprime ainsi,
    et pourquoi elle s'applique par étranglement plutôt qu'en refusant du
    travail.
    """
    chemin = _cgroup(host, BRIDE)
    attendu = _valeur(host, chemin, "cpu.max")
    if not attendu:
        pytest.skip(message(
            en=f"{chemin}/cpu.max is unreadable: the setup did not finish",
            fr=f"{chemin}/cpu.max est illisible : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("quota", "")
    assert annonce, message(
        en="the `quota=` line is empty. The limit is in the cgroup, and it is "
           "written as two numbers rather than as a fraction of a CPU.",
        fr="la ligne `quota=` est vide. La limite est dans le cgroup, et elle "
           "s'écrit en deux nombres plutôt qu'en fraction de CPU.",
    )
    assert " ".join(annonce.split()) == attendu, message(
        en=f"the announced quota is not the one the cgroup declares.\n"
           f"  you wrote : {annonce}\n"
           "The kernel counts a TIME per slice of time: the fraction used when "
           "setting the limit leaves no trace. The expected answer is the "
           "file's content, as it is.",
        fr=f"le quota annoncé n'est pas celui que le cgroup déclare.\n"
           f"  vous avez écrit : {annonce}\n"
           "Le noyau compte un TEMPS par tranche de temps : la fraction "
           "employée pour poser la limite ne laisse aucune trace. La réponse "
           "attendue est le contenu du fichier, tel quel.",
    )


def test_la_reponse_dit_combien_de_cpu_le_conteneur_voit(host) -> None:
    """Le piège du sujet, et c'est la question la plus utile du lab.

    Une limite de TEMPS n'est pas une restriction de VUE. Le conteneur bridé à
    la moitié d'un CPU en voit toujours autant que la machine, et une
    application qui dimensionne ses fils d'exécution sur ce nombre en lance deux
    fois trop.

    Le contrôle demande à la machine et au conteneur, et vérifie que les deux
    coïncident : c'est cette coïncidence qui EST la leçon.
    """
    dans = host.run("docker exec %s nproc", BRIDE)
    vus = dans.stdout.strip()
    if dans.rc != 0 or not vus:
        pytest.skip(message(
            en=f"`{BRIDE}` does not answer: the setup did not finish",
            fr=f"`{BRIDE}` ne répond pas : le setup n'a pas abouti",
        ))
    sur_l_hote = host.run("nproc").stdout.strip()

    annonce = _lire_reponses(host).get("cpu_vus", "")
    assert annonce, message(
        en=f"the `cpu_vus=` line is empty. Ask `{BRIDE}` itself how many CPUs "
           "it sees, then compare with the machine's count.",
        fr=f"la ligne `cpu_vus=` est vide. Demandez à `{BRIDE}` lui-même combien "
           "de CPU il voit, puis comparez au compte de la machine.",
    )
    assert annonce == vus, message(
        en=f"`{BRIDE}` does not see {annonce} CPUs.\n"
           f"It sees as many as the machine has ({sur_l_hote}), and that is the "
           "lesson: a TIME limit is not a VIEW restriction. An application "
           "sizing its threads on that number launches far too many, and spends "
           "its time being throttled.",
        fr=f"`{BRIDE}` ne voit pas {annonce} CPU.\n"
           f"Il en voit autant que la machine en a ({sur_l_hote}), et c'est la "
           "leçon : une limite de TEMPS n'est pas une restriction de VUE. Une "
           "application qui dimensionne ses fils d'exécution sur ce nombre en "
           "lance bien trop, et passe son temps à se faire étrangler.",
    )


def test_le_conteneur_epingle_voit_moins_de_cpu(host) -> None:
    """L'autre mécanisme, et il change la vue là où le premier ne la change pas.

    Épingler un conteneur sur un sous-ensemble de CPU n'est pas lui donner moins
    de temps : c'est lui donner moins de processeurs. Le cgroup le déclare
    ailleurs, et le conteneur, lui, le voit.

    Le contrôle exige seulement qu'il en voie MOINS que la machine, et non un
    nombre écrit d'avance : sur une machine à huit CPU, épingler sur deux est
    une réponse aussi juste que sur un.
    """
    sur_l_hote = host.run("nproc").stdout.strip()
    etat = host.run(
        "docker container inspect %s --format %s", EPINGLE, "{{.State.Status}}"
    )
    assert etat.rc == 0, message(
        en=f"no container named `{EPINGLE}` exists. It has to be started so "
           "that it sees fewer CPUs than the machine has, which is not the same "
           f"option as the one limiting `{BRIDE}`.",
        fr=f"aucun conteneur nommé `{EPINGLE}` n'existe. Il faut le lancer de "
           "sorte qu'il voie moins de CPU que la machine n'en a, ce qui n'est "
           f"pas la même option que celle qui bride `{BRIDE}`.",
    )
    assert etat.stdout.strip() == "running", message(
        en=f"`{EPINGLE}` is in state `{etat.stdout.strip()}`, not `running`: a "
           "stopped container answers nothing.",
        fr=f"`{EPINGLE}` est dans l'état `{etat.stdout.strip()}`, pas "
           "`running` : un conteneur arrêté ne répond rien.",
    )

    dans = host.run("docker exec %s nproc", EPINGLE)
    vus = dans.stdout.strip()
    assert vus.isdigit(), message(
        en=f"`{EPINGLE}` does not say how many CPUs it sees: "
           f"{dans.stderr.strip()}",
        fr=f"`{EPINGLE}` ne dit pas combien de CPU il voit : "
           f"{dans.stderr.strip()}",
    )
    assert int(vus) < int(sur_l_hote), message(
        en=f"`{EPINGLE}` sees {vus} CPUs, as many as the machine "
           f"({sur_l_hote}).\n"
           "Limiting the time changes nothing in the view, as the previous "
           "check showed. Another option restricts the set of processors "
           "themselves, and that one the container does see.",
        fr=f"`{EPINGLE}` voit {vus} CPU, autant que la machine "
           f"({sur_l_hote}).\n"
           "Limiter le temps ne change rien à la vue, le contrôle précédent "
           "l'a montré. Une autre option restreint l'ensemble des processeurs "
           "eux-mêmes, et celle-là, le conteneur la voit.",
    )

    cgroup = _cgroup(host, EPINGLE)
    declare = _valeur(host, cgroup, "cpuset.cpus")
    assert declare, message(
        en=f"`{EPINGLE}`'s cgroup declares no processor set: it sees fewer CPUs "
           "for another reason, which is not what the lab asks for.",
        fr=f"le cgroup de `{EPINGLE}` ne déclare aucun ensemble de processeurs : "
           "il voit moins de CPU pour une autre raison, qui n'est pas celle que "
           "le lab demande.",
    )


def test_la_limite_a_reellement_mordu(host) -> None:
    """La preuve, et non la déclaration.

    Le cgroup compte les étranglements. Tant que ce compteur est à zéro, la
    limite n'a jamais mordu : elle est peut-être juste, et elle n'est pas
    prouvée.

    C'est la différence entre lire une configuration et constater un
    comportement, et c'est la seule qui compte le jour où une application est
    lente sans qu'on sache pourquoi.
    """
    chemin = _cgroup(host, BRIDE)
    stat = _valeur(host, chemin, "cpu.stat")
    if not stat:
        pytest.skip(message(
            en=f"{chemin}/cpu.stat is unreadable: the setup did not finish",
            fr=f"{chemin}/cpu.stat est illisible : le setup n'a pas abouti",
        ))

    etrangles = 0
    for ligne in stat.splitlines():
        if ligne.startswith("nr_throttled"):
            morceaux = ligne.split()
            if len(morceaux) > 1 and morceaux[1].isdigit():
                etrangles = int(morceaux[1])
    assert etrangles > 0, message(
        en=f"`{BRIDE}`'s cgroup counts no throttling.\n"
           "The limit has therefore never bitten: it may well be right, and it "
           "is not proven. Put the container under enough load for the kernel "
           "to have to hold it back, then read the counter again.",
        fr=f"le cgroup de `{BRIDE}` ne compte aucun étranglement.\n"
           "La limite n'a donc jamais mordu : elle est peut-être juste, et elle "
           "n'est pas prouvée. Mettez le conteneur sous une charge suffisante "
           "pour que le noyau doive le retenir, puis relisez le compteur.",
    )
