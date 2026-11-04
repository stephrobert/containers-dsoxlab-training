"""Un seul flux corrigé, les exclusions tenues, et le tout qui survit.

Pourquoi deux contrôles là où il n'y en avait qu'un
--------------------------------------------------

Le fichier précédent portait **un** `def test_` et **une seule** assertion : il
lançait `probe.py` en entier et agrégeait tout dans son verdict. Pour deux
exigences distinctes, l'apprenant recevait un refus unique et neuf cents
caractères de trace.

Comme `container-arret-transactionnel`, ce lab se joue sur un enchaînement : la
sonde monte une topologie à quatre composants, éprouve trois sauts, puis vérifie
que les compteurs des règles de refus ont bougé. Mais sa fonction `assess()`
était déjà autonome, et il a suffi de l'exposer en deux étapes plutôt que de la
restructurer.

Les deux contrôles mesurent deux choses indépendantes :

1. le flux métier **passe**, et les trois exclusions tiennent ;
2. tout cela **survit à une recréation** de la stack.

Le second n'est pas une redite. Une règle corrigée à la main dans le namespace du
routeur disparaîtrait au redémarrage, et le lab serait réussi sur un état qui ne
survit pas. L'étape joue donc `assess()` avant et après la recréation, parce
qu'une recréation partant d'un état déjà faux ne dirait rien de la persistance.

CE QUI RESTE DANS LES GARDE-FOUS, ET POURQUOI. La topologie et les refus tiennent
déjà sur l'état initial, puisque la règle fautive bloque tout : ils ne peuvent
donc pas noter. Ils restent dans `assess()`, où ils conditionnent la mesure, et
l'un d'eux porte la finesse du lab — les compteurs nftables doivent avoir
**augmenté** après les sondes refusées, ce qui prouve que le trafic a bien
traversé les règles de protection au lieu d'être perdu ailleurs.

C'est la septième fois aujourd'hui que ce cas se présente, et la règle est
établie : ce qui est vrai avant tout travail ne peut pas être un contrôle, et
appartient à celui dont il conditionne le sens.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import lab_host, message

SONDE = Path(__file__).with_name("probe.py")

# L ÉTAPE DE RECRÉATION EN FAIT DEUX FOIS PLUS : elle joue `assess()` avant, puis
# recrée la stack, puis le rejoue. Son budget est donc plus large que celui de
# l'autre, et non le même par commodité.
DELAIS = {"etat": 110, "recreation": 180}


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _cause(stderr: str) -> str:
    """Le message de la sonde, dégagé du bruit qui l'entoure.

    La sonde lève ses assertions avec des messages écrits pour être lus. Le
    stderr brut y ajoute un « Warning: Permanently added ... » venu de ssh et une
    dizaine de lignes de traceback Python : faire fouiller l'apprenant dedans est
    ce que ce catalogue reproche à ses propres contrôles.

    Le traceback n'est pas perdu : sans assertion, c'est que la sonde a cassé
    autrement, et la trace brute est alors la seule information disponible.
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


def _etape(host, nom: str):
    """Joue une étape de la sonde sur la VM.

    Le texte de la sonde passe en argument de `-c`, et l'étape en argument de la
    sonde : avec `python3 -c <script> <etape>`, `sys.argv` vaut
    `['-c', '<etape>']`. Mesuré sur ce catalogue : les backends de testinfra
    IGNORENT leurs kwargs, donc un `stdin=` ne transmettrait rien et chaque
    contrôle jouerait la même étape en silence.
    """
    return host.run(
        "env DSOXLAB_LANG=%s timeout %s python3 -c %s %s",
        message(en="en", fr="fr"),
        str(DELAIS[nom]),
        SONDE.read_text(encoding="utf-8"),
        nom,
    )


def _verdict(resultat, nom: str, attendu_en: str, attendu_fr: str) -> None:
    assert resultat.rc != 124, message(
        en=f"The « {nom} » step exceeded its {DELAIS[nom]} s budget. Not "
           "necessarily your fault: a saturated host slows the topology down. "
           "Retry, and report it if it persists.",
        fr=f"L'étape « {nom} » a dépassé son budget de {DELAIS[nom]} s. Ce n'est "
           "pas nécessairement votre faute : un hôte saturé ralentit la "
           "topologie. Recommencez, et signalez-le si cela persiste.",
    )
    cause = _cause(resultat.stderr)
    assert resultat.rc == 0, message(
        en=f"{attendu_en}\n  {cause}",
        fr=f"{attendu_fr}\n  {cause}",
    )


def test_le_flux_metier_passe_et_les_exclusions_tiennent(host):
    """Le cœur du lab : un seul flux corrigé, et rien d'autre ouvert.

    Les trois sauts doivent répondre, et les trois sondes refusées doivent
    l'être : le client non autorisé, le port de debug, et la destination erronée.
    L'étape vérifie en outre que les compteurs des règles de refus ont augmenté,
    ce qui prouve que ce trafic a traversé les protections au lieu d'être perdu
    ailleurs.
    """
    _verdict(
        _etape(host, "etat"),
        "etat",
        "The business flow does not pass, or an exclusion no longer holds:",
        "Le flux métier ne passe pas, ou une exclusion ne tient plus :",
    )


def test_les_protections_survivent_a_une_recreation(host):
    """Ce qui distingue une correction d'un contournement.

    Une règle posée à la main dans le namespace du routeur disparaîtrait au
    redémarrage. L'étape joue donc l'évaluation complète, recrée la stack par
    Compose, et la rejoue : les deux passages doivent réussir.
    """
    _verdict(
        _etape(host, "recreation"),
        "recreation",
        "The corrected flow or the exclusions did not survive a recreation:",
        "Le flux corrigé ou les exclusions n'ont pas survécu à une recréation :",
    )
