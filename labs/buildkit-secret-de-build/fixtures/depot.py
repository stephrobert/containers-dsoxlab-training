"""Private dependency repository for an isolated training network."""

import hmac
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

STATE = Path("/root/.lab-buildkit-secret.json")


class Repository(BaseHTTPRequestHandler):
    def do_GET(self):
        state = json.loads(STATE.read_text())
        if self.path != "/artifact":
            self.send_error(404)
            return
        if not hmac.compare_digest(
            self.headers.get("Authorization", ""), f"Bearer {state['token']}"
        ):
            self.send_error(401)
            return
        body = (state["artifact"] + "\n").encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


HTTPServer(("0.0.0.0", 18083), Repository).serve_forever()
