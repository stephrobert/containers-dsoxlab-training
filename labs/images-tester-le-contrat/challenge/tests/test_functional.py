"""Tests fonctionnels du lab images-tester-le-contrat : six contrôles de poids égal.

CE QUE CE LAB NOTE, ET CE QU'IL NE NOTE PAS. Il ne note pas une image : il note
un SCRIPT, `tester-contrat.sh`, que l'apprenant écrit. Chaque contrôle JOUE ce
script contre des images et lit son code de sortie : 0 pour une image conforme,
autre chose pour une image qui ne l'est pas.

POURQUOI UN JEU D'IMAGES, ET PAS UNE SEULE. Un script qui rend toujours 0
accepte tout, un script qui rend toujours 1 refuse tout, et une seule image ne
distingue ni l'un ni l'autre d'un vrai test. Le jeu mêle donc une image
conforme et des images cassées de natures différentes : démarrage, configuration,
privilèges, arrêt. Un script qui ne contrôle que le démarrage passe le premier
groupe et échoue aux trois autres, ce qui fait six notes distinctes plutôt
qu'un tout-ou-rien.

LES IMAGES QUE L'APPRENANT N'A PAS VUES sont construites ICI, au moment de
noter, à partir de l'image conforme : une ligne ou deux de Dockerfile par
défaut. Elles ne sont posées nulle part avant, et elles sont retirées à la
fin. Seules `guichet:1.0` (conforme) et `guichet:0.9` (cassée) existent dès le
setup, parce que l'énoncé les nomme.

LA CONDITION QUI DONNE UN SENS AUX REFUS. Un script absent rend un code non nul,
un script qui refuse tout aussi : ces deux scripts « refusent » donc les images
cassées sans rien mesurer. Chaque contrôle de refus exige donc d'abord que le
script ACCEPTE l'image conforme. Sans cela, le refus ne prouve rien, et le
contrôle le dit au lieu de le créditer.

CE QUI N'EST PAS NOTÉ : les messages du script, leur formulation, l'ordre de ses
contrôles, sa durée tant qu'elle reste raisonnable. Un script écrit en shell,
en Python ou autrement, du moment qu'il s'exécute avec `bash`, est noté de la
même façon.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

ATELIER = "/opt/dsoxlab-images-tester-le-contrat"
SCRIPT = f"{ATELIER}/tester-contrat.sh"
CONFORME = "guichet:1.0"
CONNUE_CASSEE = "guichet:0.9"
PREFIXE = "dsoxlab-images-tester-le-contrat-"

# L'hôte du `meta.yml`, et le même que `runtime.targets[].host` du lab.yaml.
TARGET_HOST = "docker.lab"

# Au-delà, le script est jugé trop lent pour un test : l'image la plus lente à
# refuser, celle qui ignore SIGTERM, demande une dizaine de secondes de plus
# qu'une image conforme.
LIMITE_S = 150

# Les images que l'apprenant n'a pas vues. Chaque entrée est (nom, lignes de
# Dockerfile ajoutées à `FROM guichet:1.0`). Les `sed` modifient le programme en
# root, puis l'utilisateur de l'image est rétabli : le défaut est dans l'image,
# pas dans la façon de la lancer.
VARIANTES: dict[str, str] = {
    # Le dossier de données appartient à root : l'utilisateur de l'image ne peut
    # plus y écrire, et le service plante au démarrage.
    "donnees-de-root": (
        "USER root\n"
        "RUN chown root:root /var/lib/guichet\n"
        "USER 10042\n"
    ),
    # Le service signale l'erreur de configuration... et sort avec le code 0.
    "config-silencieuse": (
        "USER root\n"
        "RUN sed -i 's/sys.exit(64)/sys.exit(0)/' /app/guichet.py\n"
        "USER 10042\n"
    ),
    # Le service ne vérifie plus la variable obligatoire.
    "sans-verification": (
        "USER root\n"
        "RUN sed -i 's/^if not site:/if False:/' /app/guichet.py\n"
        "USER 10042\n"
    ),
    # Le service tourne avec les droits de root.
    "en-root": "USER 0\n",
    # Le service écrit hors de son dossier de données : il fonctionne tant que
    # le système de fichiers est inscriptible, et plante sous --read-only.
    "ecrit-hors-donnees": (
        "USER root\n"
        "RUN chown 10042:10042 /app && sed -i "
        "'s|^ecoute = |open(\"/app/guichet.pid\", \"w\").write(str(os.getpid()))\\necoute = |' "
        "/app/guichet.py\n"
        "USER 10042\n"
    ),
    # Le programme ignore SIGTERM : docker stop attend dix secondes, puis tue.
    "sigterm-ignore": (
        "USER root\n"
        "RUN sed -i 's/signal.signal(signal.SIGTERM, fermer)/"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)/' /app/guichet.py\n"
        "USER 10042\n"
    ),
    # Le programme s'arrête vite et proprement, mais écrit un compteur faux :
    # après redémarrage, les tickets délivrés ont disparu.
    "arret-sans-ecriture": (
        "USER root\n"
        "RUN sed -i 's/f.write(str(delivres))/f.write(\"0\")/' /app/guichet.py\n"
        "USER 10042\n"
    ),
}

# Verdicts du script, joués une seule fois par image : (code, sortie).
_verdicts: dict[str, tuple[int, str]] = {}


@pytest.fixture(scope="module")
def host():
    """La machine du lab, et surtout PAS le poste de travail.

    Sans cette fixture, pytest-testinfra en fournit une par défaut dont le
    backend est `local` : les tests tourneraient sur la machine de celui qui
    les lance, rendraient un verdict sur le mauvais système, et pourraient le
    modifier.
    """
    return lab_host(TARGET_HOST)


def _tag(nom: str) -> str:
    return f"{PREFIXE}{nom}"


@pytest.fixture(scope="module")
def jeu(host):
    """Construit les images cassées que l'apprenant n'a pas vues, puis les retire.

    Elles se construisent à partir de `guichet:1.0` : si l'apprenant l'a
    supprimée, rien ne peut être jugé et le message le dit.
    """
    if host.run("docker image inspect %s", CONFORME).rc != 0:
        pytest.fail(message(
            en=f"image `{CONFORME}` is missing. The setup builds it from the "
               f"context in {ATELIER}/guichet: do not remove it, it is the "
               "reference the other images are derived from.",
            fr=f"l'image `{CONFORME}` est absente. Le setup la construit depuis "
               f"le contexte de {ATELIER}/guichet : ne la supprimez pas, c'est "
               "la référence dont les autres images dérivent.",
        ))
    construites: dict[str, str] = {}
    try:
        for nom, lignes in VARIANTES.items():
            tag = _tag(nom)
            dockerfile = f"FROM {CONFORME}\n{lignes}"
            script = (
                f"docker build -q -t {tag} - >/dev/null <<'DOCKERFILE'\n"
                f"{dockerfile}"
                "DOCKERFILE\n"
            )
            res = host.run("bash -c %s", script)
            assert res.rc == 0, message(
                en=f"the check could not build its own image `{nom}`: "
                   f"{(res.stderr or res.stdout)[-300:]}",
                fr=f"le contrôle n'a pas pu construire sa propre image `{nom}` : "
                   f"{(res.stderr or res.stdout)[-300:]}",
            )
            construites[nom] = tag
        yield construites
    finally:
        for tag in construites.values():
            host.run("docker rmi -f %s", tag)
        host.run("docker image prune -f")


def _exiger_script(host) -> None:
    if host.run("test -f %s", SCRIPT).rc != 0:
        pytest.fail(message(
            en=f"`{SCRIPT}` does not exist. The mission asks you to write a "
               "script there that takes an image name and exits 0 or non-zero.",
            fr=f"`{SCRIPT}` n'existe pas. La mission demande d'y écrire un "
               "script qui prend un nom d'image et rend 0 ou un code non nul.",
        ))


def _jouer(host, image: str) -> tuple[int, str]:
    """Joue le script de l'apprenant sur une image, une seule fois par image."""
    if image not in _verdicts:
        res = host.run("timeout %s bash %s %s 2>&1", str(LIMITE_S), SCRIPT, image)
        _verdicts[image] = (res.rc, res.stdout[-600:])
    return _verdicts[image]


