"""Tests fonctionnels du lab docker-anatomie-dune-image : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'une image est un EMPILEMENT de couches, que ces
couches se partagent entre images, et qu'elle porte en plus une configuration
qui n'est pas dans son contenu. Le lab précédent interrogeait un conteneur en
marche ; celui-ci interroge une image au repos.

LE PIÈGE EST MESURÉ, PAS SUPPOSÉ. `greffe:1.0` porte CINQ couches pour trois
instructions qui semblent en créer une chacune, plus la base. La cinquième
vient de `WORKDIR`, qui crée le répertoire quand il n'existe pas. Relevé sur
docker.lab le 2026-10-30. C'est ce qui rend le lab utile : lire le Dockerfile
ne suffit pas, et un apprenant qui compte les instructions se trompe de une.

LE PRINCIPE QUI TIENT TOUT LE FICHIER : LA VÉRITÉ EST RECALCULÉE ICI, au moment
de la notation, en interrogeant le moteur. Aucun nombre attendu n'est écrit
dans ce fichier, et c'est volontaire : le jour où l'image de base gagnera une
couche, ces contrôles suivront d'eux-mêmes au lieu de devenir faux.

UNE HONNÊTETÉ SUR LA RÉPÉTABILITÉ. Les trois premières réponses ne changent pas
d'un passage à l'autre, parce qu'elles décrivent une construction fixe : un
apprenant qui a déjà joué le lab pourrait les recopier. La quatrième, elle, est
tirée au hasard à chaque `run`. Le lab n'est pas un jeu de devinettes, et
recopier les trois nombres suppose de les avoir trouvés une première fois.

CE QU'ON NE MESURE PAS. Jamais la commande. `docker image inspect`, `docker
history` et `docker image ls --tree` mènent au même compte ; la révision se lit
par `inspect` comme par `docker image inspect --format` sur un champ précis.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
tout ce qui suit est déjà élevé, et les contrôles mesurent le moteur sans
dépendre des groupes du compte, ce qui est le sujet d'un autre lab.
"""

from __future__ import annotations

import re

import pytest

from conftest import lab_host, message

IMAGE_V1 = "greffe:1.0"
IMAGE_V2 = "greffe:2.0"
ATELIER = "/opt/lab-anatomie"
REPONSES = f"{ATELIER}/reponses.txt"
ETIQUETTE_REVISION = "org.opencontainers.image.revision"

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


def _couches(host, image: str) -> list[str]:
    """Les couches d'une image, telles que le moteur les énumère.

    `{{json .RootFS.Layers}}` plutôt qu'un `range` : une seule ligne, et les
    empreintes s'en extraient sans dépendre d'un séparateur.
    """
    res = host.run("docker image inspect %s --format %s", image, "{{json .RootFS.Layers}}")
    if res.rc != 0:
        pytest.fail(message(
            en=f"image {image} is not on the machine any more: {res.stderr.strip()}\n"
               "Both images are needed by these checks. Replay the lab with "
               "`dsoxlab reset`.",
            fr=f"l'image {image} n'est plus sur la machine : {res.stderr.strip()}\n"
               "Les deux images sont nécessaires à ces contrôles. Rejouez le "
               "lab avec `dsoxlab reset`.",
        ))
    return re.findall(r"sha256:[0-9a-f]+", res.stdout)


