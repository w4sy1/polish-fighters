import sys
from pathlib import Path
import tempfile
import unittest
import zlib
import bz2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from read_pinned_lf2 import unpack,read_resource


class PinnedArchiveTests(unittest.TestCase):
    def test_compression_and_bounds(self):
        raw=b'fixture'*100
        for method,data in [(0,raw),(1,zlib.compress(raw)),(2,bz2.compress(raw))]:
            self.assertEqual(unpack(method,data,len(raw)),raw)
            with self.assertRaises(ValueError):unpack(method,data,len(raw)-1)
        with self.assertRaises(ValueError):unpack(9,b'',0)

    def test_rejects_unpinned_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'unknown.exe';path.write_bytes(b'MZ-untrusted-fixture')
            with self.assertRaises(ValueError):read_resource(path,'sprite/sys/jack_b.bmp')
