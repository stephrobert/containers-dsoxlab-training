"""Tests fonctionnels du lab compose-retour-arriere : quatre contrôles de poids égal.

CE QUE CE LAB PROUVE. Qu'un retour en arrière ramène le code et non les données,
et qu'il cesse d'être possible dès qu'une release a migré l'état. Les deux faits
sont liés : c'est parce que les données survivent au retour qu'une migration
irréversible le ferme définitivement.

CE QUI EST NOTÉ EST UN ÉTAT, PAS UN CHEMIN. La `3.0` tourne, par digest, l'état
est en schéma 2, les deux enregistrements y sont, et le constat est rempli.
L'apprenant peut y arriver par `docker compose up`, par une réécriture du
fichier, ou autrement : le verdict ne regarde pas ses commandes.

LE TÉMOIN EST TIRÉ AU HASARD À CHAQUE PASSAGE, et le test le relit dans le
relevé privé du banc. Une valeur en dur se recopierait d'un passage sur l'autre,
et le contrôle ne prouverait plus que la DONNÉE a survécu, seulement qu'une
chaîne connue se trouve là.

LE QUATRIÈME CONTRÔLE MESURE LE REFUS, il ne se contente pas de le lire dans le
constat. Il lance la `2.0` contre le volume migré et constate qu'elle s'arrête :
un apprenant qui aurait écrit les trois bonnes valeurs sans jamais essayer ne
peut pas les avoir trouvées, mais le contrôle ne lui fait pas confiance pour
autant. Le constat, lui, prouve qu'il a regardé.
"""

from __future__ import annotations

import json
import uuid

import pytest

from conftest import lab_host, message

ATELIER = "/opt/lab-retour"
RELEVE = "/root/.lab-retour.json"
CONSTAT = f"{ATELIER}/constat.txt"
PROJET = "dsoxlab-retour"
SERVICE = "dsoxlab-retour-service"
URL = "http://127.0.0.1:18080/etat"

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
    """Le relevé privé du banc : le témoin tiré au hasard et les trois digests."""
    res = host.run("cat %s", RELEVE)
    if res.rc != 0:
        pytest.fail(message(
            en=f"{RELEVE} is missing: the setup did not finish",
            fr=f"{RELEVE} est absent : le setup n'a pas abouti",
        ))
    return json.loads(res.stdout)


def _etat(host) -> dict:
    """Ce que le service déclare : sa release, son schéma, ses enregistrements."""
    res = host.run("curl --noproxy '*' --fail --silent --max-time 8 %s", URL)
    if res.rc != 0:
        pytest.fail(message(
            en="the service does not answer on 127.0.0.1:18080. The stack has "
               "to be running for anything to be graded.",
            fr="le service ne répond pas sur 127.0.0.1:18080. La pile doit "
               "tourner pour que quoi que ce soit soit noté.",
        ))
    return json.loads(res.stdout)


def _valeurs(etat: dict) -> list[str]:
    """Les enregistrements, quelle que soit la forme que le schéma leur donne.

    Le schéma 1 les garde en chaînes, le schéma 2 en objets. Le contenu, lui,
    ne change pas, et c'est lui que le lab demande de ne pas perdre.
    """
    rendu = []
    for r in etat.get("records", []):
        rendu.append(r["valeur"] if isinstance(r, dict) else r)
    return rendu


def _paires(host, chemin: str, quoi: str) -> dict[str, str]:
    """Un fichier `clé=valeur`, réduit à ses paires.

    Tolérant sur la forme (espaces, lignes vides, commentaires, casse de la
    clé), strict sur le fond : c'est le contenu qui est noté, pas la mise en
    page.
    """
    f = host.file(chemin)
    if not f.exists:
        pytest.fail(message(
            en=f"{chemin} is missing: {quoi}",
            fr=f"{chemin} est absent : {quoi}",
        ))
    paires = {}
    for brute in f.content_string.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        paires[cle.strip().lower()] = valeur.strip()
    return paires


