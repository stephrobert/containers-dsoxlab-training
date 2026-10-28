"""Primitives communes aux labs du catalogue : Docker, et rien d'autre.

## Ce que les tests lisent

L'état du moteur Docker, jamais les commandes tapées : une image construite, sa
taille, l'utilisateur qu'elle exécute, les montages d'un conteneur, la réponse
de l'application. L'apprenant arrive au résultat par le chemin qu'il veut.

Ce fichier est repris de `github-actions-training`, dont la structure a fait ses
preuves, en remplaçant act par Docker.

## Pourquoi tout passe par un préfixe de nom

Un lab construit des images et lance des conteneurs sur la machine de
l'apprenant, à côté de son travail à lui. Deux règles en découlent, et elles
sont tenues ici plutôt que dans chaque lab :

- tout ce qu'un test crée porte le préfixe `dsoxlab-<lab>-`, donc rien ne peut
  écraser une image de l'apprenant qui s'appellerait `mon-api` ;
- tout ce qu'un test crée est retiré à la fin, même quand il échoue. Le
  validateur photographie le moteur avant et après : une image ou un volume
  laissé derrière rend le lab ROUGE, et il a raison, parce que c'est le lab
  suivant qui en paierait le prix.

## Les ressources de la machine

Construire une image Python prend des dizaines de secondes et des centaines de
mégaoctets. Les tests construisent donc le MINIMUM : une image par propriété à
prouver, jamais une par test, et les fixtures d'un lab sont choisies pour que
le build soit court. Les délais sont généreux, parce qu'un test qui échoue sur
un `timeout` accuse le lab au lieu du réseau.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml
from typing import TYPE_CHECKING, Any

REPO_ROOT = Path(__file__).resolve().parent
LABS_ROOT = REPO_ROOT / "labs"

# Tout objet Docker créé par un test commence par là. Le validateur s'en sert
# pour distinguer ce que le lab a produit de ce qui vivait déjà sur la machine.
PREFIXE = "dsoxlab"

# Ce qu'on ne copie jamais d'un répertoire de travail.
EXCLUS_COPIE = (".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache")

_moteur_verifie = False


# ── Où travaille l'apprenant ─────────────────────────────────────────────────


def message(en: str, fr: str) -> str:
    """Le message d'une assertion, dans la langue de l'apprenant.

    Pourquoi ce helper
    ------------------

    Quand un test échoue, `dsoxlab check` affiche le **message écrit par
    l'auteur** : c'est la seule consigne que l'apprenant reçoit à cet instant.
    Or tout le reste du catalogue existe dans les deux langues (`README.md` et
    `README.fr.md`), et ce texte-là ne peut pas : le contrat dsoxlab impose un
    nom de fichier unique, `challenge/tests/test_functional.py`. Il n'y a donc
    pas de version anglaise possible par duplication, d'où ce choix à
    l'exécution. C'est la même solution que `hints.yaml`, qui porte depuis
    toujours un `text_en` et un `text_fr` côte à côte.

    Pourquoi ici et pas dans dsoxlab
    --------------------------------

    Un test de lab doit rester jouable par un simple `pytest`, sans l'outil
    installé : c'est le test de non-couplage du catalogue. Un
    `from dsoxlab… import` en tête d'un fichier de tests le casserait. dsoxlab
    ne reconnaît donc que la **forme** de l'appel, `message(en=…, fr=…)`.

    La langue vient de `DSOXLAB_LANG`, comme pour le reste de l'outil, et
    l'anglais est le défaut.

    Usage :

        from conftest import lab_host, message

        assert f.exists, message(
            en="/etc/myapp is missing. Create it with ansible.builtin.file.",
            fr="/etc/myapp est absent. Crée-le avec ansible.builtin.file.",
        )
    """
    langue = os.environ.get("DSOXLAB_LANG", "en").lower()
    return fr if langue.startswith("fr") else en


def workdir_lab(fichier_test: str | Path) -> Path:
    """Workdir du lab auquel appartient un fichier de test.

    Remonte depuis `challenge/tests/test_functional.py` jusqu'au `lab.yaml`,
    puis lit `runtime.workdir`. Un chemin en dur serait faux le jour où un lab
    déclare un autre répertoire.
    """
    chemin = Path(fichier_test).resolve()
    for parent in chemin.parents:
        contrat = parent / "lab.yaml"
        if contrat.is_file():
            donnees = yaml.safe_load(contrat.read_text(encoding="utf-8")) or {}
            relatif = ((donnees.get("runtime") or {}).get("workdir")) or "challenge/work"
            return parent / relatif
    raise RuntimeError(f"aucun lab.yaml au-dessus de {chemin}")


def exiger_workdir(workdir: Path, lab_id: str) -> None:
    """Le répertoire de travail existe, sinon on dit quoi lancer."""
    if workdir.is_dir():
        return
    pytest.fail(
        f"`{workdir}` n'existe pas. Le point de départ se pose avec "
        f"`dsoxlab run {lab_id}`, qui copie les fixtures du lab dans ce "
        "répertoire. Sans lui, il n'y a rien à corriger."
    )


# ── Outils ───────────────────────────────────────────────────────────────────


def exiger_outil(nom: str) -> str:
    """Le chemin de l'outil, ou un échec qui dit comment l'installer."""
    chemin = shutil.which(nom)
    if not chemin:
        pytest.fail(
            f"L'outil `{nom}` n'est pas sur le PATH. Les outils du catalogue "
            "sont épinglés dans `mise.toml` à sa racine : lancez "
            "`mise install`, puis rejouez `dsoxlab check`."
        )
    return chemin


def executer(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 300,
    entree: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Lance une commande et rend le résultat sans lever : c'est le test qui juge."""
    environnement = dict(os.environ)
    if env:
        environnement.update(env)
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            env=environnement,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=entree,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        sortie = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        return subprocess.CompletedProcess(cmd, 124, stdout=sortie, stderr=f"délai de {timeout} s dépassé")


