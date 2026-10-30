"""Execute real Lua picture lookup for every parsed frame at offsets 0 and 140."""
import json
import re
from pathlib import Path
from lupa.luajit21 import LuaRuntime
from import_legacy import decode
from audit_pack_compatibility import SHEET
ROOT=Path(__file__).resolve().parents[1]

def verify(pack):
    folder=ROOT/'content-packs'/pack
    assets={v:folder/r for v,r in [l[6:].split('|') for l in (folder/'package.manifest').read_text().splitlines() if l.startswith('asset=')]}
    dimensions=json.loads((folder/'sprite-layouts.json').read_text())['dimensions']
    lua=LuaRuntime(unpack_returned_tuples=True)
    original=lua.execute((ROOT/'engine/scripts/base/game/object_data.lua').read_text())
    patched=lua.execute((folder/'sprite_layout.lua').read_text())(lua.table_from({'picture':original.picture}))
    count=visible=empty=clipped=0
    for path in assets.values():
        if path.suffix!='.dat':continue
        text=decode(path.read_bytes());sheets=[];first=0
        for label,name,w,h,cols,rows in SHEET.findall(text):
            w,h,cols,rows=map(int,(w,h,cols,rows))
            sheets.append({'resource':name,'cell_width':w,'cell_height':h,'columns':cols,'rows':rows,'first_picture':first});first+=cols*rows
        if not sheets:continue
        frames={}
        for id_,body in re.findall(r'<frame>\s*(\d+)\s+\S+(.*?)<frame_end>',text,re.S):
            pic=re.search(r'\bpic:\s*(-?\d+)',body)
            if pic:frames[int(id_)]={'picture':int(pic[1])}
        data=lua.table_from({'frames':frames,'sheets':sheets},recursive=True)
        for id_ in frames:
            for offset in [0,140]:
                count+=1;result=patched.picture(data,id_,offset)
                if result is None:empty+=1;continue
                resource,rect=result
                assert resource in dimensions,resource
                x,y,w,h=[rect[i] for i in range(1,5)];actual=dimensions[resource]
                assert x>=0 and y>=0 and w>0 and h>0 and x+w<=actual[0] and y+h<=actual[1],(resource,x,y,w,h)
                visible+=1
                prior=original.picture(data,id_,offset)
                if prior and (w!=prior[1][3] or h!=prior[1][4]):clipped+=1
    return {'pack':pack,'lookups':count,'visible':visible,'empty_or_unmapped':empty,'intersections':clipped,'out_of_bounds':0,'scope':'Every parsed DAT frame, real Lua lookup, offsets 0/140; no reachability or visual equivalence proof'}
if __name__=='__main__':
    results=[verify(p) for p in ['bleach','kate','reinforced']]
    output=ROOT/'validation/maps-build-2026-10-30/sprite-source-verification.json';output.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
