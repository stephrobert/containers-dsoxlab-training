import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        data = json.dumps({"component": os.environ["ROLE"], "value": "inventory-ready"}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if os.environ["ROLE"] == "server":
    threading.Thread(
        target=ThreadingHTTPServer(("0.0.0.0", 9090), Handler).serve_forever, daemon=True,
    ).start()
ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler).serve_forever()