def moteur_pret() -> None:
    """Docker répond, sinon rien de ce catalogue ne peut être prouvé."""
    global _moteur_verifie  # noqa: PLW0603
    if _moteur_verifie:
        return
    exiger_outil("docker")
    res = executer(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=60)
    if res.returncode != 0:
        pytest.fail(
            "`docker info` ne répond pas : le démon n'est pas démarré, ou "
            "l'utilisateur n'a pas le droit de lui parler.\n\n"
            f"{(res.stdout + res.stderr).strip()[-400:]}\n\n"
            "Tous les labs de ce catalogue interrogent le moteur : aucun ne "
            "peut rien prouver tant qu'il se tait."
        )
    _moteur_verifie = True


# ── Images ───────────────────────────────────────────────────────────────────


@dataclass
class ResultatBuild:
    """Ce que `docker build` a produit, et ce qu'il a écrit."""

    tag: str
    rc: int
    sortie: str

    @property
    def reussi(self) -> bool:
        return self.rc == 0

    def resume(self, lignes: int = 15) -> str:
        """Les dernières lignes du build, pour les messages d'assertion."""
        fin = [ligne for ligne in self.sortie.splitlines() if ligne.strip()][-lignes:]
        return "\n    ".join(fin)


def nom_objet(lab: str, suffixe: str = "") -> str:
    """Un nom d'image ou de volume qui ne peut pas entrer en collision."""
    base = f"{PREFIXE}-{lab}"
    return f"{base}-{suffixe}" if suffixe else base


def construire(
    contexte: Path,
    tag: str,
    *,
    dockerfile: str = "Dockerfile",
    timeout: int = 900,
) -> ResultatBuild:
    """Construit l'image de l'apprenant, sans jamais la pousser nulle part.

    `--no-cache` n'est PAS employé : un lab de la série reconstruit la même
    application quatre fois, et refuser le cache triplerait le temps de
    `dsoxlab check` sans rien prouver de plus. Ce que les tests mesurent est
    l'image obtenue, pas le chemin qui y mène.
    """
    moteur_pret()
    fichier = contexte / dockerfile
    if not fichier.is_file():
        pytest.fail(
            f"`{dockerfile}` est introuvable dans `{contexte.name}`.\n\n"
            "C'est le fichier que l'énoncé demande d'écrire : `docker build` "
            "le cherche à la racine du contexte, sauf si on lui dit où il est "
            "avec `-f`."
        )
    res = executer(
        ["docker", "build", "-f", str(fichier), "-t", tag, "."],
        cwd=contexte,
        timeout=timeout,
    )
    return ResultatBuild(tag=tag, rc=res.returncode, sortie=res.stdout + res.stderr)


def exiger_build(contexte: Path, tag: str, **kwargs) -> ResultatBuild:
    """Construit, et échoue en montrant la fin du build si cela ne passe pas."""
    build = construire(contexte, tag, **kwargs)
    assert build.reussi, (
        f"`docker build` a échoué (code {build.rc}).\n\n"
        f"    {build.resume()}\n\n"
        "Le build doit aboutir avant que quoi que ce soit d'autre puisse être "
        "vérifié : une image qui ne se construit pas n'a ni taille, ni "
        "utilisateur, ni application."
    )
    return build


def inspecter_image(tag: str) -> dict:
    """Le descripteur de l'image, tel que le moteur le tient."""
    moteur_pret()
    res = executer(["docker", "image", "inspect", tag], timeout=60)
    assert res.returncode == 0, (
        f"L'image `{tag}` est introuvable pour le moteur.\n\n"
        f"{res.stderr.strip()[-300:]}"
    )
    return json.loads(res.stdout)[0]


