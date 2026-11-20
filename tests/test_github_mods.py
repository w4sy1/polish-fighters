import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_mod_release  # noqa: E402
import github_mods  # noqa: E402


def canonical(document):
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


class GitHubModsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)

    def tearDown(self):
        self.temporary.cleanup()

    def envelope(self, pack_id='lf4-turbo', extra=None, manifest_id=None):
        pack = self.root / 'source' / pack_id
        (pack / 'assets/a').mkdir(parents=True, exist_ok=True)
        (pack / 'package.manifest').write_text(
            f'id={manifest_id or pack_id}\nversion=1\napi=1\nasset=mods/{pack_id}/a/1.bmp|assets/a/1.bmp\n', encoding='utf-8')
        (pack / 'catalog.lua').write_text('return function(base) return base end\n', encoding='utf-8')
        (pack / 'assets/a/1.bmp').write_bytes(b'BM' + bytes(range(256)) * 4)
        files = build_mod_release.pack_files(pack)
        if extra:
            for name, data in extra.items():
                target = pack / name
                target.write_bytes(data)
                files[name] = target
        output = self.root / 'release'
        output.mkdir(exist_ok=True)
        payload = output / 'payload.zip'
        unpacked = build_mod_release.write_package(files, payload)
        manifest = {
            'schema_version': 2, 'id': pack_id, 'name': 'Pack', 'version': '1.0.0', 'author': 'Test', 'license': 'Test',
            'min_engine_version': '1.1.1', 'platforms': ['windows', 'android'], 'category': 'content-pack',
            'package_type': 'content-pack', 'dependencies': [], 'conflicts': [],
            'size_bytes': payload.stat().st_size, 'unpacked_size_bytes': unpacked,
            'sha256': hashlib.sha256(payload.read_bytes()).hexdigest(),
            'source': {'type': 'github-release-asset',
                       'url': f'https://github.com/w4sy1/polish-fighters/releases/download/mods/{pack_id}-1.0.0.zip'},
            'test_status': {'windows': 'pending', 'android': 'pending'}, 'required_assets': [],
            'installation': {'method': 'content-pack-zip', 'entrypoint': 'package.manifest'},
        }
        raw = canonical(manifest)
        index = canonical({'channel': 'stable', 'revision': 1,
                           'manifests': {f'{pack_id}@1.0.0': hashlib.sha256(raw).hexdigest()}})
        target = output / f'{pack_id}-1.0.0.zip'
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as archive:
            build_mod_release.stored(archive, 'catalog.json', index)
            build_mod_release.stored(archive, 'catalog.sig', self.key.sign(index))
            build_mod_release.stored(archive, 'manifest.json', raw)
            build_mod_release.stored(archive, 'manifest.sig', self.key.sign(raw))
            build_mod_release.stored(archive, 'package.zip', payload.read_bytes())
        return target

    def test_installs_and_updates_signed_content_pack(self):
        packs = self.root / 'content-packs'
        manifest = github_mods.install_envelope(self.envelope(), packs, self.public, expected_id='lf4-turbo')
        self.assertEqual('lf4-turbo', manifest['id'])
        self.assertTrue((packs / 'lf4-turbo/assets/a/1.bmp').is_file())
        (packs / 'lf4-turbo/stale.txt').write_text('old')
        github_mods.install_envelope(self.envelope(), packs, self.public, expected_id='lf4-turbo')
        self.assertFalse((packs / 'lf4-turbo/stale.txt').exists())
        self.assertEqual(['lf4-turbo'], [path.name for path in packs.iterdir()])

    def test_rejects_tampering_foreign_keys_and_executables(self):
        packs = self.root / 'content-packs'
        envelope = self.envelope()
        data = bytearray(envelope.read_bytes())
        data[-400] ^= 1
        envelope.write_bytes(data)
        with self.assertRaises(Exception):
            github_mods.install_envelope(envelope, packs, self.public)
        other = Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        with self.assertRaises(ValueError):
            github_mods.install_envelope(self.envelope(), packs, other)
        with self.assertRaises(ValueError):
            github_mods.install_envelope(self.envelope(extra={'run.exe': b'MZ'}), packs, self.public)
        with self.assertRaises(ValueError):
            github_mods.install_envelope(self.envelope(), packs, self.public, expected_id='dbz')
        with self.assertRaises(ValueError):
            github_mods.install_envelope(self.envelope(manifest_id='kate'), packs, self.public)
        self.assertFalse((packs / 'lf4-turbo').exists())

    def test_catalogue_signature_and_urls(self):
        entry = {'id': 'lf4-turbo', 'name': 'LF4 Turbo', 'version': '1.0.0', 'profile': 'lf_four_turbo',
                 'url': 'https://github.com/w4sy1/polish-fighters/releases/download/mods/lf4-turbo-1.0.0.zip',
                 'size_bytes': 10, 'unpacked_size_bytes': 20, 'sha256': 'a' * 64}
        document = {'format': 'polish-fighters-mods', 'channel': 'stable', 'revision': 1, 'packages': [entry]}
        raw = canonical(document)
        self.assertEqual('LF4 Turbo', github_mods.verify_catalogue(raw, self.key.sign(raw), self.public)['packages'][0]['name'])
        with self.assertRaises(ValueError):
            github_mods.verify_catalogue(raw.replace(b'10', b'11'), self.key.sign(raw), self.public)
        evil = canonical(dict(document, packages=[dict(entry, url='https://evil.example/lf4-turbo-1.0.0.zip')]))
        with self.assertRaises(ValueError):
            github_mods.verify_catalogue(evil, self.key.sign(evil), self.public)

    def test_repository_catalogue_is_signed_by_the_trusted_key(self):
        raw = (ROOT / 'mods/catalog.json').read_bytes()
        catalogue = github_mods.verify_catalogue(raw, (ROOT / 'mods/catalog.sig').read_bytes(), github_mods.trusted_key())
        ids = {entry['id'] for entry in catalogue['packages']}
        self.assertTrue({'lf4-turbo', 'dbz', 'one-piece', 'kate', 'reinforced', 'ntsd', 'bleach',
                         'polish-originals', 'mixed-all'} <= ids)

    def test_native_installer_embeds_the_trusted_key(self):
        source = (ROOT / 'engine/src/adapters/curl/github_mods.cpp').read_text(encoding='utf-8')
        block = re.search(r'trusted_key\{(.*?)\};', source, re.S)[1]
        embedded = bytes(int(value, 16) for value in re.findall(r'0x([0-9a-f]{2})', block))
        self.assertEqual(github_mods.trusted_key(), embedded)

    def test_private_key_never_lives_in_the_repository(self):
        import subprocess
        try:
            tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest('git is unavailable')
        for name in tracked.decode('utf-8').split(chr(0)):
            path = ROOT / name
            if (name and path.suffix.lower() in ('.pem', '.key', '.txt', '.json', '.md') and path.is_file()
                    and path.stat().st_size < 4 * 1024 * 1024):
                self.assertNotIn(b'BEGIN PRIVATE KEY', path.read_bytes(), name)

if __name__ == '__main__':
    unittest.main()
