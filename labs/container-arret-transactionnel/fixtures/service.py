"""A held SQLite transaction, released by SIGTERM or an explicit HTTP barrier."""

import json
import os
import signal
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DB = os.environ.get("DATABASE", "/data/ledger.sqlite")
release = threading.Event()
started = threading.Event()
stopping = threading.Event()
lock = threading.Lock()
current = None
with sqlite3.connect(DB) as connection:
    connection.execute("CREATE TABLE IF NOT EXISTS ledger (id TEXT PRIMARY KEY, value TEXT)")


def event(kind, **fields):
    print(json.dumps({"event": kind, **fields}), flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        global current
        path = urlparse(self.path)
        key = parse_qs(path.query).get("id", [""])[0]
        if path.path == "/health":
            return self.reply(200, {"ready": not stopping.is_set()})
        if path.path == "/configuration":
            return self.reply(200, {"service_mode": os.environ.get("SERVICE_MODE", "standard")})
        if path.path == "/inflight":
            return self.reply(200, {"id": current, "begun": started.is_set()})
        if path.path == "/release":
            release.set()
            return self.reply(200, {"released": True})
        if path.path == "/record":
            with sqlite3.connect(DB) as connection:
                row = connection.execute("SELECT value FROM ledger WHERE id=?", (key,)).fetchone()
            return self.reply(200 if row else 404, {"id": key, "value": row[0] if row else None})
        if path.path != "/write" or not key:
            return self.reply(404, {"error": "unknown"})
        if stopping.is_set() or not lock.acquire(blocking=False):
            return self.reply(503, {"error": "busy"})
        try:
            release.clear()
            started.clear()
            current = key
            with sqlite3.connect(DB) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("INSERT INTO ledger VALUES (?, ?)", (key, "accepted"))
                started.set()
                event("transaction_started", request_id=key)
                if not release.wait(12):
                    connection.rollback()
                    event("transaction_aborted", request_id=key)
                    return self.reply(408, {"id": key, "error": "barrier_timeout"})
                connection.commit()
                event("transaction_committed", request_id=key)
            self.reply(200, {"id": key, "value": "accepted"})
            event("request_finished", request_id=key)
        finally:
            started.clear()
            current = None
            lock.release()


server = ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler)
server.daemon_threads = False


def stop(signum, _frame):
    if stopping.is_set():
        return
    stopping.set()
    event("signal_received", signal=signum, request_id=current)
    release.set()
    threading.Thread(target=server.shutdown).start()


signal.signal(signal.SIGTERM, stop)
event("ready", pid=os.getpid())
server.serve_forever(poll_interval=0.05)
server.server_close()
event("drained")