def taille_image(tag: str) -> int:
    """La taille que l'API rend, et ce n'est PAS celle que l'apprenant voit.

    Mesuré le 2026-10-01 sur Docker 29.1.3 avec le **containerd image store**
    (`docker info` : `io.containerd.snapshotter.v1`) :

        docker image inspect --format {{.Size}}   ->   83.0 Mio
        docker images                             ->   345 MB

    Un facteur quatre, sur la même image, parce que l'API rend la taille
    COMPRESSÉE des couches — celle du registre — et la commande la taille
    décompressée sur disque. Le classic image store, lui, rendait la seconde
    des deux côtés.

    Conséquence pour les labs : un test qui écrit un seuil en octets serait
    incompréhensible, puisque l'apprenant lit l'autre chiffre dans son
    terminal. Les labs d'optimisation comparent donc des RAPPORTS entre deux
    images mesurées de la même façon, ce qui est de surcroît plus juste : « la
    moitié de l'image Debian » reste vrai quand les deux images grossissent.
    """
    return int(inspecter_image(tag)["Size"])


def taille_affichee(tag: str) -> int:
    """La taille en octets telle que `docker images` l'AFFICHE, décompressée.

    C'est le chiffre que l'apprenant a sous les yeux. Il est lu par la même
    commande que la sienne, puis converti : lui donner un ordre de grandeur
    qu'il ne retrouve pas dans son terminal ne lui apprend rien.
    """
    moteur_pret()
    res = executer(["docker", "image", "ls", "--format", "{{.Size}}", tag], timeout=60)
    brut = res.stdout.strip().splitlines()
    assert brut, f"`docker image ls {tag}` ne rend rien : l'image est-elle construite ?"
    return _octets(brut[0].strip())


_UNITES = {"B": 1, "kB": 10**3, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}


def _octets(affiche: str) -> int:
    """« 345MB » en octets. Docker emploie les unités DÉCIMALES dans cette sortie."""
    for unite, facteur in sorted(_UNITES.items(), key=lambda kv: -len(kv[0])):
        if affiche.endswith(unite):
            return int(float(affiche[: -len(unite)].strip()) * facteur)
    raise AssertionError(f"taille Docker illisible : {affiche!r}")


def store_containerd() -> bool:
    """Le moteur emploie-t-il le containerd image store ?

    Utile aux labs qui parlent de stockage ou de tailles : ce qu'ils doivent
    dire à l'apprenant n'est pas le même dans les deux modes.
    """
    moteur_pret()
    res = executer(["docker", "info", "--format", "{{.DriverStatus}}"], timeout=60)
    return "containerd.snapshotter" in res.stdout


def en_mio(octets: int) -> float:
    """Des mébioctets, arrondis : c'est l'unité dans laquelle on en parle."""
    return round(octets / (1024 * 1024), 1)


def couches(tag: str) -> list[str]:
    """Les couches de l'image, du socle au sommet."""
    return list(inspecter_image(tag).get("RootFS", {}).get("Layers") or [])


def retirer_image(tag: str) -> None:
    """Retire l'image sans bruit : le nettoyage ne doit jamais faire échouer un test."""
    executer(["docker", "image", "rm", "-f", tag], timeout=120)


@contextlib.contextmanager
def image_temporaire(contexte: Path, tag: str, **kwargs) -> Iterator[ResultatBuild]:
    """Construit une image, la rend, puis la retire quoi qu'il arrive."""
    try:
        yield exiger_build(contexte, tag, **kwargs)
    finally:
        retirer_image(tag)


# ── Conteneurs ───────────────────────────────────────────────────────────────


