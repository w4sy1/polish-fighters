"""Report real translation coverage; missing dictionaries never count as translated."""
import argparse
import json
import re
from pathlib import Path
from lupa.luajit21 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
PLANNED = ('polish', 'english', 'japanese', 'german', 'french', 'russian', 'spanish', 'korean', 'italian', 'chinese')


def check():
    lua = LuaRuntime(unpack_returned_tuples=True)
    folder = ROOT / 'engine/scripts/base/i18n'
    tables = {}
    for name in PLANNED:
        source = folder / (name + '.lua')
        if source.is_file():
            tables[name] = dict(lua.execute(source.read_text(encoding='utf-8')))
    # Existing mature dictionaries define the current reference vocabulary.
    reference = set().union(*(set(table) for table in tables.values()))
    report = {'scope': 'Dictionary keys only; does not prove every dynamic UI string or glyph is translated',
              'reference_keys': len(reference), 'languages': {}, 'format_errors': []}
    for name in PLANNED:
        if name not in tables:
            report['languages'][name] = {'implemented': False, 'complete': False}
            continue
        table = tables[name]
        missing = sorted(reference - table.keys())
        for key, value in table.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError('Dictionary must contain string keys and values: ' + name)
            if value and re.findall(r'%(?:s|d)', key) != re.findall(r'%(?:s|d)', value):
                report['format_errors'].append({'language': name, 'key': key})
        report['languages'][name] = {'implemented': True, 'complete': not missing,
                                    'entries': len(table), 'missing': missing}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = check()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for name, value in result['languages'].items():
        print(name, value.get('entries', 0), 'entries;', 'complete' if value['complete'] else 'incomplete')
    print('Format errors:', len(result['format_errors']))
    raise SystemExit(bool(result['format_errors']))
