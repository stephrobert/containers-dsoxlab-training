"""Un plafond de tâches qui refuse vraiment, sans emporter le service.

Pourquoi quatre contrôles là où il n'y en avait qu'un
----------------------------------------------------

Le fichier précédent portait **un** `def test_` et **douze** assertions
enchaînées. Comme son jumeau `container-memoire-et-oom`, il ne manquait rien à
ce qu'il mesurait : la rafale était bornée et réelle, `pids.events` était lu
avant et après, un reçu applicatif servait de témoin de survie. Les défauts
étaient dans la forme.

Le **masquage** d'abord : la première assertion qui tombait masquait les onze
suivantes, et plusieurs portaient des messages télégraphiques (« Un service
actif requis ») qui ne disaient pas quoi faire.

Le **mélange des natures** ensuite. Trois assertions ne sont pas des exigences
mais des garde-fous de mesure : qu'un seul service tourne, qu'il porte son
label, que `pids.events` soit lisible. Sans eux aucun contrôle ne peut observer,
mais les confondre avec les exigences revient à accuser l'apprenant de l'état de
la machine.

Et une assertion **redondante**, qui est le cas le plus intéressant. Le contrôle
exigeait `state["Running"] and not state["OOMKilled"]`. Mesuré sur `docker.lab` :
`OOMKilled` peut valoir `true`, avec un plafond de 8 Mio et un PID 1 qui alloue,
mais alors `Running` vaut `false`. La seconde condition ne pouvait donc jamais
être le motif **seul** d'un refus.

Ce n'est pas une assertion morte, et la nuance compte. Celle du lab jumeau,
`not OomKillDisable`, ne pouvait jamais refuser du tout : le noyau en cgroup v2
écarte l'option et le champ vaut `nil`. Celle-ci refuse, mais toujours derrière
une autre. Une assertion morte se retire ; une assertion redondante se fait
**parler**, et c'est ce qui est fait ici : au lieu d'une condition muette, un
service à l'arrêt reçoit un diagnostic qui distingue l'OOM du reste.

La rafale, elle, n'a pas eu besoin d'être recalibrée, et c'est mesuré plutôt que
supposé. Sous les 32 tâches du départ : aucun refus, `pids.events:max` reste à 0.
Sous les 16 visées : refus, le compteur passe à 1. Le cgroup porte déjà trois
tâches avant la rafale, et 3 + 24 tient sous 32.
"""

import json
import uuid

import pytest

from conftest import lab_host, message

LAB = "container-limite-de-processus"
PLAFOND_TACHES = 16
MEMOIRE_MAXIMALE = 67108864  # 64 Mio : le garde-fou mémoire à conserver.