def port_libre() -> int:
    """Un port que personne n'écoute, demandé au noyau plutôt que tiré au sort.

    Un port en dur fait échouer le lab chez l'apprenant qui a déjà quelque
    chose sur 8000, et le message n'en dit rien.
    """
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@dataclass
class Conteneur:
    """Un conteneur lancé par un test, et ce qu'on peut lui demander."""

    nom: str
    tag: str
    port: int | None = None

    def inspecter(self) -> dict:
        res = executer(["docker", "inspect", self.nom], timeout=60)
        assert res.returncode == 0, f"`{self.nom}` est introuvable : {res.stderr.strip()[-200:]}"
        return json.loads(res.stdout)[0]

    def journal(self, lignes: int = 40) -> str:
        res = executer(["docker", "logs", "--tail", str(lignes), self.nom], timeout=60)
        return (res.stdout + res.stderr).strip()

    def dans(self, *commande: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
        """Exécute une commande DANS le conteneur, pour lire ce qu'il voit."""
        return executer(["docker", "exec", self.nom, *commande], timeout=timeout)

    def montages(self) -> list[dict]:
        return list(self.inspecter().get("Mounts") or [])

    def utilisateur(self) -> str:
        """L'utilisateur que le conteneur exécute RÉELLEMENT, pas celui déclaré.

        `docker inspect` rend le `User` de la configuration, qui peut être vide
        alors que l'image en déclare un. Seul `id -u` dans le conteneur dit qui
        tourne vraiment.
        """
        res = self.dans("id", "-u")
        return res.stdout.strip() if res.returncode == 0 else ""

    def repondre(self, chemin: str = "/", *, attente: float = 30.0) -> tuple[int, str]:
        """Interroge l'application, en lui laissant le temps de démarrer.

        Un service dans un conteneur n'écoute pas à la seconde où le conteneur
        existe : il lui faut le temps de son interpréteur et de son serveur.
        Mesurer immédiatement recalerait un lab juste, ce qui est pire qu'un
        test absent.
        """
        assert self.port, f"`{self.nom}` n'a pas été lancé avec un port publié."
        limite = time.monotonic() + attente
        derniere = ""
        while time.monotonic() < limite:
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{self.port}{chemin}", timeout=5
                ) as reponse:
                    return reponse.status, reponse.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as erreur:
                return erreur.code, erreur.read().decode("utf-8", "replace")
            except (urllib.error.URLError, TimeoutError, ConnectionError) as erreur:
                derniere = str(erreur)
                time.sleep(0.5)
        return 0, derniere


@contextlib.contextmanager
def conteneur_temporaire(
    tag: str,
    nom: str,
    *,
    publier: bool = False,
    port_interne: int = 8000,
    arguments: list[str] | None = None,
    commande: list[str] | None = None,
    timeout: int = 120,
) -> Iterator[Conteneur]:
    """Lance un conteneur, le rend, puis le supprime quoi qu'il arrive.

    `--rm` n'est pas employé : il efface le conteneur dès qu'il s'arrête, et le
    test perdrait ses journaux et son descripteur, c'est-à-dire tout ce qu'il
    avait à lire. La suppression est faite ici, après les assertions.
    """
    moteur_pret()
    executer(["docker", "rm", "-f", nom], timeout=60)

    port = port_libre() if publier else None
    cmd = ["docker", "run", "-d", "--name", nom]
    if port:
        cmd += ["-p", f"127.0.0.1:{port}:{port_interne}"]
    cmd += list(arguments or [])
    cmd += [tag]
    cmd += list(commande or [])

    res = executer(cmd, timeout=timeout)
    assert res.returncode == 0, (
        f"`docker run` a échoué sur l'image `{tag}` :\n\n"
        f"{(res.stdout + res.stderr).strip()[-600:]}"
    )
    try:
        yield Conteneur(nom=nom, tag=tag, port=port)
    finally:
        executer(["docker", "rm", "-f", nom], timeout=120)


# ── Volumes ──────────────────────────────────────────────────────────────────


def volumes_existants() -> set[str]:
    moteur_pret()
    res = executer(["docker", "volume", "ls", "--format", "{{.Name}}"], timeout=60)
    return {ligne.strip() for ligne in res.stdout.splitlines() if ligne.strip()}


def inspecter_volume(nom: str) -> dict:
    res = executer(["docker", "volume", "inspect", nom], timeout=60)
    assert res.returncode == 0, (
        f"Le volume `{nom}` est introuvable.\n\n{res.stderr.strip()[-300:]}"
    )
    return json.loads(res.stdout)[0]


@contextlib.contextmanager
def volume_temporaire(nom: str) -> Iterator[str]:
    """Crée un volume nommé, le rend, puis le supprime quoi qu'il arrive."""
    moteur_pret()
    executer(["docker", "volume", "rm", "-f", nom], timeout=60)
    res = executer(["docker", "volume", "create", nom], timeout=60)
    assert res.returncode == 0, f"création du volume `{nom}` : {res.stderr.strip()[-200:]}"
    try:
        yield nom
    finally:
        executer(["docker", "volume", "rm", "-f", nom], timeout=120)


# ── Lecture du Dockerfile ────────────────────────────────────────────────────


def instructions(dockerfile: Path) -> list[tuple[str, str]]:
    """Les instructions du Dockerfile, en (VERBE, reste), continuations recollées.

    Lire le texte est parfois nécessaire : « combien d'étapes » et « quelle
    image de base » sont des propriétés du FICHIER, pas de l'image obtenue.
    `docker image inspect` ne dit pas combien de `FROM` ont servi.
    """
    if not dockerfile.is_file():
        return []

    lu: list[tuple[str, str]] = []
    tampon = ""
    for brute in dockerfile.read_text(encoding="utf-8").splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#"):
            continue
        if ligne.endswith("\\"):
            tampon += ligne[:-1] + " "
            continue
        complete = (tampon + ligne).strip()
        tampon = ""
        verbe, _, reste = complete.partition(" ")
        lu.append((verbe.upper(), reste.strip()))
    if tampon.strip():
        verbe, _, reste = tampon.strip().partition(" ")
        lu.append((verbe.upper(), reste.strip()))
    return lu


