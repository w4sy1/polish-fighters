"""Reject stale native Android libraries before packaging changed game scripts."""
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def signature(engine):
    paths = set((engine / 'src').rglob('*.cpp')) | set((engine / 'src').rglob('*.mm'))
    paths |= set((engine / 'src').rglob('*.hpp')) | set((engine / 'include').rglob('*.hpp'))
    identity = ''
    for path in sorted(paths, key=lambda p: p.relative_to(engine).as_posix()):
        data = path.read_bytes().replace(b'\r\n', b'\n')
        identity += f'{path.relative_to(engine).as_posix()}:{hashlib.sha256(data).hexdigest()}\n'
    return hashlib.sha256(identity.encode()).hexdigest()


def verify(engine, binary):
    expected = signature(engine)
    if expected.encode() not in binary.read_bytes():
        raise ValueError(f'Stara biblioteka silnika: {binary}. Przebuduj kod natywny; nie używaj SkipNative.')
    return expected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binaries', nargs='+', type=Path)
    args = parser.parse_args()
    for binary in args.binaries:
        print(binary, verify(ROOT / 'engine', binary))
