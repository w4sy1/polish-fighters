"""Byte relay for the existing TCP room protocol. No gameplay messages are rewritten."""
import json
import select
import socket
import socketserver
import threading
import time


def handshake(connection, value):
    connection.sendall(json.dumps(value).encode() + b'\n')
    reply = bytearray()
    while not reply.endswith(b'\n'):
        piece = connection.recv(1)
        if not piece:
            raise ConnectionError('Relay disconnected during handshake')
        reply.extend(piece)
        if len(reply) > 1024:
            raise ValueError('Relay handshake too large')
    message = json.loads(reply)
    if message.get('status') != 'paired':
        raise ConnectionError(message.get('error', 'Relay refused channel'))


def pump(first, second, timeout=60):
    """Bounded buffers and back pressure; either disconnect closes the whole pair."""
    buffers = {first: bytearray(), second: bytearray()}
    other = {first: second, second: first}
    first.setblocking(False)
    second.setblocking(False)
    activity = time.monotonic()
    while True:
        readable = [sock for sock in other if len(buffers[other[sock]]) < 65536]
        writable = [sock for sock in other if buffers[sock]]
        reads, writes, errors = select.select(readable, writable, list(other), 1)
        if errors or time.monotonic() - activity > timeout:
            return
        for sock in reads:
            try:
                data = sock.recv(min(16384, 65536 - len(buffers[other[sock]])))
            except BlockingIOError:
                continue
            if not data:
                # A truncated stream cannot be resumed as a valid deterministic match.
                return
            buffers[other[sock]].extend(data)
            activity = time.monotonic()
        for sock in writes:
            try:
                sent = sock.send(buffers[sock])
            except BlockingIOError:
                continue
            del buffers[sock][:sent]
            activity = time.monotonic()


class RelayServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, service):
        self.service = service
        self.condition = threading.Condition()
        self.waiting = {}
        self.active = {}
        self.slots = threading.BoundedSemaphore(64)
        super().__init__(address, RelayHandler)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class RelayHandler(socketserver.BaseRequestHandler):
    def handle(self):
        connection = self.request
        connection.settimeout(10)
        server = self.server
        waiter = None
        room = None
        try:
            header = bytearray()
            while not header.endswith(b'\n'):
                data = connection.recv(1)
                if not data:
                    return
                header.extend(data)
                if len(header) > 1024:
                    raise ValueError('Handshake too large')
            message = json.loads(header)
            if not isinstance(message, dict):
                raise ValueError('Expected handshake object')
            room, role, capacity = server.service.consume_relay_ticket(message.get('ticket'))
            if role == 'host':
                waiter = {'socket': connection, 'peer': None, 'done': threading.Event()}
                with server.condition:
                    waiting = server.waiting.setdefault(room, [])
                    if len(waiting) + server.active.get(room, 0) >= capacity - 1:
                        raise ValueError('Host channel limit reached')
                    waiting.append(waiter)
                    server.condition.notify_all()
                    if not server.condition.wait_for(lambda: waiter['peer'] is not None, timeout=60):
                        raise TimeoutError('No joining player')
                peer = waiter['peer']
                try:
                    connection.sendall(b'{"status":"paired"}\n')
                    peer.sendall(b'{"status":"paired"}\n')
                    pump(connection, peer)
                finally:
                    with server.condition:
                        server.active[room] -= 1
                    waiter['done'].set()
            else:
                with server.condition:
                    if not server.condition.wait_for(lambda: bool(server.waiting.get(room)), timeout=10):
                        raise TimeoutError('Host relay unavailable')
                    waiter = server.waiting[room].pop(0)
                    waiter['peer'] = connection
                    server.active[room] = server.active.get(room, 0) + 1
                    server.condition.notify_all()
                # Host thread owns forwarding; keep this socket alive until it finishes.
                waiter['done'].wait()
        except (OSError, ValueError, PermissionError, KeyError):
            try:
                connection.sendall(b'{"error":"Relay channel unavailable"}\n')
            except OSError:
                pass
        finally:
            if waiter and room:
                with server.condition:
                    pending = server.waiting.get(room, [])
                    if waiter in pending:
                        pending.remove(waiter)
                    if not pending:
                        server.waiting.pop(room, None)
                # Always release join thread even if handshake send failed.
                if waiter.get('socket') is connection:
                    waiter['done'].set()
