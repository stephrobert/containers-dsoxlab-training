"""Tests fonctionnels du lab compose-profils-et-variantes : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un montage de développement ne se voit pas dans le
fichier de base, mais dans la configuration EFFECTIVE, et qu'un fichier de
déploiement doit se lire sur ce qu'il produit et non sur ce qu'il déclare.

L'APPAREIL DE MESURE EST L'ÉCART ENTRE DEUX VERSIONS. L'image porte la sienne,
figée à la construction, le disque en porte une autre. La réponse du service dit
donc sans ambiguïté lequel des deux il lit : aucune interprétation n'est
nécessaire, et un montage oublié ne peut pas passer pour une absence de montage.

LES DEUX JETONS SONT TIRÉS AU HASARD À CHAQUE PASSAGE, et les tests les lisent
dans le relevé privé du banc. Des valeurs en dur se recopieraient d'un passage
sur l'autre.

LE DEUXIÈME CONTRÔLE LANCE LA VARIANTE DE DÉVELOPPEMENT, et il le fait dans un
PROJET À PART. Sans cela il remplacerait la pile de déploiement, qui est l'état
final noté par le premier contrôle : un test ne doit pas défaire ce qu'un autre
mesure. Il la retire dans un `finally`.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, message

ATELIER = "/opt/lab-variantes"
RELEVE = "/root/.lab-variantes.json"
BASE = f"{ATELIER}/compose.yaml"
DEV = f"{ATELIER}/compose.dev.yaml"
DEPLOIEMENT = f"{ATELIER}/compose.deploiement.yaml"
PROJET = "dsoxlab-variantes"
PROJET_DEV = "dsoxlab-variantes-dev"
URL = "http://127.0.0.1:18081/"

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


def _releve(host) -> dict:
    """Les deux versions tirées au hasard, et le digest de l'image."""
    res = host.run("cat %s", RELEVE)
    if res.rc != 0:
        pytest.fail(message(
            en=f"{RELEVE} is missing: the setup did not finish",
            fr=f"{RELEVE} est absent : le setup n'a pas abouti",
        ))
    return json.loads(res.stdout)


def _config(host, fichiers: list[str], profils: list[str] | None = None) -> dict:
    """La configuration EFFECTIVE, telle que Compose la résout.

    C'est ce que le lab fait regarder : un fichier d'entrée peut tout déclarer,
    seule la résolution dit ce qui sera lancé. Les profils demandés sont passés
    explicitement, puisque leur effet est précisément ce que le quatrième
    contrôle mesure.
    """
    # LES OPTIONS NE PASSENT PAS PAR `%s`, et c'est la raison d'un échec du
    # 2026-11-02. testinfra échappe chaque `%s` comme UN argument : une chaîne
    # « -f a -f b » arrive alors entre apostrophes, et une liste de profils
    # vide arrive en `''`. Docker répond `unknown docker command: "compose "`,
    # ce qui ne désigne rien de ce qui cloche. Les chemins et les profils de ce
    # contrôle sont des constantes du lab, pas des entrées d'apprenant : on les
    # écrit donc dans la commande.
    options = " ".join(f"-f {f}" for f in fichiers)
    profil = " ".join(f"--profile {p}" for p in (profils or []))
    res = host.run(
        f"cd {ATELIER} && docker compose -p {PROJET} {profil} {options} "
        "config --format json"
    )
    if res.rc != 0:
        pytest.fail(message(
            en=f"Compose cannot resolve {fichiers}: {res.stderr[-400:]}",
            fr=f"Compose ne résout pas {fichiers} : {res.stderr[-400:]}",
        ))
    return json.loads(res.stdout)


def _montages(service: dict) -> list[dict]:
    """Les montages déclarés par un service dans la configuration effective."""
    return service.get("volumes") or []


