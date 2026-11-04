"""Des capabilities réduites à une seule, déclarées, appliquées, et éprouvées.

Pourquoi trois contrôles là où il n'y en avait qu'un
---------------------------------------------------

Le fichier précédent portait **un** `def test_` et six assertions enchaînées, et
il mesurait les trois bonnes choses : ce que Docker a retenu, ce que le noyau
applique, et ce que le conteneur peut encore faire. Le défaut était le masquage,
plus un effet de bord que personne n'avait relevé.

LE MASQUAGE. La première assertion qui tombait masquait les cinq suivantes, et
son message tenait en trois mots : « Un service actif requis ». Un apprenant
ayant posé les bonnes capabilities mais dont le projet avait été relancé sous un
autre nom lisait cela, et n'apprenait rien de son travail.

L'EFFET DE BORD. La sonde tente un `chown 123:123 /proof`. Sur l'état de départ,
où le conteneur a encore `CAP_CHOWN`, **elle réussit** : le contrôle laissait donc
`/proof` appartenant à 123 après être passé. L'assertion suivante le constatait et
échouait, ce qui donnait le bon verdict pour la mauvaise raison, et surtout le
lab restait modifié. Le troisième contrôle restaure désormais le propriétaire
quand sa propre sonde a abouti : un contrôle qui change l'état qu'il mesure n'est
pas un contrôle, c'est une intervention.

Les trois contrôles mesurent trois choses indépendantes :

1. les capabilities **déclarées** à Docker ;
2. le masque que le **noyau applique** à PID 1 ;
3. ce que le conteneur **ne peut plus faire**, éprouvé par un geste réel.

1 et 2 ne sont pas redondants. Docker 29 normalise les noms avec leur préfixe
`CAP_`, et une déclaration peut être retenue sans que le masque effectif
corresponde : c'est `CapEff` qui dit ce dont le processus dispose vraiment. Le
troisième ne lit rien, il essaie, et c'est la seule preuve qui ne dépende
d'aucune lecture.
"""

import json

import pytest

from conftest import lab_host, message

LAB = "securite-capabilities"
PROJET = f"dsoxlab-{LAB}"
PREUVE = "/proof"
BIT_NET_BIND_SERVICE = 1 << 10  # CAP_NET_BIND_SERVICE, soit 0x400.


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _worker(host) -> tuple[str, dict]:
    """Le conteneur du service, ou un échec qui dit quoi faire.

    Garde-fou de mesure, non exigence : sans un service unique et étiqueté,
    aucun des trois contrôles ne peut observer quoi que ce soit.
    """
    trouve = host.run(
        "docker ps -q --filter label=com.docker.compose.project=%s "
        "--filter label=com.docker.compose.service=worker",
        PROJET,
    )
    ids = trouve.stdout.split()
    assert trouve.rc == 0 and len(ids) == 1, message(
        en=(
            f"Exactly one running `worker` service is required in project "
            f"{PROJET}, found {len(ids)}. Bring the project back up under that "
            "exact name before reducing its capabilities."
        ),
        fr=(
            f"Un seul service `worker` actif est requis dans le projet "
            f"{PROJET}, {len(ids)} trouvé(s). Relancez le projet sous ce nom "
            "exact avant de réduire ses capabilities."
        ),
    )
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the worker: cleanup removes only what carries it.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le worker : le nettoyage ne retire que ce qui le porte.",
    )
    return cid, info


def _canonique(noms) -> list[str]:
    """Les noms de capabilities sous la forme que Docker 29 rend.

    Docker 29 NORMALISE avec le préfixe `CAP_` : `--cap-add NET_BIND_SERVICE`
    ressort en `[CAP_NET_BIND_SERVICE]`. On compare donc des noms canoniques,
    ce qui accepte les deux écritures côté apprenant sans rien relâcher. `ALL`
    reste `ALL` : ce n'est pas une capability, c'est le mot qui les désigne
    toutes.
    """
    return sorted(
        n if n == "ALL" else "CAP_" + n.removeprefix("CAP_")
        for n in (noms or [])
    )


def test_les_capabilities_declarees_ne_gardent_que_net_bind_service(host):
    """Ce qui a été demandé à Docker."""
    _cid, info = _worker(host)
    config = info["HostConfig"]

    retirees = _canonique(config["CapDrop"])
    assert retirees == ["ALL"], message(
        en=(
            f"The worker drops {retirees or '[]'} instead of ['ALL']. Starting "
            "from nothing and adding back is what makes the result readable: "
            "dropping capabilities one by one leaves whatever a future image adds."
        ),
        fr=(
            f"Le worker retire {retirees or '[]'} au lieu de ['ALL']. Partir de "
            "rien puis ajouter est ce qui rend le résultat lisible : retirer les "
            "capabilities une à une laisse passer ce qu'une image future "
            "ajouterait."
        ),
    )
    ajoutees = _canonique(config["CapAdd"])
    assert ajoutees == ["CAP_NET_BIND_SERVICE"], message(
        en=(
            f"The worker adds back {ajoutees or '[]'} instead of "
            "['CAP_NET_BIND_SERVICE']. Listening on a privileged port is its only "
            "need; changing owners is not part of its work."
        ),
        fr=(
            f"Le worker rajoute {ajoutees or '[]'} au lieu de "
            "['CAP_NET_BIND_SERVICE']. Écouter sur un port privilégié est son "
            "seul besoin ; changer de propriétaire ne fait pas partie de son "
            "travail."
        ),
    )


