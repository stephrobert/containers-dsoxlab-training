"""Le service livre : il rend l'empreinte du secret de construction.

POURQUOI UNE EMPREINTE ET NON LE SECRET. C'est tout l'appareil de mesure de
l'epreuve. L'empreinte prouve que le secret a ete EMPLOYE pendant la
construction, et le secret lui-meme ne doit survivre dans AUCUNE couche : le
rendre serait exactement la faute qu'on cherche a interdire.

Le fichier est ecrit pendant la construction, a partir du secret monte par
BuildKit. Un secret monte de cette facon n'entre dans aucune couche ; un secret
copie, passe en argument de construction ou pose en variable d'environnement y
entre, et se relit dans l'historique de l'image.
"""

import pathlib
from http.server import BaseHTTPRequestHandler, HTTPServer

EMPREINTE = pathlib.Path("/app/empreinte.txt")


class Service(BaseHTTPRequestHandler):
    def do_GET(self):
        corps = EMPREINTE.read_text().strip().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *_):
        return


if __name__ == "__main__":
    HTTPServer(("", 8080), Service).serve_forever()
