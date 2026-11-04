"""Un plafond mémoire qui mord vraiment, sans emporter le service.

Pourquoi quatre contrôles là où il n'y en avait qu'un
----------------------------------------------------

Le fichier précédent portait **un** `def test_` et **douze** assertions
enchaînées. Il ne manquait rien à ce qu'il mesurait : la sonde d'allocation
était réelle, le compteur `oom_kill` était lu avant et après, et un reçu
applicatif servait de témoin de survie. Le défaut était ailleurs, et il est
double.

D'abord le **masquage** : la première assertion qui tombait masquait les onze
suivantes. Un apprenant qui avait posé la bonne limite mais dont l'hôte manquait
de marge lisait « Marge mémoire hôte insuffisante pour la sonde » et ne savait
pas que tout le reste de son travail était juste.

Ensuite le **mélange des natures**. Trois de ces douze assertions ne sont pas
des exigences : qu'un seul service tourne, qu'il porte son label, et que l'hôte
ait de la marge. Ce sont des **garde-fous de mesure** : sans eux le contrôle ne
peut rien observer, mais l'apprenant n'en est pas responsable, et deux d'entre
eux ne dépendent même pas de lui. Les confondre avec les exigences, c'est
accuser quelqu'un de l'état de la machine.

Les quatre contrôles mesurent quatre choses indépendantes :

1. les limites **déclarées** au démon ;
2. ce que le **cgroup applique**, qui est la seule vérité ;
3. qu'une allocation excessive **subit un OOM réel** ;
4. que le service **survit** à cet OOM sans redémarrer ni perdre son état.

1 et 2 ne sont pas redondants, et la différence n'est pas théorique : un
`--memory` sans `--memory-swap` laisse `memory.swap.max` ouvert, si bien que
l'allocation déborde en swap au lieu d'être tuée. Le premier lit ce qu'on a
demandé, le second ce que le noyau a retenu.

3 et 4 provoquent chacun **leur propre** sonde, plutôt que de partager celle du
précédent. C'est un OOM de plus à chaque passage, et c'est le prix de
l'indépendance : un contrôle qui suppose qu'un autre a déjà tourné mentira dès
qu'on le joue seul, ce que `-k` et un `--lf` font tous les jours.
"""

import json
import uuid

import pytest

from conftest import lab_host, message

LAB = "container-memoire-et-oom"
PLAFOND = 33554432  # 32 Mio, le budget qu'impose le contrat de déploiement.
MARGE_HOTE_KIO = 131072  # Sous cette marge, la sonde ne mesure plus le cgroup.


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _service(host) -> tuple[str, dict]:
    """Le conteneur du service, ou un échec qui dit de quoi il s'agit.

    GARDE-FOU DE MESURE, et non exigence : sans un service unique et étiqueté,
    aucun des quatre contrôles ne peut observer quoi que ce soit. Un contrôle
    qui n'a pas pu regarder ne conclut jamais au vert.
    """
    trouve = host.run(
        "docker ps -q "
        "--filter label=com.docker.compose.project=dsoxlab-%s "
        "--filter label=com.docker.compose.service=worker",
        LAB,
    )
    ids = trouve.stdout.split()
    assert trouve.rc == 0 and len(ids) == 1, message(
        en=(
            f"Exactly one running `worker` service is required in project "
            f"dsoxlab-{LAB}, found {len(ids)}. Bring the project back up before "
            "applying the budget."
        ),
        fr=(
            f"Un seul service `worker` actif est requis dans le projet "
            f"dsoxlab-{LAB}, {len(ids)} trouvé(s). Relancez le projet avant "
            "d'appliquer le budget."
        ),
    )
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the worker: cleanup removes only what carries it.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le worker : le nettoyage ne retire que ce qui le porte.",
    )
    return cid, info


