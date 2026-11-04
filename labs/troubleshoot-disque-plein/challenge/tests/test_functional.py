"""De l'espace vraiment récupéré, sans perdre le reçu ni déplacer le plafond.

Pourquoi deux contrôles seulement, et pas davantage
---------------------------------------------------

Le fichier précédent portait **un** `def test_` et dix assertions enchaînées. Il
mesurait beaucoup de bonnes choses, mais la première qui tombait masquait les
neuf suivantes, et son premier message tenait en trois mots : « Un service actif
requis ».

Le découpage s'arrête à deux, et c'est une contrainte du cycle de validation, non
un choix de confort. Le cycle exige **0 avant le travail puis 100 après** : un
contrôle qui passe sur l'état initial donnerait des points pour rien et rendrait
le lab ROUGE. Or trois des exigences de ce lab sont déjà satisfaites au départ :

- le conteneur d'origine existe, et il ne faut pas le recréer ;
- le sandbox est un tmpfs de 16 Mio, et il ne faut pas l'agrandir ;
- `keep.txt` est présent, et il ne faut pas le perdre.

Ce sont des exigences de **préservation**. Elles ne peuvent pas devenir des
contrôles séparés, et elles ne sont pas pour autant facultatives : elles vivent
dans le garde-fou commun, qui refuse la triche sans rien accorder gratuitement.
Un apprenant qui recrée le conteneur pour « nettoyer » ses données, ou qui
agrandit le sandbox au lieu de récupérer de l'espace, est donc refusé, et le
message lui dit laquelle des deux interdictions il a franchie.

La seule moitié de « préservation » qui porte sur un geste de l'apprenant,
`keep.txt`, est vérifiée **dans** le premier contrôle, à côté du retrait de
`fill.bin` : ce sont les deux faces d'une même exigence, récupérer de l'espace
sans jeter ce qui compte. Les séparer les rendrait toutes deux mesurables à vide.
"""

from __future__ import annotations

import json
import uuid

import pytest

from conftest import lab_host, message

LAB = "troubleshoot-disque-plein"
TRAVAIL = f"/opt/dsoxlab-{LAB}"
SANDBOX = "/sandbox"
PLAFOND_KIO = 16384
MEMOIRE = 67108864
RECU = "keep-this-receipt\n"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _worker(host) -> str:
    """Le conteneur du worker, ou un échec qui nomme l'interdiction franchie.

    Ce garde-fou mêle deux natures, et les messages les distinguent. Qu'un
    service unique tourne et porte son label ne dépend pas entièrement de
    l'apprenant : sans cela, rien ne peut être observé. Qu'il s'agisse du
    conteneur D'ORIGINE et que le sandbox n'ait pas grandi sont au contraire
    deux interdictions explicites du scénario, et les franchir est une faute.
    """
    trouve = host.run(
        "docker ps -q "
        "--filter label=com.docker.compose.project=dsoxlab-%s "
        "--filter label=com.docker.compose.service=worker",
        LAB,
    )
    ids = trouve.stdout.split()
    assert trouve.rc == 0 and len(ids) == 1, message(
        en=(
            f"Exactly one running `worker` service is required in project "
            f"dsoxlab-{LAB}, found {len(ids)}."
        ),
        fr=(
            f"Un seul service `worker` actif est requis dans le projet "
            f"dsoxlab-{LAB}, {len(ids)} trouvé(s)."
        ),
    )
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]

    assert info["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the worker.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le worker.",
    )

    # LE CONTENEUR D ORIGINE, et c'est une interdiction du scénario : recréer le
    # conteneur efface ses données au lieu de récupérer de l'espace. L'empreinte
    # a été posée par le setup en lecture seule.
    depart = host.run("cat %s/.starter-id", TRAVAIL)
    assert depart.rc == 0 and depart.stdout.strip(), message(
        en=f"Cannot read {TRAVAIL}/.starter-id. Not your fault: the check cannot measure anything, report it.",
        fr=f"{TRAVAIL}/.starter-id est illisible. Ce n'est pas votre faute : le contrôle ne peut rien mesurer, signalez-le.",
    )
    assert info["Id"] == depart.stdout.strip(), message(
        en=(
            "This is not the original container. Recreating it erases its data "
            "instead of reclaiming space, and the scenario forbids it."
        ),
        fr=(
            "Ce n'est pas le conteneur d'origine. Le recréer efface ses données "
            "au lieu de récupérer de l'espace, et le scénario l'interdit."
        ),
    )

    config = info["HostConfig"]
    assert SANDBOX in (config["Tmpfs"] or {}), message(
        en=f"The worker no longer declares a tmpfs on {SANDBOX}: it must stay a sandbox, never a host partition.",
        fr=f"Le worker ne déclare plus de tmpfs sur {SANDBOX} : il doit rester un bac à sable, jamais une partition hôte.",
    )
    assert config["Memory"] == MEMOIRE and config["MemorySwap"] == MEMOIRE, message(
        en=f"The memory guards changed (Memory={config['Memory']}, MemorySwap={config['MemorySwap']}): keep them at {MEMOIRE}.",
        fr=f"Les garde-fous mémoire ont changé (Memory={config['Memory']}, MemorySwap={config['MemorySwap']}) : conservez-les à {MEMOIRE}.",
    )

    # LE PLAFOND N A PAS BOUGÉ, l'autre interdiction du scénario. On lit ce que
    # le conteneur VOIT, et non la déclaration : c'est le système qui fait foi.
    vu = host.run("docker exec %s sh -c 'stat -f -c %%T %s; df -Pk %s'", cid, SANDBOX, SANDBOX)
    assert vu.rc == 0 and vu.stdout.strip(), message(
        en=f"Cannot inspect {SANDBOX} inside the worker: {vu.stderr.strip()}. Not your fault if it runs, report it.",
        fr=f"{SANDBOX} est inspectable dans le worker : {vu.stderr.strip()}. Ce n'est pas votre faute s'il tourne, signalez-le.",
    )
    lignes = vu.stdout.splitlines()
    assert lignes[0].strip() == "tmpfs", message(
        en=f"{SANDBOX} is a {lignes[0].strip()} filesystem, not a tmpfs. Never write into a host partition.",
        fr=f"{SANDBOX} est un système de fichiers {lignes[0].strip()} et non un tmpfs. N'écrivez jamais dans une partition hôte.",
    )
    taille = int(lignes[-1].split()[1])
    assert taille == PLAFOND_KIO, message(
        en=(
            f"{SANDBOX} now holds {taille} kiB instead of {PLAFOND_KIO}. Reclaiming "
            "space is not raising the ceiling, and the scenario forbids resizing it."
        ),
        fr=(
            f"{SANDBOX} porte maintenant {taille} kio au lieu de {PLAFOND_KIO}. "
            "Récupérer de l'espace n'est pas relever le plafond, et le scénario "
            "interdit de le redimensionner."
        ),
    )
    return cid