def _lire_reponses(host) -> dict[str, str]:
    """Le formulaire, réduit à ses paires clé=valeur.

    Tolérant sur la forme (espaces, lignes vides, commentaires, casse de la
    clé), strict sur le fond : c'est le contenu qui est noté, pas la mise en
    page.
    """
    f = host.file(REPONSES)
    if not f.exists:
        pytest.fail(message(
            en=f"{REPONSES} is missing. The mission asks for four lines in it: "
               "couches=, partagees=, propres= and revision=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire quatre "
               "lignes : couches=, partagees=, propres= et revision=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def _entier(valeur: str) -> int | None:
    """La réponse lue comme un nombre, ou None si elle n'en est pas un."""
    try:
        return int(valeur.strip())
    except ValueError:
        return None


def test_la_reponse_compte_les_couches_de_l_image(host) -> None:
    """Le nombre de couches, que la lecture du Dockerfile ne donne pas.

    C'est le contrôle qui porte la leçon : toutes les instructions ne créent
    pas une couche, et `WORKDIR` en crée une sans qu'on s'y attende. Un
    apprenant qui compte les instructions se trompe, et le message le lui dit
    plutôt que de le laisser recompter.
    """
    attendu = len(_couches(host, IMAGE_V1))
    if attendu == 0:
        pytest.skip(message(
            en=f"the engine reports no layer for {IMAGE_V1}: the setup did "
               "not finish",
            fr=f"le moteur n'annonce aucune couche pour {IMAGE_V1} : le setup "
               "n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("couches", "")
    assert annonce, message(
        en="the `couches=` line is empty. It expects the number of layers of "
           f"{IMAGE_V1}, as the engine counts them.",
        fr="la ligne `couches=` est vide. Elle attend le nombre de couches de "
           f"{IMAGE_V1}, tel que le moteur les compte.",
    )
    nombre = _entier(annonce)
    assert nombre is not None, message(
        en=f"`couches={annonce}` is not a number. A plain integer is expected.",
        fr=f"`couches={annonce}` n'est pas un nombre. Un entier simple est "
           "attendu.",
    )
    assert nombre == attendu, message(
        en=f"{IMAGE_V1} does not carry {nombre} layers.\n"
           "Counting the Dockerfile instructions is not enough: some create no "
           "layer at all, and one of them creates a layer without looking like "
           "it. Ask the engine rather than the file.",
        fr=f"{IMAGE_V1} ne porte pas {nombre} couches.\n"
           "Compter les instructions du Dockerfile ne suffit pas : certaines "
           "ne créent aucune couche, et l'une en crée une sans en avoir l'air. "
           "Demandez au moteur plutôt qu'au fichier.",
    )


def test_la_reponse_compte_les_couches_partagees(host) -> None:
    """Le partage, qui explique pourquoi les images ne s'additionnent pas.

    Les deux constructions ont les mêmes premières instructions et le même
    contexte : leurs premières couches sont donc les MÊMES objets, stockés une
    seule fois. C'est la raison pour laquelle dix images d'un même socle ne
    pèsent pas dix fois le socle.
    """
    communes = set(_couches(host, IMAGE_V1)) & set(_couches(host, IMAGE_V2))
    if not communes:
        pytest.skip(message(
            en="the two images share no layer: the setup did not finish, or "
               "the builds diverged",
            fr="les deux images ne partagent aucune couche : le setup n'a pas "
               "abouti, ou les constructions ont divergé",
        ))

    annonce = _lire_reponses(host).get("partagees", "")
    assert annonce, message(
        en="the `partagees=` line is empty. It expects how many layers the two "
           "images have IN COMMON.",
        fr="la ligne `partagees=` est vide. Elle attend combien de couches les "
           "deux images ont EN COMMUN.",
    )
    nombre = _entier(annonce)
    assert nombre is not None, message(
        en=f"`partagees={annonce}` is not a number. A plain integer is expected.",
        fr=f"`partagees={annonce}` n'est pas un nombre. Un entier simple est "
           "attendu.",
    )
    assert nombre == len(communes), message(
        en=f"the two images do not share {nombre} layers.\n"
           "A layer is shared when the instruction that produced it is "
           "identical, in the same order, on the same context. Compare the two "
           "lists of layers rather than the two Dockerfiles.",
        fr=f"les deux images ne partagent pas {nombre} couches.\n"
           "Une couche est partagée quand l'instruction qui l'a produite est "
           "identique, dans le même ordre, sur le même contexte. Comparez les "
           "deux listes de couches plutôt que les deux Dockerfile.",
    )


def test_la_reponse_compte_les_couches_propres_a_la_seconde_image(host) -> None:
    """Ce que la seconde image ajoute, et elle seule.

    Le complément du contrôle précédent, et il n'en est pas une redite : il se
    mesure dans l'autre sens, et c'est ce chiffre qui dit le coût réel d'une
    variante. Une image dérivée ne coûte que ses couches propres.
    """
    propres = set(_couches(host, IMAGE_V2)) - set(_couches(host, IMAGE_V1))
    if not propres:
        pytest.skip(message(
            en=f"{IMAGE_V2} has no layer of its own: the setup did not finish",
            fr=f"{IMAGE_V2} n'a aucune couche propre : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("propres", "")
    assert annonce, message(
        en="the `propres=` line is empty. It expects how many layers of "
           f"{IMAGE_V2} are absent from {IMAGE_V1}.",
        fr="la ligne `propres=` est vide. Elle attend combien de couches de "
           f"{IMAGE_V2} sont absentes de {IMAGE_V1}.",
    )
    nombre = _entier(annonce)
    assert nombre is not None, message(
        en=f"`propres={annonce}` is not a number. A plain integer is expected.",
        fr=f"`propres={annonce}` n'est pas un nombre. Un entier simple est "
           "attendu.",
    )
    assert nombre == len(propres), message(
        en=f"{IMAGE_V2} does not carry {nombre} layers of its own.\n"
           "This is the count in the other direction: the layers it has and "
           f"{IMAGE_V1} does not. It is what a variant really costs.",
        fr=f"{IMAGE_V2} ne porte pas {nombre} couches propres.\n"
           "C'est le compte dans l'autre sens : les couches qu'elle a et que "
           f"{IMAGE_V1} n'a pas. C'est ce que coûte réellement une variante.",
    )


def test_la_reponse_nomme_la_revision_portee_par_la_configuration(host) -> None:
    """Une image porte une configuration, qui n'est pas son contenu.

    La révision a été posée en ligne de commande à la construction : elle n'est
    dans aucun Dockerfile de la machine, et elle n'apparaît pas dans
    l'historique de l'image, ce qui a été vérifié. Elle n'existe que dans la
    configuration, et elle est tirée au hasard à chaque passage.
    """
    res = host.run(
        "docker image inspect %s --format %s",
        IMAGE_V1,
        '{{index .Config.Labels "' + ETIQUETTE_REVISION + '"}}',
    )
    attendu = res.stdout.strip()
    if res.rc != 0 or not attendu or attendu == "<no value>":
        pytest.skip(message(
            en=f"{IMAGE_V1} carries no `{ETIQUETTE_REVISION}` label: the setup "
               "did not finish",
            fr=f"{IMAGE_V1} ne porte aucune étiquette `{ETIQUETTE_REVISION}` : "
               "le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("revision", "")
    assert annonce, message(
        en="the `revision=` line is empty. It is written in no file on this "
           "machine, and it is not in the image history either: it lives in "
           "the image's CONFIGURATION, next to its environment and its default "
           "command.",
        fr="la ligne `revision=` est vide. Elle n'est écrite dans aucun fichier "
           "de cette machine, et elle n'est pas non plus dans l'historique de "
           "l'image : elle vit dans sa CONFIGURATION, à côté de son "
           "environnement et de sa commande par défaut.",
    )
    assert annonce == attendu, message(
        en=f"the announced revision is not the one {IMAGE_V1} carries.\n"
           f"  you wrote : {annonce}\n"
           "A fresh revision is drawn at each run, so a value from a previous "
           "pass is no longer valid.",
        fr=f"la révision annoncée n'est pas celle que porte {IMAGE_V1}.\n"
           f"  vous avez écrit : {annonce}\n"
           "Une révision neuve est tirée à chaque passage : une valeur relevée "
           "lors d'un passage précédent n'est plus valable.",
    )