def test_la_trois_tourne_et_elle_est_epinglee_par_digest(host) -> None:
    """La release en service, et la façon dont elle est désignée.

    UN DIGEST, PAS UNE ÉTIQUETTE. Une étiquette peut être déplacée sans que rien
    ne change dans le fichier qui la cite : elle ne dit donc pas ce qui tourne.
    Le contrôle lit la référence que le conteneur porte, et exige qu'elle
    désigne le digest de la `3.0`.
    """
    releve = _releve(host)
    attendu = releve["releases"]["3.0"]

    res = host.run(
        "docker container inspect %s --format %s", SERVICE, "{{.Config.Image}}"
    )
    if res.rc != 0:
        pytest.fail(message(
            en=f"container `{SERVICE}` does not exist. The stack has to be up.",
            fr=f"le conteneur `{SERVICE}` n'existe pas. La pile doit tourner.",
        ))
    reference = res.stdout.strip()
    assert "@sha256:" in reference, message(
        en=f"the service runs `{reference}`, which is not a digest.\n"
           "A tag can be moved without the file that cites it changing: it does "
           "not say what is running.",
        fr=f"le service tourne sur `{reference}`, qui n'est pas un digest.\n"
           "Une étiquette peut être déplacée sans que le fichier qui la cite "
           "change : elle ne dit pas ce qui tourne.",
    )
    assert reference == attendu, message(
        en=f"the service does not run release 3.0.\n"
           f"  it runs  : {reference}\n"
           f"  expected : {attendu}\n"
           "The three digests are in /opt/lab-retour/releases.json.",
        fr=f"le service ne tourne pas la release 3.0.\n"
           f"  il tourne : {reference}\n"
           f"  attendu   : {attendu}\n"
           "Les trois digests sont dans /opt/lab-retour/releases.json.",
    )
    etat = _etat(host)
    assert etat.get("release") == "3.0", message(
        en=f"the running service declares release `{etat.get('release')}`, "
           "not 3.0.",
        fr=f"le service en cours déclare la release `{etat.get('release')}`, "
           "pas 3.0.",
    )


def test_la_migration_a_eu_lieu(host) -> None:
    """Le schéma 2, et la forme migrée des enregistrements.

    La `3.0` migre en entrant, et le dit dans son journal. Le contrôle ne lit
    pas ce journal : il regarde l'état, qui est ce qui compte. Un journal peut
    être effacé, l'état non.
    """
    etat = _etat(host)
    assert etat.get("schema") == 2, message(
        en=f"the state is at schema {etat.get('schema')}, not 2. Release 3.0 "
           "migrates it on start.",
        fr=f"l'état est en schéma {etat.get('schema')}, pas 2. La release 3.0 "
           "le migre en démarrant.",
    )
    records = etat.get("records", [])
    assert records and all(isinstance(r, dict) and "valeur" in r for r in records), message(
        en="the records are not in their migrated form. Schema 2 keeps them as "
           "objects, schema 1 kept them as strings.",
        fr="les enregistrements ne sont pas sous leur forme migrée. Le schéma 2 "
           "les garde en objets, le schéma 1 les gardait en chaînes.",
    )


def test_les_deux_enregistrements_ont_survecu(host) -> None:
    """Le retour en arrière ramène le code, pas les données.

    DEUX ENREGISTREMENTS, ET AUCUN DES DEUX NE DOIT MANQUER. Celui que la
    production avait écrit avant l'arrivée de l'apprenant, et celui qu'il a
    écrit lui-même sous la `2.0`. Le premier prouve que la bascule n'a rien
    effacé ; le second, qu'il a bien écrit PENDANT la 2.0 et non après.

    Le témoin est tiré au hasard à chaque passage : il se lit dans le relevé du
    banc, et ne se recopie pas d'un passage sur l'autre.
    """
    temoin = _releve(host)["temoin"]
    valeurs = _valeurs(_etat(host))

    assert temoin in valeurs, message(
        en=f"the record written before you arrived (`{temoin}`) is gone.\n"
           f"  present : {valeurs or 'nothing'}\n"
           "A rollback brings back the code, not the data: the volume must not "
           "be recreated.",
        fr=f"l'enregistrement écrit avant votre arrivée (`{temoin}`) a "
           "disparu.\n"
           f"  présents : {valeurs or 'aucun'}\n"
           "Un retour en arrière ramène le code, pas les données : le volume ne "
           "doit pas être recréé.",
    )
    assert len(valeurs) >= 2, message(
        en=f"only {len(valeurs)} record(s) in the state, at least two expected: "
           "the one from before you arrived, and the one the mission asks you to "
           "write while 2.0 is running.",
        fr=f"{len(valeurs)} enregistrement(s) seulement dans l'état, deux au "
           "moins attendus : celui d'avant votre arrivée, et celui que la "
           "mission demande d'écrire pendant que la 2.0 tourne.",
    )


