"""Essai en boîte noire, joué sur la VM, une étape à la fois.

Pourquoi ce fichier a été découpé en étapes
-------------------------------------------

Il portait un unique `main()` de deux cents lignes, lancé par un unique
`def test_` qui agrégeait tout dans une seule assertion. L'apprenant recevait
donc, pour quatre exigences distinctes, un seul verdict et neuf cents caractères
de trace.

Le scénario est séquentiel par nature : il faut un conteneur d'essai durci, puis
une transaction en vol, puis un signal, puis une recréation. On ne peut donc pas
simplement séparer des assertions, comme pour les autres labs de ce catalogue.
Chaque étape **refait** ce dont elle a besoin, et c'est le prix de
l'indépendance : un contrôle qui suppose qu'un autre a déjà tourné mentirait dès
qu'on le joue seul.

Les quatre étapes, appelées par leur nom en argument :

    durcissement   le service fourni tourne-t-il comme demandé ?
    gracieux       un arrêt ordonné valide-t-il la transaction en vol ?
    recreation     la transaction validée survit-elle à une recréation ?
    force          un SIGKILL abandonne-t-il la transaction sans abîmer le reste ?

Chacune nettoie ses propres ressources, qui portent toutes l'étiquette du lab et
un suffixe aléatoire : aucune n'est partagée avec une autre étape ni avec le
service de l'apprenant.
"""

import concurrent.futures
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

LAB = "container-arret-transactionnel"
PROJECT = "dsoxlab-" + LAB + "-stack"
PINNED = (
    "python:3.14.10-slim-trixie@sha256:"
    "3cabfd7d7aaf394e6040e79fa1eec6ca1c52b74ed9188650472695d9a9326999"
)


def message(en: str, fr: str) -> str:
    """Match conftest's language choice without importing it on the VM."""
    return fr if os.environ.get("DSOXLAB_LANG", "en").lower().startswith("fr") else en


def docker(*args, timeout=20):
    result = subprocess.run(
        ["docker", *args], check=False, text=True, capture_output=True, timeout=timeout
    )
    assert result.returncode == 0, message(
        en=f"Docker operation failed: {args[0]}\n  {result.stderr.strip()[:300]}",
        fr=f"L'opération Docker échoue : {args[0]}\n  {result.stderr.strip()[:300]}",
    )
    return result.stdout.strip()


def read(base, path):
    try:
        with urllib.request.urlopen(base + path, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def wait_for(predicate, seconds=5):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            value = predicate()
            if value:
                return value
        except (OSError, ValueError):
            pass
        time.sleep(0.04)
    raise AssertionError(message(
        en="HTTP transaction barrier or readiness deadline exceeded",
        fr="Le délai de la barrière HTTP ou de disponibilité est dépassé",
    ))


def service():
    """Le service de l'apprenant, inspecté, ou un échec qui dit quoi faire.

    Garde-fou commun aux quatre étapes : sans ce service, rien ne peut être
    observé ni copié vers un conteneur d'essai.
    """
    found = docker(
        "ps", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}"
    )
    ids = found.split()
    assert len(ids) == 1, message(
        en=f"Exactly one running service is required in project {PROJECT}, "
           f"found {len(ids)}. Start the supplied ledger project.",
        fr=f"Un seul service actif est requis dans le projet {PROJECT}, "
           f"{len(ids)} trouvé(s). Démarrez le projet de registre fourni.",
    )
    original = json.loads(docker("inspect", ids[0]))[0]
    assert original["State"]["Running"], message(
        en="The supplied service must stay running.",
        fr="Le service fourni doit rester actif.",
    )
    assert original["Config"]["Labels"].get("dsoxlab.lab") == LAB, message(
        en=f"Keep the dsoxlab.lab={LAB} label on the service.",
        fr=f"Conservez le label dsoxlab.lab={LAB} sur le service.",
    )
    return original


# ── Étape « durcissement » ───────────────────────────────────────────────────


