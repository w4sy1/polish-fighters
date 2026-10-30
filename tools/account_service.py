"""Local account and public room directory service; deploy behind HTTPS for remote use.

This is a directory, not a gameplay relay or NAT traversal service.
Run: python tools/account_service.py --database userdata/accounts.sqlite
"""
import argparse
import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Service:
    def __init__(self, database, clock=time.time):
        self.clock = clock
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
        ''')
        columns = {row[1] for row in self.db.execute('PRAGMA table_info(rooms)')}
        if 'private' not in columns:
            self.db.execute('ALTER TABLE rooms ADD COLUMN private INTEGER NOT NULL DEFAULT 0')
        self.db.commit()

    def request(self, operation, data, token=''):
        with self.lock, self.db:
            now = self.clock()
            self.db.execute('DELETE FROM sessions WHERE expires <= ?', (now,))
            self.db.execute('DELETE FROM rooms WHERE expires <= ?', (now,))
            self.db.execute('DELETE FROM invites WHERE expires <= ?', (now,))
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
                return {'ticket': ticket, 'expires_in': 30}
            if operation == 'logout':
                self.db.execute('DELETE FROM sessions WHERE token=?', (digest,))
                return {'ok': True}
            if operation == 'delete-room':
                self.db.execute('DELETE FROM rooms WHERE owner=?', (user_id,))
                return {'ok': True}
            if operation == 'publish-room':
                host, port = data.get('host'), data.get('port')
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
                room_id = old[0] if old else secrets.token_urlsafe(12)
                private = data.get('private', False)
                if type(private) is not bool:
                    raise ValueError('private must be boolean')
                self.db.execute('INSERT INTO rooms(id,owner,name,host,port,profile,capacity,expires,private) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET '
                                'name=excluded.name,host=excluded.host,port=excluded.port,profile=excluded.profile,'
                                'capacity=excluded.capacity,expires=excluded.expires,private=excluded.private',
                                (room_id, user_id, name.strip(), str(address), port, profile, capacity, now + 90, int(private)))
                return {'id': room_id, 'expires_in': 90}
            if operation == 'list-rooms':
                rows = self.db.execute('SELECT id,name,host,port,profile,capacity FROM rooms WHERE private=0 OR owner=? ORDER BY name LIMIT 200', (user_id,)).fetchall()
                keys = ('id', 'name', 'host', 'port', 'profile', 'capacity')
                return {'rooms': [dict(zip(keys, row)) for row in rows],
                        'scope': 'Advertisements only; availability, player count and connection are not verified'}
            raise ValueError('Unknown operation')

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
                self.reply(200, service.request(operation, data, token))
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
