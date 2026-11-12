"""Generate Android's menu dictionary and pixel glyphs from the Lua source of truth."""
import json
from PIL import Image
from pathlib import Path
from lupa.luajit21 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]

def generate():
    lua = LuaRuntime(unpack_returned_tuples=True)
    source = ROOT / 'engine/scripts/polish-fighters'
    result = {}
    for language in ('pl', 'en'):
        result[language] = dict(lua.execute((source / f'locales/{language}.lua').read_text(encoding='utf-8')).items())
    result['ui_en'] = dict(lua.execute((source / 'locales/ui_en.lua').read_text(encoding='utf-8')).items())
    result['android_en'] = dict(lua.execute((source / 'locales/android_en.lua').read_text(encoding='utf-8')).items())
    font = lua.execute((source / 'pixel_font.lua').read_text(encoding='utf-8'))
    result['glyphs'] = {key: list(rows.values()) for key, rows in font.glyphs.items()}
    result['accents'] = dict(font.accents.items())
    return json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'

def generate_atlas():
    data=json.loads(generate())
    keys=sorted(set(data['glyphs']) | set(data['accents']))
    image=Image.new('RGB',(len(keys)*24,84))
    pixels=image.load()
    for scale,offset in ((1,0),(2,12),(4,36)):
        for index,key in enumerate(keys):
            points=[]
            for row,bits in enumerate(data['glyphs'][data['accents'].get(key,key)]):
                points += [(column,row) for column in range(5) if bits & (1 << (4-column))]
            if key=='Ł':points += [(1,4),(3,2)]
            elif key in ('Ą','Ę'):points += [(3,7),(4,8)]
            elif key=='Ż':points += [(2,-2)]
            elif key in data['accents']:points += [(2,-2),(3,-3)]
            for x,y in points:
                for dx in range(scale):
                    for dy in range(scale):pixels[(index*6+x)*scale+dx,offset+(y+3)*scale+dy]=(255,255,255)
    source=ROOT/'engine/scripts/polish-fighters'
    image.save(source/'menu-font.png')
    (source/'menu_font_index.lua').write_text('-- Generated pixel atlas coordinates, in unscaled 6px cells.\nreturn {\n'+
        ''.join(' [%s]=%d,\n'%(json.dumps(key,ensure_ascii=False),index*6) for index,key in enumerate(keys))+'}\n',encoding='utf-8')

if __name__ == '__main__':
    target = ROOT / 'engine/android/app/src/main/assets/classic-menu.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(generate(), encoding='utf-8')
    generate_atlas()
    print(target)