def etape_durcissement():
    """Le service fourni tourne-t-il comme le scénario le demande ?

    Tout se lit sur le service de l'apprenant : rien n'est lancé. C'est l'étape
    la plus rapide, et celle qui échoue d'abord quand le lancement n'a pas été
    réparé.
    """
    original = service()
    config, hote = original["Config"], original["HostConfig"]

    assert not hote["Privileged"] and not hote["CapAdd"], message(
        en=f"The service runs privileged or with added capabilities "
           f"(Privileged={hote['Privileged']}, CapAdd={hote['CapAdd']}). "
           "Hardening a shutdown does not call for widening its rights.",
        fr=f"Le service tourne en privilégié ou avec des capabilities ajoutées "
           f"(Privileged={hote['Privileged']}, CapAdd={hote['CapAdd']}). "
           "Durcir un arrêt ne demande pas d'élargir ses droits.",
    )

    assert config["User"] == "10001:10001", message(
        en=f"The service declares User={config['User'] or '(empty)'} instead of "
           "10001:10001.",
        fr=f"Le service déclare User={config['User'] or '(vide)'} au lieu de "
           "10001:10001.",
    )
    vu = docker("exec", original["Id"], "id", "-u")
    assert vu == "10001", message(
        en=f"Inside the container, id -u returns {vu} instead of 10001: the "
           "declaration was retained, the process runs as someone else.",
        fr=f"Dans le conteneur, id -u rend {vu} au lieu de 10001 : la "
           "déclaration a été retenue, le processus tourne sous un autre.",
    )

    assert hote["ReadonlyRootfs"], message(
        en="The service root filesystem is still writable. Only /data carries "
           "writable application data.",
        fr="La racine du service est encore modifiable. Seul /data porte les "
           "données applicatives inscriptibles.",
    )

    data = next((m for m in original["Mounts"] if m["Destination"] == "/data"), None)
    assert data is not None, message(
        en="Nothing is mounted on /data: the domain database has nowhere durable "
           "to live.",
        fr="Rien n'est monté sur /data : la base métier n'a aucun emplacement "
           "durable.",
    )
    assert data["Type"] == "volume", message(
        en=f"/data is a {data['Type']} mount instead of a volume. Durability is "
           "what survives the recreation this lab asks for.",
        fr=f"/data est un montage {data['Type']} au lieu d'un volume. C'est la "
           "durabilité qui survit à la recréation que ce lab demande.",
    )

    attendu = docker("image", "inspect", PINNED, "--format", "{{.Id}}")
    assert original["Image"] == attendu, message(
        en="The service no longer runs the pinned image. Replacing it changes "
           "the application instead of repairing its launch.",
        fr="Le service ne tourne plus l'image épinglée. La remplacer change "
           "l'application au lieu de réparer son lancement.",
    )
    return {"durcissement": "complet"}


# ── Le conteneur d'essai, commun aux trois étapes dynamiques ─────────────────


class Essai:
    """Un conteneur d'essai jetable, monté d'après le service de l'apprenant.

    Il reprend son image, son entrypoint, son utilisateur, sa racine en lecture
    seule et ses variables, sur un volume neuf : l'étape éprouve donc le
    lancement de l'apprenant, et non une configuration inventée ici.
    """

    def __init__(self):
        self.original = service()
        self.nom = PROJECT + "-trial-" + uuid.uuid4().hex[:10]
        self.volume = self.nom + "-data"
        self.app = next(
            m for m in self.original["Mounts"] if m["Destination"] == "/app"
        )
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        docker("volume", "create", "--label", f"dsoxlab.lab={LAB}", self.volume)
        # Le volume neuf appartient à root : on le remet à l'utilisateur du
        # service, sans quoi la base ne pourrait pas y être créée.
        docker(
            "run", "--rm", "--network", "none", "--label", f"dsoxlab.lab={LAB}",
            "--user", "0:0", "--mount", f"type=volume,src={self.volume},dst=/data",
            "--entrypoint", "python", self.original["Image"], "-c",
            "import os; os.chown('/data',10001,10001); os.chmod('/data',0o700)",
        )

    def demarrer(self, mode=None):
        entry = self.original["Config"]["Entrypoint"]
        assert entry, message(
            en="The supplied entry process must remain executable.",
            fr="Le processus d'entrée fourni doit rester exécutable.",
        )
        args = [
            "run", "-d", "--name", self.nom,
            "--label", f"dsoxlab.lab={LAB}",
            "-p", "127.0.0.1::8080",
            "--mount", f"type=volume,src={self.volume},dst=/data",
            "--mount", f"type=bind,src={self.app['Source']},dst=/app,readonly",
            "--entrypoint", entry[0],
            "--user", self.original["Config"]["User"],
            "--read-only",
        ]
        for env in self.original["Config"]["Env"]:
            args += ["-e", env]
        if mode is not None:
            args += ["-e", "SERVICE_MODE=" + mode]
        docker(
            *args, self.original["Image"], *entry[1:],
            *(self.original["Config"]["Cmd"] or []),
        )
        port = docker("port", self.nom, "8080/tcp").split(":")[-1]
        base = "http://127.0.0.1:" + port
        wait_for(lambda: read(base, "/health")[0] == 200)

        # UN AUTRE UID APPLICATIF DOIT ÊTRE REFUSÉ : c'est une exigence du
        # scénario, et elle se vérifie sur le conteneur d'essai parce que c'est
        # lui qui porte le volume de données.
        refus = subprocess.run(
            ["docker", "exec", "--user", "10002:10002", self.nom, "python", "-c",
             "from pathlib import Path; Path('/data/ledger.sqlite').read_bytes()"],
            check=False, capture_output=True, text=True, timeout=5,
        )
        assert refus.returncode != 0 and "PermissionError" in refus.stderr, message(
            en="An unexpected application UID must be refused access to "
               "persistent transactions.",
            fr="Un UID applicatif inattendu doit subir un refus d'accès aux "
               "transactions persistantes.",
        )
        return base

    def en_vol(self, base, key):
        """Ouvre une écriture et la retient avant validation."""
        future = self.pool.submit(read, base, "/write?id=" + key)
        wait_for(lambda: read(base, "/inflight")[1] == {"id": key, "begun": True})
        assert not future.done(), message(
            en="The write must really be in flight.",
            fr="L'écriture doit réellement être en cours.",
        )
        assert read(base, "/record?id=" + key)[0] == 404, message(
            en="Uncommitted data must not be visible.",
            fr="Les données non validées ne doivent pas être visibles.",
        )
        return future

    def evenements(self, key):
        lignes = [
            json.loads(ligne)
            for ligne in docker("logs", self.nom).splitlines()
            if ligne.startswith("{")
        ]
        return lignes, [e["event"] for e in lignes if e.get("request_id") == key]

    def retirer(self):
        docker("rm", "-f", self.nom, timeout=15)

    def fermer(self):
        subprocess.run(
            ["docker", "rm", "-f", self.nom],
            check=False, capture_output=True, timeout=12,
        )
        self.pool.shutdown(wait=True)
        subprocess.run(
            ["docker", "volume", "rm", self.volume],
            check=False, capture_output=True, timeout=12,
        )


