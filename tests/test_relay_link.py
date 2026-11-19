"""Real loopback relay test: tools/room_relay.py between the native host bridge and a joiner.
Run: python tests/test_relay_link.py --runner /path/to/relay-link-runner
"""
import argparse
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from room_relay import RelayServer  # noqa: E402

HOST_TICKET = 'h' * 40
JOIN_TICKET = 'j' * 40


class Tickets:
    """Single-use tickets for one two-device room, like the account service."""

    def __init__(self):
        self.lock = threading.Lock()
        self.tickets = {HOST_TICKET: ('room-1', 'host', 2), JOIN_TICKET: ('room-1', 'join', 2)}

    def consume_relay_ticket(self, ticket):
        with self.lock:
            if ticket not in self.tickets:
                raise PermissionError('Expired or consumed relay ticket')
            return self.tickets.pop(ticket)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runner', required=True)
    args = parser.parse_args()
    server = RelayServer(('127.0.0.1', 0), Tickets())
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        result = subprocess.run([str(Path(args.runner).resolve()), str(server.server_address[1]), HOST_TICKET, JOIN_TICKET],
                                capture_output=True, text=True, timeout=60)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        if result.returncode != 0:
            raise SystemExit('relay link runner failed')
        assert 'PASS' in result.stdout
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
