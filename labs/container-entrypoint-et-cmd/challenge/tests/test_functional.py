"""Tests fonctionnels du lab container-entrypoint-et-cmd : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. La différence entre `ENTRYPOINT` et `CMD`, qui ne se voit
pas dans l'image mais dans ce qui arrive quand on passe des arguments à
`docker run`. Deux règles suffisent à tout expliquer, et ce lab fait rencontrer
leurs quatre conséquences au lieu de les énoncer.

POURQUOI LES JOURNAUX, ET NON L'IMAGE. On pourrait lire `.Config.Entrypoint`
dans l'inspection d'une image : cela noterait ce que l'image DÉCLARE, que le
setup a écrit lui-même. Ce qui s'apprend ici est ce qui s'EXÉCUTE, et le seul
endroit où cela se lit est la sortie du processus principal, donc les journaux
des conteneurs produits.

CE QU'ON NE MESURE PAS. Jamais la commande tapée. Chacun des quatre résultats
s'obtient de plusieurs façons, et deux d'entre eux ont même plusieurs formes
légitimes (la forme exec et la forme shell). On confronte donc une sortie
attendue à la sortie réelle.

CHAQUE CONTRÔLE VÉRIFIE AUSSI UNE ABSENCE. C'est ce qui le rend discriminant :
un conteneur dont les journaux portent à la fois le défaut de l'image et le
texte demandé n'a rien remplacé, et un conteneur qui garde le préfixe n'a rien
contourné. Sans la partie « et pas ceci », deux des quatre contrôles
passeraient sur une démonstration ratée.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

DEFAUT_DE_L_IMAGE = "defaut-de-limage"
PREFIXE = "prefixe-entrypoint"

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


def _journaux(host, conteneur: str) -> str:
    """Les journaux d'un conteneur, sortie standard et erreur réunies.

    Les deux sont réunies parce que la forme shell et la forme exec n'écrivent
    pas toujours du même côté, et que le lab ne note pas ce détail.
    """
    res = host.run("docker logs %s", conteneur)
    if res.rc != 0:
        pytest.fail(message(
            en=f"no container named `{conteneur}` exists, or its logs cannot be "
               f"read: {res.stderr.strip()}\n"
               "The four containers must REMAIN: it is in their logs that what "
               "ran is read. A `--rm` erases the evidence.",
            fr=f"aucun conteneur nommé `{conteneur}` n'existe, ou ses journaux "
               f"sont illisibles : {res.stderr.strip()}\n"
               "Les quatre conteneurs doivent RESTER : c'est dans leurs "
               "journaux qu'on lit ce qui a tourné. Un `--rm` efface la preuve.",
        ))
    return (res.stdout + res.stderr).strip()


def test_sans_argument_le_cmd_de_l_image_s_execute(host) -> None:
    """Première règle, vue dans son cas le plus simple.

    Un `CMD` est ce que l'image exécute quand on ne lui demande rien. Rien
    d'autre n'est noté ici : c'est le point de référence auquel les trois
    autres contrôles se comparent.
    """
    sortie = _journaux(host, "defaut")
    assert DEFAUT_DE_L_IMAGE in sortie, message(
        en=f"the logs of `defaut` do not carry `{DEFAUT_DE_L_IMAGE}`.\n"
           f"  what they carry: {sortie[:160] or '(nothing)'}\n"
           "Run `img-cmd:1.0` with NO argument: its CMD is what it executes "
           "when nothing is asked of it.",
        fr=f"les journaux de `defaut` ne portent pas `{DEFAUT_DE_L_IMAGE}`.\n"
           f"  ce qu'ils portent : {sortie[:160] or '(rien)'}\n"
           "Lancez `img-cmd:1.0` SANS argument : son CMD est ce qu'elle "
           "exécute quand on ne lui demande rien.",
    )


def test_un_argument_remplace_entierement_le_cmd(host) -> None:
    """Deuxième règle : un `CMD` seul ne résiste pas.

    L'absence du défaut est aussi importante que la présence du texte demandé :
    c'est elle qui prouve le REMPLACEMENT. Un conteneur qui afficherait les
    deux n'aurait rien remplacé, et le message le dit.
    """
    sortie = _journaux(host, "remplace")
    assert "remplacement-total" in sortie, message(
        en="the logs of `remplace` do not carry `remplacement-total`.\n"
           f"  what they carry: {sortie[:160] or '(nothing)'}\n"
           "What you pass to `docker run` after the image name takes the place "
           "of its CMD, entirely: it is a command, so give it one.",
        fr="les journaux de `remplace` ne portent pas `remplacement-total`.\n"
           f"  ce qu'ils portent : {sortie[:160] or '(rien)'}\n"
           "Ce qu'on passe à `docker run` après le nom de l'image prend la "
           "place de son CMD, entièrement : c'est une commande, donnez-lui en "
           "une.",
    )
    assert DEFAUT_DE_L_IMAGE not in sortie, message(
        en=f"the logs of `remplace` still carry `{DEFAUT_DE_L_IMAGE}`: the "
           "image's CMD ran as well, so nothing was replaced. A CMD is "
           "replaced, not completed.",
        fr=f"les journaux de `remplace` portent encore "
           f"`{DEFAUT_DE_L_IMAGE}` : le CMD de l'image a tourné aussi, donc "
           "rien n'a été remplacé. Un CMD se remplace, il ne se complète pas.",
    )


def test_un_argument_complete_l_entrypoint_au_lieu_de_le_remplacer(host) -> None:
    """Troisième règle, et c'est elle qui surprend.

    Le même argument, passé à une image qui déclare un `ENTRYPOINT`, ne
    remplace plus rien : il devient l'argument de l'entrypoint. Les deux
    assertions sont donc indissociables, le préfixe ET le complément.
    """
    sortie = _journaux(host, "complete")
    assert PREFIXE in sortie, message(
        en=f"the logs of `complete` do not carry the entrypoint prefix "
           f"`{PREFIXE}`.\n  what they carry: {sortie[:160] or '(nothing)'}\n"
           "An ENTRYPOINT is not replaced by what you pass to `docker run`. If "
           "the prefix is missing, you overrode it, which is the fourth "
           "container's job.",
        fr=f"les journaux de `complete` ne portent pas le préfixe de "
           f"l'entrypoint `{PREFIXE}`.\n"
           f"  ce qu'ils portent : {sortie[:160] or '(rien)'}\n"
           "Un ENTRYPOINT n'est pas remplacé par ce qu'on passe à "
           "`docker run`. S'il manque, vous l'avez contourné, ce qui est le "
           "rôle du quatrième conteneur.",
    )
    assert "complement-cmd" in sortie, message(
        en="the logs of `complete` carry the prefix but not `complement-cmd`: "
           "the argument did not reach the entrypoint. Passed after the image "
           "name, it takes the place of the CMD and becomes the entrypoint's "
           "argument.",
        fr="les journaux de `complete` portent le préfixe mais pas "
           "`complement-cmd` : l'argument n'est pas parvenu à l'entrypoint. "
           "Passé après le nom de l'image, il prend la place du CMD et devient "
           "l'argument de l'entrypoint.",
    )


def test_l_entrypoint_peut_etre_contourne(host) -> None:
    """Quatrième cas : la règle a une porte de sortie, et elle est explicite.

    Un `ENTRYPOINT` se remplace, mais seulement si on le demande par l'option
    prévue. C'est ce qui le distingue d'un `CMD` : le contournement est un
    geste délibéré, pas un effet de bord d'un argument.
    """
    sortie = _journaux(host, "contourne")
    assert "sans-prefixe" in sortie, message(
        en="the logs of `contourne` do not carry `sans-prefixe`.\n"
           f"  what they carry: {sortie[:160] or '(nothing)'}\n"
           "An ENTRYPOINT can be replaced, but only through the option meant "
           "for it, not by an argument.",
        fr="les journaux de `contourne` ne portent pas `sans-prefixe`.\n"
           f"  ce qu'ils portent : {sortie[:160] or '(rien)'}\n"
           "Un ENTRYPOINT se remplace, mais seulement par l'option prévue pour "
           "cela, pas par un argument.",
    )
    assert PREFIXE not in sortie, message(
        en=f"the logs of `contourne` still carry `{PREFIXE}`: the entrypoint "
           "ran, so it was not overridden. Passing an argument is not enough, "
           "it would only take the CMD's place.",
        fr=f"les journaux de `contourne` portent encore `{PREFIXE}` : "
           "l'entrypoint a tourné, il n'a donc pas été remplacé. Passer un "
           "argument ne suffit pas, cela ne prendrait que la place du CMD.",
    )