# ── Étape « gracieux » ───────────────────────────────────────────────────────


def etape_gracieux():
    """Un arrêt ordonné laisse-t-il la transaction en vol se valider ?"""
    essai = Essai()
    try:
        base = essai.demarrer()
        cle = uuid.uuid4().hex
        future = essai.en_vol(base, cle)

        docker("stop", "--time", "8", essai.nom, timeout=12)

        assert future.result(timeout=2) == (200, {"id": cle, "value": "accepted"}), (
            message(
                en="The graceful stop interrupted the domain request: the write "
                   "did not return its accepted record.",
                fr="L'arrêt gracieux a interrompu la requête métier : l'écriture "
                   "n'a pas rendu son enregistrement validé.",
            )
        )
        etat = json.loads(docker("inspect", essai.nom))[0]["State"]
        assert etat["ExitCode"] == 0, message(
            en=f"The service exited with {etat['ExitCode']} instead of 0: it was "
               "killed instead of draining its requests.",
            fr=f"Le service est sorti en {etat['ExitCode']} au lieu de 0 : il a "
               "été tué au lieu de terminer ses requêtes.",
        )

        tous, pour_cle = essai.evenements(cle)
        attendu = [
            "transaction_started",
            "signal_received",
            "transaction_committed",
            "request_finished",
        ]
        assert pour_cle == attendu, message(
            en=f"The event sequence is {pour_cle} instead of {attendu}: the order "
               "is what proves the signal was received DURING the transaction, "
               "and not before it or after its commit.",
            fr=f"La séquence d'événements est {pour_cle} au lieu de {attendu} : "
               "c'est l'ordre qui prouve que le signal a été reçu PENDANT la "
               "transaction, et non avant elle ni après sa validation.",
        )
        assert tous and tous[-1]["event"] == "drained", message(
            en=f"The last event is {tous[-1]['event'] if tous else '(none)'} "
               "instead of drained: the service must announce it finished.",
            fr=f"Le dernier événement est "
               f"{tous[-1]['event'] if tous else '(aucun)'} au lieu de drained : "
               "le service doit annoncer qu'il a terminé.",
        )
        return {"gracieux": "committed", "cle": cle}
    finally:
        essai.fermer()


# ── Étape « recreation » ─────────────────────────────────────────────────────


