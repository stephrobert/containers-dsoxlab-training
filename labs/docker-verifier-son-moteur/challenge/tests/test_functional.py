"""Tests fonctionnels du lab docker-verifier-son-moteur : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'« installé » et « utilisable » sont deux états
différents, et que le second se vérifie sur quatre plans indépendants. C'est le
premier geste du catalogue : avant de lancer un conteneur, savoir si le moteur
peut en lancer un.

POURQUOI QUATRE CONTRÔLES ET NON UN. `docker run` qui réussit prouverait les
quatre d'un coup, et c'est précisément ce qu'on ne veut pas noter : il
masquerait lequel manquait. Un service démarré à la main mais désactivé au
démarrage, par exemple, passe tous les essais du jour et disparaît au premier
redémarrage. Chaque contrôle nomme donc son plan, pour que l'échec dise quoi
faire.

CE QU'ON NE MESURE PAS, ET POURQUOI. Jamais la commande tapée. `systemctl
enable --now`, un `service` sur un système sans systemd, ou une réparation à la
main du lien de l'unité mènent au même état. De même pour l'accès au socket :
`usermod -aG`, `gpasswd -a` ou une édition de `/etc/group` sont le même geste.
Un lab qui noterait la commande noterait un style, pas une compétence.

LE PIÈGE DU TROISIÈME CONTRÔLE, ET IL EST RÉEL. Ajouter un compte au groupe
`docker` ne change rien à la session déjà ouverte : les groupes sont lus à la
connexion. L'apprenant qui s'ajoute puis essaie aussitôt reçoit encore
« permission denied » et croit avoir raté. Le test mesure donc l'APPARTENANCE
déclarée, pas ce que la session courante peut faire, et le message le dit.

CE QUI REND LES QUATRE PLANS INDÉPENDANTS. `lab_host()` ouvre la machine avec
`sudo=true` : toute commande d'ici est déjà élevée. Les contrôles 1 et 4
interrogent donc le moteur sans dépendre du groupe de l'apprenant, et seul le
contrôle 3 mesure cet accès. Sans cette séparation, un groupe oublié ferait
échouer trois contrôles sur quatre, et le premier message annoncerait un démon
muet alors qu'il répond : trois points perdus pour un geste, et un diagnostic
qui envoie au mauvais endroit.

ET POURQUOI LE COMPTE NE SE DEVINE PAS. Cette élévation a un effet qu'on ne
voit pas en lisant le code : `id -un` rend `root`, jamais le compte de
connexion. Mesuré en écrivant ce lab, et le test en est mort une fois : il
vérifiait les groupes de `root`, qui n'appartient évidemment pas à `docker`, et
refusait une machine correctement réparée. Le compte se lit donc dans
`SUDO_USER`, que l'élévation renseigne.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

IMAGE_DE_PREUVE = "lab-preuve:1.0"
GROUPE = "docker"

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui
    les lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier. `pytest --collect-only` l'affiche en clair avec un paramètre
    `[local]` quand l'erreur est commise.
    """
    return lab_host(TARGET_HOST)


def _compte_apprenant(host) -> str:
    """Le compte dont l'accès au moteur est mesuré, et il ne se devine pas.

    C'est celui par lequel l'inventaire se connecte, donc celui que l'apprenant
    utilise réellement. Le coder en dur ferait rendre un verdict faux sur une
    machine où dsoxlab se connecte autrement.

    `id -un` ne convient PAS : `lab_host()` ouvre la machine avec `sudo=true`,
    et rend donc `root`. L'ordre ci-dessous couvre les deux cas, celui-là et
    celui d'un backend qui n'élèverait pas.
    """
    direct = host.run("id -un").stdout.strip()
    if direct and direct != "root":
        return direct
    for commande in ("printenv SUDO_USER", "logname"):
        res = host.run(commande)
        if res.rc == 0 and res.stdout.strip():
            return res.stdout.strip()
    pytest.fail(message(
        en="cannot tell which account connects to this machine: `id -un` says "
           "root and neither SUDO_USER nor logname answers. The check cannot "
           "name the account whose access it should measure.",
        fr="impossible de savoir quel compte se connecte à cette machine : "
           "`id -un` dit root, et ni SUDO_USER ni logname ne répondent. Le "
           "contrôle ne peut pas nommer le compte dont il doit mesurer l'accès.",
    ))
    raise AssertionError  # pragma: no cover - pytest.fail ne rend jamais


def test_le_moteur_repond(host) -> None:
    """Premier plan : le service tourne maintenant.

    On interroge le moteur plutôt que l'unité systemd. Un `systemctl is-active`
    vert sur un démon qui refuse les connexions dirait « réparé » sans que rien
    ne le soit, et c'est l'inverse de ce que ce lab enseigne.
    """
    res = host.run("docker version --format '{{.Server.Version}}'")
    assert res.rc == 0, message(
        en="the engine does not answer: `docker version` fails on its server "
           f"side.\n  output: {res.stderr.strip() or res.stdout.strip()}\n"
           "Installed is not running. Look at the service, and at the socket "
           "that starts it.",
        fr="le moteur ne répond pas : `docker version` échoue sur sa partie "
           f"serveur.\n  sortie : {res.stderr.strip() or res.stdout.strip()}\n"
           "Installé ne veut pas dire démarré. Regardez le service, et le "
           "socket qui le lance.",
    )
    assert res.stdout.strip(), message(
        en="the engine answered without naming its server version, which means "
           "the client talked to no daemon.",
        fr="le moteur a répondu sans nommer la version de son serveur, donc le "
           "client n'a parlé à aucun démon.",
    )


