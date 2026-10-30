"""Tests fonctionnels du lab container-signaux-et-pid-1 : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un conteneur qui met le délai complet à s'arrêter est
un conteneur qu'on tue, et que la cause est presque toujours la même : le
processus qui reçoit le signal n'est pas celui qui saurait l'entendre.

CE QUI A ÉTÉ MESURÉ AVANT D'ÉCRIRE CE LAB. L'explication courante dit « forme
shell, donc le shell est PID 1 ». C'est faux sur cette image : mesuré le
2026-10-29 sur Alpine, un `ENTRYPOINT /app.sh` donne `PID1=app.sh` et un arrêt
propre, parce que busybox optimise la commande unique en un `exec` direct. Un
lab bâti sur cette explication aurait comparé deux images au comportement
identique, et deux de ses contrôles auraient été indistinguables.

Ce qui produit le piège est le cas réel le plus fréquent : un script d'entrée
qui lance l'application en ENFANT. Un seul mot l'en sépare, et trois
conséquences le montrent :

    sans exec : PID1=entree.sh  code=137  arrêt en 6 s, pas de SIGTERM reçu
    avec exec : PID1=app.sh     code=0    arrêt en 1 s, SIGTERM reçu

LE PREMIER CONTRÔLE EXIGE LE SYMPTÔME, PAS SA CORRECTION. `fragile` doit avoir
été arrêté et porter un code non nul. C'est délibéré : un apprenant doit avoir
VU le défaut avant de le corriger, sinon il corrige une consigne et non un
problème. Le conteneur est la pièce à conviction, et l'énoncé dit de ne pas y
toucher.

CE QU'ON NE MESURE PAS. Jamais la commande, ni la façon de corriger. Ajouter
`exec` dans le script d'entrée, invoquer l'application directement depuis
l'`ENTRYPOINT`, ou passer par un init qui réexpédie les signaux aboutissent
tous à un PID 1 qui entend SIGTERM. Les trois comptent.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message, nom_objet

FRAGILE = "fragile"
ROBUSTE = "robuste"
IMAGE_CORRIGEE = "img-corrige:1.0"

#: La sonde que CE TEST lance porte le préfixe du dépôt, par la discipline
#: du `conftest.py` : tout ce qu'un test crée doit être reconnaissable et
#: retiré, pour qu'un objet oublié ne se noie pas dans les centaines que
#: la machine porte déjà.
SONDE = nom_objet("container-signaux-et-pid-1", "sonde-pid1")
SCRIPT_D_ENTREE = "entree.sh"
TRACE_DU_SIGNAL = "sigterm-recu"

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


def _inspection(host, cible: str, champ: str) -> tuple[int, str]:
    """Un champ de l'inspection d'un conteneur, et le code de retour."""
    res = host.run("docker container inspect %s --format %s", cible, champ)
    return res.rc, res.stdout.strip()


def test_le_conteneur_fautif_a_ete_arrete_et_porte_le_symptome(host) -> None:
    """Le défaut doit avoir été VU, et sa trace est le code de sortie.

    On exige ici le symptôme et non sa correction : `fragile` est la pièce à
    conviction. Un apprenant qui aurait « réparé » ce conteneur aurait effacé
    ce qu'il devait constater.
    """
    rc, etat = _inspection(host, FRAGILE, "{{.State.Status}}")
    assert rc == 0, message(
        en=f"`{FRAGILE}` no longer exists. It had to be STOPPED and kept: it is "
           "the evidence of the defect, and the next checks compare against it.",
        fr=f"`{FRAGILE}` n'existe plus. Il fallait l'ARRÊTER et le conserver : "
           "c'est la pièce à conviction du défaut, et les contrôles suivants "
           "s'y comparent.",
    )
    assert etat == "exited", message(
        en=f"`{FRAGILE}` is in state `{etat}`: it has not been stopped yet, so "
           "it carries no exit code. Stop it and look at what it returns.",
        fr=f"`{FRAGILE}` est dans l'état `{etat}` : il n'a pas encore été "
           "arrêté, il ne porte donc aucun code de sortie. Arrêtez-le et "
           "regardez ce qu'il rend.",
    )
    _, code = _inspection(host, FRAGILE, "{{.State.ExitCode}}")
    assert code != "0", message(
        en=f"`{FRAGILE}` exited with code 0, which this lab does not expect. "
           "Its entry script keeps SIGTERM to itself, so the application never "
           "sees it and the engine ends up killing everything. If you fixed "
           "this container, replay the lab: its failure is what you have to "
           "observe.",
        fr=f"`{FRAGILE}` est sorti avec le code 0, ce que ce lab n'attend pas. "
           "Son script d'entrée garde SIGTERM pour lui, l'application ne le "
           "voit donc jamais et le moteur finit par tout tuer. Si vous avez "
           "corrigé ce conteneur, rejouez le lab : c'est son échec qu'il faut "
           "observer.",
    )
    assert TRACE_DU_SIGNAL not in host.run("docker logs %s", FRAGILE).stdout, message(
        en=f"`{FRAGILE}` logged `{TRACE_DU_SIGNAL}`, so it did receive the "
           "signal. That is not the container the setup laid out: replay the "
           "lab.",
        fr=f"`{FRAGILE}` a écrit `{TRACE_DU_SIGNAL}`, il a donc bien reçu le "
           "signal. Ce n'est pas le conteneur que le setup a posé : rejouez le "
           "lab.",
    )


def test_l_image_corrigee_met_l_application_en_pid_1(host) -> None:
    """La cause se corrige à la racine : qui est le processus numéro un.

    On lance un conteneur jetable depuis l'image corrigée pour lire son PID 1.
    C'est le seul endroit où la correction se constate avant tout arrêt, et
    cela ne présume rien de la façon dont elle a été faite.
    """
    res = host.run("docker image inspect %s", IMAGE_CORRIGEE)
    assert res.rc == 0, message(
        en=f"the image `{IMAGE_CORRIGEE}` does not exist. The sources sit in "
           "/opt/lab-signaux: one word in the entry script separates it from "
           "the faulty image.",
        fr=f"l'image `{IMAGE_CORRIGEE}` n'existe pas. Les sources sont dans "
           "/opt/lab-signaux : un seul mot du script d'entrée la sépare de "
           "l'image fautive.",
    )
    sonde = host.run(
        "docker run -d --rm --name %s %s", SONDE, IMAGE_CORRIGEE
    )
    assert sonde.rc == 0, message(
        en=f"a container from `{IMAGE_CORRIGEE}` cannot be started: "
           f"{sonde.stderr.strip()}",
        fr=f"un conteneur issu de `{IMAGE_CORRIGEE}` ne démarre pas : "
           f"{sonde.stderr.strip()}",
    )
    try:
        lu = host.run("docker exec %s cat /proc/1/comm", SONDE)
        pid1 = lu.stdout.strip()
    finally:
        # Toujours retirer la sonde : un conteneur laissé par un TEST serait un
        # écart d'état, et le validateur du dépôt les refuse.
        host.run("docker rm -f %s", SONDE)
    assert pid1 and pid1 != SCRIPT_D_ENTREE, message(
        en=f"in a container from `{IMAGE_CORRIGEE}`, PID 1 is still "
           f"`{pid1 or 'unreadable'}`: the entry script is the one that will "
           "receive SIGTERM, and it is not the one that can act on it. The "
           "preparation must stay, only the way the application is launched "
           "changes.",
        fr=f"dans un conteneur issu de `{IMAGE_CORRIGEE}`, le PID 1 est encore "
           f"`{pid1 or 'illisible'}` : c'est le script d'entrée qui recevra "
           "SIGTERM, et ce n'est pas lui qui sait en faire quelque chose. La "
           "préparation doit rester, seule la façon de lancer l'application "
           "change.",
    )


def test_le_conteneur_corrige_s_arrete_proprement(host) -> None:
    """La conséquence qui compte pour l'exploitation : le code de sortie.

    Un code non nul sur un arrêt demandé fait croire à un incident, déclenche
    des alertes et fausse les redémarrages automatiques. C'est le vrai coût du
    défaut, et c'est ce que ce contrôle mesure.
    """
    rc, etat = _inspection(host, ROBUSTE, "{{.State.Status}}")
    assert rc == 0, message(
        en=f"no container named `{ROBUSTE}` exists. Run one from "
           f"`{IMAGE_CORRIGEE}`, then stop it.",
        fr=f"aucun conteneur nommé `{ROBUSTE}` n'existe. Lancez-en un depuis "
           f"`{IMAGE_CORRIGEE}`, puis arrêtez-le.",
    )
    assert etat == "exited", message(
        en=f"`{ROBUSTE}` is in state `{etat}`: it must have been stopped for "
           "its exit code to be read.",
        fr=f"`{ROBUSTE}` est dans l'état `{etat}` : il doit avoir été arrêté "
           "pour qu'on lise son code de sortie.",
    )
    _, code = _inspection(host, ROBUSTE, "{{.State.ExitCode}}")
    assert code == "0", message(
        en=f"`{ROBUSTE}` exited with code {code}, not 0. A 137 means the engine "
           "killed it after waiting: the signal did not reach a process able "
           "to act on it.",
        fr=f"`{ROBUSTE}` est sorti avec le code {code}, pas 0. Un 137 signifie "
           "que le moteur l'a tué après avoir attendu : le signal n'a pas "
           "atteint un processus capable d'en faire quelque chose.",
    )


def test_le_conteneur_corrige_a_vu_passer_le_signal(host) -> None:
    """La preuve directe, et elle vient de l'application elle-même.

    Le code 0 pourrait venir d'une application qui sort pour une autre raison.
    La trace écrite par le gestionnaire de signal ne laisse pas cette place au
    doute : elle n'existe que si SIGTERM a été reçu là où il devait l'être.
    """
    res = host.run("docker logs %s", ROBUSTE)
    assert res.rc == 0, message(
        en=f"cannot read the logs of `{ROBUSTE}`: {res.stderr.strip()}",
        fr=f"impossible de lire les journaux de `{ROBUSTE}` : {res.stderr.strip()}",
    )
    sortie = res.stdout + res.stderr
    assert TRACE_DU_SIGNAL in sortie, message(
        en=f"the logs of `{ROBUSTE}` do not carry `{TRACE_DU_SIGNAL}`.\n"
           f"  what they carry: {sortie.strip()[:160] or '(nothing)'}\n"
           "The application writes that line when it receives SIGTERM. Without "
           "it, the container may well have exited with 0 for another reason, "
           "and the signal still went nowhere.",
        fr=f"les journaux de `{ROBUSTE}` ne portent pas `{TRACE_DU_SIGNAL}`.\n"
           f"  ce qu'ils portent : {sortie.strip()[:160] or '(rien)'}\n"
           "L'application écrit cette ligne quand elle reçoit SIGTERM. Sans "
           "elle, le conteneur a peut-être sorti 0 pour une autre raison, et "
           "le signal n'est allé nulle part.",
    )
    assert "preparation-faite" in sortie, message(
        en=f"the logs of `{ROBUSTE}` do not carry `preparation-faite`: the "
           "entry script no longer does its work. Emptying it would also fix "
           "the signal, and would remove the reason it exists. The preparation "
           "must stay.",
        fr=f"les journaux de `{ROBUSTE}` ne portent pas `preparation-faite` : "
           "le script d'entrée ne fait plus son travail. Le vider corrigerait "
           "aussi le signal, et retirerait la raison de son existence. La "
           "préparation doit rester.",
    )
