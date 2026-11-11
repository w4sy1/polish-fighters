"""Build additive hero effects and the dedicated animated mech from untouched PNGs."""
import hashlib
import json
import re
from PIL import Image
from build_polish_originals import ROOT, PACK, character
from import_legacy import decode, encode
from read_pinned_lf2 import read_resource

HELPERS = range(430, 440)


def atlas_layout(path, target, effect=False):
    with Image.open(path) as image:
        assert image.mode == 'RGBA'
        width, height = image.size
        alpha = image.getchannel('A')
        rows = [sum(a >= 96 for a in alpha.crop((0, y, width, y+1)).getdata()) for y in range(height)]
        cuts = [0]
        for n in range(1, 8):
            expected = round(n*height/8)
            cut = min(range(expected-24, expected+25), key=lambda y: (sum(rows[y-1:y+2]), abs(y-expected)))
            cuts.append(cut)
        cuts.append(height)
        rectangles, padding = [], []
        for row in range(8):
            for col in range(8):
                x, right = round(col*width/8), round((col+1)*width/8)
                y, bottom = cuts[row], cuts[row+1]
                rect = [x, y, right-x, bottom-y]
                bounds = alpha.crop((x, y, right, bottom)).point(lambda a: 255 if a >= 64 else 0).getbbox()
                assert bounds, (path, row, col)
                rectangles.append(rect);padding.append(bottom-y-bounds[3])
    return dict(width=width, height=height, rectangles=rectangles, bottom_padding=padding,
                portrait=[70, 28, 60, 60], scale=target/(width/8), effect=effect, rows=cuts)


def write_layout(layout):
    (PACK/'layout.json').write_text(json.dumps(layout, indent=2)+'\n')
    lines=['return {']
    for key, info in layout.items():
        rects=','.join('{'+','.join(map(str,r))+'}' for r in info['rectangles'])
        extra=',effect=true' if info.get('effect') else ''
        if info.get('scales'): extra+=',scales={'+','.join(map(str,info['scales']))+'}'
        lines.append(f'{key}={{scale={info["scale"]},portrait={{{",".join(map(str,info["portrait"]))}}},'
                     f'bottom_padding={{{",".join(map(str,info["bottom_padding"]))}}},rectangles={{{rects}}}{extra}}},')
    (PACK/'layout.lua').write_text('\n'.join(lines)+'\n}\n')


