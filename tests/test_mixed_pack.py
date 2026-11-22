import sys
import unittest
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_mixed_pack import build_selection, remap_text

class MixedRemapTest(unittest.TestCase):
    def test_spawn_and_transform_are_scoped_and_resources_rewritten(self):
        original='oid: 12 state: 3012 sound: mods/dbz/a/123.wav\nnext: 12 hit_a: 12 pic: 12'
        missing=set()
        result=remap_text(original,{12:1200},{'mods/dbz/a/123.wav':'mods/mixed-all/dbz/a/123.wav'},missing)
        self.assertEqual(result,'oid: 1200 state: 301200 sound: mods/mixed-all/dbz/a/123.wav\nnext: 12 hit_a: 12 pic: 12')
        self.assertFalse(missing)
        self.assertIn('oid: 12',original)

    def test_absent_source_target_cannot_fall_through_to_base_object(self):
        missing=set()
        result=remap_text('oid: 284 state: 3151 oid: 0',{}, {},missing)
        self.assertEqual(result,'oid: 900284 state: 1200151 oid: 0')
        self.assertEqual(missing,{284,151})

    def test_regular_states_and_frame_numbers_are_not_object_ids(self):
        self.assertEqual(remap_text('state: 3 next: 3000 action: 3000',{}, {},set()),
                         'state: 3 next: 3000 action: 3000')


class MixedSelectionTest(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.packs = self.root / 'content-packs'
        for pack in ('polish-originals', 'kate', 'ntsd'):
            self.write_package(pack)

    def write_package(self, pack, duplicate=False):
        path = self.packs / pack
        path.mkdir(parents=True, exist_ok=True)
        prefix = f'mods/{pack}'
        (path / 'catalog.lua').write_text(f'base.source_path = "{prefix}/catalog.txt"')
        (path / 'package.manifest').write_text(
            f'asset={prefix}/catalog.txt|catalog.txt\nasset={prefix}/fighter.txt|fighter.txt\n'
        )
        record = f'id: 12 type: 0 file: {prefix}/fighter.txt\n'
        (path / 'catalog.txt').write_text(
            '<object>\n' + record * (2 if duplicate else 1) +
            '<object_end>\n<background>\n<background_end>\n'
        )
        (path / 'fighter.txt').write_text('oid: 12 state: 3012')

    def test_selection_is_order_independent_and_source_ids_do_not_collide(self):
        a, b = self.root / 'a', self.root / 'b'
        result = build_selection(['ntsd', 'kate'], self.packs, a)
        build_selection(['kate', 'ntsd'], self.packs, b)
        self.assertEqual(result['objects'], result['unique_ids'])
        self.assertEqual(result['objects'], 3)
        for file in a.rglob('*'):
            if file.is_file():
                self.assertEqual(file.read_bytes(), (b / file.relative_to(a)).read_bytes())
        catalog = (a / 'assets/catalog.txt').read_text()
        self.assertIn('id: 4000 type: 0', catalog)
        self.assertIn('id: 6000 type: 0', catalog)
        self.assertIn('oid: 4000 state: 304000', (a / 'assets/4/00001.txt').read_text())
        self.assertIn('oid: 6000 state: 306000', (a / 'assets/6/00001.txt').read_text())
        self.assertIn("base.profile_id='mod-mix-kate-ntsd'", (a / 'catalog.lua').read_text())

    def test_invalid_selection_never_leaves_a_generated_package(self):
        output = self.root / 'failed'
        with self.assertRaisesRegex(ValueError, 'No mixed-mode adapter'):
            build_selection(['unknown'], self.packs, output)
        self.write_package('kate', duplicate=True)
        with self.assertRaisesRegex(ValueError, 'kate: duplicate'):
            build_selection(['kate'], self.packs, output)
        self.assertFalse(output.exists())
