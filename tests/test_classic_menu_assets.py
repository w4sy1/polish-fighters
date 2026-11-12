import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from generate_classic_menu_assets import generate
from generate_module_registry import inventory

class ClassicMenuAssetsTests(unittest.TestCase):
    def test_android_dictionary_and_font_match_shared_source(self):
        self.assertEqual((ROOT/'engine/android/app/src/main/assets/classic-menu.json').read_text(encoding='utf-8'),generate())
        data=json.loads(generate())
        self.assertEqual(set(data['pl']),set(data['en']))
        for letter in 'ĄĆĘŁŃÓŚŹŻ':
            self.assertIn(data['accents'][letter],data['glyphs'])

    def test_missing_assets_are_reported_from_real_manifests(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            hub=root/'engine/scripts/polish-fighters/hub.lua';hub.parent.mkdir(parents=True)
            hub.write_text('{id="test",profile="example"}',encoding='utf-8')
            pack=root/'content-packs/example';pack.mkdir(parents=True)
            (pack/'package.manifest').write_text('asset=mods/example/frame.png|art/frame.png\n',encoding='utf-8')
            result=inventory(root)['test']
            self.assertEqual(result['missing'],['art/frame.png'])
            (pack/'art').mkdir();(pack/'art/frame.png').write_bytes(b'present')
            self.assertEqual(inventory(root)['test']['missing'],[])

    def test_module_paths_cannot_escape_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            hub=root/'engine/scripts/polish-fighters/hub.lua';hub.parent.mkdir(parents=True)
            hub.write_text('{id="test",profile="example"}',encoding='utf-8')
            pack=root/'content-packs/example';pack.mkdir(parents=True)
            (pack/'package.manifest').write_text('asset=mods/example/frame.png|../private.png\n',encoding='utf-8')
            with self.assertRaises(ValueError):inventory(root)
