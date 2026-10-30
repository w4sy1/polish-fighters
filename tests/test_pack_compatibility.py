import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_pack_compatibility import cells


class CellTests(unittest.TestCase):
    def test_effective_packed_layout_and_empty_sources(self):
        source='file(0-14): packed.bmp w: 42 h: 150 row: 15 col: 1\n<frame> 0 a\npic: 14\n<frame_end>'
        raw,_=cells(source,{'packed.bmp':[630,150]})
        effective,_=cells(source,{'packed.bmp':[630,150]}, {'packed.bmp|42|150|15|1':{'stride':[42,151]}})
        self.assertFalse(raw[0]['fits'])
        self.assertTrue(effective[0]['fits'])
        self.assertEqual(effective[0]['rect'],[588,0,42,150])
        empty,_=cells(source.replace('pic: 14','pic: 5'),{'packed.bmp':[40,10]})
        self.assertTrue(empty[0]['fully_empty'])

    def test_unused_rows_are_not_missing_animation(self):
        text='file(0-139): sheet.bmp w: 79 h: 99 row: 10 col: 14\n<frame> 0 stand\npic: 19\n<frame_end>'
        rows,unmapped=cells(text,{'sheet.bmp':[799,199]})
        self.assertTrue(rows[0]['fits'])
        self.assertEqual(rows[0]['rect'],[720,100,79,99])
        self.assertFalse(unmapped)

    def test_outside_and_unmapped_distinguished(self):
        text='file(0-9): sheet.bmp w: 9 h: 9 row: 2 col: 5\n<frame> 1 a\npic: 4\n<frame_end>\n<frame> 2 b\npic: 20\n<frame_end>'
        rows,unmapped=cells(text,{'sheet.bmp':[19,19]})
        self.assertFalse(rows[0]['fits'])
        self.assertEqual(unmapped,[{'frame':2,'picture':20}])

    def test_cumulative_native_numbering_preserved(self):
        text='file(0-1): a.bmp w: 9 h: 9 row: 2 col: 1\nfile(100-101): b.bmp w: 9 h: 9 row: 2 col: 1\n<frame> 2 b\npic: 2\n<frame_end>'
        rows,_=cells(text,{'a.bmp':[19,9],'b.bmp':[19,9]})
        self.assertEqual(rows[0]['asset'],'b.bmp')
