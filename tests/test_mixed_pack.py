import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_mixed_pack import remap_text

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
