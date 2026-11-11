"""Verify displayed action sequences against the actual generated DAT hit mappings."""
import re
from pathlib import Path
from import_legacy import decode
from test_lua_scripts import runtime

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    lua = runtime()
    guide = lua.eval("require('polish-fighters/combo_guide')")
    if isinstance(guide, tuple): guide = guide[0]
    pack = ROOT / 'content-packs/polish-originals'
    assets = dict(line[6:].split('|', 1) for line in (pack / 'package.manifest').read_text().splitlines() if line.startswith('asset='))
    catalog = (pack / assets['mods/polish-originals/catalog.txt']).read_text(encoding='latin1')
    fields = {'D > A': 'hit_Fa', 'D ^ A': 'hit_Ua', 'D v A': 'hit_Da',
              'D > J': 'hit_Fj', 'D ^ J': 'hit_Uj', 'D v J': 'hit_Dj', 'D J A': 'hit_ja'}
    count = 0
    for actor in range(410, 416):
        path = re.search(r'id:\s*' + str(actor) + r'\s+type:\s*0\s+file:\s*(\S+)', catalog)[1]
        text = decode((pack / assets[path]).read_bytes())
        defend = re.search(r'<frame>\s*110\s+(.*?)<frame_end>', text, re.S)[1]
        hits = dict(re.findall(r'\b(hit_(?:Fa|Ua|Da|Fj|Uj|Dj|ja)):\s*(-?\d+)', defend))
        for _, move in guide.moves(actor).items():
            assert int(hits[fields[move[1]]]) == move[3], (actor, move[1])
            assert re.search(r'<frame>\s*' + str(move[3]) + r'\s+', text), (actor, move[3])
            count += 1
    print(f'PASS: {count} guide combinations match actual DAT moves for five heroes and the mech')
