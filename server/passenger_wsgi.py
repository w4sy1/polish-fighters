"""Passenger entry point for the Polish Fighters account and room API.

Deploy next to account_service.py. For internet matches through a relay, add a
relay_config.py in the same folder (never in a public web directory):

    RELAY_HOST = "203.0.113.10"   # numeric public IPv4 of the relay server
    RELAY_PORT = 8766
    RELAY_KEY = "...at least 32 random characters, same as on the relay..."
"""
import json
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

    def __call__(self, environ, start_response):
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
            return 200, self.service.request(operation, data, token)
        except PermissionError as error:
            return 401, {"error": str(error)}
        except (ValueError, UnicodeError) as error:
            return 400, {"error": str(error)}
        except Exception:
            return 500, {"error": "Service error"}

database = os.environ.get("POLISH_FIGHTERS_DATABASE") or Path(__file__).with_name("accounts.sqlite")
application = AccountApplication(database, relay_settings())