def etape_recreation():
    """La transaction validée survit-elle à une recréation du conteneur ?"""
    essai = Essai()
    try:
        base = essai.demarrer()
        premiere = read(base, "/configuration")
        assert premiere[0] == 200 and "service_mode" in premiere[1], message(
            en="The service does not report its configuration over HTTP.",
            fr="Le service ne rend pas sa configuration en HTTP.",
        )

        cle = uuid.uuid4().hex
        future = essai.en_vol(base, cle)
        docker("stop", "--time", "8", essai.nom, timeout=12)
        assert future.result(timeout=2)[0] == 200, message(
            en="The graceful stop interrupted the write this step needs.",
            fr="L'arrêt gracieux a interrompu l'écriture dont cette étape a besoin.",
        )
        essai.retirer()

        # UNE AUTRE CONFIGURATION, pour que la recréation soit observable : deux
        # lancements du même service doivent se distinguer en HTTP.
        mode = "alternate-" + uuid.uuid4().hex[:10]
        base = essai.demarrer(mode)
        seconde = read(base, "/configuration")
        assert seconde == (200, {"service_mode": mode}), message(
            en=f"The recreated service reports {seconde[1]} instead of its new "
               f"mode {mode}.",
            fr=f"Le service recréé rend {seconde[1]} au lieu de son nouveau mode "
               f"{mode}.",
        )
        assert premiere[1]["service_mode"] != mode, message(
            en="Two configurations of the same service must produce distinct "
               "HTTP observations.",
            fr="Deux configurations du même service doivent produire des "
               "observations HTTP distinctes.",
        )

        assert read(base, "/record?id=" + cle) == (
            200, {"id": cle, "value": "accepted"},
        ), message(
            en="The committed transaction did not survive the recreation: "
               "durability is the point of the volume.",
            fr="La transaction validée n'a pas survécu à la recréation : c'est "
               "l'objet même du volume.",
        )
        return {"recreation": "durable", "cle": cle}
    finally:
        essai.fermer()


# ── Étape « force » ──────────────────────────────────────────────────────────


def etape_force():
    """Un SIGKILL abandonne-t-il la transaction en vol sans abîmer le reste ?"""
    essai = Essai()
    try:
        base = essai.demarrer()

        # UNE TRANSACTION VALIDÉE D ABORD, qui servira de témoin : elle doit
        # survivre à l'arrêt forcé qui suit. Cette étape la pose elle-même
        # plutôt que de compter sur une autre.
        temoin = uuid.uuid4().hex
        future = essai.en_vol(base, temoin)
        read(base, "/release")
        assert future.result(timeout=2)[0] == 200, message(
            en="The witness transaction could not be committed before the forced "
               "stop.",
            fr="La transaction témoin n'a pas pu être validée avant l'arrêt "
               "forcé.",
        )

        perdue = uuid.uuid4().hex
        future = essai.en_vol(base, perdue)
        docker("kill", "--signal", "KILL", essai.nom)
        try:
            future.result(timeout=2)
        except (OSError, ValueError):
            pass
        else:
            raise AssertionError(message(
                en="SIGKILL must abort the request held at the barrier.",
                fr="SIGKILL doit abandonner la requête retenue par la barrière.",
            ))

        etat = json.loads(docker("inspect", essai.nom))[0]["State"]
        assert etat["ExitCode"] == 137, message(
            en=f"The service exited with {etat['ExitCode']} instead of 137. A 137 "
               "is the SIGKILL this step sent, and nothing else must have "
               "intervened.",
            fr=f"Le service est sorti en {etat['ExitCode']} au lieu de 137. Un "
               "137 est le SIGKILL envoyé par cette étape, et rien d'autre ne "
               "doit être intervenu.",
        )
        journaux = docker("logs", essai.nom)
        assert "transaction_committed" not in journaux.split(perdue)[-1], message(
            en="A forced stop must not commit the in-flight transaction.",
            fr="Un arrêt forcé ne doit pas valider la transaction en vol.",
        )
        essai.retirer()

        base = essai.demarrer()
        assert read(base, "/record?id=" + perdue)[0] == 404, message(
            en="The forced stop unexpectedly committed the in-flight "
               "transaction.",
            fr="L'arrêt forcé a validé la transaction en vol de façon "
               "inattendue.",
        )
        assert read(base, "/record?id=" + temoin) == (
            200, {"id": temoin, "value": "accepted"},
        ), message(
            en="Previously committed data was damaged by the forced stop. "
               "Aborting what is in flight must not touch what was settled.",
            fr="Les données précédemment validées ont été endommagées par "
               "l'arrêt forcé. Abandonner ce qui est en vol ne doit pas toucher "
               "ce qui était acquis.",
        )

        # LA BASE RESTE UTILISABLE : un abandon qui laisse un verrou derrière lui
        # protège les données en interdisant la suite.
        suivante = uuid.uuid4().hex
        future = essai.en_vol(base, suivante)
        read(base, "/release")
        assert future.result(timeout=2)[0] == 200, message(
            en="The database cannot accept a write after the forced stop: "
               "recovery is incomplete.",
            fr="La base n'accepte plus d'écriture après l'arrêt forcé : la "
               "reprise est incomplète.",
        )
        return {"force": "aborted-only-inflight", "database": "usable"}
    finally:
        essai.fermer()


ETAPES = {
    "durcissement": etape_durcissement,
    "gracieux": etape_gracieux,
    "recreation": etape_recreation,
    "force": etape_force,
}


def main(argv):
    if len(argv) != 2 or argv[1] not in ETAPES:
        noms = ", ".join(sorted(ETAPES))
        print(f"usage: probe.py <{noms}>", file=sys.stderr)
        return 2
    print(json.dumps(ETAPES[argv[1]]()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
