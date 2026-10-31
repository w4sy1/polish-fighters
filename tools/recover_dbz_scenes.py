"""Recover authored DBZ scene modes; never infer dimensions from image size."""
import hashlib
import json
import re
from pathlib import Path
from import_legacy import decode, canonical
ROOT=Path(__file__).resolve().parents[1]

def fields(text):
    result={}
    for key,value in re.findall(r'\b(\w+):\s*([^\s]+)',text):
        if key in ('respond','arest'):
            result.setdefault(key,[]).append(int(value))
        else:
            try: result[key]=int(value)
            except ValueError: result[key]=value.replace('\\','/')
    z=re.search(r'\bzboundary:\s*(-?\d+)\s+(-?\d+)',text)
    if z:result['zboundary']=list(map(int,z.groups()))
    return result

def lua(value):
    if value is None:return 'nil'
    if isinstance(value,dict):return '{'+','.join('['+json.dumps(str(k))+']='+lua(v) for k,v in value.items())+'}'
    if isinstance(value,list):return '{'+','.join(lua(v) for v in value)+'}'
    return json.dumps(value,ensure_ascii=True)

def recover(source,pack):
    files={canonical(p.relative_to(source).as_posix()):p for p in source.rglob('*') if p.is_file() and re.fullmatch(r'[A-Za-z0-9_./\\-]+',p.relative_to(source).as_posix())}
    catalog=files['data/data.txt'].read_text('latin1').split('<background>')[1].split('<background_end>')[0]
    original=[canonical(p) for p in re.findall(r'\bfile:\s*(\S+)',catalog)]
    imported_catalog=next((pack/'assets').rglob('*.txt')).read_text('latin1').split('<background>')[1].split('<background_end>')[0]
    imported=re.findall(r'\bfile:\s*(\S+)',imported_catalog)
    manifest={v:pack/r for v,r in (line[6:].split('|',1) for line in (pack/'package.manifest').read_text().splitlines() if line.startswith('asset='))}
    hashes={hashlib.sha256(p.read_bytes()).hexdigest():v for v,p in manifest.items() if p.suffix!='.dat'}
    info=decode(files['data/bg_mode.dat'].read_bytes())
    definitions=re.findall(r'<bg_information>(.*?)<bg_information_end>',info,re.S)
    assert len(definitions)==len(original)==len(imported)
    scenes={}
    for row,definition in enumerate(definitions):
        entry=fields(definition);assert entry['bg']==row
        modefile=files[canonical(entry['file'])]
        modes=[fields(b) for b in re.findall(r'<mode>(.*?)<mode_end>',decode(modefile.read_bytes()),re.S)]
        base_fields=fields(decode(files[original[row]].read_bytes()).split('layer:')[0])
        for mode in modes:
            for key in ('width','zboundary'):
                if key not in mode and key in base_fields:mode[key]=base_fields[key]
        assert modes and all(isinstance(m.get('width'),int) and len(m.get('zboundary',[]))==2 for m in modes),entry
        for mode in modes:
            for key in ('shadow','small'):
                if key in mode:
                    path=files.get(canonical(mode[key]))
                    mode[key+'_resource']=hashes.get(hashlib.sha256(path.read_bytes()).hexdigest()) if path else None
        raw=files[original[row]].read_bytes();text=re.sub(r'#[^\r\n]*','',decode(raw))
        layers=re.findall(r'\blayer:\s*(.*?)\blayer_end\b',text,re.S)
        scenes[imported[row]]={'row':row,'source':original[row],'source_sha256':hashlib.sha256(raw).hexdigest(),
            'mode_source':entry['file'],'mode_source_sha256':hashlib.sha256(modefile.read_bytes()).hexdigest(),
            'modes':modes,'layer_respond':[fields(b).get('respond',[0])[0] for b in layers],
            'opoints':[fields(b) for b in re.findall(r'\bopoint:\s*(.*?)\bopoint_end\b',text,re.S)],
            'quests':[fields(b) for b in re.findall(r'\bquest:\s*(.*?)\bquest_end\b',text,re.S)]}
    (pack/'scene-modes.lua').write_text('return '+lua(scenes)+'\n',encoding='ascii')
    (pack/'scene-modes.json').write_text(json.dumps({'scope':'Authored geometry, respond/arest selectors and original scene instructions; quest semantics require separate engine port.','scenes':scenes},indent=2)+'\n')
    stages={}
    for virtual,path in manifest.items():
        if path.suffix!='.dat':continue
        text=re.sub(r'#[^\r\n]*','',decode(path.read_bytes()))
        definitions={}
        for body in re.findall(r'<stage>(.*?)<stage_end>',text,re.S):
            header=fields(body.split('<phase>')[0])
            if 'id' in header and 'bg' in header:
                assert 0<=header['bg']<len(original)
                definitions[str(header['id'])]={'row':header['bg'],'mode':header.get('mode',0)}
        if definitions:stages[virtual]=definitions
    (pack/'stage-scenes.lua').write_text('return '+lua(stages)+'\n',encoding='ascii')
    (pack/'stage-scenes.json').write_text(json.dumps({'scope':'DBZ bg indexes the ordered bg_mode definitions, mode indexes the selected scene mode.','stages':stages},indent=2)+'\n')
    print('Recovered',len(scenes),'scenes,',sum(len(s['modes']) for s in scenes.values()),'authored modes')

if __name__=='__main__':recover((ROOT/'../games/DBZ-recovered-2026-10-28').resolve(),ROOT/'content-packs/dbz')
