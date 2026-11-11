"""Add Remonoko and his temporary mech without rewriting the other fighters.

Run after build_polish_originals.py; optionally regenerate mixed-all afterwards.
The generated atlas is preserved verbatim and sampled through explicit rectangles.
"""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image
from build_polish_originals import ROOT, PACK, character
from import_legacy import decode, encode
from read_pinned_lf2 import read_resource

IDS = (414, 415, 427, 428, 429)


def append_catalog(path, lines):
    text = path.read_text(encoding='latin1')
    text = re.sub(r'^id:\s*(?:414|415|427|428|429)\s+type:[^\n]*\n', '', text, flags=re.M)
    path.write_text(text.replace('<object_end>', ''.join(lines) + '<object_end>', 1), encoding='latin1')


def build():
    raw = read_resource(ROOT.parent / 'downloads/LF2_v2.0a.exe', 'data/deep.dat')
    atlas = PACK / 'art/r.png'
    with Image.open(atlas) as image:
        assert image.mode == 'RGBA' and image.size == (1254, 1254)
        cuts = [0, 160, 318, 478, 633, 790, 949, 1108, 1254]
        rectangles = []
        for row in range(8):
            for col in range(8):
                x, right = round(col * image.width / 8), round((col + 1) * image.width / 8)
                rectangles.append([x, cuts[row], right - x, cuts[row + 1] - cuts[row]])
        layout = json.loads((PACK / 'layout.json').read_text())
        for key in ('r', 'm'):
            rects = rectangles if key == 'r' else [rectangles[52 + n % 4] for n in range(64)]
            padding = []
            for x, y, w, h in rects:
                bounds = image.getchannel('A').crop((x, y, x+w, y+h)).point(lambda a: 255 if a >= 64 else 0).getbbox()
                assert bounds, (key, x, y)
                padding.append(h - bounds[3])
            layout[key] = dict(width=1254, height=1254, rectangles=rects,
                               portrait=[42, 23, 77, 77], bottom_padding=padding,
                               scale=(94 if key == 'r' else 112) / (1254 / 8))
    (PACK / 'layout.json').write_text(json.dumps(layout, indent=2) + '\n')
    lua = ['return {']
    for key, info in layout.items():
        rects = ','.join('{' + ','.join(map(str, rect)) + '}' for rect in info['rectangles'])
        lua.append(f'{key}={{scale={info["scale"]},portrait={{{",".join(map(str,info["portrait"]))}}},'
                   f'bottom_padding={{{",".join(map(str,info["bottom_padding"]))}}},rectangles={{{rects}}}}},')
    (PACK / 'layout.lua').write_text('\n'.join(lua) + '\n}\n')
    manifest = (PACK / 'package.manifest').read_text().splitlines()
    manifest = [line for line in manifest if not line.startswith('asset=mods/polish-originals/r')
                and not line.startswith('asset=mods/polish-originals/m')
                and not re.match(r'asset=mods/polish-originals/42[789]\.dat', line)]
    for entry in ('module=remonoko|remonoko.lua', 'extend=base/game/combat|remonoko_combat.lua'):
        if entry not in manifest:
            manifest.append(entry)
    rows = []
    for id_, key, name in ((414, 'r', 'Remonoko'), (415, 'm', 'Kamienny_Mech')):
        text = decode(character(raw, 's', name)).replace('mods/polish-originals/s', 'mods/polish-originals/' + key)
        text = re.sub(r'^\s*sound:\s*\S+\s*$', '', text, flags=re.M)
        text = re.sub(r'running_speed [\d.]+', 'running_speed ' + ('7.0' if key == 'm' else '12.0'), text)
        poses = {300: 18, 301: 19, 310: 58, 311: 59, 320: 22, 321: 21,
                 330: 60, 331: 56, 340: 46, 341: 47, 350: 56, 351: 57, 360: 52, 361: 53}
        costs = {300: 55, 310: 100, 320: 35, 330: 90, 340: 65, 350: 70, 360: 200}
        def frame(match):
            n, body = int(match[1]), match[2]
            label = body.split()[0]
            pose = None
            if 'walking' in label: pose = 8 + n % 4
            elif 'running' in label: pose = 12 + n % 4
            elif 'lying' in label: pose = 36 + n % 4
            elif 'fall' in label: pose = 32 + n % 4
            elif 'defend' in label: pose = 24 + n % 2
            elif 'injured' in label or 'ice' in label or 'fire' in label: pose = 26 + n % 2
            elif 'rowing' in label: pose = 40 + n % 4
            elif 'dash' in label: pose = 44 + n % 4
            elif 'jump_attack' in label: pose = 48 + n % 4
            elif 'jump' in label or 'crouch' in label: pose = 29 + n % 3
            elif 'punch' in label or 'attack' in label: pose = 16 + n % 8
            if 60 <= n <= 64: pose = 16 + (n - 60) % 4
            elif 65 <= n <= 69: pose = 20 + (n - 65) % 4
            elif 70 <= n <= 74: pose = 56 + (n - 70) % 2
            if pose is not None:
                body = re.sub(r'pic:\s*\d+', 'pic: ' + str(pose), body, count=1)
            if n in poses:
                body = re.sub(r'pic:\s*\d+', 'pic: ' + str(poses[n]), body, count=1)
            if n in costs:
                body = re.sub(r'mp:\s*\d+', 'mp: ' + str(costs[n]), body)
            return f'<frame> {n} {body}<frame_end>'
        text = re.sub(r'<frame>\s*(\d+)\s+(.*?)<frame_end>', frame, text, flags=re.S)
        (PACK / f'assets/{key}.dat').write_bytes(encode(text, raw))
        rows.append(f'id: {id_} type: 0 file: mods/polish-originals/{key}.dat\n')
        manifest += [f'asset=mods/polish-originals/{key}.dat|assets/{key}.dat']
        for suffix in ('', '_h', '_s'):
            manifest.append(f'asset=mods/polish-originals/{key}{suffix}.png|art/r.png')
    for id_, pic, damage, width in ((427, 61, 18, 28), (428, 62, 70, 70), (429, 63, 0, 28)):
        text = f'''<bmp_begin>
name: rn_effect_{id_}
file(0-63): mods/polish-originals/r.png w: 79 h: 79 row: 8 col: 8
<bmp_end>
'''
        for n in (0, 10, 20, 30, 40):
            text += f'''<frame> {n} rn_effect
pic: {pic} state: {3000 if n == 0 else 3005} wait: {1 if n == 0 else 0} next: {0 if n == 0 else 1000} dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 40 hit_a: 0 hit_d: 10 hit_j: 0
'''
            if n == 0 and damage:
                text += f'''itr:
kind: 0 x: {40-width//2} y: 20 w: {width} h: 40 dvx: 9 dvy: -4 fall: 60 vrest: 18 bdefend: 35 injury: {damage}
itr_end:
bdy:
kind: 0 x: 24 y: 24 w: 32 h: 32
bdy_end:
'''
            text += '<frame_end>\n'
        (PACK / f'assets/{id_}.dat').write_bytes(encode(text, raw))
        rows.append(f'id: {id_} type: 3 file: mods/polish-originals/{id_}.dat\n')
        manifest.append(f'asset=mods/polish-originals/{id_}.dat|assets/{id_}.dat')
    append_catalog(PACK / 'assets/catalog.txt', rows)
    mixed = ROOT / 'content-packs/mixed-all/assets/catalog.txt'
    if mixed.is_file():
        append_catalog(mixed, rows)
        report_path = mixed.parents[1] / 'build-report.json'
        if report_path.is_file():
            report = json.loads(report_path.read_text())
            ids = re.findall(r'^id:\s*(\d+)\s+type:', mixed.read_text(encoding='latin1'), re.M)
            report['objects'], report['unique_ids'] = len(ids), len(set(ids))
            report['remonoko_ids'] = list(IDS)
            report_path.write_text(json.dumps(report, indent=2) + '\n')
    (PACK / 'package.manifest').write_text('\n'.join(manifest) + '\n')
    hashes = json.loads((PACK / 'asset-checksums.json').read_text())
    for file in [atlas] + [PACK / ('assets/' + name + '.dat') for name in ('r', 'm', '427', '428', '429')]:
        hashes[file.relative_to(PACK).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    hashes['assets/catalog.txt'] = hashlib.sha256((PACK / 'assets/catalog.txt').read_bytes()).hexdigest()
    (PACK / 'asset-checksums.json').write_text(json.dumps(hashes, indent=2) + '\n')
    report_path = PACK / 'import-report.json'
    report = json.loads(report_path.read_text())
    report['fighters'] = [f for f in report['fighters'] if f['id'] not in (414, 415)]
    report['fighters'] += [dict(id=id_, name=name, path=f'mods/polish-originals/{key}.dat', hidden=id_==415)
                           for id_, key, name in ((414, 'r', 'Remonoko'), (415, 'm', 'Kamienny Mech'))]
    report['helpers'] = sorted(set(report['helpers'] + [427, 428, 429]))
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print('Remonoko 414, hidden mech 415, effects 427-429; existing fighter DATs preserved')
    if (PACK/'art/m.png').is_file() and (PACK/'art/e.png').is_file():
        from build_hero_update import build as add_hero_update
        add_hero_update()


if __name__ == '__main__':
    build()