def _marge_suffisante(host) -> None:
    """Garde-fou de mesure, et il ne dépend pas de l'apprenant.

    Si l'hôte n'a plus de marge, l'allocation de la sonde peut être tuée par
    l'OOM killer GLOBAL et non par celui du cgroup : le contrôle mesurerait
    alors la machine au lieu du travail. Le message le dit, parce qu'accuser
    quelqu'un de la mémoire libre de l'hôte n'aide personne.
    """
    marge = host.run("awk '/MemAvailable/ {print $2}' /proc/meminfo")
    assert marge.rc == 0 and marge.stdout.strip().isdigit(), message(
        en="Cannot read the host memory margin. Not your fault: the check cannot measure anything, report it.",
        fr="La marge mémoire de l'hôte est illisible. Ce n'est pas votre faute : le contrôle ne peut rien mesurer, signalez-le.",
    )
    disponible = int(marge.stdout)
    assert disponible > MARGE_HOTE_KIO, message(
        en=(
            f"The host has only {disponible} kiB available, under the "
            f"{MARGE_HOTE_KIO} kiB the probe needs. Not your fault: a global OOM "
            "would be measured instead of the cgroup's. Free the host and retry."
        ),
        fr=(
            f"L'hôte n'a que {disponible} kio disponibles, sous les "
            f"{MARGE_HOTE_KIO} kio que la sonde exige. Ce n'est pas votre faute : "
            "un OOM global serait mesuré à la place de celui du cgroup. Libérez "
            "l'hôte et recommencez."
        ),
    )


