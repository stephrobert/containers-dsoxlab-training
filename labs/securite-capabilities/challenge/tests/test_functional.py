"""Une seule capability rendue, la bonne, déclarée, appliquée, et éprouvée.

CE QUE LE LAB ENSEIGNE. Qu'un service qui s'arrête quand on lui retire toutes
ses capabilities en demande UNE, qu'il se trouve en lisant ce qui est refusé, et
que le reste doit rester retiré. Le lanceur confine ses travaux avec `chroot` :
la capability qu'il lui faut est `SYS_CHROOT`, bit 18.

CE QUE LA VERSION PRÉCÉDENTE ENSEIGNAIT, ET POURQUOI ELLE A ÉTÉ REFAITE. Elle
exigeait `NET_BIND_SERVICE`, présentée comme la seule exception d'un service qui
écoute sur un port privilégié. C'est faux sous Docker : mesuré le 2026-11-02 sur
Engine 29.9.2, un conteneur sans AUCUNE capability écoute sur le port 80, parce
que le moteur pose `net.ipv4.ip_unprivileged_port_start=0` dans l'espace de
noms réseau du conteneur. Le lab apprenait une exception qui n'existe pas.

MESURÉ SUR docker.lab LE 2026-11-09 (Engine 29.9.2, Compose 5.6.1), le même
service alpine dans cinq configurations :

| Configuration | Le lanceur | Masque effectif de PID 1 |
| défaut de Docker | fonctionne | 0xa80425fb |
| tout retiré | s'arrête au démarrage | 0x0 |
| tout retiré, SYS_CHROOT rendue | fonctionne | 0x40000 |
| tout retiré, CHOWN rendue | s'arrête au démarrage | 0x1 |
| tout retiré, SYS_CHROOT et CHOWN | fonctionne ET un chown réussit | 0x40001 |

La dernière ligne est le piège : un service qui marche avec une capability de
trop passe tous les contrôles fonctionnels. Seuls le masque effectif et un geste
réel la distinguent du minimum.

TROIS CONTRÔLES, TROIS PREUVES INDÉPENDANTES :

1. ce qui a été DÉCLARÉ à Docker, et que le conteneur n'est pas privilégié ;
2. ce que le NOYAU applique à PID 1, et que le lanceur tourne vraiment ;
3. ce que le conteneur ne peut PLUS faire, éprouvé par un geste réel.

POURQUOI LE FONCTIONNEMENT EST FUSIONNÉ AVEC LE MASQUE. « Le lanceur tourne »
est vrai AVANT tout travail, avec les capabilities par défaut : seul, il ne
mesurerait rien. Joint au masque exact, il ne peut être atteint qu'après le
travail. Le mode privilégié le fait aussi tourner, ce qui est la raison pour
laquelle le premier contrôle le refuse nommément.
"""

import json
import time

import pytest

from conftest import lab_host, message

