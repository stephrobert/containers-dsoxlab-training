from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(Path("/app/value.txt").read_bytes())


HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
