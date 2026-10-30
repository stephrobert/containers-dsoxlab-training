"""Tests fonctionnels du lab reseau-interne : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'il y a DEUX isolations, qu'on confond parce qu'on les
appelle toutes les deux « isoler » :

  - `--network none` : aucun réseau du tout. Pas d'interface hors loopback, pas
    de voisin, rien. Pour un traitement qui n'a besoin de personne.
  - un réseau `--internal` : les membres se parlent ENTRE EUX, par leur nom, et
    ne sortent pas. Pour une base que seule son application doit joindre.

Les prendre l'une pour l'autre donne soit un service inutilisable, soit un
service exposé. Le lab fait obtenir les deux, sur la même machine, pour que la
différence se voie.

MESURÉ AVANT D'ÊTRE ÉCRIT, sur docker.lab le 2026-10-30 :

| Posture | interfaces hors loopback | joint le témoin | voisin par son nom |
| réseau par défaut | 1 | oui | non |
| `--network none` | 0 | non | sans objet |
| réseau interne | 1 | non | oui |

Et un détail qui dit tout du mécanisme : un conteneur d'un réseau interne n'a
AUCUNE route par défaut. L'isolation n'est pas un filtrage posé devant lui,
c'est l'absence du chemin.

COMMENT « SORTIR » EST MESURÉ, et c'est une décision. Contre un témoin publié
sur l'adresse routable de la machine, jamais contre Internet. Un lab qui
dépendrait d'un accès sortant échouerait sur une machine isolée, et son message
parlerait d'isolation réussie alors qu'il n'y a pas de réseau du tout : il
noterait l'inverse de ce qu'il mesure.

LE TÉMOIN EST PROTÉGÉ. Les contrôles 2 et 4 seraient aussi vrais si `dehors`
disparaissait : il n'y aurait plus rien à ne pas joindre. Un préalable vérifie
donc qu'il tourne et qu'il répond depuis l'hôte.

AUCUNE ADRESSE N'EST ÉCRITE DANS CE FICHIER. L'adresse routable est déduite de
la route par défaut au moment de la notation.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

TEMOIN = "dehors"
COFFRE = "coffre"
ATELIER_A = "atelier-a"
ATELIER_B = "atelier-b"
PORT_TEMOIN = 18090
RESEAU_DEMANDE = "confine"
SOUS_RESEAU_DEMANDE = "172.29.9.0/24"

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


@pytest.fixture(scope="module")
def routable(host) -> str:
    """L'adresse routable de la machine, déduite de sa route par défaut.

    Jamais écrite en dur : une adresse figée dans un test est une panne
    différée, qui se déclenche au premier changement de plan d'adressage.
    """
    res = host.run(
        "ip -o -4 route get 1.1.1.1 "
        "| awk '{for (i = 1; i <= NF; i++) if ($i == \"src\") print $(i + 1)}'"
    )
    adresse = res.stdout.strip()
    if not adresse:
        pytest.skip(message(
            en="the machine has no routable address: outbound reachability "
               "cannot be measured",
            fr="la machine n'a aucune adresse routable : la sortie ne peut pas "
               "être mesurée",
        ))
    return adresse


@pytest.fixture(scope="module")
def temoin_repond(host, routable) -> str:
    """Le témoin tourne et répond, sinon les contrôles ne prouvent rien.

    Sans lui, « ne joint pas le témoin » serait vrai parce qu'il n'y a plus de
    témoin. Un contrôle qu'on satisfait en retirant le sujet ne mesure rien.
    """
    etat = host.run(
        "docker container inspect %s --format %s", TEMOIN, "{{.State.Status}}"
    )
    if etat.rc != 0 or etat.stdout.strip() != "running":
        pytest.fail(message(
            en=f"the witness `{TEMOIN}` is not running. It must not be "
               "touched: it holds the role of everything outside the container "
               "network, and without it the isolation checks prove nothing. "
               "Replay the lab with `dsoxlab reset`.",
            fr=f"le témoin `{TEMOIN}` ne tourne pas. Il ne doit pas être "
               "touché : il tient le rôle de tout ce qui est hors du réseau des "
               "conteneurs, et sans lui les contrôles d'isolation ne prouvent "
               "rien. Rejouez le lab avec `dsoxlab reset`.",
        ))
    for _ in range(4):
        res = host.run("nc -w 3 %s %s", routable, str(PORT_TEMOIN))
        if "jeton=" in res.stdout:
            return routable
    pytest.fail(message(
        en=f"the witness `{TEMOIN}` does not answer on "
           f"{routable}:{PORT_TEMOIN}. Its publication has been changed, and "
           "the isolation checks would pass for the wrong reason.",
        fr=f"le témoin `{TEMOIN}` ne répond pas sur "
           f"{routable}:{PORT_TEMOIN}. Sa publication a été modifiée, et les "
           "contrôles d'isolation passeraient pour une mauvaise raison.",
    ))
    return routable


def _tourne(host, nom: str) -> None:
    """Le préalable de chaque contrôle, dit clairement.

    Ce lab fait RECRÉER les conteneurs, puisque `--network` ne se choisit qu'à
    la création : un nom manquant veut presque toujours dire qu'un conteneur a
    été détruit et pas relancé.
    """
    res = host.run(
        "docker container inspect %s --format %s", nom, "{{.State.Status}}"
    )
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{nom}` does not exist. This lab requires "
               "recreating containers, because `--network` is only chosen at "
               "creation: it has to be relaunched under the SAME name, from the "
               "image the setup built.",
            fr=f"le conteneur `{nom}` n'existe pas. Ce lab demande de recréer "
               "des conteneurs, puisque `--network` ne se choisit qu'à la "
               "création : il faut le relancer sous le MÊME nom, depuis l'image "
               "que le setup a construite.",
        ))
    etat = res.stdout.strip()
    if etat != "running":
        pytest.fail(message(
            en=f"container `{nom}` is in state `{etat}`, not `running`. A "
               "stopped container is not isolated, it is absent.",
            fr=f"le conteneur `{nom}` est dans l'état `{etat}`, pas `running`. "
               "Un conteneur arrêté n'est pas isolé, il est absent.",
        ))


def _joint(host, depuis: str, adresse: str, port: int) -> bool:
    """Vrai si un conteneur REÇOIT la réponse du service visé.

    La réponse est lue, jamais la seule connexion : le proxy de Docker accepte
    avant que quoi que ce soit écoute, donc un `connect()` réussi ne prouve
    rien.
    """
    for _ in range(3):
        res = host.run("docker exec %s nc -w 3 %s %s", depuis, adresse, str(port))
        if "jeton=" in res.stdout:
            return True
    return False


def _noms_d_interface(lignes: list[str]) -> str:
    """Les noms d'interface d'une sortie `ip -o link`, pour un message lisible.

    Un message qui recopierait la sortie brute noierait la seule information
    utile, qui est le nom de ce qui reste attaché.
    """
    noms = []
    for ligne in lignes:
        morceaux = ligne.split(":")
        if len(morceaux) > 1:
            noms.append(morceaux[1].strip().split("@")[0])
    return ", ".join(noms) if noms else "?"


def test_le_coffre_n_a_aucune_interface_reseau(host) -> None:
    """Aucun réseau du tout, et cela se voit de l'intérieur.

    Le contrôle regarde les interfaces DANS le conteneur, pas ce que le moteur
    déclare, et c'est volontaire : l'effet compte, pas le chemin. Recréer avec
    `--network none` est le geste franc, détacher le conteneur de ses réseaux
    donne le même résultat, et les deux comptent.
    """
    _tourne(host, COFFRE)
    res = host.run("docker exec %s ip -o link", COFFRE)
    assert res.rc == 0, message(
        en=f"cannot list `{COFFRE}`'s interfaces: {res.stderr.strip()}",
        fr=f"impossible de lister les interfaces de `{COFFRE}` : "
           f"{res.stderr.strip()}",
    )
    hors_loopback = [
        ligne.strip()
        for ligne in res.stdout.splitlines()
        if ligne.strip() and ": lo:" not in ligne
    ]
    assert not hors_loopback, message(
        en=f"`{COFFRE}` still has {len(hors_loopback)} network interface(s) "
           "besides the loopback:\n"
           f"  {_noms_d_interface(hors_loopback)}\n"
           "It must have none at all. A container with no network is created "
           "that way, and the loopback is the only interface it keeps.",
        fr=f"`{COFFRE}` porte encore {len(hors_loopback)} interface(s) réseau "
           "en plus du loopback :\n"
           f"  {_noms_d_interface(hors_loopback)}\n"
           "Il n'en doit avoir aucune. Un conteneur sans réseau se crée ainsi, "
           "et le loopback est la seule interface qu'il conserve.",
    )


def test_le_coffre_ne_joint_rien(host, temoin_repond) -> None:
    """La conséquence observable, et elle se mesure, elle ne se déduit pas.

    Le contrôle précédent lit la configuration du conteneur ; celui-ci éprouve
    ce qu'il peut faire. Les deux peuvent diverger, et c'est là tout l'intérêt
    de les séparer : un conteneur peut avoir perdu son interface et garder un
    partage de pile réseau avec un autre.
    """
    _tourne(host, COFFRE)
    assert not _joint(host, COFFRE, temoin_repond, PORT_TEMOIN), message(
        en=f"`{COFFRE}` still reaches the witness `{TEMOIN}` at "
           f"{temoin_repond}:{PORT_TEMOIN}.\n"
           "A container with no network reaches nothing at all: neither the "
           "outside, nor the host, nor its former neighbours.",
        fr=f"`{COFFRE}` joint encore le témoin `{TEMOIN}` en "
           f"{temoin_repond}:{PORT_TEMOIN}.\n"
           "Un conteneur sans réseau ne joint plus rien du tout : ni "
           "l'extérieur, ni l'hôte, ni ses anciens voisins.",
    )


def test_le_reseau_confine_existe_et_est_interne(host) -> None:
    """Un réseau dont on a déclaré qu'il ne sort pas.

    `--internal` n'est pas un filtrage posé devant les conteneurs, c'est
    l'absence de la route : un membre de ce réseau n'a aucune passerelle. Le
    sous-réseau est imposé parce qu'un réseau créé sans plan en reçoit un que le
    moteur choisit, ce qu'on veut éviter en production.
    """
    res = host.run("docker network inspect %s --format %s",
                   RESEAU_DEMANDE, "{{.Internal}}")
    assert res.rc == 0, message(
        en=f"no network named `{RESEAU_DEMANDE}` exists: {res.stderr.strip()}\n"
           "It has to be created, declared internal, with the subnet "
           f"{SOUS_RESEAU_DEMANDE}.",
        fr=f"aucun réseau nommé `{RESEAU_DEMANDE}` n'existe : "
           f"{res.stderr.strip()}\n"
           "Il faut le créer, déclaré interne, avec le sous-réseau "
           f"{SOUS_RESEAU_DEMANDE}.",
    )
    assert res.stdout.strip() == "true", message(
        en=f"`{RESEAU_DEMANDE}` exists but is not internal.\n"
           "An ordinary network lets its members out. An internal one gives "
           "them no default route at all, which is what confines them.",
        fr=f"`{RESEAU_DEMANDE}` existe mais n'est pas interne.\n"
           "Un réseau ordinaire laisse sortir ses membres. Un réseau interne ne "
           "leur donne aucune route par défaut, et c'est ce qui les confine.",
    )
    sous = host.run("docker network inspect %s --format %s",
                    RESEAU_DEMANDE, "{{(index .IPAM.Config 0).Subnet}}")
    assert sous.stdout.strip() == SOUS_RESEAU_DEMANDE, message(
        en=f"`{RESEAU_DEMANDE}` carries the subnet {sous.stdout.strip()}, not "
           f"{SOUS_RESEAU_DEMANDE}.",
        fr=f"`{RESEAU_DEMANDE}` porte le sous-réseau {sous.stdout.strip()}, pas "
           f"{SOUS_RESEAU_DEMANDE}.",
    )


def test_l_atelier_se_parle_sans_sortir(host, temoin_repond) -> None:
    """L'isolation utile : les deux se parlent, et ni l'un ni l'autre ne sort.

    Trois assertions qui ne se séparent pas. Confiner sans que les membres se
    parlent donnerait un service inutilisable ; les faire se parler sans les
    confiner ne serait qu'un réseau dédié de plus, ce qui est le lab précédent.

    Et le piège reste celui du réseau dédié : un conteneur peut être sur DEUX
    réseaux. Être sur le réseau confiné ne suffit pas, il faut aussi avoir
    quitté l'autre, sinon la sortie demeure.
    """
    _tourne(host, ATELIER_A)
    _tourne(host, ATELIER_B)
    for nom in (ATELIER_A, ATELIER_B):
        res = host.run(
            "docker container inspect %s --format %s",
            nom,
            "{{range $r, $v := .NetworkSettings.Networks}}{{println $r}}{{end}}",
        )
        reseaux = {
            ligne.strip()
            for ligne in res.stdout.splitlines()
            if ligne.strip()
        }
        assert RESEAU_DEMANDE in reseaux, message(
            en=f"`{nom}` is not attached to `{RESEAU_DEMANDE}`.\n"
               f"  it is on: {', '.join(sorted(reseaux)) or '(nothing)'}",
            fr=f"`{nom}` n'est pas attaché à `{RESEAU_DEMANDE}`.\n"
               f"  il est sur : {', '.join(sorted(reseaux)) or '(rien)'}",
        )

    assert _joint(host, ATELIER_B, ATELIER_A, 80), message(
        en=f"`{ATELIER_B}` does not reach `{ATELIER_A}` by its name on port 80.\n"
           "A confined network is not a mute network: its members resolve each "
           "other and talk to each other. Confining without that would give an "
           "unusable service.",
        fr=f"`{ATELIER_B}` ne joint pas `{ATELIER_A}` par son nom sur le port "
           "80.\n"
           "Un réseau confiné n'est pas un réseau muet : ses membres se "
           "résolvent et se parlent. Confiner sans cela donnerait un service "
           "inutilisable.",
    )

    for nom in (ATELIER_A, ATELIER_B):
        assert not _joint(host, nom, temoin_repond, PORT_TEMOIN), message(
            en=f"`{nom}` still reaches the witness `{TEMOIN}` at "
               f"{temoin_repond}:{PORT_TEMOIN}, so it is not confined.\n"
               "Being on the internal network is not enough: a container can be "
               "on TWO networks at once, and the other one lets it out. Check "
               "that it has left the default network.",
            fr=f"`{nom}` joint encore le témoin `{TEMOIN}` en "
               f"{temoin_repond}:{PORT_TEMOIN} : il n'est donc pas confiné.\n"
               "Être sur le réseau interne ne suffit pas : un conteneur peut "
               "être sur DEUX réseaux à la fois, et l'autre le laisse sortir. "
               "Vérifiez qu'il a quitté le réseau par défaut.",
        )
