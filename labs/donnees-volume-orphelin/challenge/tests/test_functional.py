"""Un volume de données reconnecté, son reçu intact, et le seul orphelin jetable retiré.

Pourquoi trois contrôles là où il n'y en avait qu'un
---------------------------------------------------

Le fichier précédent portait **un** `def test_` et huit assertions enchaînées. Il
mesurait les bonnes choses, et le défaut était la forme : la première qui tombait
masquait les sept suivantes, et son premier message tenait en trois mots, « Un
service actif requis ».

Les trois contrôles mesurent trois choses indépendantes :

1. le volume original est **reconnecté** sur `/data`, en lecture seule ;
2. le **reçu** qu'il portait est intact ;
3. seul l'orphelin **jetable** a été retiré.

Le deuxième n'est pas une redite du premier. Un volume peut être monté au bon
endroit sans porter les données attendues : il suffit d'en créer un neuf du même
nom. C'est pourquoi le garde-fou vérifie aussi que le volume n'a pas été
**recréé**, en comparant son `CreatedAt` à l'empreinte posée par le setup.

Le troisième porte l'exigence la plus fine du lab, et son titre le dit : SEUL
l'orphelin jetable. Un `volume prune` retirerait aussi le volume de données, et
le scénario l'interdit explicitement. C'est ce que vérifient les deux labels de
propriété, exigés avant toute suppression.

CE QUE CE LAB NE MESURE PAS, ET QUI EST SIGNALÉ PLUTÔT QUE COMBLÉ. La fiche de la
leçon annonce un objectif observable de plus : une copie du volume existe HORS du
volume et se relit. Or le scénario de ce lab ne demande aucune sauvegarde : il
demande de reconnecter, de conserver le reçu et de retirer le volume périmé. Un
apprenant qui rattache sans sauvegarder satisfait donc le lab, et pas la fiche.

Les deux documents divergent, et ce n'est pas au contrôle de trancher : soit le
scénario gagne une exigence de sauvegarde, soit la fiche retire son objectif.
Ajouter ici une exigence que l'énoncé n'annonce pas serait la faute inverse, et
elle a déjà été commise une fois dans ce catalogue le même jour, sur
`securite-groupe-docker`.
"""

import json

import pytest

from conftest import lab_host, message

LAB = "donnees-volume-orphelin"
PROJET = f"dsoxlab-{LAB}"
TRAVAIL = f"/opt/dsoxlab-{LAB}"
VOLUME = f"{PROJET}-data"
JETABLE = f"{PROJET}-stale"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _worker(host) -> tuple[str, dict]:
    """Le conteneur du service, ou un échec qui dit quoi faire.

    Garde-fou de mesure : sans un service unique et étiqueté, aucun des trois
    contrôles ne peut observer quoi que ce soit.
    """
    trouve = host.run(
        "docker ps -q --filter label=com.docker.compose.project=%s "
        "--filter label=com.docker.compose.service=worker",
        PROJET,
    )
    ids = trouve.stdout.split()
    assert trouve.rc == 0 and len(ids) == 1, message(
        en=f"Exactly one running `worker` service is required in project "
           f"{PROJET}, found {len(ids)}. Bring the project back up under that "
           "exact name before reconnecting the volume.",
        fr=f"Un seul service `worker` actif est requis dans le projet {PROJET}, "
           f"{len(ids)} trouvé(s). Relancez le projet sous ce nom exact avant de "
           "reconnecter le volume.",
    )
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the worker: cleanup removes only what carries it.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le worker : le nettoyage ne retire que ce qui le porte.",
    )
    return cid, info


def _volume_original(host) -> dict:
    """Le volume de données, et la preuve qu'il n'a pas été recréé.

    Garde-fou : ces trois vérifications sont vraies au départ, donc elles ne
    notent rien. Mais les franchir est une faute, et le scénario les énonce :
    conserver les deux labels de propriété, et ne pas recréer le volume.
    """
    inspecte = host.run("docker volume inspect %s", VOLUME)
    assert inspecte.rc == 0, message(
        en=f"The original volume {VOLUME} no longer exists. Removing it does "
           "clean up, by destroying the data the exercise asks you to recover.",
        fr=f"Le volume original {VOLUME} n'existe plus. Le supprimer nettoie "
           "bien, en détruisant les données que l'exercice demande de récupérer.",
    )
    volume = json.loads(inspecte.stdout)[0]

    labels = volume["Labels"] or {}
    attendus = {"dsoxlab.lab": LAB, "com.docker.compose.project": PROJET}
    manquants = {c: v for c, v in attendus.items() if labels.get(c) != v}
    assert not manquants, message(
        en=f"The volume lost its ownership labels: {manquants} expected, "
           f"{labels or '{}'} found. They are what tells a lab volume from one of "
           "yours, and the scenario asks to check them before any removal.",
        fr=f"Le volume a perdu ses labels de propriété : {manquants} attendus, "
           f"{labels or '{}'} trouvés. Ce sont eux qui distinguent un volume du "
           "lab d'un des vôtres, et le scénario demande de les vérifier avant "
           "toute suppression.",
    )

    empreinte = host.run("cat %s/.volume-created", TRAVAIL)
    assert empreinte.rc == 0 and empreinte.stdout.strip(), message(
        en=f"Cannot read {TRAVAIL}/.volume-created. Not your fault: the check "
           "cannot tell an original volume from a fresh one, report it.",
        fr=f"{TRAVAIL}/.volume-created est illisible. Ce n'est pas votre faute : "
           "le contrôle ne peut pas distinguer le volume d'origine d'un volume "
           "neuf, signalez-le.",
    )
    assert volume["CreatedAt"] == empreinte.stdout.strip(), message(
        en="This is not the original volume: its creation date differs from the "
           "one recorded at setup. Recreating a volume of the same name gives an "
           "empty one, which recovers nothing.",
        fr="Ce n'est pas le volume d'origine : sa date de création diffère de "
           "celle relevée à la préparation. Recréer un volume du même nom en "
           "donne un vide, ce qui ne récupère rien.",
    )
    return volume


