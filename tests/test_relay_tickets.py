"""Relay rooms in the account service and the standalone relay's remote ticket check."""
import importlib.util
import json
import socket
import time
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('accounts_relay', ROOT / 'tools/account_service.py')
accounts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounts)
sys.path.insert(0, str(ROOT / 'tools'))
import room_relay  # noqa: E402

KEY = 'k' * 40
RELAY = {'host': '203.0.113.10', 'port': 8766, 'key': KEY}


class RelayRoomsTest(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.service = accounts.Service(':memory:', lambda: self.now, relay=RELAY)
        self.host = self.service.request('register', {'name': 'HostPlayer', 'password': 'long password 123'})['token']
        self.guest = self.service.request('register', {'name': 'Guest', 'password': 'long password 123'})['token']

    def tearDown(self):
        self.service.db.close()

    def publish(self):
        return self.service.request('publish-room', {'relay': True, 'port': 12345, 'name': 'Online',
                                                     'profile': 'lf2-classic', 'capacity': 2}, self.host)['id']

    def test_relay_room_has_no_address_and_lists_as_relay(self):
        room = self.publish()
        listed = self.service.request('list-rooms', {}, self.guest)
        self.assertTrue(listed['relay'])
        self.assertEqual(listed['rooms'], [])
        ticket = self.service.request('relay-ticket', {'room': room, 'role': 'host'}, self.host)
        self.service.request('consume-relay-ticket', {'ticket': ticket['ticket'], 'key': KEY})
        self.assertEqual(self.service.request('list-rooms', {}, self.guest)['rooms'], [])
        with self.assertRaises(PermissionError):
            self.service.request('relay-readiness', {'room': room, 'ready': True}, self.host)
        self.service.request('relay-readiness', {'room': room, 'ready': True, 'key': KEY})
        listed = self.service.request('list-rooms', {}, self.guest)
        self.assertEqual([(r['id'], r['host'], r['relay']) for r in listed['rooms']], [(room, '', True)])
        self.now += 15
        self.assertEqual(self.service.request('list-rooms', {}, self.guest)['rooms'], [])

    def test_ticket_carries_relay_address_and_is_single_use(self):
        room = self.publish()
        ticket = self.service.request('relay-ticket', {'room': room, 'role': 'join'}, self.guest)
        self.assertEqual(ticket['relay'], {'host': '203.0.113.10', 'port': 8766})
        consumed = self.service.request('consume-relay-ticket', {'ticket': ticket['ticket'], 'key': KEY})
        self.assertEqual(consumed, {'room': room, 'role': 'join', 'capacity': 2})
        with self.assertRaises(PermissionError):
            self.service.request('consume-relay-ticket', {'ticket': ticket['ticket'], 'key': KEY})

    def test_consume_requires_relay_key_and_host_role_requires_owner(self):
        room = self.publish()
        ticket = self.service.request('relay-ticket', {'room': room, 'role': 'join'}, self.guest)['ticket']
        for key in (None, '', 'wrong' * 10):
            with self.assertRaises(PermissionError):
                self.service.request('consume-relay-ticket', {'ticket': ticket, 'key': key})
        with self.assertRaises(PermissionError):
            self.service.request('relay-ticket', {'room': room, 'role': 'host'}, self.guest)
        self.assertTrue(self.service.request('consume-relay-ticket', {'ticket': ticket, 'key': KEY}))

    def test_server_without_relay_rejects_relay_rooms_and_consume(self):
        plain = accounts.Service(':memory:', lambda: self.now)
        try:
            token = plain.request('register', {'name': 'Solo', 'password': 'long password 123'})['token']
            with self.assertRaises(ValueError):
                plain.request('publish-room', {'relay': True, 'port': 12345, 'name': 'x', 'profile': 'lf2-classic',
                                               'capacity': 2}, token)
            with self.assertRaises(PermissionError):
                plain.request('consume-relay-ticket', {'ticket': 'a' * 40, 'key': KEY})
            self.assertFalse(plain.request('list-rooms', {}, token)['relay'])
        finally:
            plain.db.close()

    def test_remote_tickets_over_http(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), accounts.handler(self.service))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            base = 'http://127.0.0.1:%d' % server.server_address[1]
            room = self.publish()
            ticket = self.service.request('relay-ticket', {'room': room, 'role': 'host'}, self.host)['ticket']
            remote = room_relay.RemoteTickets(base, KEY)
            self.assertEqual(remote.consume_relay_ticket(ticket), (room, 'host', 2))
            with self.assertRaises(PermissionError):
                remote.consume_relay_ticket(ticket)
            with self.assertRaises(PermissionError):
                room_relay.RemoteTickets(base, 'x' * 40).consume_relay_ticket('b' * 40)
            with self.assertRaises(ValueError):
                room_relay.RemoteTickets('http://example.org', KEY)
        finally:
            server.shutdown()
            server.server_close()

    def test_remote_relay_lists_waiting_host_and_withdraws_on_pairing(self):
        api = ThreadingHTTPServer(('127.0.0.1', 0), accounts.handler(self.service))
        threading.Thread(target=api.serve_forever, daemon=True).start()
        remote = room_relay.RemoteTickets('http://127.0.0.1:%d' % api.server_port, KEY)
        relay = room_relay.RelayServer(('127.0.0.1', 0), remote)
        threading.Thread(target=relay.serve_forever, daemon=True).start()

        def listed():
            return [entry['id'] for entry in self.service.request('list-rooms', {}, self.guest)['rooms']]

        def expect_listing(expected):
            deadline = time.monotonic() + 4
            while listed() != expected and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(listed(), expected)

        try:
            room = self.publish()
            host = self.service.request('relay-ticket', {'room': room, 'role': 'host'}, self.host)
            expect_listing([])
            with socket.create_connection(relay.server_address, timeout=4) as owner:
                owner.sendall(json.dumps({'ticket': host['ticket']}).encode() + b'\n')
                expect_listing([room])
                guest = self.service.request('relay-ticket', {'room': room, 'role': 'join'}, self.guest)
                with socket.create_connection(relay.server_address, timeout=4) as player:
                    room_relay.handshake(player, {'ticket': guest['ticket']})
                    self.assertEqual(owner.makefile('rb').readline(), b'{"status":"paired"}\n')
                    expect_listing([])
        finally:
            relay.shutdown()
            relay.server_close()
            api.shutdown()
            api.server_close()

    def test_passenger_status_page_for_browsers(self):
        import io
        import os
        import tempfile
        sys.path.insert(0, str(ROOT / 'tools'))
        folder = tempfile.mkdtemp()
        os.environ['POLISH_FIGHTERS_DATABASE'] = str(Path(folder) / 'accounts.sqlite')
        try:
            spec = importlib.util.spec_from_file_location('passenger_entry', ROOT / 'server/passenger_wsgi.py')
            entry = importlib.util.module_from_spec(spec)
            sys.modules['account_service'] = accounts
            spec.loader.exec_module(entry)
            app = entry.AccountApplication(':memory:', RELAY)
            app.service.request('register', {'name': 'Visible', 'password': 'long password 123'})
            seen = {}
            def start(status, headers):
                seen['status'], seen['headers'] = status, dict(headers)
            for path in ('/projekty/polish-fighters/api/', '/projekty/polish-fighters/api', '/projekty/polish-fighters/api/status'):
                body = b''.join(app({'PATH_INFO': path, 'REQUEST_METHOD': 'GET', 'wsgi.input': io.BytesIO()}, start)).decode()
                self.assertTrue(seen['status'].startswith('200'), path)
                self.assertIn('text/html', seen['headers']['Content-Type'])
                self.assertIn('działa', body)
                self.assertIn('podłączony', body)
                self.assertNotIn('Visible', body)
                self.assertNotIn(KEY, body)
                self.assertNotIn('203.0.113.10', body)
            body = b''.join(app({'PATH_INFO': '/projekty/polish-fighters/api/v1/list-rooms', 'REQUEST_METHOD': 'GET',
                                 'wsgi.input': io.BytesIO()}, start))
            self.assertTrue(seen['status'].startswith('405'))
            app.service.db.close()
            entry.application.service.db.close()
        finally:
            os.environ.pop('POLISH_FIGHTERS_DATABASE', None)

    def test_passenger_entry_reads_relay_config(self):
        source = (ROOT / 'server/passenger_wsgi.py').read_text(encoding='utf-8')
        self.assertIn('relay_settings()', source)
        self.assertIn('RELAY_KEY', source)


if __name__ == '__main__':
    unittest.main()
