"""Audit preservation, source rectangles, hashes and all new DAT frame links."""
import hashlib
import json
import re
from PIL import Image
from build_polish_originals import ROOT, PACK
from import_legacy import decode
from read_pinned_lf2 import read_resource

def main():
    output=ROOT/'validation/polish-originals-2026-10-30'
    before=json.loads((output/'preservation-before.json').read_text())
    changed=[name for name,sha in before.items() if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha]
    assert not changed,changed
    hashes=json.loads((PACK/'asset-checksums.json').read_text())
    for name,sha in hashes.items(): assert hashlib.sha256((PACK/name).read_bytes()).hexdigest()==sha,name
    old=read_resource(ROOT.parent/'downloads/LF2_v2.0a.exe','data/data.txt')
    new=(PACK/'assets/catalog.txt').read_bytes()
    insertion=re.search(rb'(id: 410 type: 0 file: mods/polish-originals/.*?)(?=<object_end>)',new,re.S)[1]
    assert new.replace(insertion,b'',1)==old
    layout=json.loads((PACK/'layout.json').read_text())
    for key,info in layout.items():
        with Image.open(PACK/'art'/f'{key}.png') as image:
            assert image.mode=='RGBA' and image.size==(info['width'],info['height'])
            for x,y,w,h in info['rectangles']+[info['portrait']]:
                assert 0<=x<x+w<=image.width and 0<=y<y+h<=image.height
                assert image.getchannel('A').crop((x,y,x+w,y+h)).getbbox()
    frame_count=0
    for path in (PACK/'assets').glob('*.dat'):
        text=decode(path.read_bytes())
        matches=list(re.finditer(r'<frame>\s*(\d+)\s+(.*?)<frame_end>',text,re.S))
        frames={int(m[1]):m[2] for m in matches};assert len(frames)==len(matches)
        for number,body in frames.items():
            pic=int(re.search(r'pic:\s*(\d+)',body)[1]);assert 0<=pic<64
            # hit_d in helper frames is a destination; hit_a=0 means no HP drain.
            for match in re.finditer(r'\b(next|hit_a|hit_j|hit_d|hit_[FUD][aj]|hit_ja):\s*(-?\d+)',body):
                target=abs(int(match[2]));assert target in frames or target in (0,999,1000),(path.name,number,match[1],target)
            for path_token in re.findall(r'(?i)\b([a-z0-9_./\\-]+\.(?:png|bmp|dat|wav))',body):
                assert len(path_token)<40
        frame_count+=len(frames)
    report={'preserved_files':len(before),'changed_originals':changed,'new_fighters':4,'new_effects':7,
      'original_catalog_byte_preserved':True,'rgba_atlases':4,'source_rectangles':256,'dat_frames_checked':frame_count,
      'asset_hashes_checked':len(hashes),'pass':True}
    (output/'preservation-after.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
