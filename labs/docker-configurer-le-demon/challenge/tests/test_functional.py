"""Des défauts de journalisation posés sur le démon, et qui mordent vraiment.

Pourquoi deux contrôles là où il n'y en avait qu'un
--------------------------------------------------

Le fichier précédent portait **un** `def test_` et cinq assertions enchaînées. Sa
méthode était juste : il créait un conteneur **sans aucune option** et inspectait
son `LogConfig`. Si ce conteneur porte les bornes, c'est que le démon les a
appliquées par défaut, ce qui mesure la configuration par son effet plutôt que
par son fichier. C'est le bon geste, et il est conservé.

CE QUI MANQUAIT : LA PREUVE QUE LES BORNES MORDENT. Le contrôle lisait ce que le
démon a **retenu**, jamais ce qu'il **applique**.

UNE RÉSERVE MESURÉE, ET ELLE CORRIGE CE COMMENTAIRE. J'avais d'abord écrit que
ce second contrôle fermait le trou du « `daemon.json` juste, démon non
rechargé » : le fichier porterait les bonnes valeurs et le moteur appliquerait
les anciennes. Éprouvé sur `docker.lab`, ce cas N'EXISTE PAS. Docker relit ses
`log-opts` à chaque création de conteneur, sans rechargement : après réécriture
du fichier et un `systemctl reload` sur l'ANCIENNE configuration, un conteneur
neuf hérite immédiatement des nouvelles valeurs.

Le contrôle reste utile, et il n'est pas du décor : il a refusé l'état initial,
où les bornes de 10 Mio laissent passer les douze mille lignes. Il mesure donc
que la rotation a lieu et tient dans son budget, ce que la seule inspection ne
dit pas. Mais il ne refuse jamais SEUL, puisque toute erreur sur les bornes est
aussi vue par le contrôle précédent.

C'est la même situation que `docker-rotation-des-journaux`, et la même raison de
le garder : l'un croit la déclaration, l'autre regarde le journal.

La rotation est pourtant observable, et elle discrimine. Mesuré sur `docker.lab`,
avec un conteneur qui émet douze mille lignes de cent octets :

    défauts du départ, max-size=10m   12 000 lignes retenues, la première est « 0 »
    défauts demandés,  max-size=1m     6 148 lignes retenues, la première est « 5852 »

Un peu plus d'un mégaoctet suffit donc à départager les deux réglages, sans
remplir le disque de la machine.

LES DEUX CONTRÔLES, et pourquoi deux et non trois. Le pilote `json-file` a
d'abord été écrit comme un contrôle à part, et il PASSE sur l'état initial :
c'est déjà le pilote par défaut de Docker. Un contrôle qui passe avant tout
travail accorde des points pour rien.

Il n'est pas accessoire, puisque le scénario demande de le **conserver** : un
apprenant qui basculerait sur `journald` perdrait les bornes en même temps. Il
rejoint donc le contrôle des bornes déclarées, dont il est la première moitié.

C'est la sixième fois que ce cas se présente dans ce catalogue, et la règle est
établie : ce qui est vrai avant tout travail ne peut pas être un contrôle, et
appartient à celui dont il conditionne le sens.
"""

from __future__ import annotations

import json
import shlex
import uuid

import pytest

from conftest import lab_host, message

LAB = "docker-configurer-le-demon"
IMAGE = (
    "alpine:3.24.3@sha256:"
    "be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a"
)
TAILLE_ATTENDUE = "1m"
FICHIERS_ATTENDUS = "2"
# Un peu plus d'un mégaoctet de journal : assez pour franchir la borne demandée,
# loin des dix mégaoctets du départ, et sans peser sur le disque de la machine.
LIGNES = 12000
BUDGET_OCTETS = 1 * 1024 * 1024 * int(FICHIERS_ATTENDUS)


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _temoin(host, *options: str) -> tuple[str, dict]:
    """Crée un conteneur témoin SANS option de journal, et rend son inspection.

    C'est le cœur de la méthode de ce lab : un conteneur créé sans rien hérite
    des défauts du démon, donc son `LogConfig` les révèle. L'appelant retire le
    témoin.
    """
    nom = f"dsoxlab-log-defaults-{uuid.uuid4().hex[:12]}"
    cree = host.run(
        shlex.join([
            "docker", "create", "--name", nom,
            "--label", f"dsoxlab.lab={LAB}", *options, IMAGE, "true",
        ])
    )
    assert cree.rc == 0, message(
        en=f"Could not create a probe container: {cree.stderr.strip()[-400:]}. "
           "Not your fault if the daemon answers, report it.",
        fr=f"Impossible de créer le conteneur témoin : {cree.stderr.strip()[-400:]}. "
           "Ce n'est pas votre faute si le démon répond, signalez-le.",
    )
    inspecte = host.run(shlex.join(["docker", "inspect", nom]))
    assert inspecte.rc == 0, message(
        en="Could not inspect the newly created probe container. Not your fault, report it.",
        fr="Impossible d'inspecter le nouveau conteneur témoin. Ce n'est pas votre faute, signalez-le.",
    )
    return nom, json.loads(inspecte.stdout)[0]


