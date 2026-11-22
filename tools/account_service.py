"""Local account and public room directory service; deploy behind HTTPS for remote use.

This is a directory, not a gameplay relay or NAT traversal service.
Run: python tools/account_service.py --database userdata/accounts.sqlite
"""
import argparse
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# The 14 bug-report categories from the project's bug-report spec. The client (bug_report_screen.lua,
# BUG_REPORT_CATEGORIES) must offer exactly this list, in this order -- keep the two in sync by hand,
# there is no shared source file between Lua and Python in this repo.
BUG_REPORT_CATEGORIES = (
    'Awaria gry / crash', 'Błąd graficzny', 'Sterowanie', 'Postacie i umiejętności', 'Kombosy',
    'Rozgrywka', 'Kampania', 'Multiplayer i połączenia sieciowe', 'Moduły gry', 'Dźwięk i muzyka',
    'Interfejs użytkownika', 'Wydajność', 'Profile i zapisy gry', 'Inne',
)
BUG_REPORT_PLATFORMS = ('android', 'windows', 'linux', 'macos', 'unknown')
# Per-IP throttle for bug reports specifically; tighter than the generic 120/min API bucket
# above (see Handler.do_POST / AccountApplication.handle), on top of it rather than instead of it.
BUG_REPORT_WINDOW_SECONDS = 600
BUG_REPORT_WINDOW_LIMIT = 5


def _redact_bug_report_text(text):
    """Strips the same categories of secret the native crash reporter redacts
    (engine/include/openlf2/core/crash_report.hpp) from player-typed free text before it is ever
    assembled into a Discord message: credential-shaped key/value pairs, bearer tokens and bare
    URLs (which can carry a token in their query string)."""
    text = re.sub(r'(?im)\b(token|password|secret|authorization)\b\s*[:=]\s*.+$', r'\1: [REDACTED]', text)
    text = re.sub(r'(?i)bearer\s+\S+', 'Bearer [REDACTED]', text)
    text = re.sub(r'https?://\S+', '[URL]', text)
    # Defuse mass/role/user mentions a player could otherwise type into the report
    # (@everyone, @here, <@id>, <@&id>) with a zero-width space, keeping the text readable.
    text = text.replace('@everyone', '@​everyone').replace('@here', '@​here')
    text = text.replace('<@', '<​@')
    return text


