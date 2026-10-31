"""Build an additive LF2 roster from pinned data and unmodified generated RGBA art.

Never executes the installer, changes original DATs, or resamples the artwork.
"""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image
from read_pinned_lf2 import read_resource
from import_legacy import decode, encode

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'content-packs/polish-originals'
CHARACTERS = [
 (410, 'w', 'Wasyl', 'exec-44d61b07-ca38-496a-8ad3-911a70e64984.png', [0,183,346,526,686,826,976,1112,1254]),
 (411, 's', 'SZ', 'exec-91c13bf6-efb3-4455-9c98-481162061832.png', [0,171,335,489,651,797,955,1098,1254]),
 (412, 'j', 'Mega Ninja Jas', 'exec-5ef26c42-9a56-47a9-88ce-f901aa6854d9.png', [0,179,348,502,674,817,970,1111,1254]),
 (413, 'b', 'Sigma Tata', 'exec-ef12b3e9-92fe-4e61-b049-fb8d83e70ea8.png', [0,160,318,478,633,782,933,1086,1254]),
]
HELPERS = [(420,'w',61),(421,'j',61),(422,'j',62),(423,'b',63),(424,'b',61),(425,'b',62),(426,'s',61)]

def picture(number, name):
    if name == 'standing': return number % 4
    if name in ('walking','heavy_obj_walk'): return 4 + number % 4
    if 'running' in name or 'run' == name: return 8 + number % 4
    if 'lying' in name: return 36 + number % 4
    if 'fall' in name: return 32 + number % 4
    if 'defend' in name: return 28 + number % 4
    if 'injured' in name or 'ice' in name or 'fire' in name: return 24 + number % 4
    if 'dash' in name: return 48 + number % 4
    if 'jump_attack' in name: return 52 + number % 4
    if 'jump' in name or 'crouch' in name: return 12 + number % 4
    if 'rowing' in name: return 40 + number % 4
    if 'punch' in name or 'attack' in name or 'throw' in name: return 16 + number % 5
    return number % 4

def character(raw, key, name):
    text = decode(raw)
    header = text.split('<bmp_end>')[0] + '<bmp_end>\n'
    header = re.sub(r'name:\s*\S+', 'name: ' + name.replace(' ', '_'), header)
    header = re.sub(r'(head|small):\s*\S+', lambda m: m[1]+': mods/polish-originals/'+key+('_h.png' if m[1]=='head' else '_s.png'), header)
    header = re.sub(r'file\([^\n]+\n', '', header)
    header = header.replace('<bmp_end>', f'file(0-63): mods/polish-originals/{key}.png w: 79 h: 79 row: 8 col: 8\n<bmp_end>')
    if key != 'b':
        header = re.sub(r'walking_speed [\d.]+', 'walking_speed 6.2', header)
        header = re.sub(r'running_speed [\d.]+', 'running_speed 10.5', header)
    frames = []
    for match in re.finditer(r'<frame>\s*(\d+)\s+(\S+)(.*?)<frame_end>', text, re.S):
        number, frame_name, body = int(match[1]), match[2], match[3]
        if number > 234 and number != 399: continue
        center_x = int(re.search(r'centerx:\s*(-?\d+)', body)[1])
        center_y = int(re.search(r'centery:\s*(-?\d+)', body)[1])
        body = re.sub(r'(?<![a-z])x:\s*(-?\d+)', lambda m: 'x: '+str(int(m[1])+40-center_x), body)
        body = re.sub(r'(?<![a-z])y:\s*(-?\d+)', lambda m: 'y: '+str(int(m[1])+79-center_y), body)
        body = re.sub(r'centerx:\s*-?\d+', 'centerx: 40', body)
        body = re.sub(r'centery:\s*-?\d+', 'centery: 79', body)
        body = re.sub(r'pic:\s*\d+', 'pic: '+str(picture(number, frame_name)), body)
        body = re.sub(r'opoint:.*?opoint_end:', '', body, flags=re.S)
        body = re.sub(r'hit_(?:Fa|Ua|Da|Fj|Uj|Dj|ja):\s*-?\d+', '', body)
        # Add combo targets to the main frame properties, never to nested blocks.
        body = re.sub(r'(hit_j:\s*-?\d+)', r'\1 hit_Fa: 300 hit_Ua: 310 hit_Da: 320 hit_Fj: 330 hit_Uj: 340 hit_Dj: 350 hit_ja: 360', body, count=1)
        if key == 'j': body = re.sub(r'injury:\s*\d+', 'injury: 15', body)
        frames.append(f'<frame> {number} {frame_name}{body}<frame_end>\n')
    skill_poses={
        'w':[(57,58),(44,45),(48,49),(52,53),(58,60),(57,58),(58,60)],
        's':[(16,17),(45,46),(48,49),(52,53),(57,58),(50,51),(58,59)],
        'j':[(59,60),(44,45),(48,49),(52,53),(59,60),(45,46),(59,60)],
        'b':[(16,17),(52,53),(21,22),(18,19),(44,45),(56,57),(58,59)],
    }
    for position,(number,cost) in enumerate([(300,55),(310,100),(320,50),(330,70),(340,180),(350,100),(360,230)]):
        pic,recovery_pic=skill_poses[key][position]
        frames.append(f'''<frame> {number} original_skill
 pic: {pic} state: 3 wait: 6 next: {number+1} dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 79 mp: {cost}
 bdy:
 kind: 0 x: 23 y: 15 w: 34 h: 64
 bdy_end:
<frame_end>
<frame> {number+1} recover
 pic: {recovery_pic} state: 3 wait: 5 next: 999 dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 79
 bdy:
 kind: 0 x: 23 y: 15 w: 34 h: 64
 bdy_end:
<frame_end>
''')
    return encode(header+'\n'.join(frames), raw)

