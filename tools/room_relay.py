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


class RemoteTickets:
    """Ticket check for a relay running on another machine than the account API.

    The API (e.g. on shared WordPress hosting) issues tickets; this relay consumes each one
    exactly once through POST <api>/v1/consume-relay-ticket with the shared relay key.
    """

    def __init__(self, api, key, timeout=10):
        import urllib.parse
        parts = urllib.parse.urlsplit(api)
        if parts.scheme != 'https' and parts.hostname not in ('127.0.0.1', 'localhost'):
            raise ValueError('Account API must use HTTPS')
        self.endpoint = api.rstrip('/') + '/v1/consume-relay-ticket'
        self.key = key
        self.timeout = timeout

    def consume_relay_ticket(self, ticket):
        import ssl
        import urllib.error
        import urllib.request
        if not isinstance(ticket, str) or not 16 <= len(ticket) <= 128:
            raise PermissionError('Invalid relay ticket')
        body = json.dumps({'ticket': ticket, 'key': self.key}).encode()
        request = urllib.request.Request(self.endpoint, data=body, method='POST',
                                         headers={'Content-Type': 'application/json', 'Accept': 'application/json',
                                                  'User-Agent': 'pf-room-relay'})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=ssl.create_default_context()) as response:
                value = json.loads(response.read(4096))
        except urllib.error.HTTPError as error:
            raise PermissionError('Ticket rejected (HTTP %d)' % error.code) from None
        except (OSError, ValueError):
            raise PermissionError('Account API unavailable') from None
        room, role, capacity = value.get('room'), value.get('role'), value.get('capacity')
        if not isinstance(room, str) or role not in ('host', 'join') or type(capacity) is not int or not 2 <= capacity <= 8:
            raise PermissionError('Invalid ticket response')
        return room, role, capacity


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='Standalone Polish Fighters match relay.')
    parser.add_argument('--api', required=True, help='Account API base URL, e.g. https://example.org/api')
    parser.add_argument('--key-file', required=True, help='File holding the shared relay key (same as on the API)')
    parser.add_argument('--bind', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args(argv)
    with open(args.key_file, encoding='utf-8') as handle:
        key = handle.read().strip()
    if len(key) < 32:
        raise SystemExit('Relay key must have at least 32 characters')
    server = RelayServer((args.bind, args.port), RemoteTickets(args.api, key))
    print('Relay listening on %s:%d, tickets via %s' % (args.bind, args.port, args.api), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
