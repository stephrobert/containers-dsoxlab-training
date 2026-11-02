"""Les trois etages de la pile, dans un seul fichier.

POURQUOI UN SEUL FICHIER ET AUCUNE DEPENDANCE. L'epreuve porte sur la
restauration d'une pile et sur l'isolement de son reseau de donnees, pas sur
l'installation d'un pilote de base. Un pilote tire par pip ajouterait une panne
possible qui n'a rien a voir avec le sujet, et il se perimerait avec
l'interpreteur : la librairie standard suffit a monter trois etages qui se
parlent vraiment.

LE ROLE VIENT DE L'ENVIRONNEMENT, `ROLE`, et c'est la seule chose qui distingue
les trois conteneurs. Ils portent la meme image, donc la restauration n'a qu'une
image a retrouver.

    front  ecoute 8080, appelle `api` et ne sait rien de `db`
    api    ecoute 8080, appelle `db` et ne publie rien
    db     ecoute 5432, persiste dans /var/lib/donnees et ne parle a personne
"""

import json
import os
import pathlib
import socket
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

ROLE = os.environ["ROLE"]
DONNEES = pathlib.Path("/var/lib/donnees/enregistrements.json")
PORT = 5432 if ROLE == "db" else 8080


def _lire() -> list[str]:
    if not DONNEES.exists():
        return []
    return json.loads(DONNEES.read_text())


def _ecrire(valeurs: list[str]) -> None:
    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    DONNEES.write_text(json.dumps(valeurs, indent=1) + "\n")


def _appeler(hote: str, chemin: str, corps: bytes | None = None) -> bytes:
    """Un etage appelle le suivant PAR SON NOM DE SERVICE.

    C'est ce qui rend l'isolement mesurable : si `db` n'est pas joignable depuis
    le reseau de `front`, l'appel direct echoue, et seul `api` passe.
    """
    req = urllib.request.Request(
        f"http://{hote}:{5432 if hote == 'db' else 8080}{chemin}",
        data=corps, method="POST" if corps else "GET",
    )
    return urllib.request.urlopen(req, timeout=8).read()


class Service(BaseHTTPRequestHandler):
    def _rendre(self, code: int, charge) -> None:
        corps = json.dumps(charge).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        if self.path != "/enregistrements":
            return self._rendre(404, {"erreur": "chemin inconnu"})
        if ROLE == "db":
            return self._rendre(200, {"etage": "db", "enregistrements": _lire()})
        suivant = "db" if ROLE == "api" else "api"
        try:
            amont = json.loads(_appeler(suivant, "/enregistrements"))
        except (urllib.error.URLError, socket.timeout, OSError) as souci:
            return self._rendre(502, {"etage": ROLE, "erreur": str(souci)})
        return self._rendre(200, {
            "etage": ROLE,
            "traverse": [ROLE, *amont.get("traverse", [amont.get("etage")])],
            "enregistrements": amont.get("enregistrements", []),
        })

    def do_POST(self):
        if self.path != "/enregistrements":
            return self._rendre(404, {"erreur": "chemin inconnu"})
        taille = int(self.headers.get("Content-Length") or 0)
        valeur = self.rfile.read(taille)
        if not valeur.strip():
            return self._rendre(400, {"erreur": "valeur vide"})
        if ROLE == "db":
            valeurs = _lire()
            valeurs.append(valeur.decode().strip())
            _ecrire(valeurs)
            return self._rendre(201, {"etage": "db", "enregistrements": valeurs})
        suivant = "db" if ROLE == "api" else "api"
        try:
            amont = json.loads(_appeler(suivant, "/enregistrements", valeur))
        except (urllib.error.URLError, socket.timeout, OSError) as souci:
            return self._rendre(502, {"etage": ROLE, "erreur": str(souci)})
        return self._rendre(201, {"etage": ROLE, **amont})

    def log_message(self, *_):
        return


if __name__ == "__main__":
    HTTPServer(("", PORT), Service).serve_forever()
