"""Un contexte SSH nommé qui joint le vrai moteur distant, sans toucher au défaut.

Pourquoi deux contrôles là où il n'y en avait qu'un
--------------------------------------------------

Le fichier précédent portait **un** `def test_` et sept assertions enchaînées, et
il mesurait les bonnes choses. Le défaut était la forme, plus un ordre qui
trahissait l'intention.

LE MASQUAGE. La première assertion qui tombait masquait les six suivantes. Un
apprenant qui avait créé le contexte, l'avait fait pointer au bon endroit et
avait préservé son défaut recevait le même refus qu'un apprenant qui n'avait rien
fait.

L'ORDRE TRAHISSAIT L'INTENTION. L'assertion qui vérifie que le contexte **joint
vraiment** son démon était la DERNIÈRE du fichier, après le refus de la clé non
autorisée. Or son résultat était déjà calculé bien plus haut, et une assertion
intermédiaire l'utilisait. Un échec de connexion se manifestait donc d'abord par
une comparaison d'identités illisible, et le message qui disait « le contexte SSH
ne joint pas son démon » n'était jamais atteint.

POURQUOI DEUX ET NON QUATRE. Un premier découpage en avait produit quatre, et le
cycle a rendu ROUGE : deux d'entre eux PASSAIENT sur l'état initial.

Le contexte par défaut reste sélectionné parce que l'apprenant n'a rien changé :
c'est une **interdiction** du scénario, pas un objectif. Elle est devenue un
garde-fou commun, et sa place y est justifiée : la franchir change la cible de
toutes les commandes suivantes, donc elle conditionne l'observation elle-même.

La clé non autorisée est refusée dès le départ par le service SSH distant : rien
à faire pour l'obtenir. Elle est devenue la **contre-épreuve** du second
contrôle. Sans elle, un service SSH qui accepterait n'importe quelle clé
satisferait la connexion sans rien prouver de l'identité employée.

C'est la cinquième fois que ce cas se présente dans ce catalogue, et la règle est
établie : ce qui est vrai avant tout travail ne peut pas être un contrôle, et
appartient à celui dont il conditionne le sens.

Restent donc :

1. le contexte nommé existe et **vise l'alias SSH** préparé, et non un socket ;
2. le contexte joint le **vrai moteur de la seconde VM**, et seule la bonne clé
   y accède.

Le second est le cœur du lab, et sa preuve est la seule qui résiste à un alias
trompeur : comparer l'identité rendue par le contexte à celle de la VM distante
ET à celle de la machine locale. Un `ssh://` qui boucle sur la source rendrait
l'identité locale, et un contexte mal nommé ne rendrait rien.
"""

from __future__ import annotations

import json
import shlex

import pytest

from conftest import lab_host, message

LAB = "docker-contexte-ssh"
TRAVAIL = f"/opt/dsoxlab-{LAB}"
CONTEXTE = "dsoxlab-maintenance"
ALIAS = "ssh://dsoxlab-ssh-target"
DISTANTE = "docker-client.lab"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _etat(host) -> dict:
    """L'état posé par le setup : le compte de l'apprenant, son défaut, l'IP.

    Garde-fou de mesure : sans ce fichier, aucun contrôle ne sait sous quel
    compte se placer ni quel contexte par défaut préserver.
    """
    fichier = host.file(f"{TRAVAIL}/state.json")
    assert fichier.exists, message(
        en=f"The prepared state {TRAVAIL}/state.json is missing. Not your fault: "
           "the checks cannot measure anything, report it.",
        fr=f"L'état préparé {TRAVAIL}/state.json est absent. Ce n'est pas votre "
           "faute : les contrôles ne peuvent rien mesurer, signalez-le.",
    )
    return json.loads(fichier.content_string)


def _en_apprenant(host, etat: dict, *args):
    """Joue une commande sous le compte de l'apprenant.

    Et non sous le compte d'automatisation : c'est le contexte Docker de
    l'apprenant qui est en jeu, pas le nôtre.
    """
    return host.run(shlex.join(["sudo", "-n", "-u", etat["learner"], "--", *args]))


