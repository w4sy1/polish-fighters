import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from repair_kate_transform import repair


class RepairTests(unittest.TestCase):
    def test_requires_unique_incoming_and_continuation(self):
        source='hit_ja: 350\n<frame>  transform\npic: 0\n<frame_end>\n<frame> 351 transform'
        result=repair(source)
        self.assertEqual(result,source.replace('<frame>  transform','<frame> 350 transform'))
        for text in [source+'\n<frame>  transform',source+'\n<frame> 350 duplicate',
                     source.replace('hit_ja: 350','hit_ja: 349'),source.replace('351 transform','352 transform')]:
            with self.assertRaises(ValueError):repair(text)
