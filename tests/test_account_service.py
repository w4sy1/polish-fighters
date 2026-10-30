import importlib.util
from pathlib import Path
import unittest
import threading
import json
import urllib.request
import urllib.error
import tempfile
import sqlite3
from http.server import ThreadingHTTPServer

spec = importlib.util.spec_from_file_location('accounts', Path(__file__).resolve().parents[1] / 'tools/account_service.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AccountsTest(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.service = module.Service(':memory:', lambda: self.now)
        registered = self.service.request('register', {'name': 'Player', 'password': 'long password 123'})
        self.token = registered['token']
        self.recovery = registered['recovery_code']

    def tearDown(self):
        self.service.db.close()

    def test_credentials_and_hashed_storage(self):
        self.assertTrue(self.service.request('login', {'name': 'PLAYER', 'password': 'long password 123'})['token'])
        with self.assertRaises(PermissionError):
            self.service.request('login', {'name': 'player', 'password': 'wrong password 123'})
        values = str(self.service.db.execute('SELECT salt,password FROM users').fetchall())
        self.assertNotIn('long password 123', values)
        self.assertNotIn(self.token, str(self.service.db.execute('SELECT token FROM sessions').fetchall()))

    def test_session_logout_and_expiry(self):
        self.service.request('logout', {}, self.token)
        with self.assertRaises(PermissionError):
            self.service.request('list-rooms', {}, self.token)
        token = self.service.request('login', {'name': 'player', 'password': 'long password 123'})['token']
        self.now += 86401
        with self.assertRaises(PermissionError):
            self.service.request('list-rooms', {}, token)

    def test_recovery_rotates_code_and_revokes_sessions(self):
        self.publish(self.token)
        replacement = self.service.request('recover', {'name': 'player', 'recovery_code': self.recovery,
                                                      'password': 'replacement password 123'})
        self.assertNotEqual(replacement['recovery_code'], self.recovery)
        with self.assertRaises(PermissionError):
            self.service.request('list-rooms', {}, self.token)
        with self.assertRaises(PermissionError):
            self.service.request('recover', {'name': 'player', 'recovery_code': self.recovery,
                                            'password': 'another replacement 123'})
        logged = self.service.request('login', {'name': 'player', 'password': 'replacement password 123'})
        self.assertFalse(self.service.request('list-rooms', {}, logged['token'])['rooms'])
        self.assertNotIn(replacement['recovery_code'], str(self.service.db.execute('SELECT * FROM recovery').fetchall()))

    def publish(self, token, **overrides):
        data = {'name': 'Pokój', 'host': '127.0.0.1', 'port': 12345, 'profile': 'lf4-turbo', 'capacity': 8}
        data.update(overrides)
        return self.service.request('publish-room', data, token)

    def test_rooms_ownership_and_heartbeat(self):
        room = self.publish(self.token)
        second = self.service.request('register', {'name': 'other', 'password': 'another password 123'})['token']
        self.service.request('delete-room', {}, second)
        self.assertEqual(len(self.service.request('list-rooms', {}, second)['rooms']), 1)
        self.now += 80
        self.assertEqual(self.publish(self.token)['id'], room['id'])
        self.now += 91
        self.assertEqual(self.service.request('list-rooms', {}, second)['rooms'], [])

    def test_input_bounds(self):
        for data in ({'capacity': 9}, {'capacity': True}, {'port': 0}, {'host': '0.0.0.0'},
                     {'profile': '../bad'}, {'name': '\nroom'}):
            with self.assertRaises(ValueError):
                self.publish(self.token, **data)
        with self.assertRaises(PermissionError):
            self.publish('invalid')

    def test_private_invites_revocation_and_heartbeat(self):
        room = self.publish(self.token, private=True)['id']
        guest = self.service.request('register', {'name': 'guest', 'password': 'guest password 123'})['token']
        self.assertFalse(self.service.request('list-rooms', {}, guest)['rooms'])
        self.assertEqual(len(self.service.request('list-rooms', {}, self.token)['rooms']), 1)
        with self.assertRaises(PermissionError):
            self.service.request('relay-ticket', {'room': room, 'role': 'join'}, guest)
        with self.assertRaises(PermissionError):
            self.service.request('create-invite', {'room': room}, guest)
        code = self.service.request('create-invite', {'room': room}, self.token)['code']
        self.assertNotIn(code, str(self.service.db.execute('SELECT * FROM invites').fetchall()))
        self.assertEqual(self.service.request('resolve-invite', {'code': code}, guest)['id'], room)
        self.assertTrue(self.service.request('relay-ticket', {'room': room, 'role': 'join', 'invite': code}, guest)['ticket'])
        self.now += 80
        self.service.request('heartbeat-room', {'room': room}, self.token)
        self.now += 20
        self.assertEqual(self.service.request('resolve-invite', {'code': code}, guest)['id'], room)
        self.service.request('revoke-invite', {'room': room, 'code': code}, self.token)
        with self.assertRaises(PermissionError):
            self.service.request('resolve-invite', {'code': code}, guest)

    def test_invite_expiry(self):
        room = self.publish(self.token)['id']
        code = self.service.request('create-invite', {'room': room, 'expires_in': 60}, self.token)['code']
        self.now += 61
        with self.assertRaises(PermissionError):
            self.service.request('resolve-invite', {'code': code}, self.token)

    def test_existing_database_migration_keeps_rooms(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder)/'old.sqlite')
            connection=sqlite3.connect(path)
            connection.executescript('CREATE TABLE rooms(id TEXT PRIMARY KEY,owner INTEGER UNIQUE,name TEXT,host TEXT,port INTEGER,profile TEXT,capacity INTEGER,expires REAL);'
                                     "INSERT INTO rooms VALUES('old',1,'Existing','127.0.0.1',12345,'lf4-turbo',8,2000);")
            connection.close()
            migrated=module.Service(path,lambda:1000)
            try:
                row=migrated.db.execute('SELECT id,name,private FROM rooms').fetchone()
                self.assertEqual(row,('old','Existing',0))
            finally:migrated.db.close()

    def test_real_http(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), module.handler(self.service))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        url = 'http://127.0.0.1:%s/v1/list-rooms' % server.server_port
        try:
            request = urllib.request.Request(url, data=b'{}',
                headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=3) as response:
                self.assertEqual(json.load(response)['rooms'], [])
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(urllib.request.Request(url, data=b'{}'), timeout=3)
            self.assertEqual(error.exception.code, 401)
            error.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