def _defaut_preserve(host, etat: dict) -> None:
    """L'interdiction du scénario : « ne changez pas le contexte par défaut ».

    Garde-fou et non exigence, puisqu'elle est déjà vraie au départ. Mais la
    franchir change la cible de toutes les commandes suivantes de l'apprenant,
    donc elle conditionne ce que les contrôles observent.
    """
    selectionne = _en_apprenant(host, etat, "docker", "context", "show")
    assert selectionne.rc == 0, message(
        en=f"Cannot read the selected context: {selectionne.stderr.strip()[:200]}",
        fr=f"Le contexte sélectionné est illisible : {selectionne.stderr.strip()[:200]}",
    )
    assert selectionne.stdout.strip() == etat["default_context"], message(
        en=f"The selected context is {selectionne.stdout.strip()!r} instead of "
           f"{etat['default_context']!r}. Creating a named context does not mean "
           "switching to it: every later command would then target the other "
           "engine.",
        fr=f"Le contexte sélectionné est {selectionne.stdout.strip()!r} au lieu "
           f"de {etat['default_context']!r}. Créer un contexte nommé ne veut pas "
           "dire basculer dessus : toutes les commandes suivantes viseraient "
           "alors l'autre moteur.",
    )


def _contexte(host, etat: dict) -> dict:
    """L'inspection du contexte nommé, ou un échec qui dit quoi faire."""
    inspecte = _en_apprenant(host, etat, "docker", "context", "inspect", CONTEXTE)
    assert inspecte.rc == 0, message(
        en=f"The named context {CONTEXTE} does not exist: "
           f"{inspecte.stderr.strip()[:200]} Create it; the default context must "
           "stay as it is.",
        fr=f"Le contexte nommé {CONTEXTE} n'existe pas : "
           f"{inspecte.stderr.strip()[:200]} Créez-le ; le contexte par défaut "
           "doit rester tel quel.",
    )
    return json.loads(inspecte.stdout)[0]


def test_le_contexte_nomme_vise_l_alias_ssh_prepare(host):
    """Ce qui a été déclaré au client Docker."""
    etat = _etat(host)
    _defaut_preserve(host, etat)
    contexte = _contexte(host, etat)
    point = contexte["Endpoints"]["docker"]["Host"]

    assert point == ALIAS, message(
        en=f"The context points at {point!r} instead of {ALIAS!r}. A local socket "
           "would make the context a second name for this same engine, and an "
           "unauthenticated TCP endpoint is not what the exercise asks for.",
        fr=f"Le contexte pointe sur {point!r} au lieu de {ALIAS!r}. Un socket "
           "local ferait du contexte un second nom de ce même moteur, et une API "
           "TCP non authentifiée n'est pas ce que l'exercice demande.",
    )


