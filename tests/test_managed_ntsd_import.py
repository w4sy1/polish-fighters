import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from import_legacy import decode, encode
from mod_library import Library


class ManagedNtsdImportTest(unittest.TestCase):
    def test_normalizes_only_catalog_and_dat_fingerprint_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            header = b'x' * 123
            catalog = (b'<object>\r\nid: 1 type: 0 file: data/hero.dat\r\n<object_end>\r\n'
                       b'<background>\r\n<background_end>\r\n')
            hero = encode('<bmp_begin>\nname: Test\nhead: data/head.bmp\n<bmp_end>\n'
                          '<frame> 0 stand\nx: -9999999999\ny: 123\n<frame_end>', header)
            fingerprints = root / 'data/mods'
            fingerprints.mkdir(parents=True)
            (fingerprints / 'ntsd-2.4-2.0a.json').write_text(json.dumps({
                'edition': 'NTSD 2.4_2.0a',
                'source_catalog_sha256': hashlib.sha256(catalog).hexdigest(),
                'source_dat_sha256': {'data/hero.dat': hashlib.sha256(hero).hexdigest()},
            }), encoding='utf-8')
            proof = root / 'content-packs/ntsd'
            proof.mkdir(parents=True)
            (proof / 'vc80-integer-normalization.json').write_text(
                '{"unique_tokens": {"-9999999999": -1410065407}}', encoding='utf-8')
            library = Library(root / 'library')
            cases = [
                ('known', catalog, hero, True),
                ('changed-dat', catalog, b'y' + hero[1:], False),
                ('changed-catalog', catalog + b'\r\n', hero, False),
            ]
            for name, source_catalog, source_hero, matched in cases:
                with self.subTest(name=name):
                    archive = root / f'{name}.zip'
                    with ZipFile(archive, 'w') as bundle:
                        bundle.writestr('data/data.txt', source_catalog)
                        bundle.writestr('data/hero.dat', source_hero)
                        bundle.writestr('data/head.bmp', b'image fixture')
                        bundle.writestr('data/stage.dat', encode('<stage> id: 0\n<stage_end>', header))
                    with patch('normalize_ntsd_vc80.ROOT', root):
                        installed = library.install(archive)['package']
                    package = library.package_path(installed['id'])
                    library.verify(installed['id'])
                    report = json.loads((package / 'import-report.json').read_text(encoding='utf-8'))
                    self.assertFalse(report['active'])
                    self.assertEqual('dat_normalization' in report, matched)
                    self.assertEqual(library.read()['profiles']['default']['mods'], [])
                    actors = [path.read_bytes() for path in (package / 'assets/a').glob('*.dat')]
                    raw = next(data for data in actors if 'name: Test' in decode(data))
                    self.assertEqual(raw[:123], source_hero[:123])
                    actor = decode(raw)
                    self.assertRegex(actor, r'head: ./a/[0-9]{6}\.bmp')
                    self.assertIn('y: 123', actor)
                    self.assertIn('x: ' + ('-1410065407' if matched else '-9999999999'), actor)
                    if matched:
                        normalization = report['dat_normalization']
                        self.assertEqual(normalization['method'], 'VC80 x86 sscanf %d')
                        self.assertEqual(normalization['fields_changed'], 1)
                        self.assertEqual(normalization['files'], [{'path': 'data/hero.dat', 'fields_changed': 1}])
