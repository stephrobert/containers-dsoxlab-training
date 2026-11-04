"""Une sauvegarde ne vaut qu'après restauration, et chaque pièce se note à part.

POURQUOI SIX CONTRÔLES LÀ OÙ IL N'Y EN AVAIT QU'UN. Ce lab est un `challenge` :
il NOTE un apprenant. Son contrôle unique mesurait pourtant sept choses
distinctes, chaînées dans une seule fonction, si bien que la note ne pouvait
valoir que 0 % ou 100 %. Celui qui avait tout réussi sauf le marqueur de
propriété obtenait le même zéro que celui qui n'avait rien fait, et il
n'apprenait rien de son échec puisque les mesures suivantes n'avaient jamais eu
lieu : la première assertion tombée arrêtait tout.

Chaque contrôle est donc indépendant. Il relit l'état du lab, vérifie ce qui le
concerne, et ne suppose rien de ce qu'un autre a mesuré. Un apprenant qui a
sauvegardé et transféré mais raté la restauration le voit maintenant dans le
détail de sa note.

CE QUI N'EST PLUS UN CONTRÔLE NOTÉ. L'ancienne version vérifiait que
`pg_restore` refuse une sauvegarde invalide (`/dev/null`). C'est une propriété
de `pg_restore`, vraie quoi que fasse l'apprenant : il ne peut ni la provoquer
ni la faire échouer, donc elle ne le notait pas. Elle reste, mais comme
GARDE-FOU DE MESURE à l'intérieur du sixième contrôle : si `pg_restore`
annonçait un succès sur une sauvegarde invalide, le succès qu'il annonce sur la
vraie ne voudrait plus rien dire.

CE QUE LA DESCRIPTION PROMETTAIT SANS LE MESURER. Le lab annonce qu'on
« vérifie le service en marche », et le scénario dit que « le service PostgreSQL
cible répond à des requêtes réelles ». Rien ne le vérifiait. Le quatrième
contrôle le fait, sur la machine de restauration, par une requête qui ne
dépendrait pas du travail de l'apprenant si le service était à l'arrêt.
"""

from __future__ import annotations

import json
import secrets
import shlex

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


@pytest.fixture
def restore_host():
    return lab_host("docker-client.lab")


@pytest.fixture
def etat(host):
    """L'état que le setup a déposé, relu à chaque contrôle.

    CHAQUE CONTRÔLE LE RELIT, et c'est le prix de leur indépendance : aucun ne
    peut supposer qu'un autre a déjà constaté la présence du fichier. Son
    absence est d'ailleurs un défaut d'infrastructure et non une faute de
    l'apprenant, donc le message le dit.
    """
    fichier = host.file("/opt/lab-postgres-sauvegarde/state.json")
    assert fichier.exists, message(
        en="The PostgreSQL source fixture is missing: the lab was not set up. "
           "Run `dsoxlab run donnees-postgres-sauvegarde` again.",
        fr="Le jeu de données PostgreSQL source est absent : le lab n'a pas été "
           "posé. Rejouez `dsoxlab run donnees-postgres-sauvegarde`.",
    )
    return json.loads(fichier.content_string)


# ────────────────────────────── les outils ──────────────────────────────────


def _psql(machine, base, sql):
    """Joue une requête sous le compte `postgres`, sans mot de passe.

    `-X` ignore le `.psqlrc` de la machine, `-A -t` rendent une sortie sans
    décor, et `ON_ERROR_STOP=1` fait échouer la commande au premier problème au
    lieu de rendre 0 avec une erreur dans la sortie.
    """
    return machine.run(
        shlex.join([
            "sudo", "-n", "-u", "postgres", "--",
            "psql", "-X", "-A", "-t", "-v", "ON_ERROR_STOP=1",
            "-d", base, "-c", sql,
        ])
    )


def _lignes(machine, base):
    """Les lignes de `orders`, dans un ordre stable, ou None si illisible.

    ON REND None AU LIEU DE LEVER, pour que l'appelant choisisse son message :
    « la base n'existe pas » et « la base existe mais ses lignes diffèrent »
    sont deux fautes distinctes, et les confondre enverrait l'apprenant chercher
    au mauvais endroit.
    """
    resultat = _psql(
        machine, base,
        "SELECT id || '|' || region || '|' || total_cents FROM orders ORDER BY id",
    )
    if resultat.rc != 0:
        return None
    return resultat.stdout.splitlines()


def _litteral_sql(valeur):
    """Échappe une chaîne pour l'insérer dans une requête.

    Les noms de bases viennent du setup et non de l'apprenant, mais on les
    échappe tout de même : un nom lu dans un fichier est une donnée, et on ne
    concatène pas une donnée dans du SQL sans l'échapper.
    """
    return "'" + valeur.replace("'", "''") + "'"


