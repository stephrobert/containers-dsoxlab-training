"""Loopback-only Docker API proxy with an exact method/path allowlist."""

from __future__ import annotations

import json
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlsplit

SOCKET_PATH = "/var/run/docker.sock"


def load_rules(path: str) -> list[dict[str, str]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rules = data.get("rules")
    if not isinstance(rules, list):
        raise ValueError("policy must contain a rules list")
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("method"), str) or not isinstance(
            rule.get("path"), str
        ):
            raise ValueError("each rule must define string method and path fields")
    return rules


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    rules: ClassVar[list[dict[str, str]]] = []

    def _allowed(self, path: str) -> bool:
        request_path = urlsplit(path).path
        return any(
            (rule["method"] == "*" or rule["method"].upper() == self.command)
            and (rule["path"] == "*" or rule["path"] == request_path)
            for rule in self.rules
        )

    def _deny(self) -> None:
        body = b'{"message":"forbidden"}\n'
        self.send_response(403)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def _forward(self) -> None:
        if not self._allowed(self.path):
            self._deny()
            return

        request = (
            f"{self.command} {self.path} HTTP/1.1\r\n"
            "Host: docker\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as upstream:
                upstream.settimeout(10)
                upstream.connect(SOCKET_PATH)
                upstream.sendall(request)
                while True:
                    chunk = upstream.recv(65536)
                    if not chunk:
                        break
                    self.connection.sendall(chunk)
            self.close_connection = True
        except OSError:
            body = b'{"message":"Docker API unavailable"}\n'
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

    do_GET = _forward
    do_HEAD = _forward
    do_OPTIONS = _forward
    do_POST = _forward
    do_PUT = _forward
    do_PATCH = _forward
    do_DELETE = _forward


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: proxy.py POLICY.json")
    ProxyHandler.rules = load_rules(sys.argv[1])
    ThreadingHTTPServer(("127.0.0.1", 2376), ProxyHandler).serve_forever()


if __name__ == "__main__":
    main()
