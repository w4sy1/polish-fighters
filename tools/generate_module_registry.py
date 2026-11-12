"""Audit real declared assets and generate the packaged menu's module inventory."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def inventory(root=ROOT):
    definitions = (root / 'engine/scripts/polish-fighters/hub.lua').read_text(encoding='utf-8')
    result = {}
    for identifier, pack in re.findall(r'id="([^"]+)",profile="([^"]+)"', definitions):
        if pack == 'lf2-classic':
            installer = root.parent / 'downloads/LF2_v2.0a.exe'
            result[identifier] = dict(pack=pack, assets=1, fighters=None, missing=[] if installer.is_file() else ['LF2_v2.0a.exe'])
            continue
        directory = root / 'content-packs' / pack
        manifest = directory / 'package.manifest'
        missing, assets = [], 0
        if not manifest.is_file():
            missing.append('package.manifest')
        else:
            for line in manifest.read_text(encoding='utf-8').splitlines():
                if not line.startswith('asset='): continue
                relative = line.split('|', 1)[1]
                if Path(relative).is_absolute() or '..' in Path(relative).parts: raise ValueError('Unsafe asset path')
                assets += 1
                if not (directory / relative).is_file(): missing.append(relative)
        report = directory / 'import-report.json'
        fighters = len(json.loads(report.read_text(encoding='utf-8')).get('fighters', [])) if report.is_file() else None
        result[identifier] = dict(pack=pack, assets=assets, fighters=fighters, missing=missing)
    return result

def generate(records):
    lines = ['-- Generated from package manifests; file presence is not proof of complete mechanics.', 'return {']
    for identifier, entry in records.items():
        lines.append(' [%s]={assets=%d,missing=%d,fighters=%s},' %
            (json.dumps(identifier), entry['assets'], len(entry['missing']), entry['fighters'] if entry['fighters'] is not None else 'nil'))
    return '\n'.join(lines + ['}', ''])

if __name__ == '__main__':
    records = inventory()
    target = ROOT / 'engine/scripts/polish-fighters/module_inventory.lua'
    target.write_text(generate(records), encoding='utf-8')
    print(json.dumps(records, ensure_ascii=False, indent=2))
    if any(entry['missing'] for entry in records.values()): raise SystemExit('Missing module assets')
