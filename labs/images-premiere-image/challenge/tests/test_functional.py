"""La première image du fil rouge : sept contrôles, de poids égal.

## Ce que ces tests lisent

L'état du moteur Docker : l'image construite, sa configuration, et ce que
l'application répond dans un conteneur. Jamais les commandes tapées.

## Le contrôle qui compte est celui de l'autonomie

Les autres passent avec une image qui télécharge ses dépendances au
démarrage : elle se construit, elle répond, elle déclare son port. Le cinquième
la lance **sans réseau du tout** et exige qu'elle réponde quand même. C'est la
différence entre une image qui embarque son application et une image qui espère
qu'Internet sera là.

Mesuré le 2026-10-01 : la solution de référence répond `200 {"status":"ok"}`
avec `--network none`, donc l'exigence est atteignable.

## Ce que ce lab ne demande PAS, et c'est délibéré

Ni utilisateur non-root, ni image allégée, ni multi-étapes. La leçon jumelée
enseigne les instructions essentielles d'un Dockerfile, et les labs suivants
reprendront cette image pour en montrer le coût. Exiger ici tout ce que la série
enseigne priverait la progression de son objet.
"""

from __future__ import annotations

import time

import pytest

from conftest import (
    conteneur_temporaire,
    en_mio,
    etapes,
    exiger_build,
    exiger_workdir,
    inspecter_image,
    nom_objet,
    retirer_image,
    taille_affichee,
    workdir_lab,
)

WORKDIR = workdir_lab(__file__)
LAB_ID = "images-premiere-image"

# L'image que les tests construisent. Le préfixe `dsoxlab-` écarte toute
# collision avec une image de l'apprenant qui s'appellerait « inventaire ».
TAG = nom_objet(LAB_ID)

# Le port que la leçon fait déclarer, et celui sur lequel uvicorn écoute.
PORT = 8000


@pytest.fixture(scope="module")
def image() -> str:
    """Construit l'image une seule fois, et la retire à la fin du module.

    Une construction par test coûterait quatre fois dix-sept secondes sur cette
    machine, pour exactement la même image. Les tests lisent tous la même, ce
    qui est aussi plus honnête : ils décrivent UN résultat.
    """
    exiger_workdir(WORKDIR, LAB_ID)
    exiger_build(WORKDIR, TAG)
    try:
        yield TAG
    finally:
        retirer_image(TAG)


def test_l_image_part_de_debian_12(image: str) -> None:
    """Le socle demandé par la leçon, lu dans le Dockerfile.

    « De quelle image part-on » est une propriété du FICHIER : une fois l'image
    construite, le moteur ne dit plus de quel `FROM` elle vient. C'est le seul
    contrôle de ce lab qui lit le texte, et il n'a pas d'autre moyen.
    """
    bases = etapes(WORKDIR / "Dockerfile")
    assert bases, (
        "Aucune instruction `FROM` dans votre Dockerfile.\n\nC'est la première "
        "ligne de tout Dockerfile : elle dit sur quoi l'image est construite, "
        "et rien ne peut se faire avant elle."
    )
    assert len(bases) == 1, (
        f"Votre Dockerfile porte {len(bases)} instructions `FROM` : {bases}.\n\n"
        "Ce lab construit une image en une seule étape. Le multi-étapes est le "
        "sujet d'un lab plus loin dans la série, et il n'apporterait rien ici."
    )
    socle = bases[0].split()[0]
    assert socle.startswith("debian:12"), (
        f"L'image part de `{socle}`, et la mission demande Debian 12.\n\n"
        "Ce n'est pas un caprice : toute la série repart de cette image pour "
        "montrer, mesure après mesure, ce que chaque optimisation retire. "
        "Commencer ailleurs ferait disparaître le point de comparaison."
    )