def _fichier(host, chemin: str) -> str:
    f = host.file(chemin)
    if not f.exists:
        pytest.fail(message(
            en=f"{chemin} is missing: the mission asks you to write it.",
            fr=f"{chemin} est absent : la mission demande de l'écrire.",
        ))
    return f.content_string


def test_le_deploiement_tourne_sans_aucun_montage(host) -> None:
    """L'état final, et il se lit sur le conteneur, pas sur un fichier.

    DEUX FAITS QUI NE SE SÉPARENT PAS. Le conteneur ne porte aucun montage, et
    le service rend la version de l'IMAGE. Le premier pourrait être obtenu en
    oubliant de lancer la pile ; le second prouve qu'elle tourne vraiment, et
    qu'elle lit bien ce que l'image porte.
    """
    releve = _releve(host)

    res = host.run(
        "docker container inspect %s --format %s",
        "dsoxlab-variantes-app", "{{json .Mounts}}",
    )
    if res.rc != 0:
        pytest.fail(message(
            en="container `dsoxlab-variantes-app` does not exist. The "
               "deployment variant has to be up.",
            fr="le conteneur `dsoxlab-variantes-app` n'existe pas. La variante "
               "de déploiement doit tourner.",
        ))
    montages = json.loads(res.stdout)
    assert not montages, message(
        en=f"the running container carries {len(montages)} mount(s), and the "
           "deployment variant must carry none:\n"
           f"  {[m.get('Destination') for m in montages]}\n"
           "A development mount left behind in deployment is the classic "
           "incident.",
        fr=f"le conteneur en service porte {len(montages)} montage(s), et la "
           "variante de déploiement ne doit en porter aucun :\n"
           f"  {[m.get('Destination') for m in montages]}\n"
           "Un montage de développement oublié en déploiement est l'incident "
           "classique.",
    )

    rendu = host.run("curl --noproxy '*' --fail --silent --max-time 8 %s", URL)
    assert rendu.rc == 0, message(
        en="the service does not answer on 127.0.0.1:18081.",
        fr="le service ne répond pas sur 127.0.0.1:18081.",
    )
    assert rendu.stdout.strip() == releve["version_image"], message(
        en=f"the service answers `{rendu.stdout.strip()}`, which is not the "
           "image's version. Without a mount it reads what the image carries.",
        fr=f"le service répond `{rendu.stdout.strip()}`, qui n'est pas la "
           "version de l'image. Sans montage, il lit ce que l'image porte.",
    )


def test_la_variante_de_developpement_monte_les_sources(host) -> None:
    """Le montage, dans la configuration effective PUIS à l'exécution.

    La configuration dit ce qui est déclaré ; l'exécution dit ce qui se passe.
    Les deux sont vérifiées, parce qu'un montage peut être déclaré sur le
    mauvais chemin et ne rien monter du tout.

    DANS UN PROJET À PART, pour ne pas remplacer la pile de déploiement, et
    retiré dans un `finally` même si le contrôle échoue.
    """
    releve = _releve(host)
    _fichier(host, DEV)

    config = _config(host, [BASE, DEV])
    app = config.get("services", {}).get("app")
    assert app, message(
        en="the development variant resolves no `app` service.",
        fr="la variante de développement ne résout aucun service `app`.",
    )
    montages = _montages(app)
    assert any(
        m.get("target") == "/app/src" for m in montages
    ), message(
        en=f"the development variant declares no mount onto /app/src:\n"
           f"  {[m.get('target') for m in montages] or 'none'}",
        fr=f"la variante de développement ne déclare aucun montage sur "
           f"/app/src :\n"
           f"  {[m.get('target') for m in montages] or 'aucun'}",
    )

    try:
        monte = host.run(
            "cd %s && docker compose -p %s -f %s -f %s run --rm --no-deps "
            "--entrypoint cat app /app/src/version.txt",
            ATELIER, PROJET_DEV, BASE, DEV,
        )
        assert monte.rc == 0, message(
            en=f"the development variant cannot be run: {monte.stderr[-400:]}",
            fr=f"la variante de développement ne peut pas être lancée : "
               f"{monte.stderr[-400:]}",
        )
        assert releve["version_source"] in monte.stdout, message(
            en=f"the development variant reads `{monte.stdout.strip()}`, not "
               "the disk's version. Its mount declares the wrong path: nothing "
               "is actually mounted.",
            fr=f"la variante de développement lit `{monte.stdout.strip()}`, pas "
               "la version du disque. Son montage désigne le mauvais chemin : "
               "rien n'est monté en réalité.",
        )
    finally:
        host.run(
            "cd %s && docker compose -p %s -f %s -f %s down --remove-orphans",
            ATELIER, PROJET_DEV, BASE, DEV,
        )