def etapes(dockerfile: Path) -> list[str]:
    """Les images de base de chaque étape, dans l'ordre des `FROM`."""
    return [reste for verbe, reste in instructions(dockerfile) if verbe == "FROM"]


# ---------------------------------------------------------------------------
# SOCLE VM, porté depuis `linux-dsoxlab-training/conftest.py` le 2026-10-28.
#
# POURQUOI IL EST LÀ. Les 46 contrats de la formation « Conteneurs et Docker »
# déclarent `environnement.reference: vm_linux_jetable` : les labs tournent sur
# une machine jetable, et non sur le poste de l'apprenant comme l'annonçait
# l'en-tête de ce fichier. Décision de Stéphane du 2026-10-28.
#
# CE QU'IL APPORTE. `lab_host(nom)` rend une machine testinfra, et la fixture
# autouse `_apply_lab_state` joue `solution/<lab>/solution.yaml` par
# ansible-runner AVANT les tests, ce qui est le seul moyen de prouver qu'une
# solution de référence passe. `LAB_NO_REPLAY=1` la désactive : c'est ce que
# fait `dsoxlab check`, qui doit noter l'état réel de la machine de l'apprenant.
#
# COMMENT UN LAB VM S'EN SERT, dans son test_functional.py :
#
#     from conftest import lab_host, message
#     TARGET_HOST = "docker.lab"
#
#     @pytest.fixture(scope="module")
#     def host():
#         return lab_host(TARGET_HOST)
#
# Les helpers Docker locaux plus haut restent valables pour un lab shell : un
# lab VM ne les utilise pas, il passe par `host`.
# ---------------------------------------------------------------------------

if TYPE_CHECKING:  # testinfra n'est importé qu'à l'usage, pour les labs VM
    import testinfra

REPO_ROOT = Path(__file__).parent.resolve()

def _build_inventory_cached() -> tuple[dict, Path | None]:
    """Construit l'inventory Ansible + un ssh_config OpenSSH une fois
    pour toute la session pytest.

    Délègue à dsoxlab.infra.inventory pour cohérence avec dsoxlab
    provision/status/ssh — même résolution IPs et même ProxyCommand
    bastion. Le ssh_config est consommé par testinfra (cf. lab_host)
    via ``ssh://<host>?ssh_config=...``, plus fiable que de bourrer
    ``ssh_extra_args`` dans une URL (espaces et quotes du ProxyCommand
    cassent le parser, d'où "Connection to UNKNOWN port 65535").

    L'inventaire ne sert qu'aux labs ``runtime: vm``. Un lab ``shell`` se
    joue sur le poste, sans la moindre VM : il ne doit donc jamais échouer
    parce que l'infra n'est pas provisionnée, ni parce qu'aucun provider
    n'a encore été choisi. Toute erreur est donc rattrapée ici et rend un
    inventaire vide ; ce sont les labs ``vm`` qui échoueront plus tard,
    dans ``lab_host()``, avec un message qui dit quoi faire.
    """
    empty = {"all": {"children": {"labenv": {"hosts": {}}}}}
    try:
        from dsoxlab.discovery.repo import read_repo_metadata
        from dsoxlab.infra.inventory import (
            build_inventory,
            read_terraform_outputs,
            write_ssh_config,
        )
    except ImportError:
        return empty, None

    # Volontairement large : provider non résolu (ProviderUnresolved), état
    # Terraform absent, meta.yml sans section infra, terraform introuvable...
    # Aucun de ces cas ne concerne un lab shell, et aucun ne justifie de faire
    # échouer le chargement de conftest.py pour TOUS les labs du dépôt.
    try:
        repo_meta = read_repo_metadata(REPO_ROOT)
        if repo_meta is None:
            return empty, None
        tf_outputs = read_terraform_outputs(repo_meta)
        inventory = build_inventory(repo_meta, terraform_outputs=tf_outputs)
        ssh_cfg = write_ssh_config(inventory, repo_meta)
        return inventory, ssh_cfg
    except Exception:  # noqa: BLE001 - degradation voulue, cf. docstring
        return empty, None


# L'inventaire est construit UNE fois pour toute la session de tests : le
# résoudre à chaque appel relancerait `terraform output` par test. `_SSH_CONFIG`
# porte le chemin du ssh_config généré, que testinfra consomme tel quel.
_INVENTORY, _SSH_CONFIG = _build_inventory_cached()
_LABENV_HOSTS: dict = _INVENTORY.get("all", {}).get("children", {}).get(
    "labenv", {}
).get("hosts", {})

