"""Tests fonctionnels du lab troubleshoot-permission-refusee : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Que trois refus d'accès qui se lisent comme un seul « ça
ne marche pas » ont trois causes sans rapport, et que les messages les
distinguent déjà.

MESURÉ SUR docker.lab LE 2026-10-30 :

| Panne | Message | Inspection | Cause |
| A | « Read-only file system » | RW=**false** | le montage interdit |
| B | « Permission denied » | RW=**true** | les droits refusent |
| C | code **126** | RW=true | le mode du fichier manque |

LA LEÇON EST DANS LA PAIRE A/B. Les deux messages sont différents, et on les lit
souvent comme un seul. Le premier accuse le MONTAGE, le second dit que le
montage est d'accord et que ce sont les DROITS qui refusent. L'inspection les
sépare en un mot, et c'est pourquoi le premier contrôle porte sur ce mot.

LE C RELIE CE LAB AU PRÉCÉDENT : son code est celui du fichier trouvé mais non
exécutable, déjà rencontré dans `troubleshoot-exit-127`. Ici la cause est
ailleurs : le fichier vient d'un montage, et son mode est celui de l'hôte, qu'un
montage ne change jamais.

LA RÉPARATION DE B EST NOTÉE SUR LE MOYEN, et c'est le seul endroit du
catalogue où un contrôle refuse une solution qui marche. Repasser le conteneur
en root réglerait le symptôme : le contrôle l'interdit, parce que
`donnees-permissions-uid-gid` a déjà montré la bonne réponse, et qu'un lab de
dépannage ne doit pas défaire ce qu'un lab de méthode a enseigné.

AUCUNE VALEUR N'EST ÉCRITE EN DUR DANS CE FICHIER. Les trois attendues sont lues
sur les conteneurs au moment de la notation.

UNE PRÉCISION SUR L'ÉLÉVATION. `lab_host()` ouvre la machine avec `sudo=true` :
les répertoires de l'épreuve appartiennent à root, et les lire sans élévation
rendrait des réponses vides.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, message

LECTURE_SEULE = "perm-a"
DROITS = "perm-b"
SANS_BIT = "perm-c"
# LE TÉMOIN reste en échec du début à la fin : c'est sur lui que se lit
# le code, parce qu'une valeur de diagnostic ne peut pas se lire sur un
# objet que la réparation modifie.
TEMOIN = "temoin-sans-bit"
ATELIER = "/opt/lab-permission"
REPONSES = f"{ATELIER}/reponses.txt"
# Ce chemin est DANS LE CONTENEUR, où il n'est pas partagé et disparaît avec
# lui : ce n'est pas un fichier temporaire de l'hôte, d'où le noqa.
PREUVE = "/tmp/preuve.txt"  # noqa: S108

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


def _champ(host, nom: str, format_go: str) -> str:
    """Un champ de l'inspection d'un conteneur, ou une chaîne vide."""
    res = host.run("docker container inspect %s --format %s", nom, format_go)
    return res.stdout.strip() if res.rc == 0 else ""


def _lire_reponses(host) -> dict[str, str]:
    """Le formulaire, réduit à ses paires clé=valeur.

    Tolérant sur la forme (espaces, lignes vides, commentaires, casse de la
    clé), strict sur le fond : c'est le contenu qui est noté, pas la mise en
    page.
    """
    f = host.file(REPONSES)
    if not f.exists:
        pytest.fail(message(
            en=f"{REPONSES} is missing. The mission asks for three lines in "
               "it: rw_b=, uid_b= and code_c=.",
            fr=f"{REPONSES} est absent. La mission demande d'y écrire trois "
               "lignes : rw_b=, uid_b= et code_c=.",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def test_la_reponse_dit_que_le_montage_de_b_autorise_l_ecriture(host) -> None:
    """Le contrôle qui porte la leçon, et il tient en un mot.

    Les deux premières pannes se ressemblent : un conteneur n'arrive pas à
    écrire. Les messages diffèrent déjà, et l'inspection tranche : le montage de
    `perm-a` interdit l'écriture, celui de `perm-b` l'autorise.

    Savoir cela écarte d'emblée la moitié des pistes sur `perm-b` : ce n'est pas
    le montage, donc c'est ailleurs.
    """
    attendu = _champ(host, DROITS, "{{(index .Mounts 0).RW}}")
    if not attendu:
        pytest.skip(message(
            en=f"container `{DROITS}` has no mount: the setup did not finish",
            fr=f"le conteneur `{DROITS}` n'a aucun montage : le setup n'a pas "
               "abouti",
        ))

    annonce = _lire_reponses(host).get("rw_b", "").lower()
    assert annonce, message(
        en=f"the `rw_b=` line is empty. `{DROITS}` cannot write, like "
           f"`{LECTURE_SEULE}`, and yet the cause is not the same: the "
           "inspection of its mount says so in one word.",
        fr=f"la ligne `rw_b=` est vide. `{DROITS}` n'arrive pas à écrire, comme "
           f"`{LECTURE_SEULE}`, et la cause n'est pourtant pas la même : "
           "l'inspection de son montage le dit en un mot.",
    )
    assert annonce == attendu.lower(), message(
        en=f"the announced value is not the one the inspection declares for "
           f"`{DROITS}`'s mount.\n"
           f"  you wrote : {annonce}\n"
           f"Compare it with `{LECTURE_SEULE}`'s: the two containers fail the "
           "same way and their mounts do not say the same thing. One forbids "
           "writing, the other allows it, and that changes where to look.",
        fr=f"la valeur annoncée n'est pas celle que l'inspection déclare pour "
           f"le montage de `{DROITS}`.\n"
           f"  vous avez écrit : {annonce}\n"
           f"Comparez-la à celle de `{LECTURE_SEULE}` : les deux conteneurs "
           "échouent de la même façon et leurs montages ne disent pas la même "
           "chose. L'un interdit l'écriture, l'autre l'autorise, et cela change "
           "l'endroit où chercher.",
    )


def test_la_reponse_donne_l_identite_du_conteneur_b(host) -> None:
    """La vraie cause de la seconde panne, et elle n'est pas dans le montage.

    Le montage autorise l'écriture ; c'est l'identité du conteneur qui n'a pas
    le droit d'écrire dans ce répertoire. Lire cette identité est le pas suivant
    du diagnostic, et c'est celui qu'on saute.
    """
    attendu = host.run("docker exec %s id -u", DROITS).stdout.strip()
    if not attendu:
        pytest.skip(message(
            en=f"container `{DROITS}` does not answer: the setup did not finish",
            fr=f"le conteneur `{DROITS}` ne répond pas : le setup n'a pas abouti",
        ))

    annonce = _lire_reponses(host).get("uid_b", "")
    assert annonce, message(
        en="the `uid_b=` line is empty. The mount allows writing, so the "
           "question becomes: who is writing? Ask the container.",
        fr="la ligne `uid_b=` est vide. Le montage autorise l'écriture, donc la "
           "question devient : qui écrit ? Demandez-le au conteneur.",
    )
    assert annonce == attendu, message(
        en=f"the announced identity is not `{DROITS}`'s.\n"
           f"  you wrote : {annonce}\n"
           "It is read inside the container, not in what was asked at creation: "
           "it is the real identity of the processes that decides the rights.",
        fr=f"l'identité annoncée n'est pas celle de `{DROITS}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "Elle se lit dans le conteneur, et non dans ce qui a été demandé à "
           "la création : c'est l'identité réelle des processus qui décide des "
           "droits.",
    )


def test_la_reponse_donne_le_code_de_sortie_de_c(host) -> None:
    """Le troisième refus, et il ne porte pas sur une écriture.

    Celui-là n'a même pas démarré. Son code est celui du fichier trouvé mais non
    exécutable, déjà rencontré dans le lab des codes de sortie, et la cause est
    ailleurs : le fichier vient d'un montage, et son mode est celui de l'hôte.

    Un montage ne change aucun mode. C'est ce qui explique qu'un script
    parfaitement exécutable sur un poste de développement ne le soit pas dans le
    conteneur qui le monte.
    """
    attendu = _champ(host, TEMOIN, "{{.State.ExitCode}}")
    if not attendu:
        pytest.skip(message(
            en=f"container `{TEMOIN}` does not exist: the setup did not finish",
            fr=f"le conteneur `{TEMOIN}` n'existe pas : le setup n'a pas "
               "abouti",
        ))

    # LE TÉMOIN DOIT ÊTRE RESTÉ EN PANNE, sans quoi la question n'a plus
    # d'objet : un conteneur réparé ne porte plus le code qu'on demande.
    tourne = _champ(host, TEMOIN, "{{.State.Running}}")
    assert tourne == "false", message(
        en=f"`{TEMOIN}` is running: it is the witness, and the brief asks "
           "for it not to be repaired. Its exit code is what the question "
           "is about, and a repaired container no longer carries one.",
        fr=f"`{TEMOIN}` tourne : c'est le témoin, et l'énoncé demande de "
           "ne pas le réparer. Son code de sortie est l'objet de la "
           "question, et un conteneur réparé n'en porte plus.",
    )

    annonce = _lire_reponses(host).get("code_c", "")
    assert annonce, message(
        en=f"the `code_c=` line is empty. `{TEMOIN}` did not even start: its "
           "exit code says why, and you have already met it.",
        fr=f"la ligne `code_c=` est vide. `{TEMOIN}` n'a même pas démarré : "
           "son code de sortie dit pourquoi, et vous l'avez déjà rencontré.",
    )
    assert annonce == attendu, message(
        en=f"the announced code is not `{TEMOIN}`'s.\n"
           f"  you wrote : {annonce}\n"
           "It is the code of a file found but not runnable. The cause is in the "
           "file's mode, which comes from the host: a mount never changes one.",
        fr=f"le code annoncé n'est pas celui de `{TEMOIN}`.\n"
           f"  vous avez écrit : {annonce}\n"
           "C'est le code d'un fichier trouvé mais non exécutable. La cause est "
           "dans le mode du fichier, qui vient de l'hôte : un montage n'en "
           "change jamais aucun.",
    )


def test_les_trois_pannes_sont_reparees(host) -> None:
    """Trois réparations, et la seconde est notée sur le MOYEN.

    C'est le seul endroit du catalogue où un contrôle refuse une solution qui
    marche. Repasser `perm-b` en root réglerait son symptôme, et le contrôle
    l'interdit : `donnees-permissions-uid-gid` a déjà montré la bonne réponse,
    et un lab de dépannage ne doit pas défaire ce qu'un lab de méthode a
    enseigné.

    Chaque réparation est éprouvée par l'EFFET, jamais par l'option : une
    écriture réelle pour les deux premières, la trace du script pour la
    troisième.
    """
    essai_a = host.run(
        "docker exec %s sh -c %s", LECTURE_SEULE, "echo epreuve > /ref/.epreuve"
    )
    assert essai_a.rc == 0, message(
        en=f"`{LECTURE_SEULE}` still cannot write into /ref: "
           f"{essai_a.stderr.strip()}\n"
           "Its mount forbids writing, and that is decided at the container's "
           "creation: it has to be recreated.",
        fr=f"`{LECTURE_SEULE}` n'écrit toujours pas dans /ref : "
           f"{essai_a.stderr.strip()}\n"
           "Son montage interdit l'écriture, et cela se décide à la création du "
           "conteneur : il faut le recréer.",
    )
    host.run("docker exec %s rm -f /ref/.epreuve", LECTURE_SEULE)

    uid_b = host.run("docker exec %s id -u", DROITS).stdout.strip()
    assert uid_b and uid_b != "0", message(
        en=f"`{DROITS}` now runs as root (uid {uid_b or '?'}).\n"
           "That would fix the symptom and it is refused here: the lab on "
           "permissions has shown the right answer, which is to align the "
           "group. A troubleshooting lab must not undo what a method lab "
           "taught.",
        fr=f"`{DROITS}` tourne désormais en root (uid {uid_b or '?'}).\n"
           "Cela réglerait le symptôme et c'est refusé ici : le lab sur les "
           "permissions a montré la bonne réponse, qui est d'aligner le groupe. "
           "Un lab de dépannage ne doit pas défaire ce qu'un lab de méthode a "
           "enseigné.",
    )
    essai_b = host.run(
        "docker exec %s sh -c %s", DROITS, "echo epreuve > /donnees/.epreuve"
    )
    assert essai_b.rc == 0, message(
        en=f"`{DROITS}` still cannot write into /donnees: "
           f"{essai_b.stderr.strip()}\n"
           "Its mount allows writing, so the rights are what refuse. Align them "
           "without making the container root.",
        fr=f"`{DROITS}` n'écrit toujours pas dans /donnees : "
           f"{essai_b.stderr.strip()}\n"
           "Son montage autorise l'écriture, donc ce sont les droits qui "
           "refusent. Alignez-les sans passer le conteneur en root.",
    )
    host.run("docker exec %s rm -f /donnees/.epreuve", DROITS)

    etat_c = _champ(host, SANS_BIT, "{{.State.Status}}")
    assert etat_c == "running", message(
        en=f"`{SANS_BIT}` is in state `{etat_c or 'absent'}`, not `running`.\n"
           "Its script's mode comes from the host, and a mount never changes "
           "one: it is on the host that it has to be made runnable, and the "
           "container has to be relaunched.",
        fr=f"`{SANS_BIT}` est dans l'état `{etat_c or 'absent'}`, pas "
           "`running`.\n"
           "Le mode de son script vient de l'hôte, et un montage n'en change "
           "jamais aucun : c'est sur l'hôte qu'il faut le rendre exécutable, et "
           "le conteneur qu'il faut relancer.",
    )
    trace = host.run("docker exec %s cat %s", SANS_BIT, PREUVE)
    assert "le-script-a-tourne" in trace.stdout, message(
        en=f"`{SANS_BIT}` runs, but {PREUVE} does not carry the script's "
           "trace.\n"
           "So it runs something else: the point is that ITS script ran, not "
           "that the container is alive.",
        fr=f"`{SANS_BIT}` tourne, mais {PREUVE} ne porte pas la trace du "
           "script.\n"
           "Il tourne donc autre chose : le but est que SON script ait tourné, "
           "pas que le conteneur soit vivant.",
    )
