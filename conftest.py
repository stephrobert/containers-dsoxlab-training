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

REPO_ROOT = Path(__file__).resolve().parent
LABS_ROOT = REPO_ROOT / "labs"

# Tout objet Docker créé par un test commence par là. Le validateur s'en sert
# pour distinguer ce que le lab a produit de ce qui vivait déjà sur la machine.
PREFIXE = "dsoxlab"

# Ce qu'on ne copie jamais d'un répertoire de travail.
EXCLUS_COPIE = (".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache")

_moteur_verifie = False


# ── Où travaille l'apprenant ─────────────────────────────────────────────────


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
