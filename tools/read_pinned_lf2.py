"""Read data from the pinned LF2 archive, using the existing engine's archive format.
No installer instructions or executable code are run.
"""
import bz2
import hashlib
import struct
import zlib
from pathlib import Path

PIN = '540c485547e234b0d09595f54d067aafd7176092c308aca61868f3cbc03030e1'


def unpack(method, data, expected):
    if not 0 <= expected <= 64*1024*1024:
        raise ValueError('Archive output limit')
    if method == 0:
        result = data
    elif method == 1:
        decoder = zlib.decompressobj()
        result = decoder.decompress(data, expected+1)
        if not decoder.eof or decoder.unused_data:
            raise ValueError('Invalid zlib stream')
    elif method == 2:
        decoder = bz2.BZ2Decompressor()
        result = decoder.decompress(data, max_length=expected+1)
        if not decoder.eof or decoder.unused_data:
            raise ValueError('Invalid bzip2 stream')
    else:
        raise ValueError('Unsupported compression')
    if len(result) != expected:
        raise ValueError('Archive size mismatch')
    return result


def read_resource(installer, requested):
    raw = Path(installer).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Unsupported LF2 installer hash')
    u16 = lambda data, offset: struct.unpack_from('<H', data, offset)[0]
    u32 = lambda data, offset: struct.unpack_from('<I', data, offset)[0]
    pe = u32(raw, 60)
    sections = pe+24+u16(raw, pe+20)
    overlay = max(u32(raw, sections+i*40+16)+u32(raw, sections+i*40+20) for i in range(u16(raw, pe+6)))
    if raw[overlay:overlay+6] != b'wwgT)H':
        raise ValueError('Archive signature mismatch')
    cursor = overlay+6
    table = None
    while cursor < len(raw):
        kind, flags, size = struct.unpack_from('<HHI', raw, cursor)
        body = cursor+8
        if kind == 0x7f7f:
            payload = body+4
            break
        if kind == 0x143a:
            table = unpack(raw[body+4], raw[body+5:body+size], u32(raw, body))
        cursor = body+size
    if table is None:
        raise ValueError('Missing archive table')
    cursor = 4
    for _ in range(u32(table, 0)):
        size, kind = struct.unpack_from('<HH', table, cursor)
        record = table[cursor:cursor+size]
        if kind == 0:
            name = record[62:].split(b'\0', 1)[0].decode('latin1').replace('\\', '/').lower()
            if name == requested:
                offset, compressed = u32(record, 6), u32(record, 10)
                expected = u32(record, 18)
                data = raw[payload+offset:payload+offset+compressed]
                return unpack(data[0], data[1:], expected)
        cursor += size
    raise FileNotFoundError(requested)