def _format_bug_report_message(number, category, player, title, description, steps, logs,
                                platform, version, module_name, resolution, created):
    import datetime
    stamp = datetime.datetime.fromtimestamp(created, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    lines = [
        'POLISH FIGHTERS | NOWE ZGŁOSZENIE BŁĘDU',
        f'Numer zgłoszenia: {number}',
        f'Kategoria: {category}',
        f'Tytuł: {title}',
        f'Gracz: {player or "(anonimowy)"}',
        f'Platforma: {platform}',
        f'Wersja gry: {version or "nieznana"}',
    ]
    if module_name:
        lines.append(f'Moduł: {module_name}')
    if resolution:
        lines.append(f'Rozdzielczość: {resolution}')
    lines.append(f'Data: {stamp}')
    lines.append('')
    lines.append('Opis problemu:')
    lines.append(description)
    if steps:
        lines.append('')
        lines.append('Kroki odtworzenia:')
        lines.append(steps)
    if logs:
        lines.append('')
        lines.append('Logi diagnostyczne (fragment):')
        lines.append(logs)
    content = _redact_bug_report_text('\n'.join(lines))
    if len(content) > 1990:
        # No file-attachment upload in this version (see docs) -- a long report is trimmed to
        # Discord's 2000-character content limit rather than rejected.
        content = content[:1950] + '\n… (zgłoszenie przycięte, zobacz pełny opis w grze)'
    return content


def send_discord_webhook(content):
    """Posts one chat message to the project's Discord bug-report channel. The webhook URL is a
    server-only secret (OPENLF2_DISCORD_WEBHOOK_URL in this process's environment) -- the game
    client never sees it; it only ever reaches this through the 'bug-report' operation below.
    Raises on failure so the caller can decide whether to tell the player or roll back."""
    url = os.environ.get('OPENLF2_DISCORD_WEBHOOK_URL', '')
    if not re.fullmatch(r'https://(discord|discordapp)\.com/api/webhooks/\d+/[\w-]+', url):
        raise RuntimeError('Brak konfiguracji webhooka Discord (OPENLF2_DISCORD_WEBHOOK_URL) po stronie serwera')
    body = json.dumps({'content': content}).encode('utf-8')
    # Discord's edge (Cloudflare) returns 403 Forbidden for requests carrying urllib's default
    # User-Agent ("Python-urllib/3.x"); a normal-looking UA avoids that false-positive block.
    headers = {'Content-Type': 'application/json', 'User-Agent': 'OpenLF2-PolishFighters-BugReport/1.0'}
    request = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status not in (200, 204):
                raise RuntimeError(f'Discord webhook returned HTTP {response.status}')
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Discord webhook returned HTTP {error.code}') from error
    except urllib.error.URLError as error:
        raise RuntimeError(f'Discord webhook unreachable: {error.reason}') from error


class Service:
    def __init__(self, database, clock=time.time, relay=None, send_discord=send_discord_webhook):
        """relay: optional {'host': numeric IPv4, 'port': int, 'key': shared secret} of a
        standalone room_relay.py that validates tickets through consume-relay-ticket.
        send_discord: injectable for tests; defaults to the real webhook POST above."""
        self.clock = clock
        self.relay = relay if relay and relay.get('host') and relay.get('port') else None
        self.send_discord = send_discord
        self.lock = threading.RLock()
        self.db = sqlite3.connect(database, check_same_thread=False)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL,
                salt BLOB NOT NULL, password BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(
                token TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), expires REAL);
            CREATE TABLE IF NOT EXISTS rooms(
                id TEXT PRIMARY KEY, owner INTEGER UNIQUE REFERENCES users(id),
                name TEXT, host TEXT, port INTEGER, profile TEXT, capacity INTEGER, expires REAL);
            CREATE TABLE IF NOT EXISTS recovery(
                user_id INTEGER PRIMARY KEY REFERENCES users(id), code TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS relay_tickets(
                ticket TEXT PRIMARY KEY, room TEXT REFERENCES rooms(id) ON DELETE CASCADE,
                role TEXT NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS invites(
                code TEXT PRIMARY KEY, room TEXT REFERENCES rooms(id) ON DELETE CASCADE,
                expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS bug_reports(
                id INTEGER PRIMARY KEY AUTOINCREMENT, client_ref TEXT UNIQUE NOT NULL,
                created REAL NOT NULL, remote_addr TEXT NOT NULL, category TEXT NOT NULL,
                sent INTEGER NOT NULL DEFAULT 0);
        ''')
        columns = {row[1] for row in self.db.execute('PRAGMA table_info(rooms)')}
        if 'private' not in columns:
            self.db.execute('ALTER TABLE rooms ADD COLUMN private INTEGER NOT NULL DEFAULT 0')
        if 'relay_ready_until' not in columns:
            self.db.execute('ALTER TABLE rooms ADD COLUMN relay_ready_until REAL NOT NULL DEFAULT 0')
        self.db.commit()

    NICK_SALT = b'nick'
    NICK_SESSION = 12 * 3600

    def nick_login(self, data, now):
        """Play under a nickname without a password. The server hands the device a nick key; that
        device can always take the nick back. Another device may take it only while nobody is
        signed in with it. Nicks never collide with password accounts."""
        name, key = data.get('name'), data.get('nick_key')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_]{3,24}', name):
            raise ValueError('name: 3-24 ASCII letters, digits or underscore')
        if key is not None and (not isinstance(key, str) or not 16 <= len(key) <= 128):
            raise ValueError('Invalid nick key')
        name = name.lower()
        row = self.db.execute('SELECT id,salt,password FROM users WHERE name=?', (name,)).fetchone()
        new_key = secrets.token_urlsafe(32)
        new_hash = hashlib.sha256(new_key.encode()).digest()
        if row is None:
            user_id = self.db.execute('INSERT INTO users(name,salt,password) VALUES(?,?,?)',
                                      (name, self.NICK_SALT, new_hash)).lastrowid
        elif row[1] != self.NICK_SALT:
            raise PermissionError('Nick taken by an account')
        else:
            user_id = row[0]
            owned = key is not None and hmac.compare_digest(hashlib.sha256(key.encode()).digest(), row[2])
            if owned:
                new_key = key  # Keep the device's key, so a lost answer never locks it out.
            else:
                if self.db.execute('SELECT 1 FROM sessions WHERE user_id=?', (user_id,)).fetchone():
                    raise PermissionError('Nick in use')
                # A free nick changes hands: the previous holder's rooms go with it.
                self.db.execute('DELETE FROM rooms WHERE owner=?', (user_id,))
                self.db.execute('UPDATE users SET password=? WHERE id=?', (new_hash, user_id))
        value = secrets.token_urlsafe(32)
        self.db.execute('INSERT INTO sessions VALUES(?,?,?)',
                        (hashlib.sha256(value.encode()).hexdigest(), user_id, now + self.NICK_SESSION))
        return {'token': value, 'expires_in': self.NICK_SESSION, 'name': name, 'nick_key': new_key}

    def request(self, operation, data, token='', remote_addr=''):
        with self.lock, self.db:
            now = self.clock()
            self.db.execute('DELETE FROM sessions WHERE expires <= ?', (now,))
            self.db.execute('DELETE FROM rooms WHERE expires <= ?', (now,))
            self.db.execute('DELETE FROM invites WHERE expires <= ?', (now,))
            if operation == 'bug-report':
                # No account required (spec: a player reports a bug without signing in).
                return self._submit_bug_report(data, now, remote_addr)
            if operation in ('consume-relay-ticket', 'relay-readiness'):
                # Called by a standalone relay, never by players: authenticated by its key.
                key = (self.relay or {}).get('key')
                supplied = data.get('key')
                if not key or not isinstance(supplied, str) or not hmac.compare_digest(supplied.encode(), key.encode()):
                    raise PermissionError('Relay key required')
                if operation == 'relay-readiness':
                    room, ready = data.get('room'), data.get('ready')
                    if not isinstance(room, str) or type(ready) is not bool:
                        raise ValueError('Invalid relay readiness')
                    self.set_relay_readiness(room, ready)
                    return {'ok': True}
                room, role, capacity = self.consume_relay_ticket(data.get('ticket'))
                return {'room': room, 'role': role, 'capacity': capacity}
            if operation == 'recover':
                name, code, password = data.get('name'), data.get('recovery_code'), data.get('password')
                if not isinstance(name, str) or not isinstance(code, str) or len(code) > 128:
                    raise ValueError('Invalid recovery request')
                if not isinstance(password, str) or not 12 <= len(password) <= 128:
                    raise ValueError('password: 12-128 characters')
                row = self.db.execute('SELECT u.id,r.code FROM users u JOIN recovery r ON r.user_id=u.id WHERE u.name=?',
                                      (name.lower(),)).fetchone()
                if not row or not hmac.compare_digest(hashlib.sha256(code.encode()).hexdigest(), row[1]):
                    raise PermissionError('Invalid recovery credentials')
                salt = secrets.token_bytes(16)
                password_hash = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
                replacement = secrets.token_urlsafe(32)
                self.db.execute('UPDATE users SET salt=?,password=? WHERE id=?', (salt, password_hash, row[0]))
                self.db.execute('UPDATE recovery SET code=? WHERE user_id=?',
                                (hashlib.sha256(replacement.encode()).hexdigest(), row[0]))
                self.db.execute('DELETE FROM sessions WHERE user_id=?', (row[0],))
                self.db.execute('DELETE FROM rooms WHERE owner=?', (row[0],))
                return {'ok': True, 'recovery_code': replacement}
            if operation == 'login' and data.get('nick') is True:
                return self.nick_login(data, now)
            if operation in ('register', 'login'):
                name, password = data.get('name'), data.get('password')
                if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_]{3,24}', name):
                    raise ValueError('name: 3-24 ASCII letters, digits or underscore')
                if not isinstance(password, str) or not 12 <= len(password) <= 128:
                    raise ValueError('password: 12-128 characters')
                name = name.lower()
                row = self.db.execute('SELECT id,salt,password FROM users WHERE name=?', (name,)).fetchone()
                if operation == 'register':
                    if row:
                        raise ValueError('Account unavailable')
                    salt = secrets.token_bytes(16)
                    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
                    user_id = self.db.execute('INSERT INTO users(name,salt,password) VALUES(?,?,?)',
                                              (name, salt, digest)).lastrowid
                    recovery_code = secrets.token_urlsafe(32)
                    self.db.execute('INSERT INTO recovery VALUES(?,?)',
                                    (user_id, hashlib.sha256(recovery_code.encode()).hexdigest()))
                else:
                    # Also perform expensive hashing when the user does not exist.
                    salt = row[1] if row else bytes(16)
                    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
                    if not row or not hmac.compare_digest(digest, row[2]):
                        raise PermissionError('Invalid credentials')
                    user_id = row[0]
                value = secrets.token_urlsafe(32)
                self.db.execute('INSERT INTO sessions VALUES(?,?,?)',
                                (hashlib.sha256(value.encode()).hexdigest(), user_id, now + 86400))
                result = {'token': value, 'expires_in': 86400, 'name': name}
                if operation == 'register':
                    result['recovery_code'] = recovery_code
                return result
            digest = hashlib.sha256(token.encode()).hexdigest()
            user = self.db.execute('SELECT user_id FROM sessions WHERE token=?', (digest,)).fetchone()
            if not user:
                raise PermissionError('Session required')
            user_id = user[0]
            if operation in ('create-invite', 'revoke-invite', 'heartbeat-room'):
                room_id = data.get('room')
                room = self.db.execute('SELECT owner FROM rooms WHERE id=?', (room_id,)).fetchone()
                if not room or room[0] != user_id:
                    raise PermissionError('Room owner required')
                if operation == 'heartbeat-room':
                    self.db.execute('UPDATE rooms SET expires=? WHERE id=?', (now+90, room_id))
                    return {'ok': True, 'expires_in': 90}
                if operation == 'revoke-invite':
                    code = data.get('code')
                    if not isinstance(code, str):
                        raise ValueError('Invite code required')
                    self.db.execute('DELETE FROM invites WHERE room=? AND code=?',
                                    (room_id, hashlib.sha256(code.encode()).hexdigest()))
                    return {'ok': True}
                ttl = data.get('expires_in', 600)
                if type(ttl) is not int or not 60 <= ttl <= 86400:
                    raise ValueError('Invite lifetime: 60-86400 seconds')
                count = self.db.execute('SELECT COUNT(*) FROM invites WHERE room=?', (room_id,)).fetchone()[0]
                if count >= 16:
                    raise ValueError('Room invite limit reached')
                code = secrets.token_urlsafe(18)
                self.db.execute('INSERT INTO invites VALUES(?,?,?)',
                                (hashlib.sha256(code.encode()).hexdigest(), room_id, now+ttl))
                return {'code': code, 'room': room_id, 'expires_in': ttl}
            if operation == 'resolve-invite':
                room_id = self.invited_room(data.get('code'), now)
                row = self.db.execute('SELECT id,name,host,port,profile,capacity FROM rooms WHERE id=?', (room_id,)).fetchone()
                if not row:
                    raise ValueError('Room expired')
                return dict(zip(('id', 'name', 'host', 'port', 'profile', 'capacity'), row))
            if operation == 'relay-ticket':
                room_id, role = data.get('room'), data.get('role')
                room = self.db.execute('SELECT owner,private FROM rooms WHERE id=?', (room_id,)).fetchone()
                if not room or role not in ('host', 'join'):
                    raise ValueError('Unknown room or relay role')
                if role == 'host' and room[0] != user_id:
                    raise PermissionError('Only owner may attach host relay channels')
                if role == 'join' and room[1] and room[0] != user_id:
                    if self.invited_room(data.get('invite'), now) != room_id:
                        raise PermissionError('Invite does not match room')
                self.db.execute('DELETE FROM relay_tickets WHERE expires <= ?', (now,))
                count = self.db.execute('SELECT COUNT(*) FROM relay_tickets WHERE room=?', (room_id,)).fetchone()[0]
                if count >= 32:
                    raise ValueError('Too many pending relay tickets')
                ticket = secrets.token_urlsafe(32)
                self.db.execute('INSERT INTO relay_tickets VALUES(?,?,?,?)',
                                (hashlib.sha256(ticket.encode()).hexdigest(), room_id, role, now + 30))
                result = {'ticket': ticket, 'expires_in': 30}
                if self.relay:
                    result['relay'] = {'host': self.relay['host'], 'port': self.relay['port']}
                return result
            if operation == 'logout':
                self.db.execute('DELETE FROM sessions WHERE token=?', (digest,))
                return {'ok': True}
            if operation == 'delete-room':
                self.db.execute('DELETE FROM rooms WHERE owner=?', (user_id,))
                return {'ok': True}
            if operation == 'publish-room':
                host, port = data.get('host'), data.get('port')
                relayed = data.get('relay', False)
                if type(relayed) is not bool:
                    raise ValueError('relay must be boolean')
                if relayed:
                    # Played through the relay: no host address is published at all.
                    if not self.relay:
                        raise ValueError('This server has no relay')
                    address = ''
                else:
                    try:
                        address = ipaddress.ip_address(host)
                    except (ValueError, TypeError):
                        raise ValueError('host must be an IP address') from None
                    if address.is_unspecified or address.is_multicast:
                        raise ValueError('Unusable host address')
                capacity, profile, name = data.get('capacity'), data.get('profile'), data.get('name')
                if type(port) is not int or not 1024 <= port <= 65535:
                    raise ValueError('port: 1024-65535')
                if type(capacity) is not int or not 2 <= capacity <= 8:
                    raise ValueError('capacity: 2-8')
                if not isinstance(profile, str) or not re.fullmatch(r'[a-z][a-z0-9-]{1,40}', profile):
                    raise ValueError('Invalid profile')
                if not isinstance(name, str) or not 1 <= len(name.strip()) <= 48 or any(ord(c) < 32 for c in name):
                    raise ValueError('Invalid room name')
                old = self.db.execute('SELECT id FROM rooms WHERE owner=?', (user_id,)).fetchone()
                room_id = old[0] if old and not relayed else secrets.token_urlsafe(12)
                private = data.get('private', False)
                if type(private) is not bool:
                    raise ValueError('private must be boolean')
                if old and relayed:
                    self.db.execute('DELETE FROM rooms WHERE id=?', (old[0],))
                self.db.execute('INSERT INTO rooms(id,owner,name,host,port,profile,capacity,expires,private) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET '
                                'name=excluded.name,host=excluded.host,port=excluded.port,profile=excluded.profile,'
                                'capacity=excluded.capacity,expires=excluded.expires,private=excluded.private',
                                (room_id, user_id, name.strip(), str(address), port, profile, capacity, now + 90, int(private)))
                return {'id': room_id, 'expires_in': 90}
            if operation == 'list-rooms':
                rows = self.db.execute('SELECT rooms.id,rooms.name,rooms.host,rooms.port,rooms.profile,rooms.capacity,users.name '
                                       'FROM rooms LEFT JOIN users ON users.id=rooms.owner '
                                       'WHERE (rooms.private=0 OR rooms.owner=?) '
                                       "AND (rooms.host<>'' OR rooms.relay_ready_until>?) "
                                       'ORDER BY rooms.name LIMIT 200', (user_id, now)).fetchall()
                keys = ('id', 'name', 'host', 'port', 'profile', 'capacity', 'owner')
                rooms = [dict(zip(keys, row)) for row in rows]
                for room in rooms:
                    room['relay'] = room['host'] == ''
                return {'rooms': rooms, 'relay': bool(self.relay),
                        'scope': 'Relay rooms require a waiting host channel; direct rooms are advertisements'}
            raise ValueError('Unknown operation')

    def _submit_bug_report(self, data, now, remote_addr):
        """Validates and relays a player-submitted bug report to Discord, server-side only --
        see send_discord_webhook above. Called with self.lock/self.db already held by request().
        Section 7/8 of the bug-report spec: no account required, generated report number unique
        under concurrent submissions (SQLite autoincrement under self.lock), idempotent retries
        (client_ref), and a dedicated per-IP rate limit on top of the generic API one."""
        category, title, description = data.get('category'), data.get('title'), data.get('description')
        player, steps, logs = data.get('player', ''), data.get('steps', ''), data.get('logs', '')
        platform, version = data.get('platform', 'unknown'), data.get('version', '')
        module_name, resolution = data.get('module', ''), data.get('resolution', '')
        client_ref = data.get('client_ref')
        if category not in BUG_REPORT_CATEGORIES:
            raise ValueError('Invalid bug report category')
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
            raise ValueError('title: 1-120 characters')
        if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1800:
            raise ValueError('description: 1-1800 characters')
        # Field limits are sized to stay well under the client's 8192-byte JSON body cap
        # (openlf2_report_bug/account_post; see engine/src/adapters/luajit/runtime.cpp) once the
        # JSON keys and quoting overhead are added, so a within-limit client request is never
        # rejected here purely for being too long once encoded.
        for name, value, limit in (('player', player, 24), ('steps', steps, 1200), ('logs', logs, 3000),
                                   ('version', version, 32), ('module', module_name, 40), ('resolution', resolution, 24)):
            if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 and c not in '\n\r\t' for c in value):
                raise ValueError(f'{name}: invalid or exceeds {limit} characters')
        if platform not in BUG_REPORT_PLATFORMS:
            raise ValueError('Invalid platform')
        if not isinstance(client_ref, str) or not 8 <= len(client_ref) <= 64:
            raise ValueError('client_ref: 8-64 characters required (idempotency key)')
        existing = self.db.execute('SELECT id,sent FROM bug_reports WHERE client_ref=?', (client_ref,)).fetchone()
        if existing:
            report_id, sent = existing
            number = f'PF-BUG-{report_id:06d}'
            if sent:
                return {'ok': True, 'report': number, 'duplicate': True}
        else:
            window_start = now - BUG_REPORT_WINDOW_SECONDS
            recent = self.db.execute('SELECT COUNT(*) FROM bug_reports WHERE remote_addr=? AND created>?',
                                     (remote_addr, window_start)).fetchone()[0]
            if recent >= BUG_REPORT_WINDOW_LIMIT:
                raise ValueError('Too many bug reports from this address; try again later')
            report_id = self.db.execute(
                'INSERT INTO bug_reports(client_ref,created,remote_addr,category,sent) VALUES(?,?,?,?,0)',
                (client_ref, now, remote_addr, category)).lastrowid
            number = f'PF-BUG-{report_id:06d}'
        message = _format_bug_report_message(number, category, player.strip(), title.strip(), description.strip(),
                                             steps.strip(), logs.strip(), platform, version, module_name, resolution, now)
        self.send_discord(message)
        self.db.execute('UPDATE bug_reports SET sent=1 WHERE id=?', (report_id,))
        return {'ok': True, 'report': number}

    def set_relay_readiness(self, room, ready):
        deadline = self.clock() + 15 if ready else 0
        with self.lock:
            self.db.execute("UPDATE rooms SET relay_ready_until=? WHERE id=? AND host=''", (deadline, room))
            self.db.commit()

    def invited_room(self, code, now):
        if not isinstance(code, str) or len(code) > 128:
            raise PermissionError('Valid invitation required')
        row = self.db.execute('SELECT room FROM invites WHERE code=? AND expires>?',
                              (hashlib.sha256(code.encode()).hexdigest(), now)).fetchone()
        if not row:
            raise PermissionError('Expired or invalid invitation')
        return row[0]

    def consume_relay_ticket(self, ticket):
        if not isinstance(ticket, str) or len(ticket) > 128:
            raise PermissionError('Invalid relay ticket')
        digest = hashlib.sha256(ticket.encode()).hexdigest()
        with self.lock, self.db:
            row = self.db.execute('SELECT t.room,t.role,r.capacity FROM relay_tickets t JOIN rooms r ON r.id=t.room '
                                  'WHERE t.ticket=? AND t.expires>? AND r.expires>?',
                                  (digest, self.clock(), self.clock())).fetchone()
            if not row:
                raise PermissionError('Expired or consumed relay ticket')
            self.db.execute('DELETE FROM relay_tickets WHERE ticket=?', (digest,))
            return row


def handler(service):
    class Handler(BaseHTTPRequestHandler):
        attempts = {}
        def setup(self):
            super().setup()
            self.connection.settimeout(10)
        def log_message(self, *_):
            pass  # Passwords and bearer tokens never enter request logs.

        def do_POST(self):
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 8192:
                    raise ValueError('Body size: 1-8192 bytes')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Expected JSON object')
                operation = self.path.removeprefix('/v1/')
                if not self.path.startswith('/v1/'):
                    raise ValueError('Unknown path')
                # Bounded process-local request throttling; reverse proxy also needs limits.
                authentication = operation in ('register', 'login', 'recover')
                key = ('auth:' if authentication else 'api:') + self.client_address[0]
                limit = 30 if authentication else 120
                now = time.monotonic()
                with service.lock:
                    self.attempts = {k: v for k, v in Handler.attempts.items() if now-v[0] < 60}
                    Handler.attempts = self.attempts
                    start, count = self.attempts.get(key, (now, 0))
                    if count >= limit or (key not in self.attempts and len(self.attempts) >= 4096):
                        self.reply(429, {'error': 'Try again later'})
                        return
                    self.attempts[key] = (start, count+1)
                token = self.headers.get('Authorization', '').removeprefix('Bearer ')
                self.reply(200, service.request(operation, data, token, self.client_address[0]))
            except PermissionError as error:
                self.reply(401, {'error': str(error)})
            except (ValueError, UnicodeError) as error:
                self.reply(400, {'error': str(error)})
            except Exception:
                self.reply(500, {'error': 'Service error'})

        def reply(self, status, value):
            body = json.dumps(value, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)
    return Handler


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--relay-port', type=int, help='Optional local raw TCP relay, behind TLS stream proxy remotely')
    args = parser.parse_args()
    service = Service(args.database)
    relay = None
    if args.relay_port:
        from room_relay import RelayServer
        relay = RelayServer(('127.0.0.1', args.relay_port), service)
        threading.Thread(target=relay.serve_forever, daemon=True).start()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler(service))
    server.daemon_threads = True
    print('Local service on', server.server_address, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if relay:
            relay.shutdown()
            relay.server_close()
        service.db.close()