def lab_host(name: str) -> testinfra.host.Host:
    """Retourne un host testinfra connecté en SSH au compte ``student``.

    Source de vérité : ``dsoxlab.infra.inventory.build_inventory()``,
    qui résout les IPs depuis les outputs Terraform et configure
    automatiquement ``ProxyCommand`` quand un bastion est présent
    (cas providers cloud avec subnet privé). Le ssh_config OpenSSH
    généré est consommé via ``?ssh_config=...`` plutôt que de tasser
    le ProxyCommand dans ``ssh_extra_args`` (parsing URL trop fragile
    avec espaces et guillemets).

    Args:
        name: FQDN du host tel que déclaré dans ``meta.yml: infra.hosts``
              (ex. ``alma-rhcsa-1.lab``).

    Raises:
        ValueError: si le nom n'est pas trouvé dans l'inventory.
        RuntimeError: si l'infra n'est pas provisionnée
            (``dsoxlab provision`` à lancer d'abord), ou si testinfra
            n'est pas installé.
    """
    try:
        import testinfra
    except ModuleNotFoundError as exc:  # pragma: no cover - dépend de l'env
        raise RuntimeError(
            "testinfra est absent : les labs vm ont besoin de "
            "pytest-testinfra. Installe-le avec "
            "'uv pip install pytest-testinfra', ou lance les labs via "
            "'dsoxlab check', qui l'embarque."
        ) from exc

    if name not in _LABENV_HOSTS:
        if not _LABENV_HOSTS:
            raise RuntimeError(
                "Aucun host dans l'inventory : as-tu lancé 'dsoxlab provision' ? "
                "Le test a besoin de l'infrastructure déployée."
            )
        raise ValueError(
            f"Host inconnu : {name}. Hôtes disponibles : {sorted(_LABENV_HOSTS)}"
        )

    if _SSH_CONFIG is None or not _SSH_CONFIG.is_file():
        raise RuntimeError(
            "ssh_config introuvable : dsoxlab non installé ou inventory vide. "
            "Lance 'dsoxlab provision' puis réessaie."
        )

    # Le User/IdentityFile/ProxyCommand vivent tous dans ssh_config.
    # On passe juste le nom du Host (alias) à testinfra.
    return testinfra.get_host(
        f"ssh://{name}?ssh_config={_SSH_CONFIG}&sudo=true"
    )


def lab_host_ip(name: str) -> str:
    """Retourne l'adresse IP d'un hôte du lab, telle que l'inventory la connaît.

    Les IP ne sont PAS déclarées dans meta.yml : Terraform les attribue (DHCP
    réservé en KVM/incus, IP privée auto dans les clouds). Un test qui code une
    adresse en dur est donc faux dès qu'on change de provider — et un sujet qui
    demande une adresse différente de celle-là coupe la notation, puisque
    testinfra se connecte via l'inventory.

    Args:
        name: FQDN de l'hôte tel que déclaré dans ``meta.yml: infra.hosts``.

    Raises:
        ValueError: si l'hôte est inconnu de l'inventory.
    """
    hote = _LABENV_HOSTS.get(name)
    if not hote or not hote.get("ansible_host"):
        raise ValueError(
            f"Pas d'IP pour {name} dans l'inventory. "
            f"Hôtes disponibles : {sorted(_LABENV_HOSTS)}"
        )
    return str(hote["ansible_host"])


def lab_target_host(default: str) -> str:
    """Retourne le FQDN de la target sur laquelle valider.

    C'est le point d'entrée des labs MULTI-DISTRIB : au lieu de coder un
    hôte en dur (ce qui rendrait une target Ubuntu déclarée mais jamais
    testée — le contrat mentirait), le test demande ici l'hôte réellement
    choisi.

    Source : ``DSOXLAB_TARGET_HOST``, exporté par ``dsoxlab check`` depuis
    la target résolue (``--target``, sinon la target de session, sinon la
    target ``default`` du lab.yaml).

    Args:
        default: FQDN à utiliser hors dsoxlab (pytest lancé à la main, CI) —
                 typiquement la target ``default`` du lab.

    Usage dans un test::

        TARGET_HOST = lab_target_host("alma-rhcsa-1.lab")
    """
    return os.environ.get("DSOXLAB_TARGET_HOST") or default


