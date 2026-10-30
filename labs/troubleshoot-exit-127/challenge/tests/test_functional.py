"""Tests fonctionnels du lab troubleshoot-exit-127 : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un code de sortie est un diagnostic, et que deux codes
voisins disent deux choses opposées. Un lab de dépannage ne s'enseigne pas avec
un symptôme : il s'enseigne avec une GRILLE, et une grille demande des cas
voisins qu'on puisse comparer.

MESURÉ SUR docker.lab LE 2026-10-30 :

| Cause | Code | Journal | Statut |
| commande introuvable | 127 | **vide** | **`created`** |
| fichier non exécutable | 126 | vide | `exited` |
| commande qui échoue | son propre code | ce qu'elle a écrit | `exited` |

LA DISTINCTION QUI VAUT LE LAB ENTIER est dans la première ligne. Quand la
commande est introuvable, le conteneur n'a JAMAIS DÉMARRÉ : son statut reste
`created`, son journal est vide, et le diagnostic est dans `.State.Error` de
l'inspection, que personne ne regarde :

    unable to start container process: exec: "…": executable file not found in
    $PATH

En revanche, si un shell enveloppe la commande, le journal PARLE, parce que le
shell a démarré, lui. Mesuré : `sh: /tmp/inexistant: not found`. **Le même code
127, deux situations opposées, et le journal est ce qui les sépare.**

AUCUN CODE N'EST ÉCRIT EN DUR DANS CE FICHIER. Les trois attendus sont lus sur
les conteneurs au moment de la notation. Un test qui aurait porté `127` serait
faux le jour où le setup changerait de panne, et le lab mourrait d'une
modification sans rapport.

LE QUATRIÈME CONTRÔLE DEMANDE UNE RÉPARATION, et il la mesure sur l'image : le
conteneur réparé doit dériver de la MÊME image que les pannes. C'est ce qui
démontre que l'image n'était pas en cause, et c'est la conclusion que le lab
veut faire tirer.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
les contrôles n'interrogent que le moteur, et l'élévation leur évite de dépendre
des groupes du compte.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

PANNE_INTROUVABLE = "panne-a"
PANNE_NON_EXECUTABLE = "panne-b"
PANNE_QUI_ECHOUE = "panne-c"
REPARE = "repare"
TAG = "lab-exit:1.0"
ATELIER = "/opt/lab-exit"
REPONSES = f"{ATELIER}/reponses.txt"

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
               "it: code_a=, code_b= and statut_a=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire trois "
               "lignes : code_a=, code_b= et statut_a=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def test_la_reponse_donne_le_code_de_la_commande_introuvable(host) -> None:
    """Le code le plus mal lu de tous, et celui qu'on attribue au conteneur.

    Il ne dit rien du conteneur ni de l'image : il dit qu'une commande n'a pas
    été trouvée. La nuance change tout le diagnostic, parce qu'elle oriente vers
    le nom qu'on a écrit et non vers ce qu'on a construit.
    """
    attendu = _champ(host, PANNE_INTROUVABLE, "{{.State.ExitCode}}")
    if not attendu:
        pytest.skip(message(
            en=f"container `{PANNE_INTROUVABLE}` does not exist: the setup did "
               "not finish",
            fr=f"le conteneur `{PANNE_INTROUVABLE}` n'existe pas : le setup "
               "n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("code_a", "")
    assert annonce, message(
        en="the `code_a=` line is empty. A stopped container keeps the code its "
           "main process returned, and the engine states it.",
        fr="la ligne `code_a=` est vide. Un conteneur arrêté garde le code que "
           "son processus principal a rendu, et le moteur l'indique.",
    )
    assert annonce == attendu, message(
        en=f"the announced code is not `{PANNE_INTROUVABLE}`'s.\n"
           f"  you wrote : {annonce}\n"
           "It is read in the container's inspection, not guessed from the "
           "symptom.",
        fr=f"le code annoncé n'est pas celui de `{PANNE_INTROUVABLE}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "Il se lit dans l'inspection du conteneur, et ne se devine pas à "
           "partir du symptôme.",
    )


def test_la_reponse_donne_le_code_du_fichier_non_executable(host) -> None:
    """Le voisin du précédent, et il dit autre chose.

    Un fichier trouvé mais non exécutable produit un code DIFFÉRENT. Les deux
    sont voisins, et c'est cette proximité qui les fait confondre : l'un
    renvoie au nom de la commande, l'autre à ses permissions ou à son format.

    Le contrôle vérifie aussi que les deux codes diffèrent, parce qu'une grille
    dont deux cases portent la même valeur n'est pas une grille.
    """
    attendu = _champ(host, PANNE_NON_EXECUTABLE, "{{.State.ExitCode}}")
    autre = _champ(host, PANNE_INTROUVABLE, "{{.State.ExitCode}}")
    if not attendu:
        pytest.skip(message(
            en=f"container `{PANNE_NON_EXECUTABLE}` does not exist: the setup "
               "did not finish",
            fr=f"le conteneur `{PANNE_NON_EXECUTABLE}` n'existe pas : le setup "
               "n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("code_b", "")
    assert annonce, message(
        en="the `code_b=` line is empty. This container's command was found, "
           "and it still could not be run.",
        fr="la ligne `code_b=` est vide. La commande de ce conteneur a été "
           "trouvée, et elle n'a pourtant pas pu être exécutée.",
    )
    assert annonce == attendu, message(
        en=f"the announced code is not `{PANNE_NON_EXECUTABLE}`'s.\n"
           f"  you wrote : {annonce}\n"
           f"It is a neighbour of `{PANNE_INTROUVABLE}`'s ({autre}), and that "
           "closeness is what makes them confused: one points at the command's "
           "name, the other at its permissions or its format.",
        fr=f"le code annoncé n'est pas celui de `{PANNE_NON_EXECUTABLE}`.\n"
           f"  vous avez écrit : {annonce}\n"
           f"C'est un voisin de celui de `{PANNE_INTROUVABLE}` ({autre}), et "
           "cette proximité est ce qui les fait confondre : l'un renvoie au nom "
           "de la commande, l'autre à ses permissions ou à son format.",
    )


def test_la_reponse_donne_le_statut_du_conteneur_jamais_demarre(host) -> None:
    """La question la plus utile du lab, et la moins attendue.

    Le statut de ce conteneur n'est pas celui d'un conteneur qui s'est arrêté.
    Il n'a jamais démarré : le moteur n'a pas pu lancer son processus, donc
    rien n'a tourné, donc rien n'a pu écrire dans le journal.

    C'est ce qui explique qu'un journal vide accompagne ce code, et que le
    diagnostic soit ailleurs : dans le champ d'erreur de l'inspection. Un
    dépanneur qui connaît cette ligne gagne un quart d'heure à chaque fois.
    """
    attendu = _champ(host, PANNE_INTROUVABLE, "{{.State.Status}}")
    if not attendu:
        pytest.skip(message(
            en=f"container `{PANNE_INTROUVABLE}` does not exist: the setup did "
               "not finish",
            fr=f"le conteneur `{PANNE_INTROUVABLE}` n'existe pas : le setup "
               "n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("statut_a", "").lower()
    assert annonce, message(
        en="the `statut_a=` line is empty. Read the container's status, and "
           "compare it with what you would expect from a container that "
           "stopped.",
        fr="la ligne `statut_a=` est vide. Lisez le statut du conteneur, et "
           "comparez-le à ce que vous attendriez d'un conteneur qui s'est "
           "arrêté.",
    )
    assert annonce == attendu.lower(), message(
        en=f"the announced status is not `{PANNE_INTROUVABLE}`'s.\n"
           f"  you wrote : {annonce}\n"
           "It is not the status of a container that stopped: this one never "
           "started. The engine could not launch its process, so nothing ran, "
           "so nothing could write to the log. That is why its log is empty, "
           "and why the diagnosis is in the inspection's error field instead.",
        fr=f"le statut annoncé n'est pas celui de `{PANNE_INTROUVABLE}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "Ce n'est pas le statut d'un conteneur qui s'est arrêté : celui-ci "
           "n'a jamais démarré. Le moteur n'a pas pu lancer son processus, donc "
           "rien n'a tourné, donc rien n'a pu écrire dans le journal. C'est "
           "pourquoi son journal est vide, et pourquoi le diagnostic est dans "
           "le champ d'erreur de l'inspection.",
    )


def test_le_conteneur_repare_tourne_sur_la_meme_image(host) -> None:
    """La réparation, et la conclusion qu'elle fait tirer.

    Le conteneur réparé doit dériver de la MÊME image que les pannes. C'est ce
    qui démontre que l'image n'était pas en cause : les trois pannes venaient de
    ce qu'on lui demandait de lancer, pas de ce qu'elle contenait.

    C'est la conclusion la plus rentable d'un dépannage : savoir ce qui N'EST
    PAS responsable écarte la moitié des pistes.
    """
    etat = _champ(host, REPARE, "{{.State.Status}}")
    assert etat, message(
        en=f"no container named `{REPARE}` exists. Start one, on the SAME "
           "image, that runs: you will have understood that the image was not "
           "at fault.",
        fr=f"aucun conteneur nommé `{REPARE}` n'existe. Lancez-en un, sur la "
           "MÊME image, qui tourne : vous aurez compris que la panne n'était "
           "pas dans l'image.",
    )
    assert etat == "running", message(
        en=f"`{REPARE}` is in state `{etat}`, not `running`.\n"
           "A container that stopped right away proves nothing: the point is to "
           "show that this image can carry a working container.",
        fr=f"`{REPARE}` est dans l'état `{etat}`, pas `running`.\n"
           "Un conteneur qui s'est arrêté aussitôt ne prouve rien : le but est "
           "de montrer que cette image peut porter un conteneur qui marche.",
    )

    image_reparee = _champ(host, REPARE, "{{.Config.Image}}")
    image_en_panne = _champ(host, PANNE_INTROUVABLE, "{{.Config.Image}}")
    assert image_reparee == image_en_panne, message(
        en=f"`{REPARE}` runs on `{image_reparee}`, while the broken containers "
           f"were on `{image_en_panne}`.\n"
           "Repairing by changing image would prove the opposite of the lesson: "
           "the point is that the image was never at fault. Knowing what is NOT "
           "responsible rules out half the leads.",
        fr=f"`{REPARE}` tourne sur `{image_reparee}`, alors que les conteneurs "
           f"en panne étaient sur `{image_en_panne}`.\n"
           "Réparer en changeant d'image prouverait l'inverse de la leçon : "
           "tout l'intérêt est que l'image n'était pas en cause. Savoir ce qui "
           "n'est PAS responsable écarte la moitié des pistes.",
    )