def _empreinte(machine, chemin):
    """L'empreinte SHA-256 d'un fichier, ou None s'il est absent."""
    resultat = machine.run("sha256sum %s", chemin)
    if resultat.rc != 0:
        return None
    return resultat.stdout.split()[0]


# ───────────────────────────── les six contrôles ────────────────────────────


def test_la_sauvegarde_existe_au_format_personnalise(host, etat) -> None:
    """Le format personnalisé, reconnu à sa signature et non à son extension.

    `pg_dump -Fc` écrit un en-tête qui commence par `PGDMP`. On le lit sur les
    cinq premiers octets : une extension `.dump` ne prouve rien, et un `pg_dump`
    sans `-Fc` produit du SQL en clair qui porterait le même nom de fichier.
    """
    sauvegarde = f"{etat['backup_dir']}/orders.dump"
    presence = host.run("test -f %s", sauvegarde)
    assert presence.rc == 0, message(
        en=f"No backup at {sauvegarde}. Create a PostgreSQL custom-format dump "
           "at exactly that path.",
        fr=f"Aucune sauvegarde à {sauvegarde}. Créez une sauvegarde PostgreSQL "
           "au format personnalisé exactement à ce chemin.",
    )
    entete = host.run("head -c 5 %s", sauvegarde)
    assert entete.rc == 0 and entete.stdout == "PGDMP", message(
        en=f"The file at {sauvegarde} is not a custom-format dump: its first "
           f"bytes are {entete.stdout!r} instead of 'PGDMP'. A plain SQL dump "
           "carries the same name but not the same format; use `pg_dump -Fc`.",
        fr=f"Le fichier {sauvegarde} n'est pas au format personnalisé : ses "
           f"premiers octets valent {entete.stdout!r} au lieu de « PGDMP ». "
           "Une sauvegarde SQL en clair porte le même nom mais pas le même "
           "format ; employez `pg_dump -Fc`.",
    )


def test_la_sauvegarde_a_ete_transferee_a_l_identique(host, restore_host, etat) -> None:
    """Le même fichier des deux côtés, et c'est l'anti-triche du lab.

    POURQUOI L'EMPREINTE ET NON LA SEULE PRÉSENCE. Sans elle, recréer les trois
    lignes à la main sur la seconde machine passerait tous les autres contrôles :
    les lignes y seraient, la base aussi, le marqueur aussi. L'empreinte exige
    que le fichier qui a servi soit CELUI qui a été produit, et c'est la seule
    mesure qui distingue une restauration d'une recopie.
    """
    sauvegarde = f"{etat['backup_dir']}/orders.dump"
    source = _empreinte(host, sauvegarde)
    assert source is not None, message(
        en=f"No backup at {sauvegarde} on docker.lab: the first check says so.",
        fr=f"Aucune sauvegarde à {sauvegarde} sur docker.lab : le premier "
           "contrôle le dit.",
    )
    cible = _empreinte(restore_host, sauvegarde)
    assert cible is not None, message(
        en=f"No backup at {sauvegarde} on docker-client.lab. Transfer the dump "
           "to the same path on the second VM.",
        fr=f"Aucune sauvegarde à {sauvegarde} sur docker-client.lab. "
           "Transférez la sauvegarde au même chemin sur la seconde VM.",
    )
    assert source == cible, message(
        en="The dump on docker-client.lab is not the one produced on "
           f"docker.lab ({cible[:16]}… against {source[:16]}…). Transfer the "
           "exact file; recreating the rows by hand is not a restore.",
        fr="La sauvegarde présente sur docker-client.lab n'est pas celle "
           f"produite sur docker.lab ({cible[:16]}… contre {source[:16]}…). "
           "Transférez le fichier exact ; recréer les lignes à la main n'est "
           "pas une restauration.",
    )