def test_le_noyau_n_applique_que_ce_bit_a_pid_1(host):
    """Ce que le noyau applique, qui est la seule vérité.

    Une déclaration peut être retenue par Docker sans que le masque effectif
    corresponde. `CapEff` dit ce dont le processus dispose vraiment, et il se lit
    dans `/proc/1/status`.
    """
    cid, _info = _worker(host)

    lu = host.run("docker exec %s cat /proc/1/status", cid)
    assert lu.rc == 0, message(
        en=f"Cannot read /proc/1/status inside the worker: {lu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"/proc/1/status est illisible dans le worker : {lu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    lignes = [ligne for ligne in lu.stdout.splitlines() if ligne.startswith("CapEff:")]
    assert lignes, message(
        en="/proc/1/status carries no CapEff line. Not your fault: the check cannot measure anything, report it.",
        fr="/proc/1/status ne porte aucune ligne CapEff. Ce n'est pas votre faute : le contrôle ne peut rien mesurer, signalez-le.",
    )
    effectif = int(lignes[0].split()[1], 16)
    assert effectif == BIT_NET_BIND_SERVICE, message(
        en=(
            f"PID 1 carries the effective mask 0x{effectif:x} instead of "
            f"0x{BIT_NET_BIND_SERVICE:x}. Only bit 10 may remain: what Docker "
            "retained and what the kernel applies can differ, and the kernel is "
            "authoritative."
        ),
        fr=(
            f"PID 1 porte le masque effectif 0x{effectif:x} au lieu de "
            f"0x{BIT_NET_BIND_SERVICE:x}. Seul le bit 10 doit rester : ce que "
            "Docker a retenu et ce que le noyau applique peuvent différer, et "
            "c'est le noyau qui fait foi."
        ),
    )


def test_un_changement_de_proprietaire_est_reellement_refuse(host):
    """Ce que le conteneur ne peut plus faire, éprouvé par un geste réel.

    Les deux contrôles précédents lisent ; celui-ci essaie. C'est la seule preuve
    qui ne dépende d'aucune lecture, et c'est elle qui compte pour l'exploitant :
    un masque juste sur le papier n'empêche rien s'il n'est pas appliqué.
    """
    cid, _info = _worker(host)

    avant = host.run("docker exec %s stat -c %%u %s", cid, PREUVE)
    assert avant.rc == 0 and avant.stdout.strip().isdigit(), message(
        en=f"Cannot read the owner of {PREUVE}: it must exist and belong to root. Keep it in place.",
        fr=f"Le propriétaire de {PREUVE} est illisible : il doit exister et appartenir à root. Conservez-le en place.",
    )
    assert avant.stdout.strip() == "0", message(
        en=f"{PREUVE} belongs to UID {avant.stdout.strip()} instead of root, so this check has nothing left to prove.",
        fr=f"{PREUVE} appartient à l'UID {avant.stdout.strip()} au lieu de root, donc ce contrôle n'a plus rien à prouver.",
    )

    essai = host.run("docker exec %s chown 123:123 %s", cid, PREUVE)
    try:
        assert essai.rc != 0, message(
            en=(
                f"The worker was still able to change the owner of {PREUVE}. "
                "CAP_CHOWN is therefore still available to it, whatever the "
                "declaration says."
            ),
            fr=(
                f"Le worker a encore pu changer le propriétaire de {PREUVE}. "
                "CAP_CHOWN lui reste donc disponible, quoi qu'en dise la "
                "déclaration."
            ),
        )
    finally:
        # ON RESTAURE CE QUE LA SONDE A PU CHANGER.
        #
        # Sur l'état de départ, le conteneur a encore `CAP_CHOWN` et ce `chown`
        # RÉUSSIT : la version précédente de ce contrôle laissait donc `/proof`
        # appartenant à 123 après être passée. Elle le constatait ensuite et
        # échouait, ce qui donnait le bon verdict pour la mauvaise raison, et
        # laissait le lab modifié pour la suite.
        #
        # Un contrôle qui change l'état qu'il mesure n'est pas un contrôle, c'est
        # une intervention.
        if essai.rc == 0:
            host.run("docker exec %s chown 0:0 %s", cid, PREUVE)

    apres = host.run("docker exec %s stat -c %%u %s", cid, PREUVE)
    assert apres.rc == 0 and apres.stdout.strip() == "0", message(
        en=(
            f"{PREUVE} no longer belongs to root after the probe. Not your fault "
            "if the refusal held: the check restores what it may have changed, "
            "report it."
        ),
        fr=(
            f"{PREUVE} n'appartient plus à root après la sonde. Ce n'est pas "
            "votre faute si le refus a tenu : le contrôle restaure ce qu'il a pu "
            "changer, signalez-le."
        ),
    )
