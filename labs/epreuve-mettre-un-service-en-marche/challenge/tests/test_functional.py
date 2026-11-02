"""Tests fonctionnels de l'épreuve mettre-un-service-en-marche : cinq contrôles de poids égal.

C'EST UNE ÉPREUVE, et cela change ce que les messages doivent dire. Un lab
guide : son message nomme le geste qui manque. Un challenge évalue : son message
nomme le SYMPTÔME précis et s'arrête là. Aucun message de ce fichier ne dit
« activez le service » ni « ajoutez-vous au groupe ». Les indices sont là pour
ça, et ils coûtent des points.

LES QUATRE OBSTACLES POSÉS, dits nulle part dans l'énoncé :
  1. `docker.service` et `docker.socket` sont arrêtés ET désactivés ;
  2. le compte de l'apprenant n'est plus dans le groupe `docker` ;
  3. un conteneur ARRÊTÉ occupe déjà le nom demandé ;
  4. un conteneur témoin, arrêté lui aussi, porte des journaux et ne doit pas
     être touché.

L'EXIGENCE CRITIQUE est le contrôle 4 : le témoin supprimé ou redémarré fait
échouer l'épreuve, même avec tout le reste en place. Il ressemble à l'obstacle
n°3 à s'y tromper, et c'est le but : distinguer « ce qui gêne » de « ce qui
ressemble à ce qui gêne » est la compétence mesurée. Dans la vraie vie, le
conteneur qu'on supprime d'un `docker rm` trop large est celui qui portait la
trace de l'incident.

POURQUOI LE CONTRÔLE 1 SÉPARE « DÉMARRÉ » DE « ACTIVÉ ». Ce sont deux faits
distincts, et seul le second survit à un redémarrage de la machine. Un poste
qui marche jusqu'au prochain reboot n'est pas un poste en marche, et c'est la
confusion la plus répandue chez qui débute avec systemd.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true`.
Les contrôles mesurent donc le moteur sans dépendre des groupes du compte, SAUF
le contrôle 1, qui vérifie justement l'appartenance au groupe : il la lit dans
les groupes du compte, et non par une commande qu'il lancerait en son nom.
"""

from __future__ import annotations

import json
import re
import uuid

import pytest

from conftest import lab_host, message

SERVICE = "annuaire"
TEMOIN = "journal-de-bord"
IMAGE = "lab-mise-en-marche:1.0"
ATELIER = "/opt/lab-mise-en-marche"
PREDICTION = f"{ATELIER}/prediction.txt"
PORT_SERVICE = 80