def build():
    assets = PACK/'assets'; assets.mkdir(parents=True, exist_ok=True)
    art = PACK/'art'; art.mkdir(exist_ok=True)
    raw = read_resource(ROOT.parent/'downloads/LF2_v2.0a.exe', 'data/deep.dat')
    catalog = read_resource(ROOT.parent/'downloads/LF2_v2.0a.exe', 'data/data.txt')
    manifest = ['id=polish-originals','version=1','api=1','requires=base@1','requires=polish-fighters@1',
                'extend=base/game/catalog|catalog.lua','module=render|render.lua','module=layout|layout.lua',
                'module=runtime|runtime.lua','extend=base/game/frame_rules|frame_rules.lua',
                'extend=base/game/match|match.lua','extend=base/game/ai|ai.lua','extend=base/ui/character_select|selection.lua',
                'extend=base/ui/match_screen|match_screen.lua']
    lines=[]; layout={}; fighters=[]; hashes={}
    for id_, key, name, filename, cuts in CHARACTERS:
        assert not re.search(rb'id:\s*'+str(id_).encode()+rb'\s', catalog)
        if not (art/(key+'.png')).exists():
            raise FileNotFoundError('Restore the unmodified project artwork: '+str(art/(key+'.png')))
        with Image.open(art/(key+'.png')) as image:
            assert image.mode == 'RGBA' and image.height == cuts[-1]
            width, height = image.size
            rectangles=[]
            for n in range(64):
                row,col=divmod(n,8);left=round(col*width/8);right=round((col+1)*width/8)
                rect=[left,cuts[row],right-left,cuts[row+1]-cuts[row]]
                rectangles.append(rect)
            # Full lying poses in Wasyl's deliberately wide row: preserve all pixels.
            if key == 'w':
                rectangles[36]=[610,725,238,102];rectangles[37]=rectangles[36]
                rectangles[38]=[1005,735,249,92];rectangles[39]=rectangles[38]
                # The generated lower rows have fewer, wider poses than the prompt.
                # Explicit full-pose rectangles avoid sampling fragments of neighbours.
                overrides={
                    40:[0,843,180,133],41:[180,843,146,133],42:[326,830,150,146],43:[476,826,144,150],
                    44:[620,826,203,150],45:[820,826,226,150],46:[1048,826,206,150],47:[620,826,203,150],
                    48:[0,976,210,136],49:[210,976,192,136],50:[396,974,236,138],51:[640,972,215,140],
                    52:[853,972,225,140],53:[640,972,215,140],54:[853,972,225,140],55:[396,974,236,138],
                    56:[242,1110,165,144],57:[408,1106,175,148],58:[552,1110,182,144],59:[242,1110,165,144],
                    60:[408,1106,175,148],61:[710,1105,184,149],62:[892,1105,189,149],63:[1078,1105,176,149],
                    21:[650,352,130,174],22:[853,972,225,140],23:[1098,352,156,174],
                }
                for n,rect in overrides.items(): rectangles[n]=rect
                rectangles[15]=rectangles[12]
            elif key == 's':
                # These source cells contain the actual airborne and shielding poses.
                rectangles[12]=[492,171,166,164];rectangles[13]=[653,171,174,164]
                rectangles[14]=rectangles[12];rectangles[15]=rectangles[13]
                rectangles[28]=rectangles[29];rectangles[31]=rectangles[30]
            elif key == 'j': rectangles[15]=rectangles[12]
            effects={
                'w':[[744,1125,147,110],[906,1114,174,118],[1085,1108,169,137]],
                's':[[825,1129,130,60],[963,1101,155,151],[1125,1102,129,151]],
                'j':[[804,1138,135,75],[960,1125,139,119],[1107,1112,147,137]],
                'b':[[828,1102,150,125],[979,1094,155,147],[1142,1114,108,132]],
            }
            for n,rect in enumerate(effects[key],61):rectangles[n]=rect
            bottom_padding=[]
            for x,y,w,h in rectangles:
                assert x>=0 and y>=0 and x+w<=width and y+h<=height
                # Ignore faint generated alpha specks when finding the visible foot baseline.
                bounds=image.getchannel('A').crop((x,y,x+w,y+h)).point(lambda a:255 if a>=64 else 0).getbbox()
                assert bounds
                bottom_padding.append(h-bounds[3])
            portrait={'w':[72,33,63,70],'s':[44,22,100,100],'j':[43,27,89,89],'b':[44,21,76,77]}[key]
            # Match LF2-sized silhouettes; portraits have their own face-only source rectangle.
            target_cell={'w':92,'s':90,'j':90,'b':98}[key]
            layout[key]={'width':width,'height':height,'rectangles':rectangles,'portrait':portrait,
                         'bottom_padding':bottom_padding,'scale':target_cell/(width/8)}
        (assets/(key+'.dat')).write_bytes(character(raw,key,name))
        lines.append(f'id: {id_} type: 0 file: mods/polish-originals/{key}.dat\n')
        fighters.append({'id':id_,'name':name,'path':f'mods/polish-originals/{key}.dat'})
        manifest.append(f'asset=mods/polish-originals/{key}.dat|assets/{key}.dat')
        manifest.append(f'asset=mods/polish-originals/{key}.png|art/{key}.png')
        manifest.append(f'asset=mods/polish-originals/{key}_h.png|art/{key}.png')
        manifest.append(f'asset=mods/polish-originals/{key}_s.png|art/{key}.png')
    for id_, key, pic in HELPERS:
        assert not re.search(rb'id:\s*'+str(id_).encode()+rb'\s', catalog)
        body=f'''<bmp_begin>
name: pf_effect_{id_}
file(0-63): mods/polish-originals/{key}.png w: 79 h: 79 row: 8 col: 8
<bmp_end>
<frame> 0 flying
pic: {pic} state: 3000 wait: 1 next: 0 dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 40 hit_a: 0 hit_d: 10 hit_j: 0
itr:
kind: 0 x: 20 y: 20 w: 40 h: 40 dvx: 7 dvy: -3 fall: 25 vrest: 15 bdefend: 15 injury: 22
itr_end:
bdy:
kind: 0 x: 24 y: 24 w: 32 h: 32
bdy_end:
<frame_end>
<frame> 10 vanish
pic: {pic} state: 3000 wait: 0 next: 1000 dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 40
<frame_end>
'''
        for frame in [20,30,40]:
            body+=f'''<frame> {frame} dissipate
pic: {pic} state: 3005 wait: 0 next: 1000 dvx: 0 dvy: 0 dvz: 0 centerx: 40 centery: 40
<frame_end>
'''
        (assets/(str(id_)+'.dat')).write_bytes(encode(body,raw))
        lines.append(f'id: {id_} type: 3 file: mods/polish-originals/{id_}.dat\n')
        manifest.append(f'asset=mods/polish-originals/{id_}.dat|assets/{id_}.dat')
    inserted=''.join(lines).encode('ascii')
    (assets/'catalog.txt').write_bytes(catalog.replace(b'<object_end>',inserted+b'<object_end>',1))
    assert (assets/'catalog.txt').read_bytes().replace(inserted,b'',1)==catalog
    manifest.append('asset=mods/polish-originals/catalog.txt|assets/catalog.txt')
    (PACK/'package.manifest').write_text('\n'.join(manifest)+'\n',encoding='utf-8')
    (PACK/'layout.json').write_text(json.dumps(layout,indent=2)+'\n')
    lua=['return {']
    for key,info in layout.items():
        rects=','.join('{'+','.join(map(str,rect))+'}' for rect in info['rectangles'])
        lua.append(f'{key}={{scale={info["scale"]},portrait={{{",".join(map(str,info["portrait"]))}}},bottom_padding={{{",".join(map(str,info["bottom_padding"]))}}},rectangles={{{rects}}}}},')
    (PACK/'layout.lua').write_text('\n'.join(lua)+'\n}\n')
    for file in sorted(assets.iterdir()):
        if file.suffix!='.png': hashes['assets/'+file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
    for file in sorted(art.iterdir()): hashes['art/'+file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
    (PACK/'asset-checksums.json').write_text(json.dumps(hashes,indent=2)+'\n')
    (PACK/'import-report.json').write_text(json.dumps({'fighters':fighters,'original_catalog_preserved':True,'art_unmodified':True,'helpers':[x[0] for x in HELPERS]},indent=2)+'\n')
    print('Built additive roster: 4 fighters, 7 effects, 256 source rectangles; original catalog preserved')

if __name__=='__main__': build()
