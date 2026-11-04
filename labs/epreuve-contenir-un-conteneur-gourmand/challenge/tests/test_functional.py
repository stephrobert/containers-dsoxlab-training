"""Tests fonctionnels de l'épreuve du conteneur gourmand : cinq contrôles de poids égal.

C'EST UNE ÉPREUVE : les messages nomment ce qui manque à l'état final, jamais
l'option de `docker run` qui l'apporterait.

L'EXIGENCE CRITIQUE est le contrôle 4 : les résultats antérieurs perdus. C'est le
piège de l'épreuve, et il est entier : poser des limites exige de RECRÉER le
conteneur, et c'est là qu'on perd un volume qu'on a oublié de remonter. Aucun
total ne compense une donnée perdue.

CE QUE LA MESURE A ÉTABLI, et qui fonde le contrôle de la pointe. Sur cette
machine, le 2026-11-04, avec une chaîne de 268 Mo dont la pointe atteint 404 Mo :

    sans limite    l'allocation réussit, 536 870 912 octets, l'hôte tient ;
    avec 128 Mo    le cgroup tue l'ENFANT gourmand (`oom_kill 1`), le PID 1
                   survit, et le conteneur reste `running`.

Le contrôle lit donc `memory.peak` et `memory.events` du cgroup : la limite a
mordu, et le service a survécu. Un contrôle qui se contenterait de lire la
limite déclarée ne dirait pas si elle AGIT.

LA POINTE EST BORNÉE À DESSEIN. Un `tail /dev/zero`, qui alloue sans fin, aurait
fait tuer sshd ou le démon par l'OOM de l'hôte au premier passage sans limite :
une épreuve ne doit pas pouvoir emporter la machine qui la mesure.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, ce qui permet de lire le relevé du lab dans
`/root`.
"""

from __future__ import annotations

import json
import re
import time

import pytest

from conftest import lab_host, message

