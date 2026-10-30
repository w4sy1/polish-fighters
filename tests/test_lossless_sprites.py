import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from encode_large_sprites import convert
from import_legacy import encode,decode


class LosslessSpritesTest(unittest.TestCase):
    def test_pixels_original_and_encrypted_reference_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'assets').mkdir()
            bmp=root/'assets/sheet.bmp'
            Image.new('RGB',(64,64),(0,75,123)).save(bmp)
            original=bmp.read_bytes()
            header=bytes(range(123))
            dat=root/'assets/object.dat'
            dat.write_bytes(encode('file(0-0): mods/test/sheet.bmp w: 64 h: 64 row: 1 col: 1',header))
            (root/'package.manifest').write_text('asset=mods/test/sheet.bmp|assets/sheet.bmp\nasset=mods/test/object.dat|assets/object.dat\n')
            evidence=convert(root,1024)
            self.assertEqual(len(evidence),1)
            self.assertEqual(bmp.read_bytes(),original)
            self.assertEqual(dat.read_bytes()[:123],header)
            self.assertIn('mods/test/sheet.png',decode(dat.read_bytes()))
            with Image.open(bmp) as a,Image.open(root/'assets/sheet.png') as b:
                self.assertEqual(a.convert('RGB').tobytes(),b.convert('RGB').tobytes())
                self.assertEqual(evidence[0]['rgb_sha256'],hashlib.sha256(a.convert('RGB').tobytes()).hexdigest())

    def test_asset_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'package.manifest').write_text('asset=escape.bmp|../escape.bmp\n')
            with self.assertRaises(ValueError):convert(root)