def test_le_remplissage_jetable_a_ete_retire_sans_perdre_le_recu(host):
    """Les deux faces d'une même exigence, et c'est pourquoi elles vont ensemble.

    Retirer le remplissage sans le reçu, c'est réussir ; retirer les deux, c'est
    vider le sandbox, ce qui récupère de l'espace en détruisant ce qu'on
    protégeait. Séparées, ces deux moitiés seraient mesurables à vide : le reçu
    est présent dès le départ.
    """
    cid = _worker(host)

    jetable = host.run("docker exec %s sh -c 'test ! -e %s/fill.bin'", cid, SANDBOX)
    assert jetable.rc == 0, message(
        en=f"{SANDBOX}/fill.bin is still there: the disposable filler is what holds the space.",
        fr=f"{SANDBOX}/fill.bin est encore là : c'est le remplissage jetable qui occupe la place.",
    )

    recu = host.run("docker exec %s cat %s/keep.txt", cid, SANDBOX)
    assert recu.rc == 0, message(
        en=(
            f"{SANDBOX}/keep.txt has disappeared. Emptying the sandbox does reclaim "
            "space, by destroying what the exercise asked you to protect."
        ),
        fr=(
            f"{SANDBOX}/keep.txt a disparu. Vider le bac à sable récupère bien de "
            "l'espace, en détruisant ce que l'exercice demandait de protéger."
        ),
    )
    assert recu.stdout == RECU, message(
        en=f"{SANDBOX}/keep.txt no longer holds its original content: it was rewritten rather than preserved.",
        fr=f"{SANDBOX}/keep.txt ne porte plus son contenu d'origine : il a été réécrit plutôt que préservé.",
    )


def test_l_espace_recupere_permet_une_ecriture_reelle(host):
    """L'espace est-il vraiment disponible ? Une écriture le dit, pas un `df`.

    Le setup garantit l'état de départ en exigeant qu'une sonde de 4 Kio ÉCHOUE :
    le sandbox est plein, et ce contrôle refuse donc avant tout travail. Après,
    une écriture d'un Mio doit aboutir et peser réellement un Mio, parce qu'un
    `dd` peut rendre 0 en ayant écrit moins que demandé.
    """
    cid = _worker(host)
    nom = f"{SANDBOX}/dsoxlab-check-{uuid.uuid4().hex}"

    try:
        ecrit = host.run("timeout 5 docker exec %s dd if=/dev/zero of=%s bs=1M count=1", cid, nom)
        assert ecrit.rc == 0, message(
            en=(
                "A real 1 MiB write into the sandbox still fails: the space has not "
                "been reclaimed. Removing the filler is what frees it."
            ),
            fr=(
                "Une vraie écriture d'un Mio dans le bac à sable échoue encore : "
                "l'espace n'a pas été récupéré. C'est le retrait du remplissage qui "
                "le libère."
            ),
        )
        pese = host.run("docker exec %s stat -c %%s %s", cid, nom)
        assert pese.rc == 0 and pese.stdout.strip() == "1048576", message(
            en=(
                f"The probe weighs {pese.stdout.strip()} bytes instead of 1048576: "
                "the write returned success without putting everything down."
            ),
            fr=(
                f"La sonde pèse {pese.stdout.strip()} octets au lieu de 1048576 : "
                "l'écriture a rendu un succès sans tout déposer."
            ),
        )
    finally:
        # ON NE RETIRE QUE SA PROPRE SONDE : le validateur photographie le
        # moteur, et un test qui nettoie large efface le travail de l'apprenant.
        host.run("docker exec %s rm -f %s", cid, nom)
