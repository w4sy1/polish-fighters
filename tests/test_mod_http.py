import http.server
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mod_http as http_tools

_CERT_DIR = tempfile.TemporaryDirectory()
_CERT = Path(_CERT_DIR.name) / 'cert.pem'
_KEY = Path(_CERT_DIR.name) / 'key.pem'
subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-keyout', str(_KEY),
                 '-out', str(_CERT), '-days', '1', '-nodes', '-subj', '/CN=127.0.0.1'],
                check=True, capture_output=True)


def setUpModule():
    # The production code always connects over real TLS (https://), so the
    # loopback test server must terminate TLS too; trust its self-signed cert
    # the same way "curl -k" would, scoped to this test module only.
    global _ORIGINAL_CONTEXT_FACTORY
    _ORIGINAL_CONTEXT_FACTORY = ssl._create_default_https_context
    ssl._create_default_https_context = ssl._create_unverified_context


def tearDownModule():
    ssl._create_default_https_context = _ORIGINAL_CONTEXT_FACTORY
    _CERT_DIR.cleanup()


def relaxed_validate_url(url):
    """Same as mod_http.validate_url but also accepts loopback, for tests only."""
    import ipaddress
    import urllib.parse
    if not isinstance(url, str) or len(url) > 2048 or any(ord(c) < 33 for c in url):
        raise ValueError('Invalid URL')
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Only public HTTPS URLs are supported')
    # Real validate_url pins the resolution probe to port 443; tests run a local
    # server on an ephemeral port, so probe whatever port the URL actually uses.
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    if not addresses or any(not (ipaddress.ip_address(item[4][0]).is_global or ipaddress.ip_address(item[4][0]).is_loopback) for item in addresses):
        raise ValueError('Private and local network addresses are forbidden')
    return urllib.parse.urlunsplit(parsed._replace(fragment=''))


class Handler(http.server.BaseHTTPRequestHandler):
    robots = 'User-agent: *\nDisallow: /blocked\n'
    page_type = 'text/html'

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == '/robots.txt':
            body = self.robots.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/missing-robots.txt':
            self.send_response(404)
            self.end_headers()
        elif self.path in ('/allowed', '/allowed-page'):
            body = b'<html><head><title>ok</title></head><body>hi</body></html>'
            self.send_response(200)
            self.send_header('Content-Type', self.page_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/blocked':
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'hi')
        else:
            self.send_response(404)
            self.end_headers()


class LocalServer:
    def __init__(self, handler=Handler):
        self.server = http.server.HTTPServer(('127.0.0.1', 0), handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(_CERT), str(_KEY))
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base(self):
        return 'https://127.0.0.1:%d' % self.server.server_address[1]

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class ValidateUrlSyntaxTests(unittest.TestCase):
    def test_rejects_non_https_scheme(self):
        with self.assertRaises(ValueError):
            http_tools.validate_url('http://example.com/a.zip')

    def test_rejects_non_default_port(self):
        with self.assertRaises(ValueError):
            http_tools.validate_url('https://example.com:8443/a.zip')

    def test_rejects_credentials_in_url(self):
        with self.assertRaises(ValueError):
            http_tools.validate_url('https://user:pass@example.com/a.zip')

    def test_rejects_control_characters(self):
        with self.assertRaises(ValueError):
            http_tools.validate_url('https://example.com/a\n.zip')

    def test_rejects_oversized_url(self):
        with self.assertRaises(ValueError):
            http_tools.validate_url('https://example.com/' + 'a' * 2048)

    def test_strips_fragment(self):
        with patch('socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 0, '', ('93.184.216.34', 443))]):
            result = http_tools.validate_url('https://example.com/a.zip#frag')
        self.assertEqual(result, 'https://example.com/a.zip')


class ValidateUrlSsrfTests(unittest.TestCase):
    def test_rejects_private_address(self):
        with patch('socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 0, '', ('127.0.0.1', 443))]):
            with self.assertRaises(ValueError):
                http_tools.validate_url('https://internal.example/a.zip')

    def test_rejects_link_local_address(self):
        with patch('socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 0, '', ('169.254.169.254', 443))]):
            with self.assertRaises(ValueError):
                http_tools.validate_url('https://metadata.example/a.zip')

    def test_accepts_public_address(self):
        with patch('socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 0, '', ('93.184.216.34', 443))]):
            self.assertEqual(http_tools.validate_url('https://example.com/a.zip'), 'https://example.com/a.zip')

    def test_rejects_if_any_resolved_address_is_private(self):
        # A hostname that resolves to both a public and a private address must
        # not be treated as safe: open_public/_open may connect to either one.
        addrs = [(socket.AF_INET, socket.SOCK_STREAM, 0, '', ('93.184.216.34', 443)),
                 (socket.AF_INET, socket.SOCK_STREAM, 0, '', ('10.0.0.5', 443))]
        with patch('socket.getaddrinfo', return_value=addrs):
            with self.assertRaises(ValueError):
                http_tools.validate_url('https://mixed.example/a.zip')


class RobotsTests(unittest.TestCase):
    def setUp(self):
        http_tools._robots.clear()
        http_tools._last_request.clear()
        self.server = LocalServer()
        self.addCleanup(self.server.close)
        self.patcher = patch('mod_http.validate_url', relaxed_validate_url)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_disallowed_path_raises(self):
        with self.assertRaises(ValueError):
            http_tools.check_robots(self.server.base + '/blocked')

    def test_allowed_path_passes(self):
        http_tools.check_robots(self.server.base + '/allowed')  # must not raise

    def test_missing_robots_txt_allows_everything(self):
        class NoRobots(Handler):
            def do_GET(self):
                if self.path == '/robots.txt':
                    self.send_response(404)
                    self.end_headers()
                else:
                    super().do_GET()
        server = LocalServer(NoRobots)
        self.addCleanup(server.close)
        http_tools.check_robots(server.base + '/blocked')  # must not raise: no robots.txt => allow

    def test_html_challenge_page_rejected_as_robots(self):
        class Challenge(Handler):
            robots = '<html><body>cf-chl-bypass challenge</body></html>'
        server = LocalServer(Challenge)
        self.addCleanup(server.close)
        with self.assertRaises(ValueError):
            http_tools.check_robots(server.base + '/allowed')

    def test_robots_is_cached_per_origin(self):
        http_tools.check_robots(self.server.base + '/allowed')
        calls_before = len(http_tools._robots)
        http_tools.check_robots(self.server.base + '/allowed-page')
        self.assertEqual(len(http_tools._robots), calls_before)


class HtmlPageTests(unittest.TestCase):
    def setUp(self):
        http_tools._robots.clear()
        http_tools._last_request.clear()
        self.server = LocalServer()
        self.addCleanup(self.server.close)
        self.patcher = patch('mod_http.validate_url', relaxed_validate_url)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_fetches_and_decodes_html(self):
        actual, text = http_tools.html_page(self.server.base + '/allowed')
        self.assertIn('hi', text)
        self.assertTrue(actual.endswith('/allowed'))

    def test_rejects_captcha_marker(self):
        class Captcha(Handler):
            page_type = 'text/html'

            def do_GET(self):
                if self.path == '/allowed':
                    body = b'<html>please complete the g-recaptcha challenge</html>'
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    super().do_GET()
        server = LocalServer(Captcha)
        self.addCleanup(server.close)
        with self.assertRaises(ValueError):
            http_tools.html_page(server.base + '/allowed')


if __name__ == '__main__':
    unittest.main()