def build():
    raw=read_resource(ROOT.parent/'downloads/LF2_v2.0a.exe','data/deep.dat')
    layout=json.loads((PACK/'layout.json').read_text())
    layout['m']=atlas_layout(PACK/'art/m.png',112)
    layout['f']=atlas_layout(PACK/'art/m.png',125,True)
    layout['e']=atlas_layout(PACK/'art/e.png',105,True)
    layout['e']['scales']=[1.05 if 16<=n<24 else layout['e']['scale'] for n in range(64)]
    layout['t']=atlas_layout(PACK/'art/e.png',76)
    layout['t']['portrait']=[12,12,132,132]
    layout['t']['rectangles']=[layout['t']['rectangles'][n%8] for n in range(64)]
    layout['t']['bottom_padding']=[layout['t']['bottom_padding'][n%8] for n in range(64)]
    write_layout(layout)
    for key in ('r','m'):
        path=PACK/f'assets/{key}.dat';text=decode(path.read_bytes())
        text=re.sub(r'walking_speed [\d.]+','walking_speed '+('4.8' if key=='m' else '6.8'),text)
        text=re.sub(r'running_speed [\d.]+','running_speed '+('8.8' if key=='m' else '13.2'),text)
        if key=='m':
            text=re.sub(r'<frame>\s*(?:380|381|390|391)\s+.*?<frame_end>','',text,flags=re.S)
            poses={300:48,301:49,310:26,311:29,320:50,321:51,330:28,331:30,
                   340:54,341:55,350:30,351:31,360:0,361:1}
            def remap(match):
                number, body=int(match[1]),match[2];name=body.split()[0]
                pic=number%4
                if 'walking' in name or 'running' in name: pic=8+number%8
                elif 'lying' in name: pic=46+number%2
                elif 'fall' in name: pic=43+number%5
                elif 'defend' in name: pic=32+number%3
                elif 'injured' in name or 'ice' in name or 'fire' in name: pic=36+number%4
                elif 'rowing' in name: pic=40+number%4
                elif 'dash' in name: pic=48+number%2
                elif 'jump_attack' in name: pic=42+number%2
                elif 'jump' in name or 'crouch' in name: pic=40+number%3
                elif 'punch' in name or 'attack' in name: pic=16+number%8
                if 60<=number<=64: pic=16+(number-60)
                elif 65<=number<=69: pic=19+(number-65)
                elif 70<=number<=74: pic=26+(number-70)
                pic=poses.get(number,pic)
                body=re.sub(r'pic:\s*\d+','pic: '+str(pic),body,count=1)
                if number==360: body=re.sub(r'mp:\s*\d+','mp: 0',body)
                if number in (300,301):
                    body=re.sub(r'\bhit_a:\s*-?\d+','',body)
                    body=body.rstrip()+'\n hit_a: 380\n'
                return f'<frame> {number} {body}<frame_end>'
            text=re.sub(r'<frame>\s*(\d+)\s+(.*?)<frame_end>',remap,text,flags=re.S)
            text=text.rstrip()+'\n'
            for number,pic,cost,next_frame,hit in ((380,52,30,381,390),(381,53,0,999,390),
                                                  (390,28,65,391,0),(391,31,0,999,0)):
                text+=f'''\n<frame> {number} mech_combo
pic: {pic} state: 3 wait: 5 next: {next_frame} dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 79 mp: {cost} hit_a: {hit}
bdy:
kind: 0 x: 15 y: 10 w: 50 h: 69
bdy_end:
<frame_end>
'''
        path.write_bytes(encode(text,raw))
    rows=[]
    specs={430:('f',56,4,22,42),431:('f',58,4,60,78),432:('e',24,8,32,35),
           434:('e',8,8,20,38),435:('e',16,8,40,70),436:('e',32,8,0,0),
           437:('e',56,8,0,0),438:('e',16,8,0,0),439:('f',62,2,0,0)}
    manifest=(PACK/'package.manifest').read_text().splitlines()
    manifest=[x for x in manifest if not re.match(r'asset=mods/polish-originals/43\d\.dat',x)
              and not re.match(r'asset=mods/polish-originals/(?:m|f|e|t)(?:_[hs])?\.png',x)]
    if 'module=heroes|heroes.lua' not in manifest: manifest.append('module=heroes|heroes.lua')
    for key,source in (('m','m'),('f','m'),('e','e'),('t','e')):
        manifest.append(f'asset=mods/polish-originals/{key}.png|art/{source}.png')
        if key in ('m','t'):
            for suffix in ('h','s'): manifest.append(f'asset=mods/polish-originals/{key}_{suffix}.png|art/{source}.png')
    for id_ in HELPERS:
        if id_==433:
            text=decode(character(raw,'b','Sigma_Toaleta')).replace('mods/polish-originals/b','mods/polish-originals/t')
            text=re.sub(r'(walking_speed|running_speed) [\d.]+',r'\1 0.0',text)
            text=re.sub(r'^\s*sound:\s*\S+\s*$','',text,flags=re.M)
            kind=0
        else:
            key,pic,count,damage,width=specs[id_];kind=3
            text=f'<bmp_begin>\nname: hero_effect_{id_}\nfile(0-63): mods/polish-originals/{key}.png w: 79 h: 79 row: 8 col: 8\n<bmp_end>\n'
            for n in range(count):
                text+=f'''<frame> {n} hero_effect
pic: {pic+n} state: 3000 wait: 1 next: {(n+1)%count} dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 40 hit_a: 0 hit_d: 10 hit_j: 0
'''
                if damage:
                    text+=f'''itr:
kind: 0 x: {40-width//2} y: 15 w: {width} h: 50 dvx: 8 dvy: -4 fall: 60 vrest: 15 bdefend: 35 injury: {damage}
itr_end:
bdy:
kind: 0 x: 25 y: 25 w: 30 h: 30
bdy_end:
'''
                text+='<frame_end>\n'
            if id_==437:
                for n in range(8):
                    text+=f'<frame> {20+n} shadow_smoke\npic: {48+n} state: 3000 wait: 1 next: {20+(n+1)%8} dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 40\n<frame_end>\n'
            for n in (10,20,30,40):
                if n==20 and id_==437: continue
                text+=f'<frame> {n} vanish\npic: {pic} state: 3005 wait: 0 next: 1000 dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 40\n<frame_end>\n'
        (PACK/f'assets/{id_}.dat').write_bytes(encode(text,raw))
        rows.append(f'id: {id_} type: {kind} file: mods/polish-originals/{id_}.dat\n')
        manifest.append(f'asset=mods/polish-originals/{id_}.dat|assets/{id_}.dat')
    for path in (PACK/'assets/catalog.txt',ROOT/'content-packs/mixed-all/assets/catalog.txt'):
        if path.is_file():
            text=path.read_text(encoding='latin1')
            text=re.sub(r'^id:\s*43\d\s+type:[^\n]*\n','',text,flags=re.M)
            path.write_text(text.replace('<object_end>',''.join(rows)+'<object_end>',1),encoding='latin1')
    (PACK/'package.manifest').write_text('\n'.join(manifest)+'\n')
    hashes=json.loads((PACK/'asset-checksums.json').read_text())
    for path in list((PACK/'art').glob('*.png'))+list((PACK/'assets').glob('*.dat'))+[PACK/'assets/catalog.txt']:
        hashes[path.relative_to(PACK).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    (PACK/'asset-checksums.json').write_text(json.dumps(hashes,indent=2)+'\n')
    report_path=ROOT/'content-packs/mixed-all/build-report.json'
    report=json.loads(report_path.read_text());catalog=(report_path.parent/'assets/catalog.txt').read_text(encoding='latin1')
    ids=re.findall(r'^id:\s*(\d+)\s+type:',catalog,re.M)
    report['objects'],report['unique_ids']=len(ids),len(set(ids));report['hero_effect_ids']=list(HELPERS)
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    own_report=PACK/'import-report.json'
    report=json.loads(own_report.read_text())
    report['helpers']=sorted(set(report['helpers']) | set(HELPERS))
    own_report.write_text(json.dumps(report,indent=2)+'\n')
    print('Hero update: dedicated mech animation, combos, effects 430-439; original imported assets retained')


if __name__=='__main__': build()