def _exiger_conforme_acceptee(host) -> None:
    """Un refus ne vaut que si la même image conforme est acceptée."""
    _exiger_script(host)
    code, sortie = _jouer(host, CONFORME)
    if code != 0:
        pytest.fail(message(
            en=f"your script exits {code} on `{CONFORME}`, which meets the "
               "contract.\nA script that refuses the correct image proves "
               "nothing by refusing the others, so none of its refusals are "
               f"credited. Its last output:\n{sortie}",
            fr=f"votre script rend {code} sur `{CONFORME}`, qui respecte le "
               "contrat.\nUn script qui refuse l'image correcte ne prouve rien "
               "en refusant les autres : aucun de ses refus n'est donc "
               f"crédité. Sa dernière sortie :\n{sortie}",
        ))


def _doit_refuser(host, image: str, defaut_en: str, defaut_fr: str) -> None:
    code, sortie = _jouer(host, image)
    assert code not in (0, 124), message(
        en=f"your script {'accepts' if code == 0 else 'runs out of time on'} "
           f"`{image}` ({defaut_en}).\nIt must exit with a non-zero code "
           f"within {LIMITE_S} s. Its last output:\n{sortie}",
        fr=f"votre script {'accepte' if code == 0 else 'dépasse le temps sur'} "
           f"`{image}` ({defaut_fr}).\nIl doit rendre un code non nul en "
           f"moins de {LIMITE_S} s. Sa dernière sortie :\n{sortie}",
    )


