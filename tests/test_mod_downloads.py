import hashlib
import http.server
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mod_downloads
import mod_http

_CERT_DIR = tempfile.TemporaryDirectory()
_CERT = Path(_CERT_DIR.name) / 'cert.pem'
_KEY = Path(_CERT_DIR.name) / 'key.pem'
subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-keyout', str(_KEY),
                 '-out', str(_CERT), '-days', '1', '-nodes', '-subj', '/CN=127.0.0.1'],
                check=True, capture_output=True)


def _zip_bytes(name='a.dat', payload=b'hello world'):
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr(name, payload)
    return buffer.getvalue()


ARCHIVE_BYTES = _zip_bytes()
ARCHIVE_SHA256 = hashlib.sha256(ARCHIVE_BYTES).hexdigest()


def setUpModule():
    global _ORIGINAL_CONTEXT_FACTORY
    _ORIGINAL_CONTEXT_FACTORY = ssl._create_default_https_context
    ssl._create_default_https_context = ssl._create_unverified_context


def tearDownModule():
    ssl._create_default_https_context = _ORIGINAL_CONTEXT_FACTORY
    _CERT_DIR.cleanup()


class ArchiveHandler(http.server.BaseHTTPRequestHandler):
    body = ARCHIVE_BYTES
    content_type = 'application/zip'
    allow_range = True
    etag = '"fixed-etag"'
    seen_ranges = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == '/robots.txt':
            self.send_response(404)
            self.end_headers()
            return
        if self.path != '/archive.zip':
            self.send_response(404)
            self.end_headers()
            return
        body = self.body
        range_header = self.headers.get('Range')
        type(self).seen_ranges.append(range_header)
        if range_header and self.allow_range:
            start = int(range_header.split('=')[1].split('-')[0])
            chunk = body[start:]
            self.send_response(206)
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, len(body) - 1, len(body)))
            self.send_header('Content-Length', str(len(chunk)))
            if self.etag:
                self.send_header('ETag', self.etag)
            self.send_header('Content-Type', self.content_type)
            self.end_headers()
            self.wfile.write(chunk)
        else:
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            if self.etag:
                self.send_header('ETag', self.etag)
            self.send_header('Content-Type', self.content_type)
            self.end_headers()
            self.wfile.write(body)


class LocalServer:
    def __init__(self, handler):
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


def relaxed_validate_url(url):
    return url  # loopback test server; real SSRF rules are covered in test_mod_http.py


class QueueTestCase(unittest.TestCase):
    def setUp(self):
        mod_http._robots.clear()
        mod_http._last_request.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.queue = mod_downloads.Queue(Path(self.tmp.name) / 'downloads')
        self.addCleanup(self.queue.close)
        self.patchers = [patch('mod_downloads.validate_url', relaxed_validate_url),
                         patch('mod_http.validate_url', relaxed_validate_url)]
        for p in self.patchers:
            p.start()
            self.addCleanup(p.stop)

    def start_server(self, handler=ArchiveHandler):
        handler = type('H', (handler,), {'seen_ranges': []})
        server = LocalServer(handler)
        self.addCleanup(server.close)
        return server, handler