def test_l_application_repond_dans_un_conteneur(image: str) -> None:
    """La preuve qu'une image sert à quelque chose : son application tourne."""
    with conteneur_temporaire(
        image, nom_objet(LAB_ID, "repond"), publier=True, port_interne=PORT
    ) as conteneur:
        code, corps = conteneur.repondre("/health")
        assert code == 200, (
            f"`GET /health` rend {code or 'rien du tout'}.\n\n"
            f"Journal du conteneur :\n{conteneur.journal()}\n\n"
            "Trois causes possibles, dans l'ordre de fréquence : l'application "
            "n'est pas lancée par le `CMD` ; elle écoute sur `127.0.0.1`, qui "
            "dans un conteneur ne désigne que le conteneur lui-même ; ou elle "
            "écoute sur un autre port que celui déclaré."
        )
        assert '"ok"' in corps, (
            f"`/health` répond 200 mais rend `{corps[:120]}`, et non "
            '`{"status": "ok"}`. L\'application servie n\'est pas celle du '
            "point de départ."
        )


def test_le_port_est_declare_par_expose(image: str) -> None:
    """`EXPOSE` ne publie rien : il documente, et les outils le lisent.

    Un conteneur répond avec `-p` même sans `EXPOSE`, donc ce contrôle ne peut
    pas se déduire du précédent. Ce qu'il vérifie est une intention écrite :
    quel port cette image attend qu'on lui publie.
    """
    ports = inspecter_image(image).get("Config", {}).get("ExposedPorts") or {}
    assert ports, (
        "L'image ne déclare aucun port.\n\n`EXPOSE` n'ouvre rien et ne publie "
        "rien : c'est de la documentation, lue par `docker inspect`, par "
        "Compose et par celui qui reprendra votre image. Sans elle, il doit "
        "lire votre code pour deviner le port."
    )
    attendu = f"{PORT}/tcp"
    assert attendu in ports, (
        f"L'image déclare {sorted(ports)}, et l'application écoute sur "
        f"{PORT}.\n\nUn `EXPOSE` qui ne correspond pas au port servi est pire "
        "qu'absent : il envoie le lecteur au mauvais endroit."
    )


def test_l_image_embarque_python_et_les_dependances(image: str) -> None:
    """Python et FastAPI sont DANS l'image, pas espérés au démarrage.

    L'image de base n'a pas Python : c'est le premier constat du lab. Ce
    contrôle vérifie que l'installation a bien eu lieu pendant le build, en
    interrogeant l'image plutôt que son Dockerfile.
    """
    with conteneur_temporaire(
        image,
        nom_objet(LAB_ID, "outils"),
        commande=["sleep", "60"],
    ) as conteneur:
        res = conteneur.dans("python3", "--version")
        assert res.returncode == 0, (
            "`python3 --version` échoue dans le conteneur.\n\n"
            f"{(res.stdout + res.stderr).strip()[:300]}\n\n"
            "L'image `debian:12` ne contient pas Python : c'est précisément ce "
            "que la première étape du lab fait constater. Il doit être "
            "installé pendant le build."
        )

        importe = conteneur.dans("python3", "-c", "import fastapi, uvicorn")
        assert importe.returncode == 0, (
            "Python est là, mais `import fastapi, uvicorn` échoue.\n\n"
            f"{(importe.stdout + importe.stderr).strip()[:300]}\n\n"
            "Les dépendances de `requirements.txt` doivent être installées "
            "dans l'image, au build."
        )