def test_le_script_accepte_l_image_conforme_et_ne_laisse_rien(host) -> None:
    """Le point de départ : l'image conforme passe, et le moteur reste propre.

    LA PREUVE LA PLUS SIMPLE, ET LA PLUS COUPANTE. Un script qui rend toujours 1
    échoue ici, et il fait échouer avec lui tous les contrôles de refus. Le
    contrôle compare aussi les conteneurs et les volumes avant et après : un
    test qui laisse derrière lui ce qu'il a créé empoisonne le suivant, et la
    leçon enseigne le nettoyage par `trap`.
    """
    _exiger_script(host)
    avant_c = set(host.run("docker ps -aq").stdout.split())
    avant_v = set(host.run("docker volume ls -q").stdout.split())
    code, sortie = _jouer(host, CONFORME)
    apres_c = set(host.run("docker ps -aq").stdout.split())
    apres_v = set(host.run("docker volume ls -q").stdout.split())

    assert code == 0, message(
        en=f"your script exits {code} on `{CONFORME}`, which meets the "
           f"contract.\nIts last output:\n{sortie}",
        fr=f"votre script rend {code} sur `{CONFORME}`, qui respecte le "
           f"contrat.\nSa dernière sortie :\n{sortie}",
    )
    laisses = sorted(apres_c - avant_c)
    assert not laisses, message(
        en=f"your script leaves {len(laisses)} container(s) behind after "
           "running. Whatever a test creates, it removes, whatever the outcome.",
        fr=f"votre script laisse {len(laisses)} conteneur(s) derrière lui. Ce "
           "qu'un test crée, il le retire, quel que soit le résultat.",
    )
    volumes = sorted(apres_v - avant_v)
    assert not volumes, message(
        en=f"your script leaves {len(volumes)} volume(s) behind after running.",
        fr=f"votre script laisse {len(volumes)} volume(s) derrière lui.",
    )


def test_le_script_refuse_une_image_qui_ne_demarre_pas_ou_n_est_pas_joignable(
    host, jeu
) -> None:
    """Démarrer ne suffit pas : il faut être JOIGNABLE par le port publié.

    `guichet:0.9` démarre, son processus vit et il répond DANS son conteneur : il
    n'écoute que sur 127.0.0.1, donc rien ne l'atteint de l'extérieur. Un script
    qui se contente de vérifier que le conteneur tourne l'accepte. La seconde
    image plante au démarrage : le dossier de données appartient à root.
    """
    _exiger_conforme_acceptee(host)
    _doit_refuser(
        host, CONNUE_CASSEE,
        "it listens on 127.0.0.1 only", "elle n'écoute que sur 127.0.0.1",
    )
    _doit_refuser(
        host, jeu["donnees-de-root"],
        "the data directory belongs to root and the service crashes at startup",
        "le dossier de données appartient à root et le service plante au "
        "démarrage",
    )