LAB = "securite-capabilities"
PROJET = f"dsoxlab-{LAB}"
PREUVE = "/proof"
ETAT = "/run/lanceur/etat"
BIT_SYS_CHROOT = 1 << 18  # CAP_SYS_CHROOT, soit 0x40000.


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
            f"{PROJET}, found {len(ids)}. If the launcher stopped, read its "
            "logs: they name the operation the kernel refuses."
        ),
        fr=(
            f"Un seul service `worker` actif est requis dans le projet "
            f"{PROJET}, {len(ids)} trouvé(s). Si le lanceur s'est arrêté, "
            "lisez ses journaux : ils nomment l'opération que le noyau refuse."
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

    Docker 29 NORMALISE avec le préfixe `CAP_` : `--cap-add SYS_CHROOT` ressort
    en `[CAP_SYS_CHROOT]`. On compare donc des noms canoniques, ce qui accepte
    les deux écritures côté apprenant sans rien relâcher. `ALL` reste `ALL` : ce
    n'est pas une capability, c'est le mot qui les désigne toutes.
    """
    return sorted(
        n if n == "ALL" else "CAP_" + n.removeprefix("CAP_")
        for n in (noms or [])
    )


def test_une_seule_capability_est_rendue_et_le_conteneur_n_est_pas_privilegie(host):
    """Ce qui a été demandé à Docker : tout retirer, rendre UNE capability.

    Le mode privilégié est refusé nommément : il rend toutes les capabilities,
    quoi que dise `cap_drop`, et ferait tourner le lanceur sans que rien ait été
    compris. Une capability rendue en plus de la bonne est refusée avec son nom :
    c'est celle qu'on rajoute « parce qu'elle va souvent avec ».
    """
    _cid, info = _worker(host)
    config = info["HostConfig"]

    assert not config.get("Privileged"), message(
        en=(
            "The worker runs in privileged mode. It gives every capability "
            "back, whatever `cap_drop` says, and removes the point of the "
            "exercise: recreate it without `privileged`."
        ),
        fr=(
            "Le worker tourne en mode privilégié. Il rend toutes les "
            "capabilities, quoi que dise `cap_drop`, et ôte son sens à "
            "l'exercice : recréez-le sans `privileged`."
        ),
    )
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
    en_trop = [n for n in ajoutees if n != "CAP_SYS_CHROOT"]
    assert not en_trop, message(
        en=(
            f"The worker gives back {en_trop} besides what the launcher needs. "
            "A service that works with one capability too many passes every "
            "functional check: the minimum is one capability."
        ),
        fr=(
            f"Le worker rend {en_trop} en plus de ce dont le lanceur a besoin. "
            "Un service qui marche avec une capability de trop passe tous les "
            "contrôles fonctionnels : le minimum est une seule capability."
        ),
    )
    assert ajoutees == ["CAP_SYS_CHROOT"], message(
        en=(
            f"The worker gives back {ajoutees or '[]'}, and the launcher stays "
            "down. Read its logs: the refused operation names the capability "
            "it needs."
        ),
        fr=(
            f"Le worker rend {ajoutees or '[]'}, et le lanceur reste arrêté. "
            "Lisez ses journaux : l'opération refusée nomme la capability dont "
            "il a besoin."
        ),
    )


def test_le_noyau_n_applique_que_ce_bit_a_pid_1_et_le_lanceur_tourne(host):
    """Ce que le noyau applique, qui est la seule vérité, et le lanceur qui vit.

    Une déclaration peut être retenue par Docker sans que le masque effectif
    corresponde. `CapEff` dit ce dont le processus dispose vraiment, et il se lit
    dans `/proc/1/status`. Le rapport du lanceur est lu DEUX fois, à trois
    secondes d'écart : un compteur qui monte dit que le `chroot` réussit encore,
    pas seulement qu'il a réussi une fois au démarrage.
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
    assert effectif == BIT_SYS_CHROOT, message(
        en=(
            f"PID 1 carries the effective mask 0x{effectif:x} instead of "
            f"0x{BIT_SYS_CHROOT:x}. Only bit 18 may remain: what Docker "
            "retained and what the kernel applies can differ, and the kernel is "
            "authoritative."
        ),
        fr=(
            f"PID 1 porte le masque effectif 0x{effectif:x} au lieu de "
            f"0x{BIT_SYS_CHROOT:x}. Seul le bit 18 doit rester : ce que "
            "Docker a retenu et ce que le noyau applique peuvent diverger, et "
            "c'est le noyau qui fait foi."
        ),
    )

    def _etat() -> tuple[str, int]:
        rapport = host.run("docker exec %s cat %s", cid, ETAT).stdout.split()
        if len(rapport) == 2 and rapport[0] == "ok" and rapport[1].isdigit():
            return "ok", int(rapport[1])
        return (rapport[0] if rapport else "absent"), 0

    premier = _etat()
    time.sleep(3)
    second = _etat()
    assert premier[0] == "ok" and second[0] == "ok" and second[1] > premier[1], message(
        en=(
            f"The launcher does not report a working state ({premier[0]} then "
            f"{second[0]}, count {premier[1]} then {second[1]}). With the "
            "single capability given back, its `chroot` must succeed every "
            "second."
        ),
        fr=(
            f"Le lanceur ne rend pas compte d'un état de marche ({premier[0]} "
            f"puis {second[0]}, compteur {premier[1]} puis {second[1]}). Avec "
            "la seule capability rendue, son `chroot` doit réussir chaque "
            "seconde."
        ),
    )


def test_un_changement_de_proprietaire_est_reellement_refuse(host):
    """Ce que le conteneur ne peut plus faire, éprouvé par un geste réel.

    Les deux contrôles précédents lisent ; celui-ci essaie. C'est la seule preuve
    qui ne dépende d'aucune lecture, et c'est elle qui compte pour l'exploitant :
    un masque juste sur le papier n'empêche rien s'il n'est pas appliqué. Le
    `chown` est aussi le geste que fait réussir la capability qu'on rajoute par
    habitude : c'est le cas que ce contrôle attrape.
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
        # RÉUSSIT : un contrôle qui laisserait `/proof` appartenant à 123 après
        # être passé donnerait le bon verdict pour la mauvaise raison, et
        # laisserait le lab modifié pour la suite.
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