def test_le_fichier_de_base_ne_porte_aucun_montage(host) -> None:
    """La variante se DÉRIVE, elle ne se glisse pas dans la base.

    Le montage doit venir de la variante de développement, et d'elle seule. Le
    mettre dans le fichier de base donnerait le même résultat en développement,
    et ramènerait l'incident exact que le lab fait éviter : le déploiement lit
    ce fichier aussi.
    """
    config = _config(host, [BASE])
    for nom, service in config.get("services", {}).items():
        montages = _montages(service)
        assert not montages, message(
            en=f"the base file declares a mount on `{nom}`:\n"
               f"  {[m.get('target') for m in montages]}\n"
               "Derive the variants instead: deployment reads this file too.",
            fr=f"le fichier de base déclare un montage sur `{nom}` :\n"
               f"  {[m.get('target') for m in montages]}\n"
               "Dérivez les variantes : le déploiement lit ce fichier aussi.",
        )
    _fichier(host, DEPLOIEMENT)
    deploiement = _config(host, [BASE, DEPLOIEMENT])
    app = deploiement.get("services", {}).get("app")
    assert app, message(
        en="the deployment variant resolves no `app` service.",
        fr="la variante de déploiement ne résout aucun service `app`.",
    )
    montages = _montages(app)
    assert not montages, message(
        en=f"the deployment variant declares {len(montages)} mount(s), and it "
           f"must declare none: {[m.get('target') for m in montages]}",
        fr=f"la variante de déploiement déclare {len(montages)} montage(s), et "
           f"elle ne doit en déclarer aucun : "
           f"{[m.get('target') for m in montages]}",
    )


def test_le_service_optionnel_n_apparait_que_sous_son_profil(host) -> None:
    """Un profil n'est pas un commentaire : il retire le service de la
    résolution.

    LE CONTRÔLE REGARDE LES DEUX SENS, et il faut les deux. Qu'un service
    optionnel apparaisse sous son profil ne prouve rien si on ne vérifie pas
    qu'il disparaît sans lui : une variante qui aurait retiré le profil
    passerait le premier sens.
    """
    sans = _config(host, [BASE, DEPLOIEMENT])
    assert "debug" not in sans.get("services", {}), message(
        en="the optional `debug` service appears without its profile being "
           "requested. A profile is what keeps it out of the resolution.",
        fr="le service optionnel `debug` apparaît sans que son profil soit "
           "demandé. C'est le profil qui le tient hors de la résolution.",
    )
    avec = _config(host, [BASE, DEPLOIEMENT], profils=["debug"])
    assert "debug" in avec.get("services", {}), message(
        en="the optional `debug` service does not appear under its `debug` "
           "profile. Deriving must not remove it.",
        fr="le service optionnel `debug` n'apparaît pas sous son profil "
           "`debug`. La dérivation ne doit pas le supprimer.",
    )
    dev_sans = _config(host, [BASE, DEV])
    assert "debug" not in dev_sans.get("services", {}), message(
        en="the optional `debug` service appears in the development variant "
           "without its profile being requested.",
        fr="le service optionnel `debug` apparaît dans la variante de "
           "développement sans que son profil soit demandé.",
    )