def _find_lab_root(test_path: Path) -> Path | None:
    """Remonte les parents pour trouver ``labs/<category>/<section>/<lab>/``.

    Retourne le dossier ``<lab>`` (parent de ``challenge/``), ou None si
    le test n'est pas dans un lab.
    """
    labs_dir = REPO_ROOT / "labs"
    for parent in test_path.parents:
        try:
            rel = parent.relative_to(labs_dir)
        except ValueError:
            continue
        # ADAPTÉ À CE CATALOGUE. La version d'origine exigeait au moins TROIS
        # composants, `<category>/<section>/<lab>`, parce que les labs de
        # `linux-dsoxlab-training` sont rangés ainsi. Ici ils sont À PLAT,
        # `labs/<lab>`, donc la condition ne tenait jamais : `_find_lab_root`
        # rendait None, la fixture `_apply_lab_state` repartait sans rien faire,
        # et les tests échouaient sur une solution jamais posée. Le symptôme
        # était muet : une pose en 1,3 s et un `reponse.txt` absent.
        #
        # La profondeur ne prouve rien de toute façon : ce qui fait la racine
        # d'un lab, c'est son `lab.yaml`. On parcourt les parents du plus proche
        # au plus lointain, donc le premier trouvé est bien le plus profond.
        if len(rel.parts) >= 1 and (parent / "lab.yaml").is_file():
            return parent
    return None


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Exécute une commande, lève une RuntimeError lisible en cas d'échec."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(
            f"Commande échouée (exit {result.returncode}) : {' '.join(cmd)}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )
    return result


def _read_lab_runtime(lab_root: Path) -> tuple[str, str | None]:
    """Lit ``lab.yaml`` et retourne ``(runtime_type, host_or_None)``."""
    lab_yaml = lab_root / "lab.yaml"
    with lab_yaml.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    runtime = data.get("runtime") or {}
    host = runtime.get("host")
    # Labs VM mono/multi-hôte : le host peut vivre dans runtime.targets[].host
    # (schéma des labs l2+). On prend la target ``default`` si déclarée, sinon
    # la première.
    if host is None:
        targets = runtime.get("targets") or []
        if targets:
            default = runtime.get("default")
            chosen = next(
                (t for t in targets if t.get("name") == default), targets[0]
            )
            host = chosen.get("host")
    return str(runtime.get("type", "shell")), host


def _replay_shell_solution(lab_root: Path, rel_path: Path) -> None:
    """Joue la solution d'un lab shell dans son workdir.

    Un lab shell n'a rien à provisionner : sa solution est un script bash joué
    dans ``challenge/work/``, exactement là où l'apprenant travaille (le
    conftest local de chaque lab y fait un chdir par test).

    Le script est chiffré ansible-vault comme les solutions VM — l'apprenant ne
    doit pas pouvoir le lire dans le dépôt. On le déchiffre en mémoire, jamais
    sur disque.

    Solution absente → no-op : les tests tournent sur l'état du workdir tel
    quel, ce qui reste le comportement voulu en ``dsoxlab check``.
    """
    solution_sh = REPO_ROOT / "solution" / rel_path / "solution.sh"
    if not solution_sh.is_file():
        return

    script = solution_sh.read_text()
    if script.lstrip().startswith("$ANSIBLE_VAULT"):
        vault_pass = REPO_ROOT / ".vault-pass"
        if not vault_pass.is_file():
            pytest.skip(
                f"[{lab_root.name}] solution.sh chiffrée mais .vault-pass "
                "absent : impossible de la rejouer."
            )
        # _run impose capture_output/text et lève si la commande échoue.
        script = _run([
            "ansible-vault", "view", str(solution_sh),
            "--vault-password-file", str(vault_pass),
        ]).stdout

    workdir = lab_root / "challenge" / "work"
    workdir.mkdir(parents=True, exist_ok=True)
    # subprocess.run direct (pas _run) : on veut le script sur stdin et un
    # message d'erreur qui nomme le lab. bash -e arrête la solution au premier
    # échec — sinon un test pourrait passer alors qu'une étape a silencieusement
    # échoué, et la solution "prouverait" un test qu'elle n'honore pas.
    res = subprocess.run(
        ["bash", "-e"],
        input=script,
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"solution.sh a échoué pour {lab_root.name} "
            f"(rc={res.returncode}).\n{res.stdout}\n{res.stderr}"
        )


def message_echec_solution(lab_id: str, result: Any) -> str:
    """Message d'échec du replay de la solution, sortie du playbook comprise.

    Sans cette sortie, un échec se résume à « 1 failure sur tel hôte » : ni la
    tâche fautive, ni sa raison. Or reproduire coûte une passe entière sur
    l'infrastructure, ce qui a fait traîner l'incident du capstone RHCSA.

    On a longtemps cru la sortie perdue, `run_playbook` créant un répertoire
    temporaire qu'il nettoie ensuite. C'est inexact : `dsoxlab` lit le stdout
    AVANT de supprimer ce répertoire. Vérifié en jouant un playbook en échec
    dans les conditions exactes d'ici (`quiet=True`, `private_data_dir=None`) :
    la tâche fautive, le `fatal:` et le `PLAY RECAP` y sont tous.

    La fin plutôt que le début : Ansible s'arrête à la tâche fautive, donc
    l'erreur est toujours dans les derniers caractères.
    """
    sortie = (result.stdout or "").strip()
    detail = f"\n\nSortie du playbook (fin) :\n{sortie[-4000:]}" if sortie else ""
    return (
        f"solution.yaml a échoué pour {lab_id} "
        f"(rc={result.rc}, status={result.status}). "
        f"Stats : {result.stats}{detail}"
    )


