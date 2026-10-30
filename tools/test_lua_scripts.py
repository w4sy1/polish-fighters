"""Run LuaJIT script tests using the prebuilt lupa wheel, without building the game."""
from pathlib import Path
import argparse
from lupa.luajit21 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]


def runtime():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().arg = lua.table_from([str(ROOT).replace('\\', '/')])
    lua.execute('package.path = ... .. "/engine/scripts/?.lua;" .. package.path', str(ROOT).replace('\\', '/'))
    return lua


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tests', nargs='*')
    args = parser.parse_args()
    scripts = sorted((ROOT / 'engine/scripts').rglob('*.lua'))
    scripts += sorted((ROOT / 'content-packs').glob('*/*.lua'))
    lua = runtime()
    for path in scripts:
        lua.execute('assert(loadfile(...))', str(path))
    print('PASS syntax:', len(scripts), 'files', flush=True)
    selected = [ROOT / name for name in args.tests] if args.tests else sorted((ROOT / 'tests').glob('*_test.lua'))
    for path in selected:
        lua = runtime()
        lua.execute(path.read_text(encoding='utf-8'))
        print('PASS', path.name, flush=True)
