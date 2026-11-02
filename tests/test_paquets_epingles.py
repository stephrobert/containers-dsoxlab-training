"""Méta-test du dépôt : la VERSION du moteur est épinglée, et une seule fois.

La règle de version du projet est explicite : « la version s'épingle sur la
combinaison réellement testée, et jamais `latest` ni `state: present` nu. Sans
épinglage, un verdict de validation ne dit plus sur quoi il portait. »

CE QUI A DÉCLENCHÉ CE TEST, le 2026-11-02. Une relecture a relevé que **75**
`setup.yaml` installent `docker-ce` en `state: present`, sans version. Le
constat est exact sur la forme, et la mesure sur la machine montre que la
garantie est pourtant tenue :

    docker-ce            5:29.9.2-1~debian.13~trixie   installé
    docker-ce-cli        5:29.9.2-1~debian.13~trixie   installé
    containerd.io        2.4.2-3~debian.13~trixie      installé
    docker-buildx-plugin 0.38.1-1~debian.13~trixie     installé
    docker-compose-plugin 5.6.1-1~debian.13~trixie     installé

    apt-mark showhold -> les cinq y sont

`infra/bootstrap.yaml` installe ces versions exactes et les met en `hold` AVANT
qu'aucun lab ne tourne. Un `state: present` sur un paquet déjà installé ne fait
rien, et un paquet retenu ne bouge pas même sur un `apt upgrade`. Les 75
`setup.yaml` ne peuvent donc pas changer la version.

POURQUOI LES 75 SETUPS N'ÉPINGLENT PAS, ET POURQUOI C'EST LE BON CHOIX
----------------------------------------------------------------------

Parce qu'y écrire la version la recopierait **soixante-quinze fois**. Le projet
s'interdit explicitement ce genre de duplication, et pour une raison qu'il a
payée : « une valeur qu'il faut penser à recopier finit toujours par mentir ».
Au premier passage à la version suivante, il y aurait soixante-quinze endroits à
changer, et il suffirait d'en oublier un pour qu'un lab mesure autre chose que
les autres sans que rien ne le dise.

La garantie vit donc à UN seul endroit, et ce fichier la défend. C'est le même
raisonnement que pour la version de `dsoxlab`, qui fait autorité dans
`pyproject.toml` seul.

CE QUE CE TEST NE PRÉTEND PAS COUVRIR
-------------------------------------

Il ne dit rien d'un lab joué sur une machine qui n'aurait pas reçu le bootstrap.
Ce cas n'existe pas aujourd'hui, puisque `dsoxlab provision` passe toujours par
`infra/`, mais il n'est pas interdit par construction. Si un jour un lab devait
s'installer seul, il lui faudrait son propre épinglage, et ce fichier devrait
être relu.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
BOOTSTRAP = RACINE / "infra" / "bootstrap.yaml"

# Les paquets dont la version décide de ce que les attestations ont mesuré. Le
# moteur, son client, son runtime, et les deux greffons que des labs emploient.
PAQUETS_DECISIFS = {
    "docker-ce",
    "docker-ce-cli",
    "containerd.io",
    "docker-buildx-plugin",
    "docker-compose-plugin",
}

# Une version Debian épinglée : un numéro, éventuellement une époque, et une
# révision. Ce qui est refusé est le flou : vide, `latest`, ou un simple `*`.
VERSION_EXACTE = re.compile(r"^(\d+:)?\d[\w.+~-]*$")


@pytest.fixture(scope="module")
def jeu() -> dict:
    """Le premier play du bootstrap, chargé une fois.

    Chargé, et non lu ligne par ligne : ce qui compte est ce que le moteur de
    playbook verra, pas ce que le fichier a l'air de dire. Un `docker_versions`
    commenté ou mal indenté n'apparaîtrait pas ici, et c'est exactement ce que
    ce test doit attraper.
    """
    assert BOOTSTRAP.is_file(), (
        f"{BOOTSTRAP} est introuvable : c'est lui qui porte l'épinglage, et son "
        "absence rendrait toute version possible."
    )
    charge = yaml.safe_load(BOOTSTRAP.read_text(encoding="utf-8"))
    assert isinstance(charge, list) and charge, (
        "le bootstrap n'est pas un playbook : il ne peut rien garantir."
    )
    return charge[0]


def test_le_bootstrap_declare_une_version_pour_chaque_paquet_decisif(
    jeu: dict,
) -> None:
    """Les paquets qui décident du verdict portent tous une version.

    Un paquet qui manque à cette liste n'est pas forcément une faute : il peut
    avoir été retiré du socle à dessein. Mais il doit alors disparaître de
    `PAQUETS_DECISIFS` ici, et ce test force à le dire au lieu de le laisser
    glisser.
    """
    versions = (jeu.get("vars") or {}).get("docker_versions")
    assert isinstance(versions, dict) and versions, (
        "`docker_versions` n'est pas déclaré dans les variables du bootstrap.\n"
        "Sans lui, les paquets s'installent à la version que le dépôt de "
        "l'éditeur sert ce jour-là, et un verdict de validation ne dit plus sur "
        "quoi il portait."
    )
    manquants = sorted(PAQUETS_DECISIFS - set(versions))
    assert not manquants, (
        "ces paquets décident de ce que les attestations mesurent, et le "
        "bootstrap ne leur donne aucune version :\n"
        + "\n".join(f"  {p}" for p in manquants)
    )


def test_chaque_version_est_exacte_et_non_flottante(jeu: dict) -> None:
    """Une version épinglée est un numéro, pas une intention.

    `latest`, une chaîne vide ou un joker ne sont pas des épinglages : ils
    laissent le dépôt de l'éditeur décider, ce qui est précisément ce que la
    règle de version interdit.
    """
    versions = (jeu.get("vars") or {}).get("docker_versions") or {}
    flottantes = {
        paquet: version
        for paquet, version in versions.items()
        if not VERSION_EXACTE.match(str(version).strip())
    }
    assert not flottantes, (
        "ces versions ne sont pas des versions exactes :\n"
        + "\n".join(f"  {p} = {v!r}" for p, v in sorted(flottantes.items()))
        + "\nUn épinglage est un numéro. Tout le reste laisse le dépôt de "
        "l'éditeur décider."
    )


def test_les_paquets_epingles_sont_retenus(jeu: dict) -> None:
    """L'épinglage sans le `hold` ne survit pas à une mise à jour.

    C'EST LE CONTRÔLE QUI COMPTE LE PLUS DE CE FICHIER. Installer une version
    exacte fixe l'instant de l'installation ; seul le `hold` empêche un
    `apt upgrade`, lancé par n'importe qui ou par une mise à jour automatique,
    de déplacer le moteur sous les pieds des attestations.

    Et c'est aussi ce qui rend inoffensif le `state: present` des setups de
    labs : un paquet retenu ne bouge pas, quoi qu'on lui demande.
    """
    taches = jeu.get("tasks") or []
    retenus = None
    for tache in taches:
        selection = tache.get("ansible.builtin.dpkg_selections") or {}
        if str(selection.get("selection", "")).strip() == "hold":
            retenus = tache
            break
    assert retenus is not None, (
        "aucune tâche ne met les paquets du moteur en `hold`.\n"
        "Sans cela, un `apt upgrade` déplace silencieusement le moteur sur "
        "lequel les attestations ont été mesurées, et le relevé devient faux "
        "sans que personne ne touche au dépôt."
    )
    # ET LE HOLD PORTE SUR LA LISTE ÉPINGLÉE, et non sur un paquet nommé à la
    # main : sans cela, ajouter un paquet à `docker_versions` l'épinglerait sans
    # le retenir, et le défaut serait invisible.
    boucle = str(retenus.get("loop", ""))
    assert "docker_versions" in boucle, (
        "le `hold` ne boucle pas sur `docker_versions`.\n"
        f"  il boucle sur : {boucle or '(rien)'}\n"
        "Un paquet ajouté à l'épinglage serait alors installé à la bonne "
        "version et laissé libre de bouger."
    )


def test_l_epinglage_ne_vit_qu_a_un_seul_endroit() -> None:
    """La version du moteur ne se recopie pas dans les labs, et c'est voulu.

    Si un `setup.yaml` se met à épingler `docker-ce` lui-même, la valeur existe
    à deux endroits, et le projet a payé ce défaut assez souvent pour en avoir
    fait une règle : « une valeur qu'il faut penser à recopier finit toujours
    par mentir ». Au passage à la version suivante, il faudrait changer tous les
    endroits, et il suffirait d'en oublier un.

    Ce test n'interdit donc pas l'épinglage dans un lab par principe : il
    interdit qu'il apparaisse SANS QUE PERSONNE NE L'AIT DÉCIDÉ. Un lab qui
    aurait une vraie raison d'épingler sa propre version devra être ajouté à
    l'exception ci-dessous, ce qui oblige à écrire pourquoi.
    """
    # Aucun lab n'a aujourd'hui de raison d'épingler sa propre version du
    # moteur : tous tournent sur l'infra, qui l'a déjà fait.
    EXCEPTIONS: set[str] = set()

    fautifs = []
    for setup in sorted((RACINE / "labs").glob("*/setup.yaml")):
        if setup.parent.name in EXCEPTIONS:
            continue
        for numero, ligne in enumerate(
            setup.read_text(encoding="utf-8").splitlines(), 1
        ):
            if ligne.lstrip().startswith("#"):
                continue
            # Une version épinglée s'écrit `docker-ce=5:29...` ou
            # `docker-ce: "5:29..."`. On cherche le signe suivi d'un chiffre,
            # ce qui écarte les simples mentions du nom du paquet.
            if re.search(r"\bdocker-ce(-cli)?\s*[=:]\s*['\"]?\d", ligne):
                fautifs.append(f"{setup.parent.name}/setup.yaml:{numero}")

    assert not fautifs, (
        "ces labs épinglent eux-mêmes la version du moteur :\n"
        + "\n".join(f"  {f}" for f in fautifs)
        + "\nLa version vit dans `infra/bootstrap.yaml`, et seulement là. La "
        "recopier dans un lab crée un second endroit à maintenir, et le jour où "
        "l'un des deux est oublié, un lab mesure autre chose que les autres "
        "sans que rien ne le dise.\n"
        "Si ce lab a une vraie raison d'épingler seul, ajoutez-le aux "
        "`EXCEPTIONS` de ce test, avec le pourquoi."
    )


def test_le_releve_dit_la_version_sur_laquelle_il_porte() -> None:
    """Un verdict qui ne dit pas sa version n'est pas un fait, c'est un souvenir.

    C'est la raison d'être de la règle d'épinglage, et elle est satisfaite par
    un autre mécanisme que l'épinglage lui-même : chaque attestation consigne la
    version du moteur sur laquelle elle a été mesurée. C'est ce qui permet de
    dire, des mois plus tard, sur quoi portait un « VALIDE ».

    Ce contrôle est ici et non ailleurs parce qu'il complète les précédents :
    l'épinglage garantit que la mesure PORTE sur une version connue, et le
    relevé garantit qu'elle la DIT.
    """
    import json

    releve = RACINE / "validation-labs.json"
    if not releve.is_file():
        pytest.skip("aucun relevé d'attestation dans ce dépôt")
    labs = json.loads(releve.read_text(encoding="utf-8"))
    muets = sorted(
        nom for nom, mesure in labs.items()
        if isinstance(mesure, dict) and not str(mesure.get("docker", "")).strip()
    )
    assert not muets, (
        "ces attestations ne disent pas sur quelle version du moteur elles ont "
        "été mesurées :\n" + "\n".join(f"  {n}" for n in muets[:10])
        + "\nUn comportement sans sa version n'est pas un fait, c'est un "
        "souvenir."
    )