# BORNÉE, et ce n'est pas une fork bomb : vingt-quatre enfants `sleep` de deux
# secondes, puis un `wait`. Le scénario l'annonce, et le nombre est choisi pour
# dépasser 16 sans approcher 32.
RAFALE = (
    "for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24; "
    "do sleep 2 & done; wait"
)


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _service(host) -> tuple[str, dict]:
    """Le conteneur du service, ou un échec qui dit de quoi il s'agit.

    Garde-fou de mesure, non exigence : sans un service unique et étiqueté,
    aucun des quatre contrôles ne peut observer quoi que ce soit.
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


def _refus_de_tache(host, cid: str) -> int:
    """Le compteur `max` de `pids.events` : combien de créations le noyau a refusées."""
    lu = host.run("docker exec %s cat /sys/fs/cgroup/pids.events", cid)
    assert lu.rc == 0, message(
        en=f"Cannot read pids.events inside the worker: {lu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"pids.events est illisible dans le worker : {lu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    return int(dict(ligne.split() for ligne in lu.stdout.splitlines())["max"])


def _rafale(host, cid: str):
    """Lance la rafale bornée, puis laisse les enfants se terminer."""
    lancee = host.run("timeout 8 docker exec %s sh -c %s", cid, RAFALE)
    host.run("sleep 3")
    return lancee


def test_les_limites_declarees_portent_le_budget_de_taches(host):
    """Ce qui a été demandé au démon, budget de tâches et garde-fous conservés."""
    _cid, info = _service(host)
    config = info["HostConfig"]

    assert config["PidsLimit"] == PLAFOND_TACHES, message(
        en=f"The worker declares PidsLimit={config['PidsLimit']} instead of {PLAFOND_TACHES}.",
        fr=f"Le worker déclare PidsLimit={config['PidsLimit']} au lieu de {PLAFOND_TACHES}.",
    )
    # LE GARDE-FOU MÉMOIRE EST UNE EXIGENCE DE CONSERVATION, et il est vérifié
    # ici plutôt que dans un contrôle à lui : posé dès le départ, un contrôle
    # séparé passerait avant tout travail et donnerait des points pour rien.
    assert 0 < config["Memory"] <= MEMOIRE_MAXIMALE, message(
        en=(
            f"The worker declares Memory={config['Memory']}, outside the range "
            f"the scenario asks you to keep (above 0, at most {MEMOIRE_MAXIMALE}). "
            "Bounding tasks must not come at the cost of the memory guard."
        ),
        fr=(
            f"Le worker déclare Memory={config['Memory']}, hors de la plage que "
            f"le scénario demande de conserver (plus de 0, au plus "
            f"{MEMOIRE_MAXIMALE}). Borner les tâches ne doit pas coûter le "
            "garde-fou mémoire."
        ),
    )


def test_le_cgroup_applique_vraiment_le_plafond_de_taches(host):
    """Ce que le noyau a retenu, qui est la seule vérité.

    Le scénario le dit : le plafond doit être une limite de **cgroup**, pas un
    `ulimit` de shell. Un `ulimit` ne vaut que pour les descendants du shell qui
    l'a posé, et disparaît avec lui.
    """
    cid, _info = _service(host)

    lu = host.run("docker exec %s cat /sys/fs/cgroup/pids.max", cid)
    assert lu.rc == 0, message(
        en=f"Cannot read the worker's pids.max: {lu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"pids.max est illisible dans le worker : {lu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    effectif = lu.stdout.strip()
    assert effectif == str(PLAFOND_TACHES), message(
        en=(
            f"The cgroup applies pids.max={effectif} instead of {PLAFOND_TACHES}. "
            "A shell ulimit does not reach here: it binds only the descendants of "
            "the shell that set it."
        ),
        fr=(
            f"Le cgroup applique pids.max={effectif} au lieu de {PLAFOND_TACHES}. "
            "Un ulimit de shell n'arrive pas jusqu'ici : il ne lie que les "
            "descendants du shell qui l'a posé."
        ),
    )


def test_une_rafale_bornee_est_refusee_par_le_noyau(host):
    """Le plafond refuse-t-il ? On l'observe dans `pids.events`, pas sur un code."""
    cid, _info = _service(host)

    avant = _refus_de_tache(host, cid)
    lancee = _rafale(host, cid)

    assert lancee.rc != 124, message(
        en="The finite trial reached its safety timeout instead of being refused. A cap that only slows down is not a cap.",
        fr="L'essai fini a atteint son délai de sécurité au lieu d'être refusé. Un plafond qui ralentit seulement n'est pas un plafond.",
    )

    apres = _refus_de_tache(host, cid)
    assert apres > avant, message(
        en=(
            f"The kernel refused no task creation (pids.events max stayed at "
            f"{avant}): twenty-four children fit under the current cap. A "
            "non-zero exit code would not prove it either, only this counter does."
        ),
        fr=(
            f"Le noyau n'a refusé aucune création de tâche (le compteur max de "
            f"pids.events reste à {avant}) : vingt-quatre enfants tiennent sous le "
            "plafond actuel. Un code de sortie non nul ne le prouverait pas "
            "davantage, seul ce compteur le dit."
        ),
    )