def test_le_retour_a_la_deux_est_refuse_et_le_constat_le_dit(host) -> None:
    """Le refus, mesuré ici, et le constat qui prouve qu'il a été regardé.

    LE CONTRÔLE MESURE LE REFUS LUI-MÊME. Il lance la `2.0` contre le volume
    migré, hors de la pile, et constate qu'elle s'arrête en nommant le schéma
    qu'elle ne sait pas lire. Un conteneur jetable, sans nom partagé et sans
    port : il ne touche ni à la pile ni au reste du moteur.

    LE CONSTAT EST NOTÉ EN PLUS, et non à la place. Les trois valeurs ne se
    devinent pas : il faut avoir lancé la 2.0 pour voir le message et le code
    de sortie. C'est la trace du geste, là où l'état ne garde que son résultat.
    """
    releve = _releve(host)
    deux = releve["releases"]["2.0"]

    # LE NOM DE LA SONDE EST UNIQUE À CHAQUE PASSAGE, et elle est retirée dans
    # un `finally`. Mesuré le 2026-11-02 : un nom fixe entre en conflit avec ce
    # qu'un passage précédent, ou l'apprenant lui-même, a laissé derrière, et
    # Docker répond alors « name is already in use ». Le contrôle accusait la
    # release 2.0 de ne pas refuser, alors qu'elle n'avait jamais démarré. Un
    # contrôle ne doit pas dépendre de ce qu'un autre a laissé.
    sonde = f"dsoxlab-retour-essai-{uuid.uuid4().hex[:12]}"
    try:
        # LA SONDE EST DETACHEE, ET SON ATTENTE EST BORNEE. Mesuré le
        # 2026-11-02 : lancée au premier plan, elle NE REND PAS LA MAIN quand
        # la release 2.0 accepte l'état, puisqu'elle démarre alors son serveur
        # et tourne. `dsoxlab check` sortait sur son propre délai de 300
        # secondes, et le relevé disait « aucun test n'a été collecté », ce qui
        # n'avait aucun rapport. Un contrôle qui peut pendre n'est pas un
        # contrôle.
        #
        # Si elle tourne encore au bout de l'attente, c'est qu'elle a ACCEPTÉ
        # l'état : le contrôle le dit alors, au lieu de pendre.
        lance = host.run(
            "docker run -d --pull never --name %s --label %s -v %s %s",
            sonde, "dsoxlab.lab=compose-retour-arriere",
            f"{PROJET}_donnees:/data", deux,
        )
        assert lance.rc == 0, message(
            en=f"release 2.0 cannot even be started: {lance.stderr[-300:]}",
            fr=f"la release 2.0 ne peut même pas être lancée : "
               f"{lance.stderr[-300:]}",
        )
        attente = host.run(
            "for i in $(seq 1 %s); do "
            "  etat=$(docker container inspect %s --format '{{.State.Status}}'); "
            "  if [ \"$etat\" != running ]; then break; fi; sleep 1; "
            "done; "
            "docker container inspect %s "
            "--format '{{.State.Status}} {{.State.ExitCode}}'",
            "20", sonde, sonde,
        )
        statut, _, code = attente.stdout.strip().partition(" ")
        assert statut == "exited", message(
            en=f"release 2.0 is still `{statut}` after 20 seconds: it accepted "
               "the state, which it should not, since it reads schema 1 at "
               "most.",
            fr=f"la release 2.0 est encore `{statut}` après vingt secondes : "
               "elle a accepté l'état, ce qu'elle ne devrait pas, puisqu'elle "
               "lit au plus le schéma 1.",
        )
        # LE JOURNAL EST LU AVANT LE RETRAIT : la sonde est détachée, donc
        # son message n'arrive pas sur la sortie de `docker run`.
        journal = host.run("docker logs %s", sonde)
        sortie_sonde = journal.stdout + journal.stderr
    finally:
        host.run("docker rm -f %s", sonde)

    assert code not in ("", "0"), message(
        en=f"release 2.0 exited with code `{code or '?'}`: it accepted the "
           "migrated state, which it should not, since it reads schema 1 at "
           "most.",
        fr=f"la release 2.0 est sortie avec le code `{code or '?'}` : elle a "
           "accepté l'état migré, ce qu'elle ne devrait pas, puisqu'elle lit "
           "au plus le schéma 1.",
    )
    assert "refus" in sortie_sonde.lower() and "2.0" in sortie_sonde, message(
        en=f"release 2.0 failed, but not with its refusal message:\n"
           f"  {sortie_sonde[-300:]}",
        fr=f"la release 2.0 a échoué, mais pas sur son message de refus :\n"
           f"  {sortie_sonde[-300:]}",
    )

    constat = _paires(
        host, CONSTAT,
        message(
            en="the mission asks for three lines in it: release_qui_refuse=, "
               "schema_illisible= and code_de_sortie=",
            fr="la mission demande d'y écrire trois lignes : "
               "release_qui_refuse=, schema_illisible= et code_de_sortie=",
        ),
    )
    attendu = {
        "release_qui_refuse": "2.0",
        "schema_illisible": "2",
        "code_de_sortie": code,
    }
    for cle, valeur in attendu.items():
        annonce = constat.get(cle, "")
        assert annonce, message(
            en=f"the `{cle}=` line is empty. It is read on the machine, by "
               "running release 2.0 against the migrated state.",
            fr=f"la ligne `{cle}=` est vide. Elle se lit sur la machine, en "
               "lançant la release 2.0 contre l'état migré.",
        )
        assert annonce == valeur, message(
            en=f"`{cle}` does not state what the machine states.\n"
               f"  you wrote : {annonce}\n"
               "The refusal message names the release, the schema it cannot "
               "read, and the process returns its own exit code.",
            fr=f"`{cle}` ne dit pas ce que dit la machine.\n"
               f"  vous avez écrit : {annonce}\n"
               "Le message de refus nomme la release et le schéma qu'elle ne "
               "sait pas lire, et le processus rend son propre code de sortie.",
        )