def test_les_nouveaux_conteneurs_heritent_du_pilote_et_des_bornes(host):
    """Ce que le démon a retenu, lu sur un conteneur créé sans option.

    Le pilote et les deux bornes vont ensemble : basculer sur un autre pilote
    ferait perdre les bornes en même temps, et le scénario demande de conserver
    `json-file`.
    """
    nom, info = _temoin(host)
    try:
        config = info["HostConfig"]["LogConfig"]

        assert config["Type"] == "json-file", message(
            en=f"New containers use the {config['Type']} driver instead of "
               "json-file. The scenario asks to keep it: another driver would "
               "ignore these bounds entirely.",
            fr=f"Les nouveaux conteneurs utilisent le pilote {config['Type']} au "
               "lieu de json-file. Le scénario demande de le conserver : un autre "
               "pilote ignorerait ces bornes entièrement.",
        )
        taille = config["Config"].get("max-size")
        assert taille == TAILLE_ATTENDUE, message(
            en=f"New containers inherit max-size={taille or '(none)'} instead of "
               f"{TAILLE_ATTENDUE}. These are the daemon's defaults, so they are "
               "set once and apply to everything created afterwards.",
            fr=f"Les nouveaux conteneurs héritent de max-size={taille or '(aucun)'} "
               f"au lieu de {TAILLE_ATTENDUE}. Ce sont les défauts du démon : ils "
               "se posent une fois et valent pour tout ce qui est créé ensuite.",
        )
        fichiers = config["Config"].get("max-file")
        assert fichiers == FICHIERS_ATTENDUS, message(
            en=f"New containers inherit max-file={fichiers or '(none)'} instead of "
               f"{FICHIERS_ATTENDUS}.",
            fr=f"Les nouveaux conteneurs héritent de max-file={fichiers or '(aucun)'} "
               f"au lieu de {FICHIERS_ATTENDUS}.",
        )
    finally:
        host.run(shlex.join(["docker", "rm", "--force", nom]))


def test_les_bornes_heritees_mordent_vraiment_sur_un_journal(host):
    """Ce que le démon applique, éprouvé par un journal qui déborde.

    L'inspection dit ce que le démon a retenu au moment de la création ; seul un
    journal qui déborde dit que la rotation tourne et tient dans son budget.

    MESURÉ : le cas « fichier juste, démon non rechargé » n'est pas atteignable,
    Docker relisant ses `log-opts` à chaque création. Ce contrôle ne refuse donc
    jamais seul. Il discrimine en revanche les bornes par leur effet, et c'est
    lui qui a refusé l'état initial, où 10 Mio laissent passer les douze mille
    lignes.

    Le conteneur est lancé SANS option : il hérite, comme tous les nouveaux.
    """
    nom = f"dsoxlab-log-rotation-{uuid.uuid4().hex[:12]}"
    emetteur = (
        f'i=0; while [ "$i" -lt {LIGNES} ]; do printf "%0100d\\n" "$i"; '
        'i=$((i+1)); done; sleep 30'
    )
    lance = host.run(
        shlex.join([
            "docker", "run", "--detach", "--name", nom,
            "--label", f"dsoxlab.lab={LAB}", IMAGE, "sh", "-c", emetteur,
        ])
    )
    try:
        assert lance.rc == 0, message(
            en=f"Could not start the rotation probe: {lance.stderr.strip()[-400:]}. "
               "Not your fault if the daemon answers, report it.",
            fr=f"Impossible de lancer la sonde de rotation : "
               f"{lance.stderr.strip()[-400:]}. Ce n'est pas votre faute si le "
               "démon répond, signalez-le.",
        )
        host.run("sleep 6")

        lu = host.run(shlex.join(["docker", "logs", nom]))
        assert lu.rc == 0, message(
            en=f"Cannot read the probe's logs: {lu.stderr.strip()[-200:]}. Not your fault, report it.",
            fr=f"Les journaux de la sonde sont illisibles : {lu.stderr.strip()[-200:]}. Ce n'est pas votre faute, signalez-le.",
        )
        lignes = [ligne for ligne in lu.stdout.splitlines() if ligne.strip()]
        assert lignes, message(
            en="The probe wrote nothing, so nothing can be concluded about rotation. Not your fault, report it.",
            fr="La sonde n'a rien écrit, donc rien ne peut être conclu sur la rotation. Ce n'est pas votre faute, signalez-le.",
        )

        premiere = lignes[0].strip().lstrip("0") or "0"
        assert premiere != "0", message(
            en=f"The journal still starts at line « {premiere} », so all {LIGNES} "
               "lines are retained and nothing was rotated. Declared bounds that "
               "do not bite bound nothing: it is the journal that says whether "
               "the engine applies them.",
            fr=f"Le journal commence encore à la ligne « {premiere} », donc les "
               f"{LIGNES} lignes sont conservées et rien n'a tourné. Des bornes "
               "déclarées qui ne mordent pas ne bornent rien : c'est le journal "
               "qui dit si le moteur les applique.",
        )

        volume = sum(len(ligne.encode()) + 1 for ligne in lignes)
        assert volume <= BUDGET_OCTETS, message(
            en=f"The retained journal holds {volume} bytes, above the "
               f"{BUDGET_OCTETS} that {FICHIERS_ATTENDUS} files of "
               f"{TAILLE_ATTENDUE} can keep. And this is a lower bound: the JSON "
               "files wrapping these lines are larger still.",
            fr=f"Le journal retenu porte {volume} octets, au-delà des "
               f"{BUDGET_OCTETS} que {FICHIERS_ATTENDUS} fichiers de "
               f"{TAILLE_ATTENDUE} peuvent conserver. Et c'est un minorant : les "
               "fichiers JSON qui encapsulent ces lignes pèsent davantage encore.",
        )
    finally:
        host.run(shlex.join(["docker", "rm", "--force", nom]))
