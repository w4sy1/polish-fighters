"""Passenger entry point for the Polish Fighters account and room API.

Deploy next to account_service.py. For internet matches through a relay, add a
relay_config.py in the same folder (never in a public web directory):

    RELAY_HOST = "203.0.113.10"   # numeric public IPv4 of the relay server
    RELAY_PORT = 8766
    RELAY_KEY = "...at least 32 random characters, same as on the relay..."
"""
import json
from html import escape
import os
from http import HTTPStatus
from pathlib import Path
import threading
import time

from account_service import Service

PREFIX = "/projekty/polish-fighters/api"
AUTH_OPERATIONS = {"register", "login", "recover"}

def relay_settings():
    try:
        import relay_config
    except ImportError:
        return None
    host, port, key = (getattr(relay_config, name, None) for name in ("RELAY_HOST", "RELAY_PORT", "RELAY_KEY"))
    if not (isinstance(host, str) and isinstance(port, int) and isinstance(key, str) and len(key) >= 32):
        return None
    return {"host": host, "port": port, "key": key}


class AccountApplication:
    def __init__(self, database, relay=None):
        self.service = Service(database, relay=relay)
        self.attempts = {}
        self.lock = threading.Lock()

    def status_page(self):
        """Public, read-only summary for a browser; no names, addresses or secrets."""
        with self.service.lock:
            now = time.time()
            rooms = self.service.db.execute(
                "SELECT COUNT(*), COALESCE(SUM(host=''),0) FROM rooms WHERE expires>? AND private=0", (now,)).fetchone()
            accounts = self.service.db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        relay = "podłączony" if self.service.relay else "nie skonfigurowany (gra tylko po adresie IP gospodarza)"
        rows = [("Stan", "działa"), ("Konta", str(accounts)), ("Otwarte pokoje", str(rooms[0])),
                ("w tym przez przekaźnik", str(rooms[1])), ("Przekaźnik meczów", relay)]
        cells = "".join(f"<tr><th>{escape(k)}</th><td>{escape(v)}</td></tr>" for k, v in rows)
        return ("<!doctype html><html lang=pl><meta charset=utf-8>"
                "<meta name=viewport content='width=device-width,initial-scale=1'>"
                "<title>Polish Fighters API</title>"
                "<style>body{font:16px system-ui,sans-serif;background:#0b0b0b;color:#eee;margin:0;padding:24px}"
                "h1{color:#e3ab4a;font-size:24px}table{border-collapse:collapse;max-width:560px;width:100%}"
                "th,td{text-align:left;padding:10px;border-bottom:1px solid #333}th{color:#aaa;font-weight:500}"
                "p{color:#aaa;max-width:560px}</style>"
                "<h1>Polish Fighters — serwer gry</h1><table>" + cells + "</table>"
                "<p>Ten adres wpisuje się w grze w „Graj przez internet”. Serwer odpowiada grze, "
                "a ta strona pokazuje tylko jego stan.</p></html>")

    def __call__(self, environ, start_response):
        raw = environ.get("PATH_INFO", "")
        path = "/" if raw == PREFIX else "/" + raw.removeprefix(PREFIX + "/").lstrip("/")
        if path in ("/", "/status") and environ.get("REQUEST_METHOD") in ("GET", "HEAD"):
            try:
                body = self.status_page().encode("utf-8")
                status = 200
            except Exception:
                body, status = "<!doctype html><title>Polish Fighters API</title>Błąd odczytu stanu.".encode("utf-8"), 500
            start_response(f"{status} {HTTPStatus(status).phrase}", [
                ("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store"),
                ("Content-Length", str(len(body)))])
            return [] if environ.get("REQUEST_METHOD") == "HEAD" else [body]
        status, payload = self.handle(environ)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        start_response(f"{status} {HTTPStatus(status).phrase}", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Cache-Control", "no-store"),
            ("Content-Length", str(len(body))),
        ])
        return [body]

    def handle(self, environ):
        path = environ.get("PATH_INFO", "").removeprefix(PREFIX + "/")
        path = "/" + path.lstrip("/")
        if not path.startswith("/v1/"):
            return 404, {"error": "Unknown path"}
        if environ["REQUEST_METHOD"] != "POST":
            return 405, {"error": "POST required"}
        operation = path.removeprefix("/v1/")
        try:
            length = int(environ.get("CONTENT_LENGTH") or "0")
            if not 0 < length <= 8192:
                return 400, {"error": "Body size: 1-8192 bytes"}
            data = json.loads(environ["wsgi.input"].read(length))
            if not isinstance(data, dict):
                return 400, {"error": "Expected JSON object"}
            auth = operation in AUTH_OPERATIONS
            key = (auth, environ.get("REMOTE_ADDR", ""))
            now = time.monotonic()
            with self.lock:
                start, count = self.attempts.get(key, (now, 0))
                if now - start >= 60:
                    start, count = now, 0
                if count >= (30 if auth else 120):
                    return 429, {"error": "Try again later"}
                if key not in self.attempts and len(self.attempts) >= 4096:
                    self.attempts = {k: v for k, v in self.attempts.items() if now - v[0] < 60}
                    if len(self.attempts) >= 4096:
                        return 429, {"error": "Try again later"}
                self.attempts[key] = (start, count + 1)
            token = environ.get("HTTP_AUTHORIZATION", "").removeprefix("Bearer ")
            return 200, self.service.request(operation, data, token, environ.get("REMOTE_ADDR", ""))
        except PermissionError as error:
            return 401, {"error": str(error)}
        except (ValueError, UnicodeError) as error:
            return 400, {"error": str(error)}
        except Exception:
            return 500, {"error": "Service error"}

database = os.environ.get("POLISH_FIGHTERS_DATABASE") or Path(__file__).with_name("accounts.sqlite")
application = AccountApplication(database, relay_settings())
