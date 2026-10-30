"""Tests fonctionnels du lab troubleshoot-boucle-de-redemarrage : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'une politique de redémarrage ne répare rien. Elle
décide seulement de ce qui se passe après l'échec, et les trois conteneurs du
lab partagent le MÊME défaut pour trois issues différentes.

MESURÉ SUR docker.lab LE 2026-10-30 :

| Politique | État | RestartCount | Ce qui se passe |
| `on-failure:N` | `exited` | figé à **N** | le moteur a renoncé |
| `always` | `restarting` | **grimpe** (10 en 60 s) | il relance sans fin |
| `always`, cause levée | `running` | figé | il repart SEUL, en ~60 s |

LES DEUX LEÇONS SONT LÀ. La première : un conteneur qui boucle n'est pas un
conteneur mal configuré, c'est un conteneur qui échoue, et la politique ne fait
que rendre l'échec bruyant. La seconde : lever la cause suffit, le moteur
rattrape de lui-même, parce qu'il attend entre deux tentatives et que ce délai
croît.

LE PLAFOND EST LE TÉMOIN, et c'est ce qui rend ses valeurs lisibles : le moteur
a renoncé, donc son compteur ne bouge plus et son code reste celui de la
dernière tentative. Un conteneur relancé n'a plus ni l'un ni l'autre, d'où
l'interdiction de le réparer et le contrôle qui la vérifie.

LE QUATRIÈME CONTRÔLE REFUSE LE GESTE SPONTANÉ. Retirer la politique fait
cesser la boucle sans rien régler : le conteneur cesse d'être relancé, et le
défaut est intact. Le contrôle exige donc la politique INCHANGÉE, et le
conteneur sain INTACT, parce que repartir d'une table rase emporterait un
service qui tournait.

AUCUNE VALEUR N'EST ÉCRITE EN DUR DANS CE FICHIER. Le plafond, le code et la
politique sont tirés au hasard à chaque passage, et les trois sont recalculés
en interrogeant le moteur au moment de la notation.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
l'atelier appartient à root, et le lire sans élévation rendrait des réponses
vides.
"""

from __future__ import annotations

import time

import pytest

from conftest import lab_host, message

# LE TÉMOIN, dont le moteur a cessé de s'occuper : il porte DEUX des trois
# réponses, et l'énoncé interdit de le réparer.
PLAFOND = "appli-plafond"
SANS_FIN = "appli-sans-fin"
SAINE = "appli-saine"
ATELIER = "/opt/lab-boucle"
REPONSES = f"{ATELIER}/reponses.txt"
JETON = f"{ATELIER}/conf/jeton"
EMPREINTE = f"{ATELIER}/.empreinte-saine"
# Ce chemin est DANS LE CONTENEUR, où il disparaît avec lui : ce n'est pas un
# fichier temporaire de l'hôte, d'où le noqa.
TRACE = "/tmp/trace"  # noqa: S108

# Le délai d'attente du moteur entre deux tentatives CROÎT, et il atteint la
# minute en une dizaine de relances : mesuré à 60 s le 2026-10-30. Le contrôle
# de réparation l'accorde, mais seulement quand la cause est levée, pour ne pas
# faire attendre deux minutes un `check` joué sans rien avoir corrigé.
ATTENTE_MAX_S = 150
PAS_S = 5

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


def _champ(host, nom: str, format_go: str) -> str:
    """Un champ de l'inspection d'un conteneur, ou une chaîne vide."""
    res = host.run("docker container inspect %s --format %s", nom, format_go)
    return res.stdout.strip() if res.rc == 0 else ""