# Le programme et l'argument que l'image déclare, et ce que la commande de
# l'énoncé en fait. C'est la vérité que le contrôle 5 recalcule sur la machine
# plutôt que de la supposer.
COMMANDE_A_PREDIRE = "--verbeux"

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui les
    lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier.
    """
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def salle(host) -> str:
    """La valeur de configuration attendue, lue dans le LABEL de l'image.

    Elle est tirée au sort à chaque passage par le setup : un mot figé dans un
    dépôt public est une réponse publiée. Le label la rend lisible au contrôle
    sans qu'aucun fichier de l'hôte n'ait à la porter.
    """
    res = host.run(
        "docker image inspect %s --format %s",
        IMAGE,
        '{{index .Config.Labels "dsoxlab.salle"}}',
    )
    if res.rc != 0 or not res.stdout.strip():
        pytest.fail(message(
            en=f"image `{IMAGE}` is gone, or no longer carries the expected "
               "configuration value. It is the image the brief provides: it is "
               "not to be rebuilt.",
            fr=f"l'image `{IMAGE}` a disparu, ou ne porte plus la valeur de "
               "configuration attendue. C'est l'image que l'énoncé fournit : "
               "elle n'est pas à reconstruire.",
        ))
    return res.stdout.strip()


def test_le_moteur_tourne_est_active_et_le_compte_lui_parle(host) -> None:
    """Trois faits qu'un seul geste ne règle pas, et c'est le sujet du contrôle.

    « Démarré » et « activé » sont distincts : seul le second survit au prochain
    redémarrage. Et parler au moteur n'est pas la même chose que le démarrer :
    un démon en marche refuse un compte qui n'est pas dans son groupe, avec un
    message qui ressemble à une panne du démon alors que c'est une permission.
    """
    for unite in ("docker.service", "docker.socket"):
        actif = host.run("systemctl is-active %s", unite)
        assert actif.stdout.strip() == "active", message(
            en=f"`{unite}` is `{actif.stdout.strip() or 'unknown'}`, not "
               "`active`.",
            fr=f"`{unite}` est `{actif.stdout.strip() or 'inconnu'}`, et non "
               "`active`.",
        )
        active = host.run("systemctl is-enabled %s", unite)
        etat = active.stdout.strip()
        assert etat in {"enabled", "enabled-runtime"}, message(
            en=f"`{unite}` is `{etat or 'unknown'}`, not `enabled`.\n"
               "A running service and a service that comes back after a reboot "
               "are two different facts. The brief asks for both.",
            fr=f"`{unite}` est `{etat or 'inconnu'}`, et non `enabled`.\n"
               "Un service en marche et un service qui revient après un "
               "redémarrage sont deux faits différents. L'énoncé demande les "
               "deux.",
        )

    compte = _compte_apprenant(host)
    groupes = host.run("id -nG %s", compte)
    assert groupes.rc == 0, message(
        en=f"account `{compte}` cannot be read on this machine.",
        fr=f"le compte `{compte}` ne peut pas être lu sur cette machine.",
    )
    porte = groupes.stdout.split()
    assert "docker" in porte, message(
        en=f"account `{compte}` is not in the `docker` group.\n"
           f"  its groups: {', '.join(porte) or '(none)'}\n"
           "Without it, every command without `sudo` reports the daemon as "
           "unreachable, which looks like a daemon failure and is a permission "
           "refusal.",
        fr=f"le compte `{compte}` n'est pas dans le groupe `docker`.\n"
           f"  ses groupes : {', '.join(porte) or '(aucun)'}\n"
           "Sans lui, toute commande sans `sudo` annonce le démon injoignable, "
           "ce qui ressemble à une panne du démon et n'est qu'un refus de "
           "permission.",
    )


def test_le_service_tourne_et_rend_la_valeur_demandee(host, salle) -> None:
    """Le conteneur demandé, en marche, et configuré comme l'énoncé le dit.

    La valeur est lue dans la RÉPONSE du service, jamais dans `Config.Env` : ce
    qui compte est qu'elle soit arrivée jusqu'au programme. Une variable posée
    sur un conteneur qui ne l'utilise pas ne prouve rien, et c'est exactement
    l'écart que ce contrôle existe pour attraper.
    """
    etat = host.run(
        "docker container inspect %s --format %s", SERVICE, "{{.State.Status}}"
    )
    assert etat.rc == 0, message(
        en=f"no container named `{SERVICE}` exists.",
        fr=f"aucun conteneur nommé `{SERVICE}` n'existe.",
    )
    statut = etat.stdout.strip()
    assert statut == "running", message(
        en=f"container `{SERVICE}` is `{statut}`, not `running`.\n"
           "A stopped container keeps its name, which is worth knowing when a "
           "`docker run` refuses one.",
        fr=f"le conteneur `{SERVICE}` est `{statut}`, et non `running`.\n"
           "Un conteneur arrêté garde son nom, ce qui est bon à savoir quand un "
           "`docker run` en refuse un.",
    )
    issu = host.run(
        "docker container inspect %s --format %s", SERVICE, "{{.Config.Image}}"
    )
    assert IMAGE in issu.stdout, message(
        en=f"`{SERVICE}` does not come from `{IMAGE}`.\n"
           f"  its image: {issu.stdout.strip() or '(unknown)'}",
        fr=f"`{SERVICE}` n'est pas issu de `{IMAGE}`.\n"
           f"  son image : {issu.stdout.strip() or '(inconnue)'}",
    )
    recu = _interroge(host, SERVICE)
    assert f"salle={salle}" in recu, message(
        en=f"`{SERVICE}` answers, but not with the value the brief asks for.\n"
           f"  what came back: {recu.strip() or '(nothing)'}\n"
           f"  expected      : salle={salle}\n"
           "The value is read in the service's ANSWER, not in its environment: "
           "a variable set on a container that does not use it proves nothing.",
        fr=f"`{SERVICE}` répond, mais pas avec la valeur que l'énoncé "
           "demande.\n"
           f"  ce qui revient : {recu.strip() or '(rien)'}\n"
           f"  attendu        : salle={salle}\n"
           "La valeur est lue dans la RÉPONSE du service, pas dans son "
           "environnement : une variable posée sur un conteneur qui ne s'en "
           "sert pas ne prouve rien.",
    )


def test_l_ancien_conteneur_homonyme_a_disparu(host) -> None:
    """Un seul conteneur doit porter ce nom, et c'est le neuf.

    L'ancien était ARRÊTÉ : il n'empêchait rien de tourner, mais il occupait le
    nom, et c'est pour cela qu'un `docker run` échouait. Le contrôle vérifie
    qu'il n'en reste qu'un, et qu'il tourne : deux conteneurs ne peuvent pas
    porter le même nom, donc constater qu'il n'y en a qu'un et qu'il est en
    marche suffit à prouver que l'ancien est parti.
    """
    res = host.run(
        "docker ps -a --filter %s --format %s",
        f"name=^{SERVICE}$",
        "{{.ID}} {{.Status}}",
    )
    lignes = [l for l in res.stdout.splitlines() if l.strip()]
    assert len(lignes) == 1, message(
        en=f"{len(lignes)} containers carry the name `{SERVICE}`:\n"
           f"  {chr(10).join('  ' + l for l in lignes) or '  (none)'}\n"
           "Exactly one is expected, and it is the one that runs.",
        fr=f"{len(lignes)} conteneur(s) portent le nom `{SERVICE}` :\n"
           f"  {chr(10).join('  ' + l for l in lignes) or '  (aucun)'}\n"
           "Il en est attendu exactement un, et c'est celui qui tourne.",
    )
    assert "Up" in lignes[0], message(
        en=f"the only container named `{SERVICE}` is not running:\n"
           f"  {lignes[0]}\n"
           "The old stopped one is still there, and it is what the `docker run` "
           "was tripping over.",
        fr=f"le seul conteneur nommé `{SERVICE}` ne tourne pas :\n"
           f"  {lignes[0]}\n"
           "L'ancien, arrêté, est encore là, et c'est sur lui que le "
           "`docker run` butait.",
    )


def test_le_temoin_est_conserve_arrete_et_ses_journaux_lisibles(host) -> None:
    """L'EXIGENCE CRITIQUE : elle n'est compensée par aucun total.

    Le témoin ressemble à l'obstacle à s'y tromper : un conteneur arrêté, issu
    de la même image. La différence est qu'il porte la trace d'un incident, et
    l'énoncé demande explicitement de le conserver.

    TROIS FAITS SONT VÉRIFIÉS, et le deuxième surprend : il doit rester ARRÊTÉ.
    Le redémarrer n'est pas anodin, parce que l'énoncé dit « tel quel » et parce
    qu'un conteneur relancé peut écraser ce qu'il portait. C'est la discipline
    qu'une épreuve d'exploitation doit mesurer : on ne touche pas à une pièce
    qu'on est venu préserver.
    """
    res = host.run(
        "docker container inspect %s --format %s",
        TEMOIN,
        "{{.State.Status}} {{.State.StartedAt}} {{.RestartCount}}",
    )
    assert res.rc == 0, message(
        en=f"the witness container `{TEMOIN}` no longer exists.\n"
           "The brief asks for it to be kept as it is: it carries the trace of "
           "an incident operations must be able to read again. No total makes "
           "up for its loss.",
        fr=f"le conteneur témoin `{TEMOIN}` n'existe plus.\n"
           "L'énoncé demande de le conserver tel quel : il porte la trace d'un "
           "incident que l'exploitation doit pouvoir relire. Aucun total ne "
           "compense sa perte.",
    )
    statut = res.stdout.split()[0] if res.stdout.split() else ""
    assert statut == "exited", message(
        en=f"the witness container `{TEMOIN}` is `{statut}`, not `exited`.\n"
           "The brief asks for it as it is, and it was stopped. Restarting it "
           "is not harmless: a container that runs again can overwrite what it "
           "carried.",
        fr=f"le conteneur témoin `{TEMOIN}` est `{statut}`, et non `exited`.\n"
           "L'énoncé le demande tel quel, et il était arrêté. Le relancer n'est "
           "pas anodin : un conteneur qui repart peut écraser ce qu'il portait.",
    )
    journaux = host.run("docker logs %s", TEMOIN)
    assert journaux.rc == 0 and "annuaire demarre" in (
        journaux.stdout + journaux.stderr
    ), message(
        en=f"the witness container's logs can no longer be read.\n"
           f"  what came back: "
           f"{(journaux.stdout + journaux.stderr).strip()[:200] or '(nothing)'}\n"
           "Keeping the container and keeping its logs are the same "
           "requirement: a container kept without its trace keeps nothing.",
        fr=f"les journaux du conteneur témoin ne se lisent plus.\n"
           f"  ce qui revient : "
           f"{(journaux.stdout + journaux.stderr).strip()[:200] or '(rien)'}\n"
           "Conserver le conteneur et conserver ses journaux sont la même "
           "exigence : un conteneur gardé sans sa trace ne garde rien.",
    )


def test_la_prediction_annonce_le_programme_et_les_arguments_effectifs(
    host,
) -> None:
    """Prédire avant de lancer, et la vérité est recalculée sur la machine.

    Le contrôle ne compare pas à des valeurs écrites ici : il CRÉE le conteneur
    que l'énoncé décrit, sans le démarrer, lit ce que le moteur a retenu, puis
    le retire. C'est la seule façon de ne pas figer dans un test ce que la
    prochaine version du moteur pourrait changer, et c'est aussi ce qui rend le
    contrôle juste : il mesure la prédiction contre le moteur, pas contre
    l'opinion de celui qui a écrit le test.

    LE CONTENEUR PORTE UN NOM UNIQUE et il est retiré dans tous les cas : deux
    exécutions simultanées ne doivent pas se gêner, et un objet laissé derrière
    ferait échouer la photographie du cycle de validation.
    """
    annonce = _lire_prediction(host)
    jetable = f"prediction-{uuid.uuid4().hex[:8]}"
    try:
        cree = host.run(
            "docker create --name %s %s %s", jetable, IMAGE, COMMANDE_A_PREDIRE
        )
        assert cree.rc == 0, message(
            en=f"the lab could not create the reference container to establish "
               f"the truth:\n  {cree.stderr.strip()[:200]}",
            fr=f"le lab n'a pas pu créer le conteneur de référence qui établit "
               f"la vérité :\n  {cree.stderr.strip()[:200]}",
        )
        lu = host.run(
            "docker container inspect %s --format %s",
            jetable,
            "{{.Path}}|{{json .Args}}",
        )
        assert lu.rc == 0, message(
            en="the reference container could not be inspected.",
            fr="le conteneur de référence n'a pas pu être inspecté.",
        )
        brut, args_json = lu.stdout.strip().split("|", 1)
        attendu_path = brut.strip()
        attendu_args = " ".join(json.loads(args_json) or [])
    finally:
        host.run("docker rm -f %s", jetable)

    assert annonce.get("path") == attendu_path, message(
        en=f"the announced program is not the effective one.\n"
           f"  you wrote: {annonce.get('path') or '(nothing)'}\n"
           "The program the engine keeps is the one the image declares as its "
           "entry point, and a command-line argument does not change it.",
        fr=f"le programme annoncé n'est pas le programme effectif.\n"
           f"  vous avez écrit : {annonce.get('path') or '(rien)'}\n"
           "Le programme que le moteur retient est celui que l'image déclare "
           "comme point d'entrée, et un argument de ligne de commande ne le "
           "change pas.",
    )
    assert annonce.get("args", "").split() == attendu_args.split(), message(
        en=f"the announced arguments are not the effective ones.\n"
           f"  you wrote: {annonce.get('args') or '(nothing)'}\n"
           "What is passed on the command line REPLACES what the image declares "
           "by default, it is not added to it.",
        fr=f"les arguments annoncés ne sont pas les arguments effectifs.\n"
           f"  vous avez écrit : {annonce.get('args') or '(rien)'}\n"
           "Ce qui est passé sur la ligne de commande REMPLACE ce que l'image "
           "déclare par défaut, il ne s'y ajoute pas.",
    )


def _compte_apprenant(host) -> str:
    """Le compte humain de la machine, celui qui doit parler au moteur.

    C'est `ansible_user` du point de vue de l'inventaire, donc `ansible` par
    défaut dans ce catalogue. Il est lu et non supposé : une machine dont le
    compte diffère rendrait un verdict faux sur un compte qui n'existe pas.
    """
    for candidat in ("ansible", "student"):
        if host.run("id -u %s", candidat).rc == 0:
            return candidat
    pytest.fail(message(
        en="no usable account was found on this machine.",
        fr="aucun compte exploitable n'a été trouvé sur cette machine.",
    ))


def _interroge(host, nom: str) -> str:
    """Ce que le service répond, lu depuis un voisin de son réseau.

    La réponse est lue, jamais la seule connexion. Et l'interrogation se fait
    par `docker exec` DANS le conteneur lui-même, sur son propre port : l'épreuve
    interdit le port publié, donc l'hôte n'a aucun chemin vers lui.
    """
    dernier = ""
    for _ in range(5):
        res = host.run(
            "docker exec %s nc -w 3 127.0.0.1 %s", nom, str(PORT_SERVICE)
        )
        dernier = res.stdout
        if "salle=" in dernier:
            return dernier
    return dernier


def _lire_prediction(host) -> dict[str, str]:
    """Les deux lignes du formulaire, telles que l'apprenant les a laissées.

    Un formulaire absent ou vide est un contrôle qui échoue, pas une erreur du
    lab : le message le dit sans donner la réponse.
    """
    res = host.run("cat %s", PREDICTION)
    if res.rc != 0:
        pytest.fail(message(
            en=f"the file `{PREDICTION}` cannot be read. The brief asks for two "
               "lines in it, `path=` and `args=`.",
            fr=f"le fichier `{PREDICTION}` ne se lit pas. L'énoncé y demande "
               "deux lignes, `path=` et `args=`.",
        ))
    reponses: dict[str, str] = {}
    for ligne in res.stdout.splitlines():
        trouve = re.match(r"\s*(path|args)\s*=\s*(.*?)\s*$", ligne)
        if trouve:
            reponses[trouve.group(1)] = trouve.group(2)
    if "path" not in reponses:
        pytest.fail(message(
            en=f"no `path=` line was found in `{PREDICTION}`.",
            fr=f"aucune ligne `path=` n'a été trouvée dans `{PREDICTION}`.",
        ))
    return reponses