CONTENEUR = "traitement"
IMAGE = "lab-gourmand:1.0"
VOLUME = "dsoxlab-gourmand-resultats"
ATELIER = "/opt/lab-gourmand"
RELEVE_APPRENANT = f"{ATELIER}/releve.txt"
ETAT = "/root/.lab-gourmand-state.json"
RESULTATS = "/resultats"
DECLENCHEUR = "/tmp/pointe"  # noqa: S108 -- le fichier vit sur la machine du lab, jamais sur un poste partagé
LIGNE_DE_FIN = "fin du lot"

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
    """Les empreintes des résultats antérieurs, prises par le `run`.

    L'empreinte, et non la seule liste des noms : le contrôle doit distinguer
    « les fichiers sont là » de « les fichiers sont intacts ». Un volume recréé
    vide, puis regarni par le traitement, porterait des noms plausibles et un
    contenu différent.
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


def test_les_trois_limites_sont_posees_et_appliquees(host) -> None:
    """Trois limites, et chacune lue à DEUX endroits.

    L'inspection dit ce que le moteur a RETENU, le cgroup dit ce que le noyau
    APPLIQUE. Les deux peuvent différer, et le cas est courant : une limite
    changée sur un conteneur existant n'est pas appliquée, parce qu'un cgroup se
    pose à la création. Lire les deux est la seule façon de ne pas valider une
    intention.

    Aucune valeur n'est imposée. Une limite trop basse tuerait le service, et le
    contrôle de la réponse après la pointe le verrait.
    """
    etat = _inspecte(host)
    hote = etat["HostConfig"]

    memoire = int(hote.get("Memory") or 0)
    assert memoire > 0, message(
        en="the container carries no memory limit the engine retained.\n"
           "  HostConfig.Memory: 0\n"
           "Two routes set one: recreating the container, or `docker update` on "
           "the running one. Both work; recreating is where a volume gets lost.",
        fr="le conteneur ne porte aucune limite mémoire que le moteur ait "
           "retenue.\n"
           "  HostConfig.Memory : 0\n"
           "Deux voies en posent une : recréer le conteneur, ou `docker update` "
           "sur celui qui tourne. Les deux marchent ; c'est en recréant qu'un "
           "volume se perd.",
    )
    processus = int(hote.get("PidsLimit") or 0)
    assert processus > 0, message(
        en="the container carries no limit on its number of processes.\n"
           "  HostConfig.PidsLimit: 0\n"
           "Without it, a loop that forks fills the host's process table, and "
           "nothing can be started any more, not even to diagnose it.",
        fr="le conteneur ne porte aucune limite sur son nombre de processus.\n"
           "  HostConfig.PidsLimit : 0\n"
           "Sans elle, une boucle qui se duplique remplit la table des "
           "processus de l'hôte, et plus rien ne peut être lancé, pas même pour "
           "diagnostiquer.",
    )
    quota = int(hote.get("CpuQuota") or 0)
    parts = int(hote.get("NanoCpus") or 0)
    assert quota > 0 or parts > 0, message(
        en="the container carries no CPU limit.\n"
           f"  CpuQuota: {quota}, NanoCpus: {parts}\n"
           "A batch job with no CPU limit slows down everything else on the "
           "machine, including whatever would let you observe it.",
        fr="le conteneur ne porte aucune limite de processeur.\n"
           f"  CpuQuota : {quota}, NanoCpus : {parts}\n"
           "Un traitement par lots sans limite de processeur ralentit tout le "
           "reste de la machine, y compris ce qui permettrait de l'observer.",
    )

    # ET LE NOYAU LES APPLIQUE. `memory.max` et `pids.max` portent un nombre,
    # `cpu.max` deux champs dont le premier vaut `max` quand rien ne limite.
    for fichier, attendu in (("memory.max", memoire), ("pids.max", processus)):
        brut = _cgroup(host, fichier)
        assert brut and brut != "max", message(
            en=f"the kernel applies no limit through `{fichier}`.\n"
               f"  read: {brut or '(unreadable)'}",
            fr=f"le noyau n'applique aucune limite par `{fichier}`.\n"
               f"  lu : {brut or '(illisible)'}",
        )
        assert int(brut) == attendu, message(
            en=f"`{fichier}` does not carry the declared limit.\n"
               f"  declared: {attendu}\n  applied : {brut}",
            fr=f"`{fichier}` ne porte pas la limite déclarée.\n"
               f"  déclarée : {attendu}\n  appliquée : {brut}",
        )
    cpu = _cgroup(host, "cpu.max")
    assert cpu and not cpu.startswith("max"), message(
        en=f"the kernel applies no CPU limit.\n  cpu.max: {cpu or '(unreadable)'}\n"
           "`max` as the first field means no quota at all.",
        fr=f"le noyau n'applique aucune limite de processeur.\n"
           f"  cpu.max : {cpu or '(illisible)'}\n"
           "`max` en premier champ signifie aucun quota.",
    )


def test_la_pointe_est_contenue_par_la_limite(host, releve) -> None:
    """La limite AGIT, et cela se mesure en provoquant la pointe.

    Lire une limite déclarée ne dit pas si elle contient quoi que ce soit. Le
    contrôle déclenche donc la pointe, puis lit le cgroup :

      `memory.peak`   le plus haut niveau atteint. Il ne doit pas dépasser la
                      limite, ce qui est la définition même de « contenu » ;
      `memory.events` le compteur `max`, qui dit combien de fois la limite a été
                      atteinte, et `oom_kill`, qui dit que le noyau a tué dans
                      ce cgroup. Un `max` à zéro après une pointe de 404 Mo
                      signifierait que la pointe n'a pas eu lieu.

    ET L'HÔTE N'A RIEN PERDU : le contrôle vérifie qu'aucun processus de l'hôte
    n'a été tué par manque de mémoire pendant la pointe. C'est le vrai sujet :
    un conteneur sans limite ne se punit pas lui-même, il punit son voisin.
    """
    _inspecte(host)
    avant_oom = _oom_de_l_hote(host)

    pose = host.run("docker exec %s touch %s", CONTENEUR, DECLENCHEUR)
    assert pose.rc == 0, message(
        en=f"the pointe trigger could not be placed:\n"
           f"  {pose.stderr.strip()[:200]}",
        fr=f"le déclencheur de pointe n'a pas pu être posé :\n"
           f"  {pose.stderr.strip()[:200]}",
    )
    # Le traitement évalue le déclencheur après chaque requête servie.
    _interroge(host)

    evenements = ""
    for _ in range(40):
        time.sleep(1)
        evenements = _cgroup(host, "memory.events")
        if re.search(r"\bmax (\d+)", evenements) and int(
            re.search(r"\bmax (\d+)", evenements).group(1)
        ) > 0:
            break
    limite = _cgroup_nombre(host, "memory.max")

    assert limite > 0, message(
        en="there is no memory limit to contain the pointe with.",
        fr="il n'y a aucune limite mémoire pour contenir la pointe.",
    )
    # IL N Y A PLUS D ASSERTION `pic <= limite` ICI, ET C EST MESURÉ.
    #
    # Elle comparait `memory.peak` à `memory.max`. Or `memory.peak` retient le
    # maximum depuis la CRÉATION du cgroup, et il n est pas réinitialisable
    # depuis le conteneur : « Read-only file system ». Relevé sur docker.lab,
    # Docker 29.9.2 :
    #
    #     conteneur sans limite, pointe de 128 Mio   memory.peak = 202567680
    #     puis docker update --memory 64m            memory.peak = 202567680
    #     la limite appliquée                        memory.max  =  67108864
    #
    # Un candidat qui OBSERVE la pointe avant d agir, ce qui est le geste de
    # diagnostic que l épreuve veut encourager, puis pose la limite par
    # `docker update`, échouait donc avec le diagnostic « a dépassé sa propre
    # limite ». Il ne l avait pas dépassée : il l avait posée après.
    #
    # Cette assertion ne pouvait refuser QUE dans ce cas. Un cgroup n autorise
    # pas le dépassement de sa propre limite, donc `pic > limite` ne signifie
    # jamais autre chose qu une pointe antérieure à la pose. Elle ne refusait
    # que les candidats qui avaient bien travaillé.
    #
    # ET ELLE N APPORTAIT RIEN : l assertion suivante lit `memory.events`, dont
    # le compteur `max` dit combien de fois la limite a été ATTEINTE pendant la
    # pointe que ce contrôle déclenche lui-même. C est un différentiel, donc il
    # est insensible à l histoire du cgroup, et c est la seule mesure qui prouve
    # que la limite mord.
    atteintes = re.search(r"\bmax (\d+)", evenements)
    assert atteintes and int(atteintes.group(1)) > 0, message(
        en=f"the limit was never reached, so the pointe did not take place.\n"
           f"  memory.events: {evenements or '(unreadable)'}\n"
           f"  the lab asks for about {releve['pointe_mo']} MB to be allocated\n"
           "A check that passes without the pointe having happened measures "
           "nothing.",
        fr=f"la limite n'a jamais été atteinte, donc la pointe n'a pas eu "
           f"lieu.\n  memory.events : {evenements or '(illisible)'}\n"
           f"  le lab demande d'allouer environ {releve['pointe_mo']} Mo\n"
           "Un contrôle qui passe sans que la pointe ait eu lieu ne mesure "
           "rien.",
    )

    apres_oom = _oom_de_l_hote(host)
    assert apres_oom <= avant_oom, message(
        en=f"the host killed processes for lack of memory during the pointe.\n"
           f"  host OOM kills: {avant_oom} then {apres_oom}\n"
           "A container with no limit does not punish itself, it punishes its "
           "neighbour.",
        fr=f"l'hôte a tué des processus par manque de mémoire pendant la "
           f"pointe.\n  OOM de l'hôte : {avant_oom} puis {apres_oom}\n"
           "Un conteneur sans limite ne se punit pas lui-même, il punit son "
           "voisin.",
    )


def test_le_traitement_repond_encore_apres_la_pointe(host) -> None:
    """Contenir n'est pas tuer, et c'est toute la différence.

    Une limite bien posée tue le processus gourmand, pas le service. Le
    traitement doit donc répondre encore : s'il est mort avec son enfant, la
    limite a protégé l'hôte en sacrifiant l'application, ce qui n'est pas ce
    qu'on cherche.

    Ce contrôle est séparé du précédent parce que sa cause est différente : il
    peut échouer avec une limite parfaitement posée, si elle est trop basse pour
    le service lui-même.

    IL EXIGE D'ABORD QU'UNE LIMITE EXISTE, et ce n'est pas une redondance avec
    le premier contrôle : sans cette exigence, il passait AVANT tout travail,
    puisqu'un service sans aucune limite répond parfaitement. Mesuré le
    2026-11-02 par le cycle de validation, qui l'a compté comme « un test qui
    passe avant le travail ». La phrase que ce contrôle mesure n'est pas « le
    service répond », c'est « le service répond ENCORE, alors qu'une limite l'a
    contenu ».
    """
    limite = _cgroup_nombre(host, "memory.max")
    assert limite > 0, message(
        en="there is no memory limit, so there is nothing to have survived.\n"
           "This check measures that the service answers DESPITE being "
           "contained, not that it answers.",
        fr="il n'y a aucune limite mémoire, donc rien à quoi survivre.\n"
           "Ce contrôle mesure que le service répond MALGRÉ la contention, pas "
           "qu'il répond.",
    )
    etat = _inspecte(host)
    statut = etat["State"]["Status"]
    assert statut == "running", message(
        en=f"after the pointe, `{CONTENEUR}` is `{statut}`.\n"
           "A well-set limit kills the greedy process, not the service. If the "
           "whole container died, the limit is protecting the host by "
           "sacrificing the application.",
        fr=f"après la pointe, `{CONTENEUR}` est `{statut}`.\n"
           "Une limite bien posée tue le processus gourmand, pas le service. Si "
           "le conteneur entier est mort, la limite protège l'hôte en "
           "sacrifiant l'application.",
    )
    recu = _interroge(host)
    assert "traitement=pret" in recu, message(
        en=f"after the pointe, the batch job no longer answers.\n"
           f"  what came back: {recu.strip()[:200] or '(nothing)'}",
        fr=f"après la pointe, le traitement ne répond plus.\n"
           f"  ce qui revient : {recu.strip()[:200] or '(rien)'}",
    )


def test_les_resultats_anterieurs_sont_intacts_et_aucun_n_est_tronque(
    host, releve
) -> None:
    """L'EXIGENCE CRITIQUE : les données d'avant, et elles ne se reproduisent pas.

    C'est le piège de l'épreuve, et il est entier : poser des limites exige de
    RECRÉER le conteneur, et c'est là qu'on perd un volume qu'on a oublié de
    remonter. Le traitement regarnit alors `/resultats` avec des fichiers de
    noms plausibles, et tout a l'air normal.

    LE CONTRÔLE COMPARE DES EMPREINTES, pas des noms. C'est ce qui distingue
    « les fichiers sont là » de « les fichiers sont intacts ».

    ET AUCUN FICHIER N'EST TRONQUÉ : chacun doit porter sa ligne de fin. Le
    traitement écrit de façon atomique, par un temporaire puis un renommage :
    un fichier incomplet signifie donc qu'il a été écrit autrement, ou qu'un
    volume a été remplacé en cours de route.
    """
    attendues = releve["anterieurs"]
    assert attendues, message(
        en="the lab's own measurement carries no digest of the earlier results. It is taken during `dsoxlab run`: replay it.",
        fr="la mesure prise par le lab ne porte aucune empreinte des résultats antérieurs. Elle est faite pendant `dsoxlab run` : rejouez-le.",
    )

    lu = host.run(
        "docker exec %s sh -c %s",
        CONTENEUR,
        f"cd {RESULTATS} && sha256sum lot-anterieur-*.txt 2>/dev/null | sort",
    )
    trouvees = {}
    for ligne in lu.stdout.splitlines():
        morceaux = ligne.split()
        if len(morceaux) == 2:
            trouvees[morceaux[1]] = morceaux[0]

    manquants = sorted(set(attendues) - set(trouvees))
    assert not manquants, message(
        en="earlier results have disappeared:\n"
           + "\n".join(f"  {n}" for n in manquants) + "\n"
           "Setting a limit requires recreating the container, and that is "
           "where a volume gets forgotten. Those results do not come back, and "
           "no total makes up for them.",
        fr="des résultats antérieurs ont disparu :\n"
           + "\n".join(f"  {n}" for n in manquants) + "\n"
           "Poser une limite exige de recréer le conteneur, et c'est là qu'un "
           "volume s'oublie. Ces résultats ne reviennent pas, et aucun total ne "
           "les compense.",
    )
    alteres = sorted(n for n, e in attendues.items() if trouvees.get(n) != e)
    assert not alteres, message(
        en="earlier results are present but altered:\n"
           + "\n".join(f"  {n}" for n in alteres) + "\n"
           "The names are plausible and the contents are not the same: the "
           "volume was replaced, and the batch job refilled it.",
        fr="des résultats antérieurs sont présents mais altérés :\n"
           + "\n".join(f"  {n}" for n in alteres) + "\n"
           "Les noms sont plausibles et le contenu ne l'est pas : le volume a "
           "été remplacé, et le traitement l'a regarni.",
    )

    # ET AUCUN FICHIER, ancien ou nouveau, n'est tronqué.
    incomplets = host.run(
        "docker exec %s sh -c %s",
        CONTENEUR,
        f"cd {RESULTATS} && for f in *.txt; do "
        f"grep -q '{LIGNE_DE_FIN}' \"$f\" || echo \"$f\"; done",
    )
    fautifs = [ligne.strip() for ligne in incomplets.stdout.splitlines() if ligne.strip()]
    assert not fautifs, message(
        en="these result files are truncated:\n"
           + "\n".join(f"  {n}" for n in fautifs) + "\n"
           f"A complete file carries its `{LIGNE_DE_FIN}` line. The batch job "
           "writes atomically, so an incomplete file means it was written some "
           "other way.",
        fr="ces fichiers de résultats sont tronqués :\n"
           + "\n".join(f"  {n}" for n in fautifs) + "\n"
           f"Un fichier complet porte sa ligne `{LIGNE_DE_FIN}`. Le traitement "
           "écrit de façon atomique : un fichier incomplet signifie qu'il a été "
           "écrit autrement.",
    )


def test_le_releve_dit_le_pid_hote_et_le_runtime(host) -> None:
    """Deux faits que seul le moteur connaît, et que l'apprenant doit consigner.

    LE PID HÔTE DU PID 1 est la jointure entre les deux mondes : le processus
    qui se croit seul et numéro un dans son conteneur porte un autre numéro sur
    la machine, et c'est celui-là qu'on voit dans `ps`, dans `top`, et dans un
    journal du noyau. Qui ne sait pas faire cette jointure ne peut pas rattacher
    une trace de l'hôte à un conteneur.

    LE RUNTIME PAR DÉFAUT est l'autre bout de la chaîne : c'est le programme qui
    crée réellement le conteneur sous le démon.

    LE CONTRÔLE RECALCULE LES DEUX et compare. Il ne garde aucune valeur en dur :
    le PID change à chaque démarrage, et le runtime dépend de la machine.
    """
    lu = host.run("cat %s", RELEVE_APPRENANT)
    assert lu.rc == 0, message(
        en=f"the file `{RELEVE_APPRENANT}` does not exist. The brief asks for "
           "two lines in it, `pid_hote=` and `runtime=`.",
        fr=f"le fichier `{RELEVE_APPRENANT}` n'existe pas. L'énoncé y demande "
           "deux lignes, `pid_hote=` et `runtime=`.",
    )
    annonce = {}
    for ligne in lu.stdout.splitlines():
        trouve = re.match(r"\s*(pid_hote|runtime)\s*=\s*(\S+)\s*$", ligne)
        if trouve:
            annonce[trouve.group(1)] = trouve.group(2)

    etat = _inspecte(host)
    pid_reel = str(etat["State"]["Pid"])
    assert annonce.get("pid_hote") == pid_reel, message(
        en=f"the announced host PID is not the one the engine reports.\n"
           f"  you wrote: {annonce.get('pid_hote') or '(nothing)'}\n"
           "It is the number the container's PID 1 carries ON THE HOST, the one "
           "`ps` and the kernel log show.",
        fr=f"le PID hôte annoncé n'est pas celui que le moteur déclare.\n"
           f"  vous avez écrit : {annonce.get('pid_hote') or '(rien)'}\n"
           "C'est le numéro que le PID 1 du conteneur porte SUR L'HÔTE, celui "
           "que montrent `ps` et le journal du noyau.",
    )

    info = host.run("docker info --format %s", "{{.DefaultRuntime}}")
    runtime_reel = info.stdout.strip()
    assert runtime_reel, message(
        en="the engine does not report a default runtime.",
        fr="le moteur ne déclare aucun runtime par défaut.",
    )
    assert annonce.get("runtime") == runtime_reel, message(
        en=f"the announced runtime is not the engine's default.\n"
           f"  you wrote: {annonce.get('runtime') or '(nothing)'}\n"
           "It is the program that actually creates containers under the "
           "daemon.",
        fr=f"le runtime annoncé n'est pas celui du moteur par défaut.\n"
           f"  vous avez écrit : {annonce.get('runtime') or '(rien)'}\n"
           "C'est le programme qui crée réellement les conteneurs sous le "
           "démon.",
    )


def _inspecte(host) -> dict:
    """L'inspection complète du conteneur, ou un échec qui nomme l'absence."""
    res = host.run("docker container inspect %s", CONTENEUR)
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{CONTENEUR}` does not exist. The brief names it, "
               "and the checks look for it by name: if you recreated it, it has "
               "to carry the same name.",
            fr=f"le conteneur `{CONTENEUR}` n'existe pas. L'énoncé le nomme, et "
               "les contrôles le cherchent nommément : si vous l'avez recréé, "
               "il doit porter le même nom.",
        ))
    return json.loads(res.stdout)[0]


def _cgroup(host, fichier: str) -> str:
    """Un fichier du cgroup du conteneur, lu DEPUIS le conteneur.

    Depuis le conteneur, et non depuis l'hôte : le chemin du scope sur l'hôte
    dépend du pilote de cgroup et de la version de systemd, alors que
    `/sys/fs/cgroup` est monté dans le conteneur sur son propre cgroup. Mesuré
    dans ce catalogue : ces fichiers se lisent sans privilège.
    """
    res = host.run(
        "docker exec %s cat %s", CONTENEUR, f"/sys/fs/cgroup/{fichier}"
    )
    return res.stdout.strip() if res.rc == 0 else ""


def _cgroup_nombre(host, fichier: str) -> int:
    """La valeur NUMERIQUE d'un fichier de cgroup, ou zero.

    `int()` DIRECTEMENT SUR LA LECTURE LEVE, et c'est pour cela que ce helper
    existe : un cgroup sans limite ne porte pas `0`, il porte la chaine `max`.
    Un `int(lu or 0)` passe donc sur un cgroup limite et casse sur un cgroup
    libre, c'est-a-dire exactement dans le cas que le controle doit savoir
    nommer. Zero veut dire « aucune limite », ce que tous les appelants
    attendent.
    """
    brut = _cgroup(host, fichier)
    return int(brut) if brut.isdigit() else 0


def _oom_de_l_hote(host) -> int:
    """Le nombre de processus que l'HÔTE a tués par manque de mémoire.

    Lu dans le journal du noyau, et compté plutôt que daté : on compare un
    avant et un après, ce qui suffit à dire si la pointe a coûté quelque chose à
    la machine. Un journal illisible rend zéro, et le contrôle ne conclut alors
    rien de ce côté : on ne peint pas en rouge ce qu'on ignore.
    """
    res = host.run("dmesg --notime 2>/dev/null | grep -c %s", "Out of memory: Killed")
    try:
        return int(res.stdout.strip())
    except ValueError:
        return 0


def _interroge(host) -> str:
    """Ce que le traitement répond, lu depuis l'intérieur du conteneur.

    Depuis l'intérieur, parce que ce lab ne publie aucun port : son sujet est le
    cgroup, pas le réseau. La réponse est lue, jamais la seule connexion.
    """
    dernier = ""
    for _ in range(10):
        res = host.run("docker exec %s nc -w 3 127.0.0.1 80", CONTENEUR)
        dernier = res.stdout
        if "traitement=" in dernier:
            return dernier
        time.sleep(1)
    return dernier
