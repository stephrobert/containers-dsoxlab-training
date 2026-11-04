"""Un filtre dérivé du défaut, chargé par le noyau, et qui ne desserre rien.

Pourquoi quatre contrôles là où il n'y en avait qu'un
----------------------------------------------------

Le fichier précédent portait **un** `def test_` et six assertions enchaînées.
Il mesurait les trois bonnes choses, et le défaut était la forme : la première
assertion qui tombait masquait les cinq suivantes, et son message tenait en trois
mots, « Un service actif requis ».

Les quatre contrôles mesurent quatre choses indépendantes :

1. le filtre **déclaré** au runtime, et l'absence de `unconfined` ;
2. le mode que le **noyau applique** à PID 1 ;
3. ce que le syscall visé **obtient réellement**, éprouvé par la sonde ;
4. ce que le profil **refuse toujours**, et qui prouve qu'il dérive du défaut.

1 et 2 ne sont pas redondants. Une option `seccomp=` acceptée par Docker sans que
le noyau charge le filtre laisserait tout passer, et `/proc/1/status` le dit par
son champ `Seccomp`. Le troisième ne lit rien, il appelle, et c'est la seule
preuve qu'un filtre chargé fait ce qu'on attend de lui plutôt que d'exister.

LE DÉTAIL QUI REND CE LAB MESURABLE, et qu'il faut garder en tête : sans filtre,
interroger le PID réservé rend `ESRCH`, parce que ce PID n'existe pas. Avec le
filtre attendu, il rend `EPERM`. Les deux erreurs sont différentes, et c'est
cette différence qui distingue un filtre qui mord d'un filtre absent. Un contrôle
qui se contenterait de constater un échec accepterait les deux.

CE QUE LE QUATRIÈME CONTRÔLE A CHANGÉ DANS LE SUJET. Les trois premiers étaient
satisfaits par un profil `defaultAction: SCMP_ACT_ALLOW` portant un seul refus,
que la leçon qualifie de « jamais pour un service » : tout passe, sauf une ligne.
L'apprenant construisait donc un filtre permissif au lieu de resserrer celui du
moteur, et aucun contrôle ne pouvait faire la différence.

Le lab part désormais du **profil par défaut du moteur**, fourni et épinglé dans
`assets/seccomp-defaut.json`, et le quatrième contrôle exige qu'un appel refusé
par défaut le reste. Les trois états se distinguent alors deux à deux, ce qui a
été mesuré le 2026-11-04 sur Docker 29.9.2 :

| profil | `getpgid(sentinelle)` | `unshare -U` |
| --- | --- | --- |
| défaut intact | ESRCH, pas EPERM | refusé |
| permissif, un seul refus | EPERM | **passe** |
| dérivé du défaut | EPERM | refusé |

POURQUOI LE PROFIL EST FOURNI ET NON RELEVÉ SUR LA MACHINE : Docker embarque le
sien **en dur**, il n'existe aucun fichier à copier sur l'hôte. La copie de
référence vient de `moby/profiles`, tag `seccomp/v0.3.0`, dépôt dédié vers lequel
le profil a migré entre moby v28.0.0 et v28.5.2. C'est donc une référence
épinglée, et non le profil exact du moteur local : le lab mesure ce que le profil
**fourni** produit, ce que le scénario dit.
"""

import json

import pytest

from conftest import lab_host, message

