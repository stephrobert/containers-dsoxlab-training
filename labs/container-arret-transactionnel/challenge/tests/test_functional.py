"""Quatre étapes de l'arrêt transactionnel, jouées et notées séparément.

Pourquoi quatre contrôles là où il n'y en avait qu'un
----------------------------------------------------

Le fichier précédent portait **un** `def test_` et **une seule** assertion : il
lançait `probe.py` en entier et agrégeait tout dans son verdict. Pour quatre
exigences distinctes, l'apprenant recevait un refus unique et neuf cents
caractères de trace, à charge pour lui de deviner laquelle avait échoué.

LE SCÉNARIO EST SÉQUENTIEL PAR NATURE, et c'est ce qui rend ce lab différent des
autres de ce catalogue. Il faut un conteneur d'essai durci, puis une transaction
en vol, puis un signal, puis une recréation. On ne peut donc pas séparer des
assertions sur un état déjà posé : chaque contrôle doit **refaire** ce dont il a
besoin.

C'est le prix de l'indépendance, et il est assumé : un contrôle qui suppose qu'un
autre a déjà tourné mentirait dès qu'on le joue seul, ce que `-k` et `--lf` font
tous les jours. La sonde a donc été découpée en quatre étapes autonomes, chacune
montant son propre conteneur d'essai sur un volume neuf et le retirant ensuite.

Les trois contrôles :

1. le service fourni est **durci** comme le scénario le demande, ce qui se lit
   sans rien lancer ;
2. un arrêt **gracieux** laisse la transaction en vol se valider, là où un arrêt
   **forcé** l'abandonne sans abîmer ce qui était acquis ;
3. la transaction validée **survit à une recréation**, avec une configuration
   différente pour que la recréation soit observable.

POURQUOI TROIS ET NON QUATRE. L'arrêt forcé a d'abord été écrit comme un contrôle
à part, et le cycle a rendu ROUGE : il PASSE sur l'état initial. C'est attendu, et
le scénario le dit à sa façon en demandant de « comparer » un arrêt forcé : un
`SIGKILL` abandonne naturellement une transaction non validée, puisque rien ne
l'a écrite. L'apprenant n'a rien à réparer pour l'obtenir.

Il n'est pas accessoire pour autant, et c'est même lui qui donne son sens au
deuxième contrôle : sans la comparaison, un arrêt gracieux qui valide pourrait
passer pour un hasard. Sa place est donc DANS ce contrôle, dont il est la seconde
moitié. C'est la quatrième fois que ce cas se présente dans ce catalogue, et la
règle s'énonce ainsi : ce qui est vrai avant tout travail ne peut pas être un
contrôle, et appartient à celui dont il conditionne le sens.

L'étape forcée pose elle-même sa transaction témoin avant le `SIGKILL`, plutôt
que de réutiliser celle de l'étape gracieuse : les deux restent donc jouables
séparément, ce que `-k` fait tous les jours.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import lab_host, message

SONDE = Path(__file__).with_name("probe.py")

# CHAQUE ÉTAPE MONTE SON CONTENEUR D ESSAI, donc chacune a besoin de son propre
# budget. L ancien contrôle disposait de 110 s pour le scénario entier ; les
# étapes dynamiques en reçoivent autant chacune, et le durcissement, qui ne lance
# rien, s en contente de beaucoup moins.
DELAIS = {
    "durcissement": 40,
    "gracieux": 110,
    "recreation": 140,
    "force": 140,
}


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _etape(host, nom: str):
    """Joue une étape de la sonde sur la VM, et rend sa trace en cas d'échec.

    LE TEXTE DE LA SONDE PASSE EN ARGUMENT DE `-c`, et l'étape en argument de la
    sonde : avec `python3 -c <script> <etape>`, `sys.argv` vaut
    `['-c', '<etape>']`, donc la sonde lit son étape dans `sys.argv[1]`.

    Un premier essai la passait par l'entrée standard, avec `python3 -` et un
    `stdin=` sur `host.run`. Mesuré avant de livrer : `run(self, command, *args,
    **kwargs)` IGNORE ses kwargs dans les deux backends de testinfra, le SSH
    comme le paramiko. La sonde n'aurait donc jamais reçu son étape, et chaque
    contrôle aurait joué la même chose en silence.

    C'est testinfra qui quote le script, par `get_command`, et c'est la forme que
    ce lab employait déjà.
    """
    return host.run(
        "env DSOXLAB_LANG=%s timeout %s python3 -c %s %s",
        message(en="en", fr="fr"),
        str(DELAIS[nom]),
        SONDE.read_text(encoding="utf-8"),
        nom,
    )


def _cause(stderr: str) -> str:
    """Le message de la sonde, dégagé du bruit qui l'entoure.

    MESURÉ SUR UN ÉCHEC RÉEL, et c'est la raison de cette fonction. Le stderr
    brut donnait à l'apprenant, dans cet ordre : le texte du contrôle, un
    « Warning: Permanently added ... to the list of known hosts » venu de ssh,
    dix lignes de traceback Python avec ses `^^^^`, et SEULEMENT ENSUITE le
    message utile, « Le service déclare User=(vide) au lieu de 10001:10001 ».

    Faire fouiller l'apprenant dans un traceback est précisément ce que ce
    catalogue reproche à ses propres contrôles. La sonde lève ses assertions avec
    des messages écrits pour être lus : on garde le dernier, qui est la cause.

    Le traceback n'est pas perdu pour autant : s'il n'y a aucune assertion, c'est
    que la sonde a cassé autrement, et la trace brute est alors la seule
    information disponible.
    """
    lignes = [
        ligne.strip()
        for ligne in stderr.splitlines()
        if ligne.strip().startswith("AssertionError:")
    ]
    if lignes:
        return lignes[-1].removeprefix("AssertionError:").strip()
    bruit = ("Warning: Permanently added", "Traceback (most recent call last)")
    utiles = [
        ligne for ligne in stderr.splitlines()
        if ligne.strip() and not ligne.strip().startswith(bruit)
    ]
    return "\n".join(utiles[-12:])


def _verdict(resultat, nom: str, attendu_en: str, attendu_fr: str) -> None:
    assert resultat.rc != 124, message(
        en=f"The « {nom} » step exceeded its {DELAIS[nom]} s budget. Not "
           "necessarily your fault: a saturated host slows the trial container "
           "down. Retry, and report it if it persists.",
        fr=f"L'étape « {nom} » a dépassé son budget de {DELAIS[nom]} s. Ce n'est "
           "pas nécessairement votre faute : un hôte saturé ralentit le "
           "conteneur d'essai. Recommencez, et signalez-le si cela persiste.",
    )
    cause = _cause(resultat.stderr)
    assert resultat.rc == 0, message(
        en=f"{attendu_en}\n  {cause}",
        fr=f"{attendu_fr}\n  {cause}",
    )


def test_le_service_fourni_est_durci_comme_demande(host):
    """Ce qui se lit sur le service, sans rien lancer.

    C'est l'étape la plus rapide, et celle qui échoue d'abord quand le lancement
    n'a pas été réparé : utilisateur 10001, racine en lecture seule, volume
    durable sur /data, image épinglée, et aucun privilège ajouté.
    """
    _verdict(
        _etape(host, "durcissement"),
        "durcissement",
        "The supplied service is not hardened as the scenario asks:",
        "Le service fourni n'est pas durci comme le scénario le demande :",
    )


def test_un_arret_gracieux_valide_la_transaction_la_ou_un_arret_force_l_abandonne(host):
    """Les deux moitiés de l'exercice, et c'est leur contraste qui le mesure.

    D'abord l'ordonné : une écriture est retenue avant validation, puis le
    conteneur reçoit un arrêt gracieux. La requête doit aboutir, le conteneur
    sortir en 0, et la séquence d'événements montrer que le signal est arrivé
    PENDANT la transaction : c'est l'ordre qui prouve la réception, pas la seule
    présence des lignes.

    Puis le brutal, qui n'est pas une exigence mais la comparaison sans laquelle
    la première moitié ne prouve rien. L'étape valide une transaction témoin,
    retient une seconde, envoie un `SIGKILL`, et vérifie que seule la seconde est
    perdue, que le témoin est intact, et que la base accepte encore une écriture :
    un abandon qui laisse un verrou derrière lui protège les données en
    interdisant la suite.
    """
    _verdict(
        _etape(host, "gracieux"),
        "gracieux",
        "A graceful stop did not let the in-flight transaction commit:",
        "Un arrêt gracieux n'a pas laissé la transaction en vol se valider :",
    )
    _verdict(
        _etape(host, "force"),
        "force",
        "A forced stop did not abort only the in-flight transaction:",
        "Un arrêt forcé n'a pas abandonné seulement la transaction en vol :",
    )


def test_la_transaction_validee_survit_a_la_recreation(host):
    """La durabilité, qui est l'objet du volume.

    L'étape recrée le conteneur avec une configuration différente, et l'exige
    observable en HTTP : sans cela, rien ne distinguerait une recréation d'un
    conteneur jamais arrêté.
    """
    _verdict(
        _etape(host, "recreation"),
        "recreation",
        "The committed transaction did not survive the recreation:",
        "La transaction validée n'a pas survécu à la recréation :",
    )

