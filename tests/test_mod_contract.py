import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from verify_mod_package import verify_catalog, verify_package


def canonical(document):
    return json.dumps(document, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':')).encode('utf-8')


class ModContractTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.archive = self.root / 'arena.zip'
        self.signer = Ed25519PrivateKey.generate()
        self.key = self.signer.public_key().public_bytes_raw()

    def fixture(self, extra=None):
        files = {'arena.json': b'{}'}
        files.update(extra or {})
        with zipfile.ZipFile(self.archive, 'w') as output:
            for name, contents in files.items():
                output.writestr(name, contents)
        return {
            'schema_version': 2, 'id': 'arena', 'name': 'Arena', 'version': '1.0.0',
            'author': 'Test', 'license': 'CC-BY-4.0', 'min_engine_version': '1.4.0',
            'platforms': ['windows', 'android'], 'category': 'areny', 'package_type': 'data-only',
            'dependencies': [], 'conflicts': [], 'required_assets': [],
            'size_bytes': self.archive.stat().st_size,
            'unpacked_size_bytes': sum(map(len, files.values())),
            'sha256': hashlib.sha256(self.archive.read_bytes()).hexdigest(),
            'source': {'type': 'github-release-asset', 'url': 'https://github.com/w4sy1/polish-fighters-mody/releases/download/arena-v1.0.0/arena.zip'},
            'test_status': {'windows': 'pending', 'android': 'pending'},
            'installation': {'method': 'managed-data-zip', 'entrypoint': 'arena.json'},
        }

    def verify(self, manifest):
        raw = canonical(manifest)
        return verify_package(raw, self.signer.sign(raw), self.key, self.archive, google_play=True)

    def test_signed_data_package(self):
        self.assertEqual(self.verify(self.fixture())['id'], 'arena')

    def test_wrong_signature_and_wrong_hash(self):
        manifest = self.fixture()
        raw = canonical(manifest)
        other_signer = Ed25519PrivateKey.generate()
        with self.assertRaisesRegex(ValueError, 'signature'):
            verify_package(raw, other_signer.sign(raw), self.key, self.archive)
        manifest['sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.verify(manifest)

    def test_play_rejects_lua_native_and_legacy_extensions(self):
        for name in ('catalog.lua', 'sounds.LUA', 'libmod.so', 'plugin.dex', 'code.jar', 'data.dat'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'executable|forbidden'):
                self.verify(self.fixture({name: b'data'}))

    def test_invalid_manifest(self):
        manifest = self.fixture()
        del manifest['license']
        with self.assertRaisesRegex(ValueError, 'license'):
            self.verify(manifest)

    def test_catalog_signature_channel_and_revision(self):
        raw = canonical({'channel': 'test', 'revision': 2, 'manifests': {}})
        signature = self.signer.sign(raw)
        self.assertEqual(verify_catalog(raw, signature, self.key, 'test')['revision'], 2)
        with self.assertRaisesRegex(ValueError, 'signature'):
            verify_catalog(raw.replace(b'"test"', b'"stable"'), signature, self.key, 'stable')
        for channel, revision in [('stable', 1), ('test', 3)]:
            with self.subTest(channel=channel, revision=revision), self.assertRaises(ValueError):
                verify_catalog(raw, signature, self.key, channel, min_revision=revision)

    def test_cli_requires_manifest_pinned_by_catalog(self):
        raw = canonical(self.fixture())
        sources = [self.root / name for name in ('manifest', 'manifest.sig', 'key', 'index', 'index.sig')]
        for path, data in zip(sources, (raw, self.signer.sign(raw), self.key)):
            path.write_bytes(data)
        for pinned in (False, True):
            manifests = {'arena@1.0.0': hashlib.sha256(raw).hexdigest()} if pinned else {}
            catalog = canonical({'channel': 'stable', 'revision': 1, 'manifests': manifests})
            sources[3].write_bytes(catalog)
            sources[4].write_bytes(self.signer.sign(catalog))
            command = [sys.executable, str(ROOT / 'tools/verify_mod_package.py'),
                       *map(str, sources[:3]), str(self.archive), '--catalog', str(sources[3]),
                       '--catalog-signature', str(sources[4]), '--google-play']
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0 if pinned else 1, result.stderr)
            if not pinned:
                self.assertIn('not pinned', result.stderr)
