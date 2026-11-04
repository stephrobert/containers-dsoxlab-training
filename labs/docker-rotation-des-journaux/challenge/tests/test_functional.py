"""Une rotation des journaux qui jette vraiment, et pas seulement déclarée.

Pourquoi trois contrôles là où il n'y en avait qu'un
---------------------------------------------------

Le fichier précédent portait **un** `def test_` et six assertions, et toutes
lisaient la même chose : `HostConfig.LogConfig`, c'est-à-dire **ce qui a été
demandé au démon**. Rien ne vérifiait que la rotation ait lieu.

C'est le défaut que ce catalogue a rencontré partout aujourd'hui, sous des formes
différentes : une déclaration dit ce qu'on a demandé, le système dit ce qui est.
Un `--log-opt max-size=1k` accepté par le démon et jamais appliqué aurait passé
ce contrôle, et l'apprenant aurait eu le point sans que son journal soit borné.

La rotation est pourtant observable sans aucun privilège, et c'est mesuré. Le
service du lab émet cent lignes de cent chiffres, puis dort. Relevé sur
`docker.lab` avec les deux réglages, par `docker logs` seul :

    max-size=20m max-file=5   100 lignes retenues, la première est « 0 »
    max-size=1k  max-file=3    16 lignes retenues, la première est « 84 »

Les lignes anciennes ont donc réellement été jetées, et le volume retenu est
tombé sous le budget. Aucun de ces deux faits ne se lit dans la déclaration.

Les trois contrôles mesurent donc trois choses indépendantes :

1. le pilote et les bornes **déclarés** ;
2. les lignes les plus anciennes ont été **jetées** ;
3. le volume retenu tient dans le **budget** que ces bornes définissent.

Le troisième n'est pas une redite du deuxième. Jeter les lignes anciennes montre
que la rotation tourne ; tenir dans le budget montre qu'elle tourne avec les
bonnes valeurs. Une rotation réglée sur 1 Mio jetterait aussi, beaucoup plus
tard, et le deuxième contrôle seul l'accepterait.

CE QUE LA TRICHE A MONTRÉ, ET QU'IL FAUT DIRE. Les contrôles 2 et 3 refusent
réellement, et ils l'ont fait sur l'état initial comme sur une rotation réglée
trop large. Mais ils ne refusent **jamais seuls** : toute dégradation des bornes
est aussi vue par le contrôle 1, puisque Docker applique ce qu'il déclare. Il n'y
a donc aucune dégradation qui les isole.

Ce n'est pas la même chose qu'un contrôle inatteignable, et la distinction a
coûté un aller-retour sur un lab voisin. Un diagnostic qu'aucun travail ne peut
déclencher est du décor et se retire. Ici les deux contrôles mordent, et ce qu'ils
mesurent n'est pas ce que mesure le premier : le premier croit la déclaration,
eux regardent le journal. Le jour où le moteur accepterait une option sans
l'appliquer, ou la nommerait autrement, ils seraient les seuls à le voir. C'est
de la défense en profondeur, pas une redondance de confort, et cette note existe
pour qu'on ne les retire pas en les prenant pour l'autre.

Le relevé ne touche pas `/var/lib/docker`. C'est délibéré : lire les fichiers de
journal demande root, et le glob y échoue pour un compte non privilégié, ce qui
rendrait le contrôle dépendant d'un détail d'environnement. Le contenu brut rendu
par `docker logs` est de toute façon **plus petit** que les fichiers qui
l'encapsulent en JSON : s'il dépasse le budget, les fichiers le dépassent aussi.
"""

from __future__ import annotations

import json
import shlex

import pytest

from conftest import lab_host, message

CONTENEUR = "dsoxlab-log-rotation"
LAB = "docker-rotation-des-journaux"
TAILLE_MAXIMALE = "1k"
FICHIERS_MAXIMUM = "3"
BUDGET_OCTETS = 3 * 1024  # max-file fois max-size, tout ce que la rotation garde.


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _service(host) -> dict:
    """L'inspection du service, ou un échec qui dit quoi faire.

    Garde-fou de mesure et non exigence : sans un service étiqueté et actif,
    aucun des trois contrôles ne peut observer quoi que ce soit.
    """
    inspecte = host.run(shlex.join(["docker", "inspect", CONTENEUR]))
    assert inspecte.rc == 0, message(
        en=(
            f"The {CONTENEUR} service does not exist. Recreate it with the bounded "
            "log options, keeping its name and its label."
        ),
        fr=(
            f"Le service {CONTENEUR} n'existe pas. Recréez-le avec les options de "
            "journal bornées, en conservant son nom et son label."
        ),
    )
    conteneur = json.loads(inspecte.stdout)[0]
    assert conteneur["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the service: cleanup removes only what carries it.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le service : le nettoyage ne retire que ce qui le porte.",
    )
    assert conteneur["State"]["Running"], message(
        en=f"The {CONTENEUR} service is stopped. Leave it running.",
        fr=f"Le service {CONTENEUR} est arrêté. Laissez-le actif.",
    )
    return conteneur


