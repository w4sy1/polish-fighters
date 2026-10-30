import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from recover_kate_oid99 import recover
from import_legacy import encode,decode

class KateRecoveryTests(unittest.TestCase):
    def fixture(self,folder):
        root=Path(folder);source=root/'reference';pack=root/'pack'
        (source/'data').mkdir(parents=True);(pack/'assets').mkdir(parents=True)
        (source/'data/data.txt').write_text('id: 99 type: 0 file: data/Pkmnt.dat\n')
        (source/'data/Pkmnt.dat').write_bytes(encode('<bmp_begin>\nname: Helper\n<bmp_end>\n<frame> 390 start\npic: 0\n<frame_end>\n<frame> 392 other\npic: 0\n<frame_end>',bytes(range(123))))
        (pack/'assets/catalog.txt').write_text('<object>\nid: 1 type: 0 file: old.dat\n<object_end>\n')
        (pack/'package.manifest').write_text('asset=mods/kate/catalog.txt|assets/catalog.txt\n')
        return source,pack

    def test_additive_short_paths_and_repeated_import_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source,pack=self.fixture(folder);original=(source/'data/Pkmnt.dat').read_bytes()
            proof=recover(source,pack)
            self.assertEqual(proof['actions'],[390,392])
            self.assertEqual((source/'data/Pkmnt.dat').read_bytes(),original)
            catalog=(pack/'assets/catalog.txt').read_text()
            self.assertLess(catalog.index('id: 1'),catalog.index('id: 99'))
            self.assertIn('mods/kate/r99/0000.dat',catalog)
            self.assertEqual((pack/'assets/r99/0000.dat').read_bytes()[:123],original[:123])
            with self.assertRaises(ValueError):recover(source,pack)

    def test_missing_dependency_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            source,pack=self.fixture(folder);before=(pack/'package.manifest').read_bytes()
            p=source/'data/Pkmnt.dat';raw=p.read_bytes();p.write_bytes(encode(decode(raw)+'\nopoint: kind: 1 oid: 777 opoint_end:',raw))
            with self.assertRaises(ValueError):recover(source,pack)
            self.assertEqual((pack/'package.manifest').read_bytes(),before)
            self.assertFalse((pack/'assets/r99').exists())