def _lire_reponses(host) -> dict[str, str]:
    """Le formulaire, réduit à ses paires clé=valeur.

    Tolérant sur la forme (espaces, lignes vides, commentaires, casse de la
    clé), strict sur le fond : c'est le contenu qui est noté, pas la mise en
    page.
    """
    f = host.file(REPONSES)
    if not f.exists:
        pytest.fail(message(
            en=f"{REPONSES} is missing. The mission asks for three lines in "
               "it: tentatives=, code= and politique=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire trois "
               "lignes : tentatives=, code= et politique=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def test_la_reponse_donne_le_nombre_de_relances(host) -> None:
    """Combien de fois le moteur a relancé le conteneur plafonné.

    LA VALEUR EST TIRÉE AU HASARD à chaque passage, et elle est recalculée ici
    en interrogeant le moteur : rien dans le dépôt ne la porte.

    Elle est stable parce que le moteur a RENONCÉ. C'est ce qui distingue ce
    conteneur de l'autre, dont le compteur grimpe encore, et c'est pourquoi la
    question se pose sur lui.
    """
    attendu = _champ(host, PLAFOND, "{{.RestartCount}}")
    if not attendu:
        pytest.skip(message(
            en=f"container `{PLAFOND}` does not exist: the setup did not "
               "finish",
            fr=f"le conteneur `{PLAFOND}` n'existe pas : le setup n'a pas "
               "abouti",
        ))

    # LE TÉMOIN DOIT ÊTRE RESTÉ EN PANNE, sans quoi la question n'a plus
    # d'objet : un conteneur relancé repart de zéro, et son compteur ne dit
    # plus combien de fois le moteur a essayé avant de renoncer.
    etat = _champ(host, PLAFOND, "{{.State.Status}}")
    assert etat == "exited", message(
        en=f"`{PLAFOND}` is in state `{etat or 'absent'}`, not `exited`: it is "
           "the witness, and the brief asks for it not to be repaired. Its "
           "restart count is what the question is about, and a relaunched "
           "container counts from zero again.",
        fr=f"`{PLAFOND}` est dans l'état `{etat or 'absent'}`, pas `exited` : "
           "c'est le témoin, et l'énoncé demande de ne pas le réparer. Son "
           "compteur de relances est l'objet de la question, et un conteneur "
           "relancé repart de zéro.",
    )

    reponses = _lire_reponses(host)
    donnee = reponses.get("tentatives", "")
    assert donnee, message(
        en=f"the `tentatives=` line is empty. The engine relaunched "
           f"`{PLAFOND}` a fixed number of times, then gave up: that ceiling "
           "is declared in its restart policy, and the count of the attempts "
           "actually made is in its inspection.",
        fr=f"la ligne `tentatives=` est vide. Le moteur a relancé `{PLAFOND}` "
           "un nombre fixé de fois, puis il a renoncé : ce plafond est déclaré "
           "dans sa politique de redémarrage, et le compte des tentatives "
           "réellement faites est dans son inspection.",
    )
    assert donnee == attendu, message(
        en=f"the announced number of restarts is not `{PLAFOND}`'s.\n"
           f"  announced: {donnee}\n"
           "A container under a ceiling policy is relaunched exactly as many "
           "times as the ceiling allows, then the engine gives up. The count "
           "is in the inspection, and so is the ceiling.",
        fr=f"le nombre de relances annoncé n'est pas celui de `{PLAFOND}`.\n"
           f"  annoncé : {donnee}\n"
           "Un conteneur sous politique plafonnée est relancé exactement "
           "autant de fois que le plafond l'autorise, puis le moteur renonce. "
           "Le compte est dans l'inspection, et le plafond aussi.",
    )


def test_la_reponse_donne_le_code_de_sortie(host) -> None:
    """Le code de sortie de la dernière tentative.

    IL EST TIRÉ AU HASARD, hors des codes qui ont déjà un sens dans ce
    catalogue : ni 0, ni 1, ni 2, ni la plage 125-127, pour qu'il ne soit pas
    devinable par élimination.

    C'est le code DU SCRIPT, et il ne se lit pas dans les traces : les traces
    disent ce qui manque, l'inspection dit avec quel code le processus est
    sorti. Les deux sources sont complémentaires, et c'est la méthode du lab.
    """
    attendu = _champ(host, PLAFOND, "{{.State.ExitCode}}")
    if not attendu:
        pytest.skip(message(
            en=f"container `{PLAFOND}` does not exist: the setup did not "
               "finish",
            fr=f"le conteneur `{PLAFOND}` n'existe pas : le setup n'a pas "
               "abouti",
        ))

    reponses = _lire_reponses(host)
    donnee = reponses.get("code", "")
    assert donnee, message(
        en=f"the `code=` line is empty. `{PLAFOND}` is stopped, and the code "
           "its script exited with is kept in its inspection, under its "
           "state.",
        fr=f"la ligne `code=` est vide. `{PLAFOND}` est arrêté, et le code "
           "avec lequel son script est sorti est conservé dans son "
           "inspection, sous son état.",
    )
    assert donnee == attendu, message(
        en=f"the announced code is not `{PLAFOND}`'s.\n"
           f"  announced: {donnee}\n"
           "It is the code of the LAST attempt, and it is the script's own: "
           "the traces say what is missing, the inspection says with which "
           "code the process left.",
        fr=f"le code annoncé n'est pas celui de `{PLAFOND}`.\n"
           f"  annoncé : {donnee}\n"
           "C'est le code de la DERNIÈRE tentative, et c'est celui du script "
           "lui-même : les traces disent ce qui manque, l'inspection dit avec "
           "quel code le processus est sorti.",
    )


def test_la_reponse_donne_la_politique_du_conteneur_qui_boucle(host) -> None:
    """La politique du conteneur que le moteur relance sans fin.

    DEUX POLITIQUES DONNENT LA MÊME BOUCLE, et le setup en tire une au hasard.
    C'est délibéré : la question ne se devine pas, elle se lit. Les deux ne se
    distinguent que sur un point, qui n'a rien à voir avec la boucle, et c'est
    le sort d'un conteneur arrêté à la main au redémarrage du moteur.

    LA QUESTION PORTE SUR LE CONTENEUR QU'ON RÉPARE, et c'est voulu : la lire
    AVANT de réparer est la seule façon d'avoir la réponse, puisque réparer en
    retirant la politique la fait disparaître. Le quatrième contrôle vérifie
    d'ailleurs qu'elle est restée en place.
    """
    attendu = _champ(host, SANS_FIN, "{{.HostConfig.RestartPolicy.Name}}")
    if not attendu:
        pytest.skip(message(
            en=f"container `{SANS_FIN}` does not exist: the setup did not "
               "finish",
            fr=f"le conteneur `{SANS_FIN}` n'existe pas : le setup n'a pas "
               "abouti",
        ))

    reponses = _lire_reponses(host)
    donnee = reponses.get("politique", "")
    assert donnee, message(
        en=f"the `politique=` line is empty. `{SANS_FIN}` is relaunched "
           "without end, and the policy deciding that is declared in its "
           "inspection, under its host configuration.",
        fr=f"la ligne `politique=` est vide. `{SANS_FIN}` est relancé sans "
           "fin, et la politique qui en décide est déclarée dans son "
           "inspection, sous sa configuration d'hôte.",
    )
    assert donnee == attendu, message(
        en=f"the announced policy is not `{SANS_FIN}`'s.\n"
           f"  announced: {donnee}\n"
           "Write it as the engine declares it, which is the value of the "
           "policy's name in the inspection. Two different policies produce "
           "the same endless loop, so it has to be read, not guessed.",
        fr=f"la politique annoncée n'est pas celle de `{SANS_FIN}`.\n"
           f"  annoncée : {donnee}\n"
           "Écrivez-la telle que le moteur la déclare, c'est-à-dire la valeur "
           "du nom de la politique dans l'inspection. Deux politiques "
           "différentes produisent la même boucle sans fin : elle se lit, elle "
           "ne se devine pas.",
    )


def test_la_boucle_est_reparee_sans_rien_couper(host) -> None:
    """La réparation, et ses trois moitiés.

    LE CONTRÔLE REFUSE LE GESTE SPONTANÉ. Retirer la politique fait cesser la
    boucle sans rien régler : le conteneur cesse d'être relancé, et le défaut
    est intact. C'est la faute que ce lab existe pour empêcher.

    IL ACCORDE LE TEMPS DU MOTEUR, mais seulement quand la cause est levée. Le
    délai entre deux tentatives croît et atteint la minute : un conteneur dont
    la cause vient d'être levée est encore en attente de son tour, et le punir
    pour cela enseignerait de recréer au lieu de corriger.

    ET IL VÉRIFIE LE CONTENEUR SAIN PAR SON IDENTIFIANT, pas par son nom : un
    homonyme recréé après une table rase porterait le même nom, et c'est
    exactement le geste qui emporte un service qui tournait.
    """
    politique = _champ(host, SANS_FIN, "{{.HostConfig.RestartPolicy.Name}}")
    assert politique in ("always", "unless-stopped"), message(
        en=f"`{SANS_FIN}`'s restart policy is `{politique or 'absent'}`.\n"
           "Removing it makes the loop stop without fixing anything: the "
           "container stops being relaunched, and the failure is untouched. "
           "The policy is not at fault, the cause is.",
        fr=f"la politique de redémarrage de `{SANS_FIN}` est "
           f"`{politique or 'absente'}`.\n"
           "La retirer fait cesser la boucle sans rien régler : le conteneur "
           "cesse d'être relancé, et le défaut est intact. Ce n'est pas la "
           "politique qui est en faute, c'est la cause.",
    )

    cause_levee = host.file(JETON).exists
    assert cause_levee, message(
        en=f"{JETON} is still missing, and that is the cause.\n"
           "The container's traces name it, as many times as there were "
           "attempts. As long as it is missing, every restart fails the same "
           "way.",
        fr=f"{JETON} est toujours absent, et c'est la cause.\n"
           "Les traces du conteneur la nomment, autant de fois qu'il y a eu "
           "de tentatives. Tant qu'il manque, chaque relance échoue de la "
           "même façon.",
    )

    # LE MOTEUR A SON PROPRE RYTHME, et la cause est levée : on lui laisse le
    # temps de sa prochaine tentative plutôt que de conclure à l'échec.
    limite = time.monotonic() + ATTENTE_MAX_S
    etat = _champ(host, SANS_FIN, "{{.State.Status}}")
    while etat != "running" and time.monotonic() < limite:
        time.sleep(PAS_S)
        etat = _champ(host, SANS_FIN, "{{.State.Status}}")
    assert etat == "running", message(
        en=f"`{SANS_FIN}` is in state `{etat or 'absent'}` after "
           f"{ATTENTE_MAX_S} s of waiting, not `running`.\n"
           "The cause is lifted, so the engine should have caught up on its "
           "own: the delay between two attempts grows, and it reaches the "
           "minute. Relaunching the container does not wait for it.",
        fr=f"`{SANS_FIN}` est dans l'état `{etat or 'absent'}` après "
           f"{ATTENTE_MAX_S} s d'attente, pas `running`.\n"
           "La cause est levée, le moteur devrait donc avoir rattrapé tout "
           "seul : le délai entre deux tentatives croît, et il atteint la "
           "minute. Relancer le conteneur ne l'attend pas.",
    )

    trace = host.run("docker exec %s cat %s", SANS_FIN, TRACE)
    assert "demarre" in trace.stdout, message(
        en=f"`{SANS_FIN}` runs, but {TRACE} does not carry its script's "
           "trace.\n"
           "So it runs something else: the point is that ITS script got past "
           "the check that was failing, not that the container is alive.",
        fr=f"`{SANS_FIN}` tourne, mais {TRACE} ne porte pas la trace de son "
           "script.\n"
           "Il tourne donc autre chose : le but est que SON script ait passé "
           "le contrôle qui échouait, pas que le conteneur soit vivant.",
    )

    attendue = host.file(EMPREINTE)
    if attendue.exists:
        empreinte = attendue.content_string.strip()
        actuelle = _champ(host, SAINE, "{{.Id}}")
        assert actuelle == empreinte, message(
            en=f"`{SAINE}` is not the container the lab started with.\n"
               "It was working, and nothing said it was useless. Starting "
               "from a clean slate carries away a running service, and that is "
               "the most destructive answer to a loop that concerned another "
               "container.",
            fr=f"`{SAINE}` n'est pas le conteneur du départ.\n"
               "Il marchait, et rien ne disait qu'il était inutile. Repartir "
               "d'une table rase emporte un service qui tournait, et c'est la "
               "réponse la plus destructrice à une boucle qui concernait un "
               "autre conteneur.",
        )
    etat_saine = _champ(host, SAINE, "{{.State.Status}}")
    assert etat_saine == "running", message(
        en=f"`{SAINE}` is in state `{etat_saine or 'absent'}`, not `running`.\n"
           "It was working. A loop that concerns another container is no "
           "reason to stop it.",
        fr=f"`{SAINE}` est dans l'état `{etat_saine or 'absent'}`, pas "
           "`running`.\n"
           "Il marchait. Une boucle qui concerne un autre conteneur n'est pas "
           "une raison de l'arrêter.",
    )
