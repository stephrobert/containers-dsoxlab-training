"""Tests fonctionnels du lab docker-cycle-de-vie : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que les états d'un conteneur forment un graphe, et qu'on
s'y déplace sans repartir de zéro. Le lab précédent enseignait trois verbes ;
celui-ci enseigne qu'un conteneur arrêté se **redémarre**, garde son identité
et garde ce qu'on a écrit dedans.

LE CONTRÔLE QUI PORTE TOUT LE LAB. Comparer l'identifiant de `dormeur` à celui
que le setup a relevé AVANT tout travail. C'est le seul moyen de distinguer
« j'ai redémarré le conteneur » de « j'en ai lancé un autre du même nom » : les
deux donnent un conteneur qui tourne, et un seul est le geste enseigné. Ici le
chemin EST la compétence, donc il se mesure, et il se mesure par son empreinte
plutôt qu'en espionnant les commandes tapées.

POURQUOI LE FICHIER N'EST PAS UNE REDITE. Un conteneur recréé perd ce qui avait
été écrit dedans. Le contrôle qui lit `/empreinte.txt` mesure donc la
conséquence observable de la faute que le précédent détecte : c'est ce qu'un
apprenant constate de lui-même, et c'est ce qui rend la leçon tenable sans
qu'on la lui affirme.

CE QU'ON NE MESURE PAS. Jamais la commande. `docker start`, `docker restart`
sur un conteneur arrêté, ou un démarrage par l'API aboutissent au même état
avec le même identifiant. `docker pause` et un gel par cgroup de même.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

A_REDEMARRER = "dormeur"
A_METTRE_EN_PAUSE = "actif"
A_FAIRE_SORTIR = "sortie"
CODE_ATTENDU = 42
EMPREINTE_HOTE = "/opt/lab-cycle/id-dormeur.txt"
EMPREINTE_CONTENEUR = "/empreinte.txt"
MARQUE = "je-suis-le-conteneur-dorigine"

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


def _champ(host, conteneur: str, format_go: str) -> tuple[int, str]:
    """Un champ de l'inspection d'un conteneur, et le code de retour."""
    res = host.run("docker container inspect %s --format %s", conteneur, format_go)
    return res.rc, res.stdout.strip()


def test_le_conteneur_arrete_a_ete_redemarre(host) -> None:
    """Il tourne à nouveau, et c'est bien LUI.

    Deux assertions, dans cet ordre : d'abord qu'il tourne, ensuite que son
    identifiant n'a pas changé. L'inverse donnerait un message trompeur à qui
    n'a encore rien fait, en lui parlant d'identifiant alors qu'il n'a pas
    redémarré le conteneur du tout.
    """
    rc, etat = _champ(host, A_REDEMARRER, "{{.State.Status}}")
    assert rc == 0, message(
        en=f"`{A_REDEMARRER}` no longer exists. It had to be restarted, not "
           "removed: a stopped container is still there, and that is what this "
           "lab is about.",
        fr=f"`{A_REDEMARRER}` n'existe plus. Il fallait le redémarrer, pas le "
           "supprimer : un conteneur arrêté est toujours là, et c'est le sujet "
           "de ce lab.",
    )
    assert etat == "running", message(
        en=f"`{A_REDEMARRER}` is not running (state: {etat}). A stopped "
           "container is restarted, without being recreated.",
        fr=f"`{A_REDEMARRER}` ne tourne pas (état : {etat}). Un conteneur "
           "arrêté se redémarre, sans être recréé.",
    )

    fichier = host.file(EMPREINTE_HOTE)
    if not fichier.exists:
        pytest.skip(message(
            en=f"{EMPREINTE_HOTE} is missing: the setup did not record the "
               "original identifier",
            fr=f"{EMPREINTE_HOTE} est absent : le setup n'a pas relevé "
               "l'identifiant d'origine",
        ))
    attendu = fichier.content_string.strip()
    _, actuel = _champ(host, A_REDEMARRER, "{{.Id}}")
    assert actuel == attendu, message(
        en=f"`{A_REDEMARRER}` is running, but it is NOT the same container.\n"
           f"  original  : {attendu[:20]}…\n"
           f"  current   : {actuel[:20]}…\n"
           "You recreated it instead of restarting it. Both give a running "
           "container, and only one keeps its identity, its logs and what was "
           "written inside it.",
        fr=f"`{A_REDEMARRER}` tourne, mais ce n'est PAS le même conteneur.\n"
           f"  d'origine : {attendu[:20]}…\n"
           f"  actuel    : {actuel[:20]}…\n"
           "Vous l'avez recréé au lieu de le redémarrer. Les deux donnent un "
           "conteneur qui tourne, et un seul garde son identité, ses journaux "
           "et ce qui avait été écrit dedans.",
    )


def test_ce_qui_avait_ete_ecrit_dans_le_conteneur_est_toujours_la(host) -> None:
    """L'arrêt ne détruit pas la couche d'écriture du conteneur.

    C'est la conséquence observable du contrôle précédent, et elle se constate
    plutôt qu'elle ne s'affirme : un conteneur recréé est vierge.
    """
    res = host.run(
        "docker exec %s cat %s", A_REDEMARRER, EMPREINTE_CONTENEUR
    )
    assert res.rc == 0, message(
        en=f"cannot read {EMPREINTE_CONTENEUR} inside `{A_REDEMARRER}`: "
           f"{res.stderr.strip()}\n"
           "A container must be running to be entered. And a recreated "
           "container is blank: the file was in the original one.",
        fr=f"impossible de lire {EMPREINTE_CONTENEUR} dans `{A_REDEMARRER}` : "
           f"{res.stderr.strip()}\n"
           "Un conteneur doit tourner pour qu'on y entre. Et un conteneur "
           "recréé est vierge : le fichier était dans celui d'origine.",
    )
    assert MARQUE in res.stdout, message(
        en=f"{EMPREINTE_CONTENEUR} exists but does not carry the original "
           f"mark.\n  found: {res.stdout.strip()[:120] or '(empty)'}",
        fr=f"{EMPREINTE_CONTENEUR} existe mais ne porte pas la marque "
           f"d'origine.\n  trouvé : {res.stdout.strip()[:120] or '(vide)'}",
    )


def test_le_conteneur_en_service_est_en_pause(host) -> None:
    """Un état que ni `stop` ni `rm` ne donnent, et qui se défait.

    La pause gèle les processus sans les terminer : le conteneur n'est ni en
    marche ni arrêté, et c'est le troisième état du graphe. Le message nomme
    les deux fautes voisines, parce qu'elles appellent des gestes opposés.
    """
    rc, etat = _champ(host, A_METTRE_EN_PAUSE, "{{.State.Status}}")
    assert rc == 0, message(
        en=f"`{A_METTRE_EN_PAUSE}` no longer exists: it had to be PAUSED, "
           "neither stopped nor removed.",
        fr=f"`{A_METTRE_EN_PAUSE}` n'existe plus : il fallait le METTRE EN "
           "PAUSE, ni l'arrêter ni le supprimer.",
    )
    assert etat == "paused", message(
        en=f"`{A_METTRE_EN_PAUSE}` is in state `{etat}`, not `paused`. "
           "Pausing freezes the processes without ending them: the container "
           "is neither running nor stopped, and that state is reversible.",
        fr=f"`{A_METTRE_EN_PAUSE}` est dans l'état `{etat}`, pas `paused`. La "
           "pause gèle les processus sans les terminer : le conteneur n'est ni "
           "en marche ni arrêté, et cet état se défait.",
    )


def test_un_conteneur_termine_porte_le_code_de_sortie_demande(host) -> None:
    """Le code de sortie survit au conteneur, et c'est ce qui le rend utile.

    Un conteneur terminé garde le code rendu par son processus principal :
    c'est ce qu'un orchestrateur lit pour décider de relancer ou d'alerter.
    """
    rc, etat = _champ(host, A_FAIRE_SORTIR, "{{.State.Status}}")
    assert rc == 0, message(
        en=f"no container named `{A_FAIRE_SORTIR}` exists. It must have run "
           f"and finished with exit code {CODE_ATTENDU}.",
        fr=f"aucun conteneur nommé `{A_FAIRE_SORTIR}` n'existe. Il doit avoir "
           f"tourné puis s'être terminé avec le code de sortie {CODE_ATTENDU}.",
    )
    assert etat == "exited", message(
        en=f"`{A_FAIRE_SORTIR}` is in state `{etat}`: it has not finished yet, "
           "so it carries no exit code.",
        fr=f"`{A_FAIRE_SORTIR}` est dans l'état `{etat}` : il ne s'est pas "
           "encore terminé, il ne porte donc aucun code de sortie.",
    )
    _, code = _champ(host, A_FAIRE_SORTIR, "{{.State.ExitCode}}")
    assert code == str(CODE_ATTENDU), message(
        en=f"`{A_FAIRE_SORTIR}` finished with exit code {code}, not "
           f"{CODE_ATTENDU}. The code is the one returned by the container's "
           "main process, and it outlives the container.",
        fr=f"`{A_FAIRE_SORTIR}` s'est terminé avec le code {code}, pas "
           f"{CODE_ATTENDU}. Le code est celui que rend le processus principal "
           "du conteneur, et il survit au conteneur.",
    )