LAB = "securite-seccomp"
PROJET = f"dsoxlab-{LAB}"
TRAVAIL = f"/opt/dsoxlab-{LAB}"
SONDE = "/usr/local/bin/syscall-probe"
ATTENDU = "getpgid(sentinel)=EPERM getpgid(0)=allowed getpid=allowed"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _worker(host) -> tuple[str, dict]:
    """Le conteneur du service, ou un échec qui nomme ce qui manque.

    Deux natures mêlées, que les messages distinguent. Qu'un service unique
    tourne et porte son label conditionne toute observation. Que l'image soit
    l'ORIGINALE est une interdiction : remplacer l'image retirerait la sonde au
    lieu de filtrer ses appels.
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
            "exact name before attaching the filter."
        ),
        fr=(
            f"Un seul service `worker` actif est requis dans le projet "
            f"{PROJET}, {len(ids)} trouvé(s). Relancez le projet sous ce nom "
            "exact avant d'attacher le filtre."
        ),
    )
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]

    assert info["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the worker: cleanup removes only what carries it.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le worker : le nettoyage ne retire que ce qui le porte.",
    )

    depart = host.run("cat %s/.probe-image-id", TRAVAIL)
    assert depart.rc == 0 and depart.stdout.strip(), message(
        en=f"Cannot read {TRAVAIL}/.probe-image-id. Not your fault: the check cannot measure anything, report it.",
        fr=f"{TRAVAIL}/.probe-image-id est illisible. Ce n'est pas votre faute : le contrôle ne peut rien mesurer, signalez-le.",
    )
    assert info["Image"] == depart.stdout.strip(), message(
        en=(
            "The worker no longer runs the original probe image. Replacing it "
            "removes the probe instead of filtering its calls."
        ),
        fr=(
            "Le worker ne tourne plus l'image de la sonde d'origine. La "
            "remplacer retire la sonde au lieu de filtrer ses appels."
        ),
    )
    return cid, info


def test_un_filtre_explicite_est_declare_et_aucun_unconfined_ne_subsiste(host):
    """Ce qui a été demandé à Docker."""
    _cid, info = _worker(host)
    options = info["HostConfig"]["SecurityOpt"] or []

    assert any(
        o.startswith("seccomp=") or o.startswith("seccomp:") for o in options
    ), message(
        en=(
            f"The worker declares no explicit seccomp profile.\n"
            f"  SecurityOpt: {options or '[]'}\n"
            "The profile is attached to the service as a runtime option, and the "
            "JSON path must be reachable by the daemon."
        ),
        fr=(
            f"Le worker ne déclare aucun profil seccomp explicite.\n"
            f"  SecurityOpt : {options or '[]'}\n"
            "Le profil s'attache au service comme option de runtime, et le "
            "chemin du JSON doit être atteignable par le démon."
        ),
    )
    laxistes = [o for o in options if "unconfined" in o]
    assert not laxistes, message(
        en=(
            f"The worker still carries {laxistes}. `unconfined` turns the filter "
            "off entirely: an explicit profile alongside it changes nothing."
        ),
        fr=(
            f"Le worker porte encore {laxistes}. `unconfined` désactive le "
            "filtre entièrement : un profil explicite posé à côté n'y change "
            "rien."
        ),
    )


def test_le_noyau_filtre_vraiment_pid_1(host):
    """Ce que le noyau applique, qui est la seule vérité.

    Le champ `Seccomp` de `/proc/1/status` vaut 2 quand un filtre BPF est chargé,
    et 0 quand il n'y en a aucun. Une option retenue par Docker sans filtre
    chargé laisserait tout passer.
    """
    cid, _info = _worker(host)

    lu = host.run("docker exec %s cat /proc/1/status", cid)
    assert lu.rc == 0, message(
        en=f"Cannot read /proc/1/status inside the worker: {lu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"/proc/1/status est illisible dans le worker : {lu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    lignes = [ligne for ligne in lu.stdout.splitlines() if ligne.startswith("Seccomp:")]
    assert lignes, message(
        en="/proc/1/status carries no Seccomp line. Not your fault: the check cannot measure anything, report it.",
        fr="/proc/1/status ne porte aucune ligne Seccomp. Ce n'est pas votre faute : le contrôle ne peut rien mesurer, signalez-le.",
    )
    mode = lignes[0].split()[1]
    assert mode == "2", message(
        en=(
            f"PID 1 announces Seccomp: {mode} instead of 2. A 0 means no filter "
            "is loaded at all: the declaration was retained, the kernel applies "
            "nothing."
        ),
        fr=(
            f"PID 1 annonce Seccomp : {mode} au lieu de 2. Un 0 signifie "
            "qu'aucun filtre n'est chargé : la déclaration a été retenue, le "
            "noyau n'applique rien."
        ),
    )


def test_le_syscall_vise_est_refuse_sans_bloquer_les_autres(host):
    """Ce que le filtre fait réellement, éprouvé par trois appels.

    Les deux contrôles précédents lisent ; celui-ci appelle. La sonde n'effectue
    que des appels en lecture et affiche leur verdict : elle ne modifie rien.

    Les trois appels ensemble font la mesure. Refuser le PID réservé prouve que
    le filtre mord ; laisser passer `getpgid(0)` et `getpid` prouve qu'il ne mord
    pas trop, ce qu'un filtre qui refuserait tout satisferait aussi mal.
    """
    cid, _info = _worker(host)

    sonde = host.run("docker exec %s %s", cid, SONDE)
    assert sonde.rc == 0, message(
        en=(
            f"The probe could not be run: {sonde.stderr.strip()}\n"
            "It must stay executable: a filter that prevents the probe from "
            "starting is not a filter on its calls."
        ),
        fr=(
            f"La sonde n'a pas pu être exécutée : {sonde.stderr.strip()}\n"
            "Elle doit rester exécutable : un filtre qui empêche la sonde de "
            "démarrer n'est pas un filtre sur ses appels."
        ),
    )
    rendu = sonde.stdout.strip()
    assert rendu == ATTENDU, message(
        en=(
            f"The probe reports:\n  {rendu or '(nothing)'}\nexpected:\n"
            f"  {ATTENDU}\n"
            "Watch the errno on the reserved PID: without a filter it is ESRCH, "
            "because that PID does not exist, and with the expected filter it is "
            "EPERM. Both are failures, and only one proves the filter bit."
        ),
        fr=(
            f"La sonde rapporte :\n  {rendu or '(rien)'}\nattendu :\n"
            f"  {ATTENDU}\n"
            "Regardez l'errno sur le PID réservé : sans filtre c'est ESRCH, "
            "parce que ce PID n'existe pas, et avec le filtre attendu c'est "
            "EPERM. Les deux sont des échecs, et un seul prouve que le filtre a "
            "mordu."
        ),
    )


def test_le_profil_ne_desserre_pas_ce_que_le_defaut_refuse(host):
    """La preuve que le profil DÉRIVE du défaut, et ne le remplace pas.

    Les trois contrôles précédents sont tous satisfaits par un profil
    `defaultAction: SCMP_ACT_ALLOW` portant un unique refus : le filtre est
    déclaré, le noyau le charge, et le syscall visé rend bien EPERM. Aucun ne
    voit que TOUT LE RESTE est passé en autorisation.

    `unshare` est le témoin, et il l'est pour une raison nommable. Dans le profil
    par défaut, il ne figure en autorisation que dans un bloc conditionné à
    `CAP_SYS_ADMIN` (`includes: caps`). Un conteneur sans cette capacité ne
    trouve donc `unshare` dans aucune liste permise, et l'appel tombe sur
    `defaultAction: SCMP_ACT_ERRNO`. Mesuré le 2026-11-04 sur Docker 29.9.2 :
    refusé sous le défaut et sous un dérivé du défaut, **accepté** sous un profil
    permissif, et accepté sous `unconfined`.

    Ce contrôle refuse donc deux gestes à la fois : écrire un profil permissif,
    et ajouter une capacité pour contourner le filtre.
    """
    cid, _info = _worker(host)

    essai = host.run("docker exec %s unshare -U true", cid)
    assert essai.rc != 0, message(
        en=(
            "`unshare -U` succeeded inside the worker, so the profile allows "
            "what the engine default refuses.\n"
            "A profile whose defaultAction is SCMP_ACT_ALLOW permits everything "
            "except the lines it denies: it is a blacklist, not a policy, and "
            "the lesson rules it out for a service. Derive the supplied "
            "reference profile instead of writing a new one, and add no "
            "capability."
        ),
        fr=(
            "`unshare -U` a réussi dans le worker, donc le profil autorise ce que "
            "le défaut du moteur refuse.\n"
            "Un profil dont le defaultAction vaut SCMP_ACT_ALLOW permet tout sauf "
            "les lignes qu'il refuse : c'est une liste noire, pas une politique, "
            "et la leçon l'exclut pour un service. Dérivez le profil de référence "
            "fourni au lieu d'en écrire un neuf, et n'ajoutez aucune capacité."
        ),
    )