def test_le_service_cible_repond_et_porte_la_base_marquee(restore_host, etat) -> None:
    """Le service en marche, puis la base et son marqueur.

    DANS CET ORDRE, ET C'EST VOULU. Si le service ne répond pas, toute question
    sur la base rend la même erreur, et le message accuserait l'apprenant de ne
    pas avoir créé une base alors que c'est le moteur qui est muet. On interroge
    donc d'abord le service par une requête qui ne dépend d'aucun travail.

    C'est aussi ce que la description du lab promettait sans jamais le mesurer.
    """
    vivant = _psql(restore_host, "postgres", "SELECT 1")
    assert vivant.rc == 0 and vivant.stdout.strip() == "1", message(
        en="PostgreSQL does not answer on docker-client.lab: "
           f"{vivant.stderr[-300:]}. Start the service before restoring.",
        fr="PostgreSQL ne répond pas sur docker-client.lab : "
           f"{vivant.stderr[-300:]}. Démarrez le service avant de restaurer.",
    )
    marqueur = _psql(
        restore_host, "postgres",
        "SELECT COALESCE(shobj_description(oid, 'pg_database'), '') "
        "FROM pg_database WHERE datname = " + _litteral_sql(etat["restored_db"]),
    )
    assert marqueur.rc == 0, message(
        en=f"Cannot query the database list on docker-client.lab: "
           f"{marqueur.stderr[-300:]}",
        fr=f"Impossible d'interroger la liste des bases sur docker-client.lab : "
           f"{marqueur.stderr[-300:]}",
    )
    trouve = marqueur.stdout.strip()
    assert trouve, message(
        en=f"The database {etat['restored_db']} does not exist on "
           "docker-client.lab, or carries no comment. Create it there and "
           "apply the OWNERSHIP marker from state.env.",
        fr=f"La base {etat['restored_db']} n'existe pas sur docker-client.lab, "
           "ou ne porte aucun commentaire. Créez-la là-bas et posez le "
           "marqueur OWNERSHIP de state.env.",
    )
    assert trouve == etat["ownership"], message(
        en=f"The restore database carries {trouve!r} instead of the exact "
           f"OWNERSHIP marker {etat['ownership']!r}. Cleanup identifies the "
           "session's resources by this comment.",
        fr=f"La base de restauration porte {trouve!r} au lieu du marqueur "
           f"OWNERSHIP exact {etat['ownership']!r}. Le nettoyage identifie les "
           "ressources de la session par ce commentaire.",
    )


def test_la_base_restauree_porte_toutes_les_lignes(host, restore_host, etat) -> None:
    """Chaque ligne restaurée, et la source laissée intacte.

    On compare l'ensemble ordonné et non un décompte : trois lignes dont une
    valeur a changé donnent le même compte que trois lignes justes, et c'est
    exactement la faute qu'une recopie à la main produit.

    POURQUOI L'INTÉGRITÉ DE LA SOURCE EST VÉRIFIÉE ICI, et non dans un contrôle
    à elle. Elle en avait un, et le cycle de validation l'a refusé avec raison :
    avant tout travail, la source EST intacte, donc ce contrôle passait, et un
    contrôle qui passe avant le travail ne mesure pas le travail. Il annonçait
    1/6 là où le validateur exige 0. Rattachée à la restauration, la même
    vérification garde toute sa valeur : elle refuse un travail qui aurait
    restauré SUR la source au lieu de la seconde machine, et elle ne peut plus
    être satisfaite sans que la restauration ait eu lieu.
    """
    lignes = _lignes(restore_host, etat["restored_db"])
    assert lignes is not None, message(
        en=f"Cannot read the orders table in {etat['restored_db']} on "
           "docker-client.lab. The table must exist there after the restore.",
        fr=f"Impossible de lire la table orders dans {etat['restored_db']} sur "
           "docker-client.lab. La table doit y exister après la restauration.",
    )
    assert lignes == etat["rows"], message(
        en=f"The restored rows differ from the source. Expected "
           f"{etat['rows']}, found {lignes}.",
        fr=f"Les lignes restaurées diffèrent de la source. Attendu "
           f"{etat['rows']}, trouvé {lignes}.",
    )

    # LA SOURCE N'A PAS BOUGÉ. On sauvegarde une base, on ne la modifie pas, et
    # son marqueur est vérifié aussi : un `dropdb` suivi d'un `createdb`
    # effacerait le commentaire sans toucher aux lignes.
    source = _lignes(host, etat["source_db"])
    assert source is not None, message(
        en=f"The source database {etat['source_db']} is unreadable or gone. It "
           "must be left exactly as it was: the backup is taken FROM it.",
        fr=f"La base source {etat['source_db']} est illisible ou a disparu. "
           "Elle doit rester exactement telle quelle : la sauvegarde se prend "
           "DEPUIS elle.",
    )
    assert source == etat["rows"], message(
        en=f"The source rows changed. Expected {etat['rows']}, found {source}. "
           "Restore onto the second VM, never onto the source.",
        fr=f"Les lignes de la source ont changé. Attendu {etat['rows']}, "
           f"trouvé {source}. Restaurez sur la seconde VM, jamais sur la "
           "source.",
    )
    marqueur = _psql(
        host, "postgres",
        "SELECT COALESCE(shobj_description(oid, 'pg_database'), '') "
        "FROM pg_database WHERE datname = " + _litteral_sql(etat["source_db"]),
    )
    assert marqueur.rc == 0 and marqueur.stdout.strip() == etat["ownership"], (
        message(
            en=f"The source database lost its ownership marker (found "
               f"{marqueur.stdout.strip()!r}). Dropping and recreating it "
               "erases the comment even when the rows look right.",
            fr=f"La base source a perdu son marqueur de propriété (trouvé "
               f"{marqueur.stdout.strip()!r}). La supprimer puis la recréer "
               "efface le commentaire même quand les lignes semblent justes.",
        )
    )