def test_le_script_refuse_une_configuration_mal_verifiee(host, jeu) -> None:
    """Une variable obligatoire absente doit arrêter le service, vite, avec un code.

    Deux défauts de nature différente. Le premier signale l'erreur et sort avec
    le code 0 : pour un orchestrateur, tout s'est bien passé. Le second ne vérifie
    plus rien et démarre sans la variable. Le script doit distinguer un arrêt en
    erreur d'un arrêt réussi, et un service qui tourne alors qu'il ne devrait
    pas.
    """
    _exiger_conforme_acceptee(host)
    _doit_refuser(
        host, jeu["config-silencieuse"],
        "it reports the configuration error but exits 0",
        "il signale l'erreur de configuration mais sort avec le code 0",
    )
    _doit_refuser(
        host, jeu["sans-verification"],
        "it starts without the mandatory variable",
        "il démarre sans la variable obligatoire",
    )


def test_le_script_refuse_une_image_qui_exige_trop_de_privileges(host, jeu) -> None:
    """Pas de root, et pas d'écriture hors du dossier de données.

    La première image tourne en root. La seconde ne l'est pas, mais écrit dans
    son propre dossier d'application : elle fonctionne tant que le système de
    fichiers est inscriptible, et plante dès que l'exploitant la lance avec
    `--read-only`. Seul un contrôle qui relance l'image sous cette contrainte la
    voit.
    """
    _exiger_conforme_acceptee(host)
    _doit_refuser(
        host, jeu["en-root"],
        "the process runs as root", "le processus tourne en root",
    )
    _doit_refuser(
        host, jeu["ecrit-hors-donnees"],
        "it writes outside its data directory and fails under --read-only",
        "il écrit hors de son dossier de données et plante sous --read-only",
    )


def test_le_script_refuse_une_image_qui_s_arrete_mal(host, jeu) -> None:
    """Un arrêt propre est rapide ET sans perte : deux défauts, deux mesures.

    La première image ignore SIGTERM : `docker stop` attend dix secondes, puis
    tue le conteneur (code 137). La seconde s'arrête en une fraction de seconde
    avec le code 0, mais écrit un compteur faux : les tickets délivrés
    disparaissent au redémarrage. Seul un contrôle qui relance l'image sur les
    mêmes données la voit, et le code de sortie ne suffit pas à la distinguer
    d'une image saine.
    """
    _exiger_conforme_acceptee(host)
    _doit_refuser(
        host, jeu["sigterm-ignore"],
        "it ignores SIGTERM and is killed after the grace period",
        "elle ignore SIGTERM et se fait tuer à la fin du délai de grâce",
    )
    _doit_refuser(
        host, jeu["arret-sans-ecriture"],
        "it stops cleanly but loses its counter",
        "elle s'arrête proprement mais perd son compteur",
    )


def test_le_script_refuse_ce_qu_il_ne_peut_pas_juger(host) -> None:
    """Sans argument, ou sur une image qui n'existe pas, le script refuse.

    Un test qui ne peut pas conclure ne conclut pas au vert : c'est la règle de
    ce dépôt pour ses propres contrôles, et elle vaut pour celui que l'apprenant
    écrit. Le contrôle suppose, comme les autres, que le script accepte l'image
    conforme.
    """
    _exiger_conforme_acceptee(host)
    sans_argument = host.run("timeout 30 bash %s >/dev/null 2>&1", SCRIPT)
    assert sans_argument.rc not in (0, 124), message(
        en="your script exits 0 (or never ends) when it is given no image "
           "name. It cannot judge anything: it must refuse.",
        fr="votre script rend 0 (ou ne termine pas) quand on ne lui donne aucun "
           "nom d'image. Il ne peut rien juger : il doit refuser.",
    )
    inconnue = host.run(
        "timeout 60 bash %s %s >/dev/null 2>&1", SCRIPT,
        "guichet-qui-n-existe-pas:9.9",
    )
    assert inconnue.rc not in (0, 124), message(
        en="your script exits 0 (or never ends) on an image that does not "
           "exist. An image it cannot even start is not an accepted image.",
        fr="votre script rend 0 (ou ne termine pas) sur une image qui n'existe "
           "pas. Une image qu'il ne peut même pas lancer n'est pas une image "
           "acceptée.",
    )
