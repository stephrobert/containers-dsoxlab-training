"""Tests fonctionnels de l'épreuve epreuve-restaurer-une-stack : quatre contrôles de poids égal.

CE QUE CETTE ÉPREUVE PROUVE. Qu'une pile se remonte ailleurs, avec SES DONNÉES,
sans perdre au passage ce qui la rendait défendable : l'isolement du réseau de
données. Les deux moitiés sont indissociables, parce que remettre tout à plat
est précisément le raccourci qui fait « marcher » une restauration.

LE SEUIL EST À 75 %, soit trois contrôles sur quatre. C'est délibéré pour un
capstone : un candidat qui remonte la pile, restaure le témoin et traverse les
trois étages a démontré l'essentiel.

LES CONTRÔLES REGARDENT LE CLIENT, et c'est tout leur intérêt. L'hôte d'origine
n'est plus de confiance : une pile qui ne tournerait que là n'aurait rien
restauré.

L'ISOLEMENT EST MESURÉ, PAS LU. Le quatrième contrôle lance une sonde sur le
réseau public et constate qu'elle n'atteint PAS `db`, puis vérifie que `api`, lui,
l'atteint. Lire `internal: true` dans un fichier ne prouverait rien : le fichier
peut déclarer ce qu'il veut, c'est le moteur qui décide.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, message

ATELIER = "/opt/lab-restauration"
RELEVE = "/root/.lab-restauration.json"
PROJET = "dsoxlab-restauration"
URL = "http://127.0.0.1:18090/enregistrements"
IMAGE = "lab-restauration/service:1.0"

ORIGINE = "docker.lab"
CLIENT = "docker-client.lab"


@pytest.fixture(scope="module")
def host():
    """L'hôte d'origine : il ne porte plus que le relevé privé du banc."""
    return lab_host(ORIGINE)


@pytest.fixture(scope="module")
def client():
    """Le client, et c'est LUI qui doit porter la pile restaurée."""
    return lab_host(CLIENT)


def _releve(host) -> dict:
    """Le témoin tiré au hasard, écrit avant la panne."""
    res = host.run("cat %s", RELEVE)
    if res.rc != 0:
        pytest.fail(message(
            en=f"{RELEVE} is missing: the setup did not finish",
            fr=f"{RELEVE} est absent : le setup n'a pas abouti",
        ))
    return json.loads(res.stdout)


def _services(client) -> dict:
    """Les trois conteneurs du projet, par leur service Compose."""
    res = client.run(
        "docker ps -aq --filter %s",
        f"label=com.docker.compose.project={PROJET}",
    )
    identifiants = res.stdout.split()
    if res.rc != 0 or not identifiants:
        pytest.fail(message(
            en=f"no container of project `{PROJET}` on {CLIENT}. The stack has "
               "to be brought back up there.",
            fr=f"aucun conteneur du projet `{PROJET}` sur {CLIENT}. La pile "
               "doit y être remontée.",
        ))
    # LES IDENTIFIANTS NE PASSENT PAS PAR `%s`, et c'est la raison d'un
    # échec du 2026-11-02. testinfra échappe chaque `%s` comme UN
    # argument : une liste jointe arrive entre apostrophes, et `docker
    # inspect 'id1 id2 id3'` ne désigne rien. Ce sont des identifiants
    # rendus par le moteur, pas des entrées d'apprenant : on les écrit
    # donc dans la commande.
    inspecte = client.run("docker inspect " + " ".join(identifiants))
    if inspecte.rc != 0:
        pytest.fail(message(
            en="cannot inspect the project's containers.",
            fr="impossible d'inspecter les conteneurs du projet.",
        ))
    return {
        c["Config"]["Labels"].get("com.docker.compose.service"): c
        for c in json.loads(inspecte.stdout)
    }


def _requete(client) -> dict:
    """La requête métier, telle qu'un utilisateur la ferait : par le front."""
    res = client.run(
        "curl --noproxy '*' --fail --silent --max-time 10 %s", URL,
    )
    if res.rc != 0:
        pytest.fail(message(
            en=f"the front end does not answer on 127.0.0.1:18090 on {CLIENT}: "
               f"{res.stderr[-200:]}",
            fr=f"le front ne répond pas sur 127.0.0.1:18090 sur {CLIENT} : "
               f"{res.stderr[-200:]}",
        ))
    return json.loads(res.stdout)


