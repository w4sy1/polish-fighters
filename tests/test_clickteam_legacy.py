import hashlib
import sys
import tempfile
import unittest
import zlib
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from clickteam_legacy import inflate, recover, tree, checksum


def stored(data):
    return b'\x0f'+struct.pack('<H',len(data))+data


def installer(entries):
    records, payload = [], bytearray()
    for name, data in entries:
        encoded = stored(data)
        record = bytearray(36)+name.encode()+b'\0'
        struct.pack_into('<IHIIII',record,0,len(record),0,len(payload),len(encoded),len(data),checksum(data)^0x12345678)
        records.append(record)
        payload.extend(encoded)
    table = struct.pack('<I',len(entries))+b''.join(records)
    metadata = struct.pack('<I',len(table))+stored(table)
    stub = b'MZ'+bytes(77822)+struct.pack('<HHI',0x1239,1,0)
    return stub+struct.pack('<HHI',0x123a,1,len(metadata))+metadata+struct.pack('<HHII',0x7f7f,0,len(payload),len(payload))+payload


class LegacyCompressionTests(unittest.TestCase):
    def test_extracts_data_and_excludes_programs(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'input.exe', Path(folder)/'output'
            source.write_bytes(installer([('data/test.dat',b'test-data'),('game.exe',b'MZ-do-not-export')]))
            report = recover(source,target)
            self.assertEqual((target/'data/test.dat').read_bytes(),b'test-data')
            self.assertFalse((target/'game.exe').exists())
            self.assertEqual(report['skipped'],['game.exe'])
            self.assertTrue((target/'RECOVERY.json').exists())
            with self.assertRaises(ValueError):
                recover(source,target)

    def test_traversal_and_duplicate_paths_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'input.exe', Path(folder)/'output'
            for entries in [[('../escape.dat',b'x')],[('data/a.dat',b'a'),('DATA/A.DAT',b'b')]]:
                source.write_bytes(installer(entries))
                with self.assertRaises(ValueError):
                    recover(source,target)
                self.assertFalse(target.exists())

    def test_fixed_huffman_back_references(self):
        expected = b'fixed-Huffman-fixture-'*200
        compressor = zlib.compressobj(level=9, wbits=-15, strategy=zlib.Z_FIXED)
        raw = compressor.compress(expected)+compressor.flush()
        self.assertEqual(raw[0] & 7, 3)  # RFC1951 final fixed block.
        # Insert the extra Clickteam header bit, retaining the Huffman payload.
        bits = [1, 0, 1, 1]+[(raw[i//8] >> (i%8)) & 1 for i in range(3,len(raw)*8)]
        encoded = bytearray((len(bits)+7)//8)
        for i, bit in enumerate(bits):
            encoded[i//8] |= bit << (i%8)
        self.assertEqual(inflate(bytes(encoded), len(expected)), expected)

    def test_real_dynamic_metadata(self):
        compressed = (Path(__file__).parent/'fixtures/clickteam-metadata.bin').read_bytes()
        decoded = inflate(compressed, 2508)
        self.assertEqual(hashlib.sha256(decoded).hexdigest(),
                         '8d745e7001323a93644438ebc8c1452464eb955973723e8bb951b16186799900')
        for cut in (0, 1, 50, len(compressed)-1):
            with self.assertRaises(ValueError):
                inflate(compressed[:cut], 2508)
        with self.assertRaises(ValueError):
            inflate(compressed, 2507)

    def test_stored_and_output_bounds(self):
        # Final stored block: BTYPE=7, FINAL=1, byte alignment, LEN, bytes.
        self.assertEqual(inflate(b'\x0f\x03\x00abc', 3), b'abc')
        for size in (0, 2, 4, 64*1024*1024+1):
            with self.assertRaises(ValueError):
                inflate(b'\x0f\x03\x00abc', size)

    def test_invalid_codes_and_unknown_installer(self):
        with self.assertRaises(ValueError):
            tree([1, 1, 1])
        with self.assertRaises(ValueError):
            inflate(b'\x00', 0)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'input.exe'
            source.write_bytes(b'MZ-invalid')
            destination = Path(folder)/'output'
            with self.assertRaises(ValueError):
                recover(source, destination)
            self.assertFalse(destination.exists())