def _journal(host) -> list[str]:
    """Les lignes que le moteur a RETENUES, après rotation."""
    lu = host.run(shlex.join(["docker", "logs", CONTENEUR]))
    assert lu.rc == 0, message(
        en=f"Cannot read the service logs: {lu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"Les journaux du service sont illisibles : {lu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    return [ligne for ligne in lu.stdout.splitlines() if ligne.strip()]


def test_le_pilote_declare_borne_les_journaux(host):
    """Ce qui a été demandé au démon."""
    conteneur = _service(host)
    config = conteneur["HostConfig"]["LogConfig"]

    assert config["Type"] == "json-file", message(
        en=f"The service uses the {config['Type']} driver instead of json-file.",
        fr=f"Le service utilise le pilote {config['Type']} au lieu de json-file.",
    )
    assert config["Config"].get("max-size") == TAILLE_MAXIMALE, message(
        en=(
            f"The service declares max-size={config['Config'].get('max-size')} "
            f"instead of {TAILLE_MAXIMALE}."
        ),
        fr=(
            f"Le service déclare max-size={config['Config'].get('max-size')} "
            f"au lieu de {TAILLE_MAXIMALE}."
        ),
    )
    assert config["Config"].get("max-file") == FICHIERS_MAXIMUM, message(
        en=(
            f"The service declares max-file={config['Config'].get('max-file')} "
            f"instead of {FICHIERS_MAXIMUM}."
        ),
        fr=(
            f"Le service déclare max-file={config['Config'].get('max-file')} "
            f"au lieu de {FICHIERS_MAXIMUM}."
        ),
    )


def test_les_lignes_les_plus_anciennes_ont_ete_jetees(host):
    """La rotation tourne-t-elle ? Ce n'est pas la déclaration qui le dit.

    Le service émet cent lignes numérotées de 0 à 99, puis dort. Si la rotation
    mord, les premières ne sont plus lisibles et les dernières le restent.
    """
    _service(host)
    lignes = _journal(host)

    assert lignes, message(
        en="The service logs are empty: nothing can be concluded about rotation. Not your fault if it runs, report it.",
        fr="Les journaux du service sont vides : rien ne peut être conclu sur la rotation. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )

    premiere = lignes[0].strip().lstrip("0") or "0"
    derniere = lignes[-1].strip().lstrip("0") or "0"

    assert derniere == "99", message(
        en=(
            f"The last emitted line is missing: the journal ends at « {derniere} » "
            "instead of 99. Rotation must drop the OLDEST lines, not the newest."
        ),
        fr=(
            f"La dernière ligne émise manque : le journal s'arrête à « {derniere} » "
            "au lieu de 99. La rotation doit jeter les lignes les PLUS ANCIENNES, "
            "non les plus récentes."
        ),
    )
    assert premiere != "0", message(
        en=(
            f"The journal still starts at line « {premiere} », so all one hundred "
            "lines are retained and nothing has been rotated. The declaration alone "
            "proves nothing: a cap the engine never applies passes it."
        ),
        fr=(
            f"Le journal commence encore à la ligne « {premiere} », donc les cent "
            "lignes sont conservées et rien n'a tourné. La déclaration seule ne "
            "prouve rien : un plafond que le moteur n'applique pas la satisfait."
        ),
    )


def test_le_volume_retenu_tient_dans_le_budget_declare(host):
    """La rotation tourne-t-elle avec les BONNES valeurs ?

    Ce contrôle n'est pas une redite du précédent. Jeter les lignes anciennes
    montre que la rotation tourne ; tenir dans le budget montre qu'elle tourne
    avec les bornes demandées. Une rotation réglée sur 1 Mio jetterait aussi,
    beaucoup plus tard, et le contrôle précédent seul l'accepterait.
    """
    _service(host)
    lignes = _journal(host)
    volume = sum(len(ligne.encode()) + 1 for ligne in lignes)

    assert volume <= BUDGET_OCTETS, message(
        en=(
            f"The retained journal holds {volume} bytes, above the {BUDGET_OCTETS} "
            f"that {FICHIERS_MAXIMUM} files of {TAILLE_MAXIMALE} can keep. And this "
            "is a lower bound: the JSON files wrapping these lines are larger "
            "still."
        ),
        fr=(
            f"Le journal retenu porte {volume} octets, au-delà des "
            f"{BUDGET_OCTETS} que {FICHIERS_MAXIMUM} fichiers de "
            f"{TAILLE_MAXIMALE} peuvent conserver. Et c'est un minorant : les "
            "fichiers JSON qui encapsulent ces lignes pèsent davantage encore."
        ),
    )
