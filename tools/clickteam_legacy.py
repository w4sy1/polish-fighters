"""Bounded static reader for old Clickteam compression; never executes input.

Format reference: ScummVM common/compression/gzio.cpp (Clickteam mode).
This independent implementation uses canonical Huffman codes and RFC1951 tables.
"""
import struct
import hashlib
import json
import argparse
from pathlib import Path
from import_legacy import canonical


class Bits:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def read(self, count):
        if self.pos + count > len(self.data) * 8:
            raise ValueError('Truncated compressed stream')
        start = self.pos // 8
        shift = self.pos % 8
        value = int.from_bytes(self.data[start:(self.pos+count+7)//8], 'little')
        self.pos += count
        return (value >> shift) & ((1 << count)-1)


def tree(lengths):
    counts = [lengths.count(i) for i in range(16)]
    counts[0] = 0
    codes, code, result = {}, 0, {}
    for size in range(1, 16):
        code = (code + counts[size-1]) << 1
        if code + counts[size] > 1 << size:
            raise ValueError('Oversubscribed Huffman tree')
        codes[size] = code
    for symbol, size in enumerate(lengths):
        if size:
            result[size, codes[size]] = symbol
            codes[size] += 1
    return result


def symbol(bits, table):
    code = 0
    for size in range(1, 16):
        code = (code << 1) | bits.read(1)
        if (size, code) in table:
            return table[size, code]
    raise ValueError('Invalid Huffman symbol')


LENGTH = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258]
LEXTRA = [0]*8 + [1]*4 + [2]*4 + [3]*4 + [4]*4 + [5]*4 + [0]
DIST = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577]
DEXTRA = [0]*4 + [n for n in range(1,14) for _ in range(2)]


def inflate(data, expected):
    if not 0 <= expected <= 64*1024*1024:
        raise ValueError('Output limit')
    bits, out = Bits(data), bytearray()
    final = False
    while not final:
        kind, final = bits.read(3), bits.read(1)
        if kind == 7:
            bits.pos = (bits.pos+7)//8*8
            count = bits.read(16)
            if len(out)+count > expected:
                raise ValueError('Output exceeds declared size')
            for _ in range(count):
                out.append(bits.read(8))
            continue
        if kind == 5:
            literals = tree([8]*144+[9]*112+[7]*24+[8]*8)
            distances = tree([5]*32)
        elif kind == 6:
            nl, nd, nc = bits.read(5)+257, bits.read(5)+1, bits.read(4)+4
            if nl > 286 or nd > 30:
                raise ValueError('Invalid code counts')
            order = [18,17,16]+list(range(16))
            lengths = [0]*19
            for i in range(nc):
                lengths[order[i]] = bits.read(3)
            codes, lengths = tree(lengths), []
            while len(lengths) < nl+nd:
                value = symbol(bits, codes)
                if value < 16:
                    lengths.append(value)
                    continue
                if value == 16:
                    if not lengths:
                        raise ValueError('Repeat without previous code')
                    count, value = bits.read(2)+3, lengths[-1]
                elif value == 17:
                    count, value = bits.read(3)+3, 0
                else:
                    count, value = bits.read(7)+11, 0
                if len(lengths)+count > nl+nd:
                    raise ValueError('Code length overflow')
                lengths.extend([value]*count)
            if lengths[256] == 0:
                raise ValueError('Missing end code')
            literals, distances = tree(lengths[:nl]), tree(lengths[nl:])
        else:
            raise ValueError('Unknown Clickteam block type')
        while True:
            value = symbol(bits, literals)
            if value == 256:
                break
            if value < 256:
                if len(out) >= expected:
                    raise ValueError('Output exceeds declared size')
                out.append(value)
                continue
            if value > 285:
                raise ValueError('Invalid length')
            count = LENGTH[value-257]+bits.read(LEXTRA[value-257])
            distance = symbol(bits, distances)
            if distance >= 30:
                raise ValueError('Invalid distance')
            distance = DIST[distance]+bits.read(DEXTRA[distance])
            if distance > len(out) or len(out)+count > expected:
                raise ValueError('Invalid back reference or output size')
            for _ in range(count):
                out.append(out[-distance])
    if len(out) != expected:
        raise ValueError('Output size mismatch')
    return bytes(out)