def test_les_trois_etages_tournent_sur_le_client_et_la_requete_les_traverse(client) -> None:
    """La pile est remontée AILLEURS, et la requête traverse vraiment.

    TROIS CONTENEURS NE SUFFISENT PAS. Ils pourraient tourner sans se parler :
    la requête métier le dit, puisqu'elle n'aboutit que si `front` joint `api`
    et que `api` joint `db`. Le service rend la liste des étages traversés.
    """
    services = _services(client)
    assert set(services) >= {"front", "api", "db"}, message(
        en=f"the restored stack carries {sorted(services)} and the three "
           "services front, api and db are expected.",
        fr=f"la pile restaurée porte {sorted(services)} et les trois services "
           "front, api et db sont attendus.",
    )
    arretes = [
        nom for nom, c in services.items() if not c["State"]["Running"]
    ]
    assert not arretes, message(
        en=f"these services are not running: {arretes}.",
        fr=f"ces services ne tournent pas : {arretes}.",
    )

    rendu = _requete(client)
    assert rendu.get("traverse") == ["front", "api", "db"], message(
        en=f"the business request does not cross the three tiers.\n"
           f"  crossed : {rendu.get('traverse')}\n"
           "Each tier calls the next by its service name: a tier that answers "
           "alone has not restored the chain.",
        fr=f"la requête métier ne traverse pas les trois étages.\n"
           f"  traversé : {rendu.get('traverse')}\n"
           "Chaque étage appelle le suivant par son nom de service : un étage "
           "qui répond seul n'a pas rétabli la chaîne.",
    )


def test_le_temoin_a_ete_restaure(host, client) -> None:
    """La donnée, et c'est la raison d'être d'une restauration.

    LE TÉMOIN EST TIRÉ AU HASARD À CHAQUE PASSAGE, et le test le lit dans le
    relevé privé de l'hôte d'origine. Une valeur en dur se recopierait d'un
    passage sur l'autre, et le contrôle ne prouverait plus que la sauvegarde de
    CE passage a été relue.

    IL EST LU À TRAVERS LE FRONT, et non dans le volume : une donnée qu'on ne
    peut pas servir n'est pas restaurée, elle est seulement présente.
    """
    temoin = _releve(host)["temoin"]
    rendu = _requete(client)
    enregistrements = rendu.get("enregistrements", [])
    assert temoin in enregistrements, message(
        en=f"the witness record (`{temoin}`) is not served by the restored "
           "stack.\n"
           f"  served : {enregistrements or 'nothing'}\n"
           "The backup is in /opt/lab-restauration/sauvegarde.",
        fr=f"l'enregistrement témoin (`{temoin}`) n'est pas servi par la pile "
           "restaurée.\n"
           f"  servis : {enregistrements or 'aucun'}\n"
           "La sauvegarde est dans /opt/lab-restauration/sauvegarde.",
    )


def test_le_reseau_de_donnees_est_reste_isole(client) -> None:
    """L'isolement, lu sur le MOTEUR et non dans un fichier.

    DEUX FAITS QUI NE SE SÉPARENT PAS. Le réseau qui porte `db` est interne, et
    `db` ne publie aucun port. Un réseau interne n'a pas de passerelle : rien
    n'y entre depuis l'hôte. Un port publié ferait exactement le trou que
    l'isolement devait fermer.

    Le fichier de la pile n'est pas lu : il peut déclarer ce qu'il veut, c'est
    le moteur qui décide.
    """
    services = _services(client)
    db = services.get("db")
    assert db, message(
        en="no `db` service in the restored stack.",
        fr="aucun service `db` dans la pile restaurée.",
    )
    assert not db["HostConfig"]["PortBindings"], message(
        en=f"`db` publishes {list(db['HostConfig']['PortBindings'])}, and it "
           "must publish nothing: a published port opens exactly the hole the "
           "isolation was closing.",
        fr=f"`db` publie {list(db['HostConfig']['PortBindings'])}, et il ne "
           "doit rien publier : un port publié ouvre exactement le trou que "
           "l'isolement fermait.",
    )

    reseaux = list(db["NetworkSettings"]["Networks"])
    assert reseaux, message(
        en="`db` is attached to no network at all.",
        fr="`db` n'est rattaché à aucun réseau.",
    )
    # Même raison que plus haut : des noms rendus par le moteur, joints.
    inspecte = client.run("docker network inspect " + " ".join(reseaux))
    assert inspecte.rc == 0, message(
        en=f"cannot inspect `db`'s networks: {reseaux}",
        fr=f"impossible d'inspecter les réseaux de `db` : {reseaux}",
    )
    details = json.loads(inspecte.stdout)
    assert all(r.get("Internal") for r in details), message(
        en="at least one of `db`'s networks is not internal:\n"
           f"  {[(r['Name'], r.get('Internal')) for r in details]}\n"
           "Flattening the stack onto one network is the shortcut that makes a "
           "restoration «work» and is refused here.",
        fr="au moins un des réseaux de `db` n'est pas interne :\n"
           f"  {[(r['Name'], r.get('Internal')) for r in details]}\n"
           "Mettre la pile à plat sur un seul réseau est le raccourci qui fait "
           "« marcher » une restauration, et il est refusé ici.",
    )


