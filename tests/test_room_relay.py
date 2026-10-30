import sys
import threading
import socket
import unittest
import asyncio
from types import SimpleNamespace
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from account_service import Service, handler
from room_relay import RelayServer, handshake
from relay_bridge import open_channel, bridge


class RelayTest(unittest.TestCase):
    def setUp(self):
        self.service = Service(':memory:')
        self.host = self.service.request('register', {'name': 'host', 'password': 'host password 123'})['token']
        self.join = self.service.request('register', {'name': 'join', 'password': 'join password 123'})['token']
        self.room = self.service.request('publish-room', {'name': 'Room', 'host': '127.0.0.1', 'port': 12345,
                                        'profile': 'lf4-turbo', 'capacity': 8}, self.host)['id']
        self.server = RelayServer(('127.0.0.1', 0), self.service)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.service.db.close()

    def ticket(self, role, token):
        return self.service.request('relay-ticket', {'room': self.room, 'role': role}, token)['ticket']

    def test_one_time_tickets_and_owner(self):
        with self.assertRaises(PermissionError):
            self.ticket('host', self.join)
        ticket = self.ticket('join', self.join)
        self.assertEqual(self.service.consume_relay_ticket(ticket)[1], 'join')
        with self.assertRaises(PermissionError):
            self.service.consume_relay_ticket(ticket)

    def test_http_tickets_and_async_bridge(self):
        room=self.service.request('publish-room',{'name':'Private','host':'127.0.0.1','port':12345,
                                  'profile':'lf4-turbo','capacity':8,'private':True},self.host)['id']
        self.assertEqual(room,self.room)
        invitation=self.service.request('create-invite',{'room':room},self.host)['code']
        http = ThreadingHTTPServer(('127.0.0.1', 0), handler(self.service))
        worker = threading.Thread(target=http.serve_forever, daemon=True)
        worker.start()
        args = SimpleNamespace(service='http://127.0.0.1:%s' % http.server_port, room=self.room,
                               relay_host='127.0.0.1', relay_port=self.server.server_address[1], plain_local_only=True,invite=invitation)
        async def check():
            async def echo(reader, writer):
                try:
                    while data := await reader.read(16384):
                        writer.write(data)
                        await writer.drain()
                finally:
                    writer.close()
                    await writer.wait_closed()
            echo_server = await asyncio.start_server(echo, '127.0.0.1', 0)
            try:
                host, join = await asyncio.wait_for(asyncio.gather(open_channel(args, self.host, 'host'),
                                                                  open_channel(args, self.join, 'join')), timeout=5)
                local = await asyncio.open_connection('127.0.0.1', echo_server.sockets[0].getsockname()[1])
                forwarding = asyncio.create_task(bridge(host, local))
                payload = b'unchanged room protocol\n' + bytes(range(256)) * 400
                join[1].write(payload)
                await join[1].drain()
                self.assertEqual(await asyncio.wait_for(join[0].readexactly(len(payload)), timeout=5), payload)
                join[1].close()
                await join[1].wait_closed()
                await asyncio.wait_for(forwarding, timeout=3)
            finally:
                echo_server.close()
                await echo_server.wait_closed()
        try:
            asyncio.run(check())
        finally:
            http.shutdown()
            http.server_close()
            worker.join(timeout=3)

    def test_existing_protocol_bytes_bidirectional_and_disconnect(self):
        errors = []
        ticket = self.ticket('host', self.host)
        host_ready = threading.Event()
        packet = b'{"op":"hello","protocol":1,"name":"Player"}\n' + bytes(range(256)) * 300

        def host():
            try:
                with socket.create_connection(self.server.server_address, timeout=5) as connection:
                    host_ready.set()
                    handshake(connection, {'ticket': ticket})
                    received = bytearray()
                    while len(received) < len(packet):
                        received.extend(connection.recv(16384))
                    self.assertEqual(bytes(received), packet)
                    connection.sendall(b'{"op":"welcome","slot":1}\n')
                    self.assertEqual(connection.recv(1), b'')
            except BaseException as error:
                errors.append(error)
        worker = threading.Thread(target=host, daemon=True)
        worker.start()
        self.assertTrue(host_ready.wait(2))
        with socket.create_connection(self.server.server_address, timeout=5) as client:
            handshake(client, {'ticket': self.ticket('join', self.join)})
            client.sendall(packet)
            reply = bytearray()
            while not reply.endswith(b'\n'):
                reply.extend(client.recv(1))
            self.assertEqual(reply, b'{"op":"welcome","slot":1}\n')
        worker.join(timeout=5)
        self.assertFalse(worker.is_alive(), 'disconnect must propagate')
        if errors:
            raise errors[0]


if __name__ == '__main__':
    unittest.main()