def test_le_volume_original_est_reconnecte_en_lecture_seule(host):
    """Ce qui a été monté, et comment."""
    _cid, info = _worker(host)
    _volume_original(host)

    montages = [m for m in info["Mounts"] if m["Destination"] == "/data"]
    assert len(montages) == 1, message(
        en=f"/data carries {len(montages)} mounts instead of one. The worker "
           "started without it: the data volume has to be reconnected.",
        fr=f"/data porte {len(montages)} montages au lieu d'un. Le worker a "
           "démarré sans lui : le volume de données doit être reconnecté.",
    )
    montage = montages[0]
    assert montage["Type"] == "volume", message(
        en=f"/data is a {montage['Type']} mount instead of a volume. A bind would "
           "not be the retained volume, whatever it contains.",
        fr=f"/data est un montage {montage['Type']} au lieu d'un volume. Un bind "
           "ne serait pas le volume conservé, quoi qu'il contienne.",
    )
    assert montage["Name"] == VOLUME, message(
        en=f"/data carries the volume {montage['Name']!r} instead of {VOLUME!r}. "
           "The other one is the expendable orphan, and it is empty.",
        fr=f"/data porte le volume {montage['Name']!r} au lieu de {VOLUME!r}. "
           "L'autre est l'orphelin jetable, et il est vide.",
    )
    assert not montage["RW"], message(
        en="The volume is mounted read-write. The scenario asks for read-only: "
           "recovering data does not call for the right to change it.",
        fr="Le volume est monté en lecture-écriture. Le scénario demande la "
           "lecture seule : récupérer des données ne demande pas le droit de les "
           "modifier.",
    )


def test_le_recu_original_est_intact(host):
    """Ce que le volume contient, et non seulement qu'il est monté.

    Un volume peut être monté au bon endroit sans porter les données attendues :
    il suffit d'en créer un neuf du même nom. Le garde-fou l'écarte par la date
    de création ; ce contrôle lit le contenu.
    """
    cid, _info = _worker(host)
    _volume_original(host)

    attendu = host.run("cat %s/expected.txt", TRAVAIL)
    assert attendu.rc == 0 and attendu.stdout, message(
        en=f"Cannot read the expected receipt from {TRAVAIL}/expected.txt. Not "
           "your fault: the check has nothing to compare against, report it.",
        fr=f"Le reçu attendu est illisible dans {TRAVAIL}/expected.txt. Ce n'est "
           "pas votre faute : le contrôle n'a rien à comparer, signalez-le.",
    )

    lu = host.run("docker exec %s cat /data/receipt.txt", cid)
    assert lu.rc == 0, message(
        en=f"/data/receipt.txt is not readable in the worker: "
           f"{lu.stderr.strip()[:200]}\nThe receipt is the data to recover; a "
           "volume without it recovers nothing.",
        fr=f"/data/receipt.txt n'est pas lisible dans le worker : "
           f"{lu.stderr.strip()[:200]}\nLe reçu est la donnée à récupérer ; un "
           "volume sans lui ne récupère rien.",
    )
    assert lu.stdout.startswith("receipt="), message(
        en=f"The receipt does not have its expected shape: {lu.stdout[:120]!r}",
        fr=f"Le reçu n'a pas la forme attendue : {lu.stdout[:120]!r}",
    )
    assert lu.stdout == attendu.stdout, message(
        en="The receipt no longer matches the one recorded at setup: the data was "
           "rewritten rather than recovered.",
        fr="Le reçu ne correspond plus à celui relevé à la préparation : la "
           "donnée a été réécrite plutôt que récupérée.",
    )


def test_seul_l_orphelin_jetable_a_ete_retire(host):
    """L'exigence la plus fine du lab, et son titre la porte : SEUL le jetable.

    Le garde-fou a déjà vérifié que le volume de données survit, avec ses labels
    et sa date d'origine. Ce contrôle ajoute la moitié qui manque : le volume
    périmé est parti. Un `volume prune` satisferait cette moitié en emportant
    l'autre, et le scénario l'interdit explicitement.
    """
    _worker(host)
    _volume_original(host)

    reste = host.run("docker volume inspect %s", JETABLE)
    assert reste.rc != 0, message(
        en=f"The expendable orphan {JETABLE} is still there. It is empty, it "
           "carries this lab's labels, and it is the only one to remove.",
        fr=f"L'orphelin jetable {JETABLE} est encore là. Il est vide, il porte "
           "les labels de ce lab, et c'est le seul à retirer.",
    )