def test_l_image_est_autonome_sans_aucun_reseau(image: str) -> None:
    """Le contrôle qui distingue une image d'un script d'installation.

    ## Pourquoi les deux moitiés sont dans le même test

    « L'application répond » est déjà vrai au premier contrôle : isolé, le
    second serait une hypothèse du setup. Réunis, ils disent autre chose, et
    c'est le cœur du lab : l'image répond ENCORE quand on lui retire le réseau,
    donc tout ce dont elle a besoin est dedans.

    Une image qui installerait ses dépendances dans son `CMD` passerait les
    quatre premiers contrôles et échouerait ici. Elle échouerait aussi chez un
    apprenant hors ligne, dans une usine sans Internet, ou le jour où PyPI
    répond mal : ce lab fait rencontrer ce défaut tout de suite.

    ## Pourquoi on interroge depuis l'intérieur

    Avec `--network none`, le conteneur n'a aucune interface : on ne peut pas
    lui publier de port, donc pas l'interroger depuis l'hôte. On lui demande
    d'interroger sa propre boucle locale, qui est tout ce qu'il lui reste.
    """
    sonde = (
        "import json, urllib.request;"
        f"r = urllib.request.urlopen('http://127.0.0.1:{PORT}/health', timeout=5);"
        "print(r.status, r.read().decode())"
    )

    with conteneur_temporaire(
        image, nom_objet(LAB_ID, "sans-reseau"), arguments=["--network", "none"]
    ) as conteneur:
        # L'application a besoin de quelques instants pour écouter : on
        # réessaie, plutôt que de mesurer trop tôt et de recaler un lab juste.
        derniere = ""
        for _ in range(40):
            res = conteneur.dans("python3", "-c", sonde)
            if res.returncode == 0 and "200" in res.stdout:
                break
            derniere = (res.stdout + res.stderr).strip()
            time.sleep(0.5)
        else:
            pytest.fail(
                "Sans réseau, l'application ne répond pas.\n\n"
                f"Dernière tentative : {derniere[:400]}\n\n"
                f"Journal du conteneur :\n{conteneur.journal()}\n\n"
                "Une image doit être autonome : tout ce que l'application "
                "exige est installé pendant le build, jamais au démarrage. "
                "Si vos dépendances s'installent dans le `CMD`, elles "
                "manqueront partout où le réseau manque."
            )

    # La seconde moitié : l'image reste fonctionnelle AVEC le réseau. Un
    # Dockerfile qui aurait tout cassé pour satisfaire la première moitié
    # échouerait ici.
    with conteneur_temporaire(
        image, nom_objet(LAB_ID, "avec-reseau"), publier=True, port_interne=PORT
    ) as conteneur:
        code, _ = conteneur.repondre("/health")
        assert code == 200, (
            "L'application répond sans réseau mais plus avec : "
            f"`GET /health` rend {code or 'rien'}.\n\n"
            f"{conteneur.journal()}"
        )

    # Ce que l'apprenant a sous les yeux, dit une fois dans le rapport : c'est
    # le point de comparaison de tous les labs d'optimisation qui suivent.
    print(f"\nimage `{TAG}` : {en_mio(taille_affichee(TAG))} Mio affichés par `docker images`")


def test_le_repertoire_de_travail_de_l_image_est_declare(image: str) -> None:
    """`WORKDIR` : où l'application vit dans l'image.

    Sans lui, les chemins relatifs du `CMD` partent de `/`, et `uvicorn
    main:app` ne trouve pas son module. Un lab qui passerait le reste sans
    `WORKDIR` aurait écrit des chemins absolus partout, ce qui marche et se
    relit mal.
    """
    config = inspecter_image(image).get("Config", {})
    travail = (config.get("WorkingDir") or "").rstrip("/")
    assert travail, (
        "L'image ne déclare aucun `WORKDIR`.\n\nLes chemins relatifs partent "
        "alors de la racine, et `uvicorn main:app` ne trouve pas son module : "
        "il le cherche dans `/`. Déclarer le répertoire de l'application rend "
        "aussi la suite du Dockerfile lisible."
    )


def test_la_commande_de_demarrage_est_declaree(image: str) -> None:
    """Une image sans `CMD` ne démarre rien, et le dit mal.

    `docker run` sans commande rend alors le `CMD` de l'image de base, c'est-à-
    dire `bash` pour Debian : le conteneur démarre, s'arrête aussitôt faute
    d'entrée, et rien n'explique pourquoi l'API ne répond pas.
    """
    config = inspecter_image(image).get("Config", {})
    demarrage = (config.get("Cmd") or []) + (config.get("Entrypoint") or [])
    assert demarrage, (
        "L'image ne déclare ni `CMD` ni `ENTRYPOINT`.\n\n`docker run` "
        "exécuterait alors la commande de `debian:12`, c'est-à-dire un shell "
        "qui s'arrête immédiatement."
    )
    joint = " ".join(demarrage)
    assert "uvicorn" in joint or "main" in joint, (
        f"La commande de démarrage est `{joint}`, et ne lance pas "
        "l'application.\n\nC'est `uvicorn` qui sert une application FastAPI."
    )