def test_le_moteur_repartira_au_prochain_demarrage(host) -> None:
    """Deuxième plan : la persistance, et c'est celui qu'on oublie.

    Un moteur démarré à la main fonctionne jusqu'au redémarrage. C'est la
    panne qui se découvre en production un lundi matin, pas en atelier, et
    c'est pour cela que ce contrôle pèse autant que les trois autres.

    Le service OU le socket suffit : sur Debian, `docker.socket` active le
    service à la première connexion, et n'activer que lui est une réponse
    défendable. Exiger les deux imposerait un chemin, ce que le lab ne fait
    jamais.
    """
    service = host.run("systemctl is-enabled docker.service").stdout.strip()
    socket = host.run("systemctl is-enabled docker.socket").stdout.strip()
    assert "enabled" in (service, socket), message(
        en=f"nothing will bring the engine back after a reboot.\n"
           f"  docker.service : {service or 'unreadable'}\n"
           f"  docker.socket  : {socket or 'unreadable'}\n"
           "Starting a service and enabling it at boot are two distinct "
           "actions. Either one being enabled is enough here.",
        fr=f"rien ne relancera le moteur après un redémarrage.\n"
           f"  docker.service : {service or 'illisible'}\n"
           f"  docker.socket  : {socket or 'illisible'}\n"
           "Démarrer un service et l'activer au démarrage sont deux gestes "
           "distincts. L'un des deux activé suffit ici.",
    )


def test_le_compte_parle_au_moteur_sans_sudo(host) -> None:
    """Troisième plan : l'accès au socket, qui est une question de groupe.

    On mesure l'APPARTENANCE au groupe, pas ce que la session courante peut
    faire : les groupes sont lus à la connexion, et un compte ajouté à l'instant
    reste refusé jusqu'à la suivante. Mesurer la session punirait un apprenant
    qui a fait le bon geste.
    """
    compte = _compte_apprenant(host)
    res = host.run("id -nG %s", compte)
    assert res.rc == 0, message(
        en=f"cannot read the groups of {compte}: {res.stderr.strip()}",
        fr=f"impossible de lire les groupes de {compte} : {res.stderr.strip()}",
    )
    groupes = res.stdout.split()
    assert GROUPE in groupes, message(
        en=f"`{compte}` is not a member of `{GROUPE}`, so it can only reach the "
           f"engine through sudo.\n  its groups: {' '.join(groupes)}\n"
           "Membership is read at login: after adding it, a new session is "
           "needed for the current shell to benefit. The check looks at the "
           "membership, not at your shell.",
        fr=f"`{compte}` n'appartient pas au groupe `{GROUPE}` : il ne peut donc "
           f"joindre le moteur qu'en passant par sudo.\n"
           f"  ses groupes : {' '.join(groupes)}\n"
           "L'appartenance est lue à la connexion : après l'ajout, il faut une "
           "nouvelle session pour que le shell courant en profite. Le contrôle "
           "regarde l'appartenance, pas votre shell.",
    )
    assert "sudo" in groupes, message(
        en=f"`{compte}` has lost the `sudo` group. That is not what the mission "
           "asked for, and it leaves the account unable to administer the "
           "machine. Add the engine group, do not replace the others.",
        fr=f"`{compte}` a perdu le groupe `sudo`. Ce n'est pas ce que la mission "
           "demandait, et le compte ne peut plus administrer la machine. "
           "Ajoutez le groupe du moteur, ne remplacez pas les autres.",
    )


def test_un_conteneur_a_reellement_ete_execute(host) -> None:
    """Quatrième plan : le moteur EXÉCUTE, il ne se contente pas de répondre.

    Un démon peut répondre à `docker version` et échouer à lancer le moindre
    conteneur : pilote de stockage cassé, cgroups absents, image illisible.
    Seule une exécution le prouve, et le setup n'en laisse aucune derrière lui.

    On accepte n'importe quel état de sortie : un conteneur terminé prouve
    autant qu'un conteneur vivant, et `hello-world` s'arrête de lui-même.
    """
    res = host.run(
        "docker ps -a --filter ancestor=%s --format '{{.ID}} {{.Status}}'",
        IMAGE_DE_PREUVE,
    )
    assert res.rc == 0, message(
        en=f"cannot list containers: {res.stderr.strip()}",
        fr=f"impossible de lister les conteneurs : {res.stderr.strip()}",
    )
    lignes = [ligne for ligne in res.stdout.splitlines() if ligne.strip()]
    assert lignes, message(
        en=f"no container was ever run from `{IMAGE_DE_PREUVE}`. The image is "
           "already on the machine, so no registry access is needed: run a "
           "container from it, and leave it there as the proof.",
        fr=f"aucun conteneur n'a été exécuté depuis `{IMAGE_DE_PREUVE}`. L'image "
           "est déjà sur la machine, donc aucun accès au registre n'est "
           "nécessaire : lancez-en un conteneur, et laissez-le là comme preuve.",
    )