def test_la_sauvegarde_se_restaure_dans_une_base_vierge(restore_host, etat) -> None:
    """La sauvegarde est-elle réutilisable, ou le résultat tient-il à l'histoire ?

    CE QUE CE CONTRÔLE AJOUTE AUX AUTRES. Les précédents constatent un état :
    la base de restauration contient les bonnes lignes. Celui-ci rejoue la
    sauvegarde dans une base NEUVE et vérifie qu'elle reproduit la source.
    C'est la différence entre « ça marche aujourd'hui » et « la sauvegarde est
    bonne », et c'est la seule question qui compte le jour où on s'en sert.

    LE GARDE-FOU DE MESURE, qui n'est pas une note. On vérifie d'abord que
    `pg_restore` REFUSE une sauvegarde invalide. Ce n'est pas un travail de
    l'apprenant, il ne peut ni le provoquer ni le rater : c'est la condition
    pour que le succès annoncé ensuite veuille dire quelque chose. Si
    `pg_restore` rendait 0 sur `/dev/null`, son 0 sur la vraie sauvegarde ne
    prouverait rien.

    LA BASE D'ESSAI PORTE UN NOM ALÉATOIRE et disparaît dans un `finally` : un
    contrôle qui laisse un objet derrière lui fait payer le lab suivant.
    """
    sauvegarde = f"{etat['backup_dir']}/orders.dump"
    base_essai = f"dsoxlab_check_{secrets.token_hex(6)}"
    cree = restore_host.run(
        shlex.join(["sudo", "-n", "-u", "postgres", "--", "createdb", base_essai])
    )
    assert cree.rc == 0, message(
        en=f"Could not create the temporary verification database: "
           f"{cree.stderr[-300:]}",
        fr=f"Impossible de créer la base temporaire de vérification : "
           f"{cree.stderr[-300:]}",
    )
    try:
        invalide = restore_host.run(
            shlex.join(["sudo", "-n", "-u", "postgres", "--", "pg_restore",
                        "--no-owner", "--no-privileges", "-d", base_essai,
                        "/dev/null"])
        )
        assert invalide.rc != 0, message(
            en="`pg_restore` reported success on an empty file. The tool on "
               "this machine cannot tell a valid dump from an invalid one, so "
               "no restore result can be trusted. This is not your mistake: "
               "report it.",
            fr="`pg_restore` a annoncé un succès sur un fichier vide. L'outil "
               "de cette machine ne distingue pas une sauvegarde valide d'une "
               "sauvegarde invalide, donc aucun résultat de restauration n'est "
               "fiable. Ce n'est pas votre faute : signalez-le.",
        )
        rejoue = restore_host.run(
            shlex.join(["sudo", "-n", "-u", "postgres", "--", "pg_restore",
                        "--no-owner", "--no-privileges", "-d", base_essai,
                        sauvegarde])
        )
        assert rejoue.rc == 0, message(
            en=f"The saved dump cannot be restored into a fresh database: "
               f"{rejoue.stderr[-400:]}. A dump that only works on the "
               "database it came from is not a backup.",
            fr=f"La sauvegarde ne peut pas être restaurée dans une base "
               f"vierge : {rejoue.stderr[-400:]}. Une sauvegarde qui ne "
               "fonctionne que sur la base dont elle vient n'est pas une "
               "sauvegarde.",
        )
        lignes = _lignes(restore_host, base_essai)
        assert lignes == etat["rows"], message(
            en=f"Restoring into a fresh database gives {lignes} instead of "
               f"{etat['rows']}. The dump does not carry the source rows.",
            fr=f"La restauration dans une base vierge donne {lignes} au lieu "
               f"de {etat['rows']}. La sauvegarde ne porte pas les lignes de "
               "la source.",
        )
    finally:
        retire = restore_host.run(
            shlex.join(["sudo", "-n", "-u", "postgres", "--", "dropdb",
                        "--if-exists", base_essai])
        )
        assert retire.rc == 0, message(
            en=f"Could not remove the temporary database {base_essai} from "
               "docker-client.lab. It must not survive the check.",
            fr=f"Impossible de retirer la base temporaire {base_essai} de "
               "docker-client.lab. Elle ne doit pas survivre au contrôle.",
        )
