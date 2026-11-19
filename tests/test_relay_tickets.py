"""Relay rooms in the account service and the standalone relay's remote ticket check."""
import importlib.util
import json
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
        self.assertEqual([(r['id'], r['host'], r['relay']) for r in listed['rooms']], [(room, '', True)])

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

    def test_passenger_entry_reads_relay_config(self):
        source = (ROOT / 'server/passenger_wsgi.py').read_text(encoding='utf-8')
        self.assertIn('relay_settings()', source)
        self.assertIn('RELAY_KEY', source)


if __name__ == '__main__':
    unittest.main()