def test_le_service_survit_a_la_saturation_et_garde_son_etat(host):
    """Le plafond borne l'incident, il ne le propage pas."""
    cid, info = _service(host)

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

        avant = _refus_de_tache(host, cid)
        _rafale(host, cid)
        apres = _refus_de_tache(host, cid)

        # SANS SATURATION, CE CONTRÔLE NE MESURE RIEN : un service qui n'a rien
        # subi survit trivialement. La saturation fait donc partie de l'exigence
        # ici, plutôt que d'un test dont celui-ci dépendrait.
        assert apres > avant, message(
            en=(
                "No task refusal was counted, so this check cannot tell survival "
                "from nothing having happened. Make the cap refuse first."
            ),
            fr=(
                "Aucun refus de tâche n'a été compté, donc ce contrôle ne "
                "distingue pas la survie du fait que rien ne s'est produit. "
                "Faites d'abord refuser le plafond."
            ),
        )

        etat = json.loads(host.run("docker inspect %s", cid).stdout)[0]["State"]

        # IL N Y A PAS D ASSERTION SUR `OOMKilled` ICI, ET C EST MESURÉ.
        #
        # Le contrôle unique exigeait `Running and not OOMKilled` d'un bloc. Cette
        # seconde condition ne pouvait jamais être le motif SEUL d'un refus :
        # relevé sur `docker.lab`, quand `OOMKilled` vaut true, `Running` vaut
        # false, donc la première suffisait déjà.
        #
        # J'ai d'abord voulu la faire parler, par un `pytest.fail` qui distingue
        # l'OOM du reste. Puis j'ai cherché à l'éprouver, et elle est
        # INATTEIGNABLE dans ce lab. Relevé sur cinq paliers de mémoire, rafale
        # de vingt-quatre `sleep` jouée à chaque fois :
        #
        #     8 Mio    le conteneur ne démarre pas
        #     10 Mio   démarre, après la rafale : OOMKilled=false, Exit=0
        #     12 Mio   démarre, après la rafale : OOMKilled=false, Exit=0
        #     16 Mio   démarre, après la rafale : OOMKilled=false, Exit=0
        #     20 Mio   démarre, après la rafale : OOMKilled=false, Exit=0
        #     32 Mio   démarre, après la rafale : OOMKilled=false, Exit=0
        #
        # Il n'existe donc aucune fenêtre où le service tourne et où la rafale le
        # tue par OOM : vingt-quatre `sleep` busybox ne consomment presque rien,
        # et sous le seuil de démarrage c'est le garde-fou « un service actif »
        # qui refuse avant. Un diagnostic qu'aucun travail ne peut déclencher est
        # du décor, c'est-à-dire le défaut même qu'on corrige ici.
        #
        # LE CODE DE SORTIE EST DONC DANS LE MESSAGE, ce qui donne le diagnostic
        # sans prétendre le trier : un 137 dit un OOM, et le cahier des charges
        # le rappelle.
        assert etat["Running"], message(
            en=(
                f"The worker is down after the burst (exit code {etat['ExitCode']}). "
                "The cap must bound the incident, not propagate it. An exit code of "
                "137 means the kernel killed it for memory, not for tasks."
            ),
            fr=(
                f"Le worker est à l'arrêt après la rafale (code de sortie "
                f"{etat['ExitCode']}). Le plafond doit borner l'incident, non le "
                "propager. Un code 137 signifie que le noyau l'a tué pour la "
                "mémoire, et non pour les tâches."
            ),
        )
        assert etat["StartedAt"] == info["State"]["StartedAt"], message(
            en=(
                "The worker restarted during the burst (StartedAt changed). Its "
                "PID 1 must survive: a restart loses everything the service held."
            ),
            fr=(
                "Le worker a redémarré pendant la rafale (StartedAt a changé). Son "
                "PID 1 doit survivre : un redémarrage perd tout ce que le service "
                "tenait."
            ),
        )

        relu = host.run("docker exec %s cat %s", cid, chemin)
        assert relu.rc == 0 and relu.stdout == temoin, message(
            en=(
                "The receipt written before the burst is gone: the service did not "
                "keep its state across the incident. Surviving as a process is not "
                "enough."
            ),
            fr=(
                "Le reçu écrit avant la rafale a disparu : le service n'a pas "
                "conservé son état pendant l'incident. Survivre comme processus ne "
                "suffit pas."
            ),
        )
    finally:
        # ON NE RETIRE QUE SON PROPRE REÇU : le validateur photographie le
        # moteur, et un test qui nettoie large efface le travail de l'apprenant.
        host.run("docker exec %s rm -f %s", cid, chemin)