def test_la_sonde_sur_le_reseau_public_n_atteint_pas_la_base(client) -> None:
    """L'isolement, ÉPROUVÉ, et pas seulement déclaré.

    LE CONTRÔLE MESURE LES DEUX SENS, et il faut les deux. Une sonde posée sur
    le réseau public ne doit PAS joindre `db` ; `api`, lui, doit le joindre.
    Sans le second sens, une pile dont `db` serait simplement arrêté passerait
    le premier.

    LA SONDE EST JETABLE, sans nom partagé et sans port : elle ne touche à rien.
    """
    services = _services(client)
    db = services["db"]
    api = services["api"]

    publics = [
        nom for nom in api["NetworkSettings"]["Networks"]
        if nom in db["NetworkSettings"]["Networks"]
    ]
    assert publics, message(
        en="`api` and `db` share no network: the chain cannot hold.",
        fr="`api` et `db` ne partagent aucun réseau : la chaîne ne peut pas "
           "tenir.",
    )
    cote_public = [
        nom for nom in api["NetworkSettings"]["Networks"] if nom not in publics
    ]
    assert cote_public, message(
        en="`api` is only on `db`'s network: the front end cannot reach it.",
        fr="`api` n'est que sur le réseau de `db` : le front ne peut pas "
           "l'atteindre.",
    )

    sonde = client.run(
        "docker run --rm --pull never --network %s --label %s %s "
        "python -c %s",
        cote_public[0], "dsoxlab.lab=epreuve-restaurer-une-stack", IMAGE,
        "import socket,sys\n"
        "try:\n"
        "    socket.create_connection(('db', 5432), timeout=4).close()\n"
        "    print('ATTEINTE')\n"
        "except OSError as souci:\n"
        "    print('REFUSEE')\n",
    )
    assert "REFUSEE" in sonde.stdout, message(
        en=f"a probe on the public network reaches `db`:\n"
           f"  {sonde.stdout.strip() or sonde.stderr[-200:]}\n"
           "The data network has to stay unreachable from the public side.",
        fr=f"une sonde sur le réseau public atteint `db` :\n"
           f"  {sonde.stdout.strip() or sonde.stderr[-200:]}\n"
           "Le réseau de données doit rester injoignable depuis le côté "
           "public.",
    )

    # ET `api` DOIT L'ATTEINDRE : sans ce sens, un `db` arrete passerait.
    depuis_api = client.run(
        "docker exec %s python -c %s", api["Id"],
        "import socket\n"
        "socket.create_connection(('db', 5432), timeout=4).close()\n"
        "print('ATTEINTE')\n",
    )
    assert "ATTEINTE" in depuis_api.stdout, message(
        en=f"`api` does not reach `db` either:\n"
           f"  {depuis_api.stdout.strip() or depuis_api.stderr[-200:]}\n"
           "Isolation is not meant to cut the chain, only to close the public "
           "side.",
        fr=f"`api` n'atteint pas `db` non plus :\n"
           f"  {depuis_api.stdout.strip() or depuis_api.stderr[-200:]}\n"
           "L'isolement n'est pas censé couper la chaîne, seulement fermer le "
           "côté public.",
    )