@pytest.fixture(scope="module", autouse=True)
def _apply_lab_state(request) -> None:
    """Applique la solution officielle du formateur avant les tests.

    Cette fixture sert à la **validation CI** (rejouer la solution
    officielle pour vérifier que les tests passent). Pour la validation
    apprenant via ``dsoxlab check`` qui teste l'état actuel de la VM,
    désactiver via ``LAB_NO_REPLAY=1``.

    Comportement :

    - ``runtime: vm`` (et alias kvm/incus) → joue
      ``solution/<category>/<chemin-relatif-du-lab>/solution.yaml``
      via ansible-runner sur la target par défaut. Si le fichier est
      chiffré ansible-vault, lit ``.vault-pass`` à la racine.
    - ``runtime: shell`` → no-op (l'apprenant a fait ses commandes
      en local, on teste l'état du workdir tel quel).
    - Solution absente → log + skip soft (les tests tournent quand même
      sur l'état actuel, mais peuvent échouer si rien n'a été fait).
    """
    if os.environ.get("LAB_NO_REPLAY") == "1":
        return

    test_path = Path(str(request.fspath)).resolve()
    lab_root = _find_lab_root(test_path)
    if lab_root is None:
        return  # test hors d'un lab

    runtime_type, host_name = _read_lab_runtime(lab_root)

    # Labs multi-distrib : la solution doit se rejouer sur la MÊME target que
    # celle où portent les tests, sinon on validerait un hôte et on
    # provisionnerait l'autre.
    host_name = lab_target_host(host_name) if host_name else os.environ.get(
        "DSOXLAB_TARGET_HOST"
    )

    rel_path = lab_root.relative_to(REPO_ROOT / "labs")

    # Atelier shell-local : la solution est un SCRIPT joué dans le workdir.
    # Ansible ne sert à rien ici (rien à provisionner, tout est local), mais
    # une solution reste indispensable : sans elle, les tests d'un lab shell ne
    # sont JAMAIS prouvés passables — c'est exactement le trou qui rendait le
    # capstone RHCSA injouable sans que personne le sache.
    if runtime_type == "shell":
        _replay_shell_solution(lab_root, rel_path)
        return

    # Runtime VM : cherche solution.yaml côté formateur (solution/...)
    solution_yaml = REPO_ROOT / "solution" / rel_path / "solution.yaml"
    if not solution_yaml.is_file():
        # Solution absente : log puis skip soft (les tests tournent sur
        # l'état actuel — utile pour valider le travail manuel apprenant).
        return

    if host_name is None:
        raise RuntimeError(
            f"Lab {lab_root.name} : runtime.type=vm mais aucun "
            f"runtime.targets[].host trouvable. Vérifie lab.yaml."
        )

    # Joue solution.yaml via ansible-runner (cohérent avec dsoxlab run).
    # Import local pour éviter d'exiger dsoxlab installé pour les labs
    # shell-only.
    try:
        from dsoxlab.discovery.repo import read_repo_metadata
        from dsoxlab.infra import ansible as ansible_infra
        from dsoxlab.infra.inventory import build_inventory, read_terraform_outputs
    except ImportError:
        pytest.skip(
            f"[{lab_root.name}] dsoxlab non installé. Pour la validation "
            f"VM, lance 'uv tool install --editable ~/Projets/dsoxlab'."
        )

    repo_meta = read_repo_metadata(REPO_ROOT)
    if repo_meta is None:
        pytest.skip(f"[{lab_root.name}] meta.yml introuvable.")

    tf_outputs = read_terraform_outputs(repo_meta)
    inventory = build_inventory(
        repo_meta,
        terraform_outputs=tf_outputs,
        target_fqdn=host_name,
    )

    vault_password_file: Path | None = None
    vault_pass = REPO_ROOT / ".vault-pass"
    if vault_pass.is_file():
        vault_password_file = vault_pass

    result = ansible_infra.run_playbook(
        playbook_path=solution_yaml,
        inventory=inventory,
        vault_password_file=vault_password_file,
    )
    if not result.ok:
        raise RuntimeError(message_echec_solution(lab_root.name, result))