def test_le_contexte_joint_le_vrai_moteur_et_seule_la_bonne_cle_y_accede(host):
    """Le cœur du lab, et la seule preuve qui résiste à un alias trompeur.

    Trois identités de démon sont comparées : celle que rend le contexte, celle
    de la VM distante, et celle de la machine locale. Le contexte doit rendre la
    distante, et elle doit différer de la locale. Sans la seconde comparaison,
    un `ssh://` qui bouclerait sur la source passerait, en rendant l'identité du
    moteur local.
    """
    etat = _etat(host)
    _defaut_preserve(host, etat)
    _contexte(host, etat)

    par_le_contexte = _en_apprenant(
        host, etat, "docker", "--context", CONTEXTE, "info", "--format", "{{.ID}}"
    )
    assert par_le_contexte.rc == 0 and par_le_contexte.stdout.strip(), message(
        en=f"The context cannot reach its Docker daemon: "
           f"{par_le_contexte.stderr.strip()[-400:]} The dedicated SSH identity "
           "is prepared; the alias must resolve and the remote user must be "
           "allowed to talk to the engine.",
        fr=f"Le contexte ne joint pas son démon Docker : "
           f"{par_le_contexte.stderr.strip()[-400:]} L'identité SSH dédiée est "
           "prête ; l'alias doit résoudre et l'utilisateur distant doit avoir le "
           "droit de parler au moteur.",
    )

    distante = lab_host(DISTANTE).run("docker info --format '{{.ID}}'")
    locale = host.run("docker info --format '{{.ID}}'")
    assert distante.rc == 0 and locale.rc == 0, message(
        en="One of the two engines did not answer its identity. Not your fault: "
           "the comparison cannot be made, report it.",
        fr="L'un des deux moteurs n'a pas rendu son identité. Ce n'est pas votre "
           "faute : la comparaison ne peut pas être faite, signalez-le.",
    )
    assert distante.stdout.strip() != locale.stdout.strip(), message(
        en="Both VMs report the same engine identity, so this comparison proves "
           "nothing. Not your fault: report it.",
        fr="Les deux VM rendent la même identité de moteur, donc cette "
           "comparaison ne prouve rien. Ce n'est pas votre faute : signalez-le.",
    )
    assert par_le_contexte.stdout.strip() == distante.stdout.strip(), message(
        en=f"The context reaches an engine whose identity is "
           f"{par_le_contexte.stdout.strip()!r}, while the second VM reports "
           f"{distante.stdout.strip()!r}. The context must contact the real "
           "remote engine, not a loopback alias back to this machine.",
        fr=f"Le contexte joint un moteur dont l'identité est "
           f"{par_le_contexte.stdout.strip()!r}, alors que la seconde VM annonce "
           f"{distante.stdout.strip()!r}. Le contexte doit joindre le vrai moteur "
           "distant, et non un alias qui boucle sur cette machine.",
    )

    # LA CONTRE-ÉPREUVE, et non un contrôle à part : elle passe sur l'état
    # initial, puisque le service distant refuse déjà cette clé. Mais sans elle,
    # un service SSH qui accepterait n'importe quelle clé satisferait la
    # connexion ci-dessus sans rien prouver de l'identité employée.
    #
    # Les deux moitiés comptent. Un service injoignable refuserait aussi la clé :
    # on exige donc à la fois le code 255 d'un refus SSH et un « Permission
    # denied ». Sans cette distinction, couper le réseau suffirait.
    #
    # La clé est posée par le setup, lisible par l'apprenant, et indépendante de
    # celle du contexte : l'essai ne touche à rien.
    commande = shlex.join([
        "ssh", "-F", "/dev/null", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=5", "-i", f"{TRAVAIL}/unauthorized",
        f"dsoxlab-context@{etat['remote_ip']}", "docker", "info", "--format", "{{.ID}}",
    ])
    # TESTINFRA PREND UN 255 SORTANT POUR UNE PANNE DE TRANSPORT, puisque c'est
    # son propre code d'erreur ssh. On encapsule donc l'essai : le shell rend 0
    # quand le ssh interne a bien rendu 255, et le code réel est imprimé pour
    # qu'on le lise plutôt que de le déduire.
    essai = _en_apprenant(
        host, etat, "sh", "-c",
        commande + '; status=$?; printf "ssh_exit=%s\n" "$status"; test "$status" -eq 255',
    )

    assert essai.stdout.strip() == "ssh_exit=255", message(
        en=f"The unauthorized key did not get an SSH refusal: "
           f"{essai.stdout.strip() or '(no exit code reported)'} "
           f"{essai.stderr.strip()[-300:]} A 255 is what SSH returns when it "
           "refuses an identity. Another code means the command ran, so the key "
           "was accepted.",
        fr=f"La clé non autorisée n'a pas reçu de refus SSH : "
           f"{essai.stdout.strip() or '(aucun code de sortie rapporté)'} "
           f"{essai.stderr.strip()[-300:]} Un 255 est ce que SSH rend lorsqu'il "
           "refuse une identité. Un autre code signifie que la commande a "
           "tourné, donc que la clé a été acceptée.",
    )
    assert "Permission denied" in essai.stderr, message(
        en=f"The SSH attempt failed, but not on an authentication refusal: "
           f"{essai.stderr.strip()[-300:]} An unreachable service fails the same "
           "way while proving nothing about authorisation. The remote service "
           "must answer, and say no.",
        fr=f"La tentative SSH a échoué, mais pas sur un refus d'authentification : "
           f"{essai.stderr.strip()[-300:]} Un service injoignable échoue de la "
           "même façon sans rien prouver de l'autorisation. Le service distant "
           "doit répondre, et refuser.",
    )
