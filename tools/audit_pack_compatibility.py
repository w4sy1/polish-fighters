"""Audit actual referenced sprite cells and spawn targets, without changing assets.

Cell numbering follows existing resources/object_data.cpp: cumulative row*col,
not the cosmetic file(A-B) label. All frames count, including unreachable ones.
"""
import argparse
import json
import re
from pathlib import Path
from PIL import Image
from import_legacy import decode


SHEET = re.compile(r'file\(([^)]*)\):\s*(\S+)\s+w:\s*(\d+)\s+h:\s*(\d+)\s+row:\s*(\d+)\s+col:\s*(\d+)')


def cells(text, dimensions, layouts=None):
    sheets, first = [], 0
    for label, path, w, h, columns, rows in SHEET.findall(text):
        w,h,columns,rows = map(int,(w,h,columns,rows))
        if not columns or not rows:
            raise ValueError('Zero sprite grid')
        sheets.append({'asset':path,'label':label,'first':first,'count':columns*rows,
                       'w':w,'h':h,'columns':columns,'rows':rows,'actual':dimensions.get(path)})
        first += columns*rows
    checks, unmapped = [], []
    for frame, body in re.findall(r'<frame>\s*(\d+)\s+\S+(.*?)<frame_end>',text,re.S):
        header = re.split(r'\b(?:bpoint|wpoint|cpoint|opoint|itr|bdy):',body,maxsplit=1)[0]
        picture = re.search(r'\bpic:\s*(-?\d+)',header)
        if picture is None:
            continue
        picture = int(picture[1])
        sheet = next((s for s in sheets if s['first'] <= picture < s['first']+s['count']),None)
        if sheet is None:
            unmapped.append({'frame':int(frame),'picture':picture})
            continue
        cell = picture-sheet['first']
        key=f"{sheet['asset']}|{sheet['w']}|{sheet['h']}|{sheet['columns']}|{sheet['rows']}"
        stride=(layouts or {}).get(key,{}).get('stride',[sheet['w']+1,sheet['h']+1])
        x,y = cell % sheet['columns']*stride[0], cell//sheet['columns']*stride[1]
        actual = sheet['actual']
        checks.append({'asset':sheet['asset'],'frame':int(frame),'picture':picture,
                       'rect':[x,y,sheet['w'],sheet['h']],
                       'fits':bool(actual and x+sheet['w']<=actual[0] and y+sheet['h']<=actual[1]),
                       'fully_empty':bool(actual and (x>=actual[0] or y>=actual[1]))})
    return checks, unmapped


def audit(root):
    root = Path(root)
    assets = {}
    for line in (root/'package.manifest').read_text().splitlines():
        if line.startswith('asset='):
            virtual,relative=line[6:].split('|')
            p=(root/relative).resolve()
            if not p.is_relative_to(root.resolve()):raise ValueError('Asset escape')
            assets[virtual]=p
    dimensions={}
    for name,p in assets.items():
        if p.suffix in ('.bmp','.png'):
            with Image.open(p) as image:dimensions[name]=list(image.size)
    catalog=next(p for p in assets.values() if p.suffix=='.txt')
    source=catalog.read_text(encoding='latin1')
    records=[(int(i),int(k),p) for i,k,p in re.findall(r'id:\s*(\d+)\s+type:\s*(\d+)\s+file:\s*(\S+)',source)]
    ids={i for i,_,_ in records}
    metadata=root/'sprite-layouts.json'
    layouts=json.loads(metadata.read_text())['layouts'] if metadata.exists() else {}
    checks,unmapped,spawns,extensions=[],[],[],{}
    for id_,kind,name in records:
        text=decode(assets[name].read_bytes())
        current,missing=cells(text,dimensions,layouts)
        checks.extend(dict(c,object=id_) for c in current)
        unmapped.extend(dict(c,object=id_) for c in missing)
        for frame,body in re.findall(r'<frame>\s*(\d+)\s+\S+(.*?)<frame_end>',text,re.S):
            for point in re.findall(r'\bopoint:(.*?)opoint_end:',body,re.S):
                fields={k:int(v) for k,v in re.findall(r'\b(kind|oid|action):\s*(-?\d+)',point)}
                oid=fields.get('oid',0)
                if oid not in ids:
                    status='inactive_zero_oid' if oid<=0 or fields.get('kind',0)<=0 else 'missing_active_target'
                    spawns.append(dict(fields,object=id_,frame=int(frame),status=status))
        for tag in ['state','effect','kind']:
            extensions.setdefault(tag,set()).update(int(x) for x in re.findall(r'\b'+tag+r':\s*(-?\d+)',text))
    old=json.loads((root/'sprite-edge-repairs.json').read_text())['unresolved']
    classified=[]
    aliases={}
    encodings=root/'lossless-image-encodings.json'
    if encodings.exists():
        for entry in json.loads(encodings.read_text()):
            aliases['mods/'+root.name+'/'+entry['original'].removeprefix('assets/')]='mods/'+root.name+'/'+entry['encoded'].removeprefix('assets/')
    for row in old:
        uses=[c for c in checks if c['asset']==aliases.get(row['asset'],row['asset'])]
        bad=[c for c in uses if not c['fits']]
        status='partial_clipping_remaining' if any(not c['fully_empty'] for c in bad) else ('empty_sources_suppressed' if bad else 'referenced_cells_fit')
        classified.append(dict(row,status=status,
                               checked_frame_references=len(uses),outside=bad))
    return {'pack':root.name,'scope':'Static rectangles after render layout overrides; all declared frames, no reachability or dynamic offsets',
            'original_sheet_alerts':len(old),'sheet_alerts':classified,
            'actual_outside_frame_references':[c for c in checks if not c['fits']],
            'unmapped_pictures':unmapped,'spawn_targets':spawns,
            'observed_values':{k:sorted(v) for k,v in extensions.items()}}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package');p.add_argument('--output',required=True)
    a=p.parse_args();r=audit(a.package)
    Path(a.output).write_text(json.dumps(r,indent=2)+'\n')
    print(r['pack'],'sheet alerts',r['original_sheet_alerts'],'partial clipping sheets',sum(s['status']=='partial_clipping_remaining' for s in r['sheet_alerts']),
          'outside frames',len(r['actual_outside_frame_references']),'unmapped pictures',len(r['unmapped_pictures']))