class DownloadFlowTests(QueueTestCase):
    def test_full_download_completes_with_correct_sha256(self):
        server, _ = self.start_server()
        job = self.queue.add(server.base + '/archive.zip')
        self.queue.run()
        job = self.queue.job(job['id'])
        self.assertEqual(job['status'], 'completed')
        self.assertEqual(job['sha256'], ARCHIVE_SHA256)
        self.assertTrue(job['result_path'].endswith('.zip'))
        self.assertEqual(Path(job['result_path']).read_bytes(), ARCHIVE_BYTES)

    def test_duplicate_enqueue_returns_same_job(self):
        server, _ = self.start_server()
        first = self.queue.add(server.base + '/archive.zip')
        second = self.queue.add(server.base + '/archive.zip')
        self.assertEqual(first['id'], second['id'])
        self.assertEqual(len(self.queue.jobs()), 1)

    def test_sha256_mismatch_is_rejected_and_file_not_kept(self):
        server, _ = self.start_server()
        wrong = '0' * 64
        job = self.queue.add(server.base + '/archive.zip', expected_sha256=wrong)
        self.queue.run()
        job = self.queue.job(job['id'])
        self.assertEqual(job['status'], 'failed')
        self.assertFalse(list((Path(self.tmp.name) / 'downloads').glob('*.zip')))

    def test_html_response_is_rejected_before_download(self):
        class NotArchive(ArchiveHandler):
            body = b'<html>not an archive</html>'
            content_type = 'text/html'
        server, _ = self.start_server(NotArchive)
        job = self.queue.add(server.base + '/archive.zip')
        self.queue.run()
        job = self.queue.job(job['id'])
        self.assertEqual(job['status'], 'failed')
        self.assertIn('page instead of an archive', job['error'])

    def test_non_archive_binary_is_rejected_by_magic_bytes(self):
        class NotArchive(ArchiveHandler):
            body = b'not actually a zip file, just plain bytes........'
            content_type = 'application/octet-stream'
        server, _ = self.start_server(NotArchive)
        job = self.queue.add(server.base + '/archive.zip')
        self.queue.run()
        job = self.queue.job(job['id'])
        self.assertEqual(job['status'], 'failed')
        self.assertIn('not a supported archive', job['error'])
        self.assertFalse(list((Path(self.tmp.name) / 'downloads').glob('*.part')))

    def test_malformed_reference_sha256_is_rejected_at_enqueue(self):
        with self.assertRaises(ValueError):
            self.queue.add('https://example.com/a.zip', expected_sha256='not-hex')

    def test_resume_uses_range_request_with_etag(self):
        server, handler = self.start_server()
        job = self.queue.add(server.base + '/archive.zip')
        part = self.queue.directory / (job['id'] + '.part')
        part.write_bytes(ARCHIVE_BYTES[:4])
        self.queue.db.execute('UPDATE jobs SET etag=? WHERE id=?', (ArchiveHandler.etag, job['id']))
        self.queue.db.commit()
        self.queue.run()
        job = self.queue.job(job['id'])
        self.assertEqual(job['status'], 'completed')
        self.assertEqual(Path(job['result_path']).read_bytes(), ARCHIVE_BYTES)
        self.assertTrue(any(r and r.startswith('bytes=4') for r in handler.seen_ranges))

    def test_duplicate_bytes_reuse_existing_file_on_disk(self):
        server, _ = self.start_server()
        first = self.queue.add(server.base + '/archive.zip?a=1')
        self.queue.db.execute('UPDATE jobs SET url=? WHERE id=?', (server.base + '/archive.zip', first['id']))
        self.queue.db.commit()
        self.queue.run()
        self.assertEqual(self.queue.job(first['id'])['status'], 'completed')
        second = self.queue.db.execute(
            "INSERT INTO jobs(id,url,status,created,updated) VALUES ('deadbeefdeadbeefdeadbeefdeadbeef',?,?,?,?)",
            (server.base + '/archive.zip', 'queued', mod_downloads.now(), mod_downloads.now()))
        self.queue.db.commit()
        self.queue.run()
        updated = self.queue.job('deadbeefdeadbeefdeadbeefdeadbeef')
        self.assertEqual(updated['status'], 'completed')
        self.assertEqual(updated['result_path'], self.queue.job(first['id'])['result_path'])

    def test_control_pause_resume_cancel_state_machine(self):
        server, _ = self.start_server()
        job = self.queue.add(server.base + '/archive.zip')
        self.queue.control(job['id'], 'pause')
        self.assertEqual(self.queue.job(job['id'])['status'], 'paused')
        with self.assertRaises(ValueError):
            self.queue.control(job['id'], 'pause')
        self.queue.control(job['id'], 'resume')
        self.assertEqual(self.queue.job(job['id'])['status'], 'queued')
        self.queue.control(job['id'], 'cancel')
        self.assertEqual(self.queue.job(job['id'])['status'], 'cancelled')
        self.queue.control(job['id'], 'cancel')  # cancel is idempotent, not an error
        self.assertEqual(self.queue.job(job['id'])['status'], 'cancelled')
        with self.assertRaises(ValueError):
            self.queue.control(job['id'], 'resume')  # cannot resume a cancelled job

    def test_unknown_job_id_raises(self):
        with self.assertRaises(ValueError):
            self.queue.job('does-not-exist')


if __name__ == '__main__':
    unittest.main()
