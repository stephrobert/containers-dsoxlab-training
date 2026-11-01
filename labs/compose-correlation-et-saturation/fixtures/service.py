"""Two supplied components: a gateway and a CPU-bound quote calculator."""

import json
import os
import re
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROLE = os.environ.get("ROLE", "gateway")
CORRELATE = os.environ.get("CORRELATE", "0") == "1"
SAFE = os.environ.get("SAFE_LOGS", "0") == "1"


def quote(quantity):
    return {"quantity": quantity, "total_cents": quantity * 125}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, body):
        encoded = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = urlparse(self.path)
        if path.path == "/health":
            return self.reply(200, {"role": ROLE})
        rid = self.headers.get("X-Request-ID", "")
        try:
            quantity = int(parse_qs(path.query)["quantity"][0])
            if path.path != "/quote" or not 1 <= quantity <= 20 or not re.fullmatch(r"[a-zA-Z0-9-]{1,80}", rid):
                raise ValueError
        except (ValueError, KeyError):
            return self.reply(400, {"error": "invalid_quote"})
        request_id = rid if CORRELATE else ROLE + "-uncorrelated"
        record = {"component": ROLE, "event": "quote_finished", "request_id": request_id}
        if not SAFE:
            record["headers"] = dict(self.headers)
        if ROLE == "worker":
            deadline = time.thread_time() + 0.12
            number = 1
            while time.thread_time() < deadline:
                number = (number * 48271) % 2147483647
            result = {"request_id": request_id, **quote(quantity)}
        else:
            request = urllib.request.Request(
                os.environ.get("UPSTREAM", "http://worker:8080") + f"/quote?quantity={quantity}",
                headers={"X-Request-ID": request_id, "Authorization": self.headers.get("Authorization", "")},
            )
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    result = json.load(response)
            except (OSError, urllib.error.URLError):
                return self.reply(502, {"error": "upstream"})
        record.update(result)
        print(json.dumps(record), flush=True)
        self.reply(200, result)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler).serve_forever()
