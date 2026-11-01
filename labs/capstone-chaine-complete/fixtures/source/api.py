import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import psycopg2


def connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", "5433")),
        dbname="delivery", user="delivery",
        password=Path(os.environ.get("DB_SECRET", "/run/secrets/missing")).read_text().strip(),
        connect_timeout=2,
    )


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        try:
            with connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("CREATE TABLE IF NOT EXISTS items (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                    if self.path == "/ready":
                        return self.reply(200, {"ready": True})
                    key = self.path.removeprefix("/items/")
                    cursor.execute("SELECT value FROM items WHERE key=%s", (key,))
                    row = cursor.fetchone()
                    return self.reply(200 if row else 404, {"value": row[0] if row else None})
        except Exception:
            self.reply(503, {"ready": False})

    def do_POST(self):
        try:
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("CREATE TABLE IF NOT EXISTS items (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                    cursor.execute(
                        "INSERT INTO items VALUES (%s,%s) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
                        (data["key"], data["value"]),
                    )
            self.reply(201, {"stored": True})
        except Exception:
            self.reply(503, {"stored": False})


ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
