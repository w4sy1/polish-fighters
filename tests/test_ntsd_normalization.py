import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from normalize_ntsd_vc80 import normalize
from import_legacy import encode,decode

class NormalizeTest(unittest.TestCase):
    def test_only_overflow_fields_and_preserve_header(self):
        text='name: Nine9999999999\r\nx: -2147483648 y: 2147483647\r\nw: 9999999999 next: 999\r\n'
        result,proof=normalize(text,{'9999999999':1410065407})
        self.assertEqual(result,text.replace('w: 9999999999','w: 1410065407'))
        self.assertEqual(len(proof),1)
        self.assertEqual(proof[0]['field'],'w')
        header=bytes(range(123))
        raw=encode(result,header)
        self.assertEqual(raw[:123],header)
        self.assertEqual(decode(raw),result)
    def test_no_silent_fallback(self):
        with self.assertRaises(KeyError):normalize('x: 9999999999',{})
        with self.assertRaises(ValueError):normalize('x: 9999999999',{'9999999999':2147483648})