def _oom_kill(host, cid: str) -> int:
    """Le compteur d'OOM du cgroup, lu dans `memory.events` et non deviné."""
    lu = host.run("docker exec %s cat /sys/fs/cgroup/memory.events", cid)
    assert lu.rc == 0, message(
        en=f"Cannot read memory.events inside the worker: {lu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"memory.events est illisible dans le worker : {lu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    return int(dict(ligne.split() for ligne in lu.stdout.splitlines())["oom_kill"])


def _sonde(host, cid: str):
    """Une allocation BORNÉE dans le cgroup du conteneur, calibrée pour discriminer.

    Bornée à dessein : un allocateur sans fin stresserait l'hôte, et le scénario
    l'interdit.

    L'EXPOSANT EST MESURÉ, PAS ESTIMÉ, et il valait 26 jusqu'ici. Une sonde doit
    être tuée sous le plafond visé de 32 Mio **et survivre** sous les 96 Mio de
    l'état de départ : sans la seconde moitié, elle déclare la mission accomplie
    avant tout travail. Relevé sur `docker.lab`, oom_kill lu dans
    `memory.events` avant et après chaque passage :

        exposant   sous 32 Mio   sous 96 Mio
        2^24       réussit       réussit
        2^25       TUÉE          réussit      <- le seul qui discrimine
        2^26       TUÉE          TUÉE

    2^26 était donc tué dans les deux cas, et les deux contrôles d'OOM passaient
    sur l'état initial. La cause est dans `awk` : `s = s s` double la chaîne à
    chaque tour, si bien qu'au dernier tour le processus détient l'ancienne ET la
    nouvelle. Le pic vaut au moins le double du résultat annoncé, ce qu'aucun
    calcul sur la taille finale ne dit.

    Le défaut préexistait et restait invisible : l'ancien contrôle unique plaçait
    ses assertions sur les limites avant la sonde, et tombait donc avant de
    l'atteindre.
    """
    return host.run(
        "timeout 10 docker exec %s awk 'BEGIN {s=\"x\"; for(i=0;i<25;i++) s=s s; print length(s)}'",
        cid,
    )


def test_les_limites_declarees_bornent_la_memoire_et_interdisent_le_swap(host):
    """Ce qui a été demandé au démon."""
    _cid, info = _service(host)
    config = info["HostConfig"]

    assert config["Memory"] == PLAFOND, message(
        en=f"The worker declares Memory={config['Memory']} instead of {PLAFOND} bytes (32 MiB).",
        fr=f"Le worker déclare Memory={config['Memory']} au lieu de {PLAFOND} octets (32 Mio).",
    )
    assert config["MemorySwap"] == PLAFOND, message(
        en=(
            f"The worker declares MemorySwap={config['MemorySwap']} instead of "
            f"{PLAFOND}. Equal to Memory is what forbids swap: left alone, the "
            "allocation spills into swap instead of being killed."
        ),
        fr=(
            f"Le worker déclare MemorySwap={config['MemorySwap']} au lieu de "
            f"{PLAFOND}. C'est l'égalité avec Memory qui interdit le swap : "
            "laissé libre, l'allocation déborde en swap au lieu d'être tuée."
        ),
    )
    # IL N Y A PAS DE TROISIEME ASSERTION ICI, ET C EST MESURE.
    #
    # Ce contrôle portait `assert not config["OomKillDisable"]`, héritée du
    # contrôle unique précédent. Elle ne pouvait PAS refuser. Relevé sur
    # `docker.lab`, qui est en cgroup v2 :
    #
    #     $ docker run --oom-kill-disable ...
    #     WARNING: Your kernel does not support OomKillDisable. OomKillDisable discarded.
    #     $ docker inspect -f '{{.HostConfig.OomKillDisable}}'
    #     <nil>
    #
    # Le noyau ne sait pas désactiver l'OOM killer en v2 : Docker écarte
    # l'option, et le champ ne vaut même pas `false` mais `nil`, donc `None` en
    # Python, dont la négation est toujours vraie. L'assertion passait quoi que
    # l'apprenant écrive, y compris en demandant explicitement la désactivation.
    #
    # ET ELLE EST INUTILE, parce que ce qu'elle visait est déjà mesuré, et mieux :
    # `test_une_allocation_excessive_subit_un_oom_reel` observe un `oom_kill`
    # réel dans `memory.events`. Un OOM compté EST la preuve que le tueur est
    # actif. Un drapeau dit ce qu'on a demandé, un compteur dit ce qui est
    # arrivé.


def test_le_cgroup_applique_vraiment_la_borne(host):
    """Ce que le noyau a retenu, qui est la seule vérité."""
    cid, _info = _service(host)

    lu = host.run(
        "docker exec %s sh -c 'cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.swap.max'",
        cid,
    )
    assert lu.rc == 0, message(
        en=f"Cannot read the worker's cgroup limits: {lu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"Les limites du cgroup du worker sont illisibles : {lu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    effectives = lu.stdout.split()
    assert effectives == [str(PLAFOND), "0"], message(
        en=(
            f"The cgroup applies memory.max/memory.swap.max = {effectives} "
            f"instead of ['{PLAFOND}', '0']. A declaration the kernel did not "
            "retain bounds nothing."
        ),
        fr=(
            f"Le cgroup applique memory.max/memory.swap.max = {effectives} "
            f"au lieu de ['{PLAFOND}', '0']. Une déclaration que le noyau n'a "
            "pas retenue ne borne rien."
        ),
    )


def test_une_allocation_excessive_subit_un_oom_reel(host):
    """Le budget mord-il ? On l'observe dans `memory.events`, pas sur un code."""
    cid, _info = _service(host)
    _marge_suffisante(host)

    avant = _oom_kill(host, cid)
    sonde = _sonde(host, cid)

    assert sonde.rc != 124, message(
        en="The bounded probe timed out instead of hitting an OOM. A ceiling that only slows down is not a ceiling.",
        fr="La sonde bornée a expiré au lieu de subir un OOM. Un plafond qui ralentit seulement n'est pas un plafond.",
    )
    assert sonde.rc != 0, message(
        en=(
            "The bounded probe completed without being killed: the "
            "ceiling does not bite. Check that swap is forbidden, not only that "
            "memory is limited."
        ),
        fr=(
            "La sonde bornée est allée au bout sans être tuée : le plafond "
            "ne mord pas. Vérifiez que le swap est interdit, et non seulement que "
            "la mémoire est limitée."
        ),
    )

    apres = _oom_kill(host, cid)
    assert apres > avant, message(
        en=(
            f"The probe failed but the cgroup counted no OOM (oom_kill stayed at "
            f"{avant}). A non-zero exit code is not proof: it is memory.events "
            "that says the kernel killed the allocation."
        ),
        fr=(
            f"La sonde a échoué mais le cgroup n'a compté aucun OOM (oom_kill "
            f"reste à {avant}). Un code de sortie non nul ne prouve rien : c'est "
            "memory.events qui dit que le noyau a tué l'allocation."
        ),
    )


def test_le_service_survit_a_l_oom_et_garde_son_etat(host):
    """Le plafond borne l'incident, il ne le propage pas.

    C'est l'autre moitié de l'exigence, et la plus facile à perdre : un budget
    qui emporte le PID 1 à chaque pic ne protège pas le service, il le remplace
    par un redémarrage.
    """
    cid, info = _service(host)
    _marge_suffisante(host)

    reserve = host.run("docker exec %s mktemp", cid)
    chemin = reserve.stdout.strip()
    assert reserve.rc == 0 and chemin, message(
        en="Cannot create a receipt file inside the worker. Not your fault if it runs, report it.",
        fr="Impossible de créer un fichier de reçu dans le worker. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )

    try:
        temoin = uuid.uuid4().hex
        ecrit = host.run("docker exec %s sh -c %s", cid, f"printf %s {temoin} > {chemin}")
        assert ecrit.rc == 0, message(
            en="Cannot write the receipt inside the worker. Not your fault if it runs, report it.",
            fr="Impossible d'écrire le reçu dans le worker. Ce n'est pas votre faute s'il tourne, signalez-le.",
        )

        avant = _oom_kill(host, cid)
        _sonde(host, cid)
        apres = _oom_kill(host, cid)

        # SANS OOM, CE CONTRÔLE NE MESURE RIEN : un service qui n'a rien subi
        # survit trivialement. C'est pourquoi l'OOM fait partie de l'exigence
        # ici, et non d'un test dont celui-ci dépendrait.
        assert apres > avant, message(
            en=(
                "No OOM was counted, so this check cannot tell survival from "
                "nothing having happened. Make the ceiling bite first."
            ),
            fr=(
                "Aucun OOM n'a été compté, donc ce contrôle ne distingue pas la "
                "survie du fait que rien ne s'est produit. Faites d'abord mordre "
                "le plafond."
            ),
        )

        etat = json.loads(host.run("docker inspect %s", cid).stdout)[0]["State"]
        assert etat["Running"], message(
            en="The worker is down after the OOM. The ceiling must bound the incident, not propagate it.",
            fr="Le worker est à l'arrêt après l'OOM. Le plafond doit borner l'incident, non le propager.",
        )
        assert etat["StartedAt"] == info["State"]["StartedAt"], message(
            en=(
                "The worker restarted during the OOM (StartedAt changed). Its PID 1 "
                "must survive: a restart loses everything the service held."
            ),
            fr=(
                "Le worker a redémarré pendant l'OOM (StartedAt a changé). Son "
                "PID 1 doit survivre : un redémarrage perd tout ce que le service "
                "tenait."
            ),
        )

        relu = host.run("docker exec %s cat %s", cid, chemin)
        assert relu.rc == 0 and relu.stdout == temoin, message(
            en=(
                "The receipt written before the OOM is gone: the service did not "
                "keep its state across the incident. Surviving as a process is not "
                "enough."
            ),
            fr=(
                "Le reçu écrit avant l'OOM a disparu : le service n'a pas conservé "
                "son état pendant l'incident. Survivre comme processus ne suffit "
                "pas."
            ),
        )
    finally:
        # ON NE RETIRE QUE SON PROPRE REÇU, jamais le reste : le validateur
        # photographie le moteur, et un test qui nettoie large efface le travail
        # de l'apprenant.
        host.run("docker exec %s rm -f %s", cid, chemin)
