import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from prepare_android_game import bundle


class AndroidBundleTest(unittest.TestCase):
    def test_shared_payload_is_stored_once_and_all_logical_paths_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a, b, c = root / 'a', root / 'b', root / 'c'
            a.write_bytes(b'PNG shared data')
            b.write_bytes(a.read_bytes())
            c.write_bytes(b'unique Lua module')
            report = bundle({'content-packs/a/assets/a.png': a,
                             'content-packs/mixed/assets/a.png': b,
                             'scripts/base/test.lua': c}, root / 'out')
            self.assertEqual(report['files'], 3)
            self.assertEqual(report['unique_payloads'], 2)
            with ZipFile(root / 'out/game-bundle.zip') as archive:
                manifest = archive.read('manifest.json')
                self.assertEqual(hashlib.sha256(manifest).hexdigest(),
                                 (root / 'out/game-bundle.id').read_text().strip())
                entries = json.loads(manifest)['files']
                self.assertEqual({e['path'] for e in entries},
                                 {'content-packs/a/assets/a.png', 'content-packs/mixed/assets/a.png', 'scripts/base/test.lua'})
                for entry in entries:
                    payload = archive.read('blobs/' + entry['sha256'])
                    self.assertEqual(len(payload), entry['bytes'])
                    self.assertEqual(hashlib.sha256(payload).hexdigest(), entry['sha256'])
                self.assertEqual(len(archive.namelist()), 3)


if __name__ == '__main__':
    unittest.main()