def checksum(data):
    value = 0
    end = len(data)//4*4
    for (word,) in struct.iter_unpack('<I', data[:end]):
        value = (word + (value >> 31) + (value << 1)) & 0xffffffff
    for byte in data[end:]:
        value = (byte + (value >> 31) + (value << 1)) & 0xffffffff
    return value


def recover(source, destination):
    raw = Path(source).read_bytes()
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('Destination exists')
    # Inspected legacy stub layout; no speculative archive scanning.
    if raw[:2] != b'MZ' or raw[77824:77828] != bytes.fromhex('39120100'):
        raise ValueError('Unrecognized legacy installer')
    cursor, table, payload = 77824, None, None
    while cursor+8 <= len(raw):
        kind, flags, size = struct.unpack_from('<HHI', raw, cursor)
        start = cursor+8
        if size > len(raw)-start:
            raise ValueError('Truncated installer block')
        if kind == 0x7f7f:
            if start+4+size != len(raw) or int.from_bytes(raw[start:start+4], 'little') != size:
                raise ValueError('Invalid payload length')
            payload = raw[start+4:start+4+size]
            break
        if kind == 0x123a:
            if flags != 1 or size < 4:
                raise ValueError('Unsupported file table')
            table = inflate(raw[start+4:start+size], int.from_bytes(raw[start:start+4], 'little'))
        cursor = start+size
    if table is None or payload is None:
        raise ValueError('Missing file table or payload')
    count = int.from_bytes(table[:4], 'little')
    if count > 10000:
        raise ValueError('File count limit')
    cursor, total, names, items = 4, 0, set(), []
    for _ in range(count):
        if cursor+36 > len(table):
            raise ValueError('Truncated file record')
        size, kind = struct.unpack_from('<IH', table, cursor)
        if size < 36 or size > len(table)-cursor or kind != 0:
            raise ValueError('Unsupported file record')
        record = table[cursor:cursor+size]
        offset, compressed, expected, crc = struct.unpack_from('<IIII', record, 6)
        flags = int.from_bytes(record[22:24], 'little')
        string_offset = 36+(18 if flags & 6 else 0)+(24 if flags & 8 else 0)
        name = canonical(record[string_offset:].split(b'\0',1)[0].decode('latin1'))
        if name in names or not name or compressed > len(payload)-offset:
            raise ValueError('Invalid resource record: '+name)
        names.add(name)
        total += expected
        if total > 2*1024*1024*1024 or expected > 64*1024*1024:
            raise ValueError('Archive output limit')
        items.append((name, offset, compressed, expected, crc))
        cursor += size
    if cursor != len(table):
        raise ValueError('Trailing file table bytes')
    report = {'source_sha256':hashlib.sha256(raw).hexdigest(), 'files':[], 'skipped':[],
              'executed_input':False, 'checksum_mode':'common XOR inferred from first resource; checked across all resources'}
    destination.mkdir(parents=True)
    crc_xor = None
    for name, offset, compressed, expected, crc in items:
        data = inflate(payload[offset:offset+compressed], expected)
        actual = checksum(data)
        # Clickteam's generated uninstaller has no stored checksum.
        if not (crc == 0 and name == 'uninstal.exe'):
            if crc_xor is None:
                crc_xor = actual ^ crc
            if actual ^ crc != crc_xor:
                raise ValueError('Resource checksum mismatch: '+name)
        if Path(name).suffix not in {'.dat','.txt','.bmp','.png','.wav','.mp3','.wma','.ogg'}:
            report['skipped'].append(name)
            continue
        output = destination/name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        report['files'].append({'path':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    report['crc_xor'] = crc_xor
    (destination/'RECOVERY.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('destination')
    args = parser.parse_args()
    result = recover(args.source, args.destination)
    print('Recovered', len(result['files']), 'data files; skipped', len(result['skipped']))
