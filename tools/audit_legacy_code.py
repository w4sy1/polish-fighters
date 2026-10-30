"""Read-only PE section comparison. Input code is never loaded or executed."""
import hashlib
import json
import struct
import zipfile
from pathlib import Path
import pefile
from clickteam_legacy import inflate
from read_pinned_lf2 import read_resource


def embedded_program(source, requested):
    raw=Path(source).read_bytes();cursor=77824;table=None
    if raw[cursor:cursor+4] != bytes.fromhex('39120100'):raise ValueError('Unknown stub')
    while cursor+8 <= len(raw):
        kind,flags,size=struct.unpack_from('<HHI',raw,cursor);body=cursor+8
        if body+size>len(raw):raise ValueError('Truncated block')
        if kind==0x123a:table=inflate(raw[body+4:body+size],int.from_bytes(raw[body:body+4],'little'))
        if kind==0x7f7f:
            if body+4+size!=len(raw):raise ValueError('Payload length')
            payload=raw[body+4:];break
        cursor=body+size
    if table is None:raise ValueError('No table')
    cursor=4
    for _ in range(int.from_bytes(table[:4],'little')):
        size=int.from_bytes(table[cursor:cursor+4],'little');record=table[cursor:cursor+size]
        if size<36 or len(record)!=size:raise ValueError('Invalid file record')
        flags=int.from_bytes(record[22:24],'little')
        name=record[36+(18 if flags&6 else 0)+(24 if flags&8 else 0):].split(b'\0',1)[0].decode('latin1')
        if name.lower()==requested.lower():
            offset,compressed,expected=struct.unpack_from('<III',record,6)
            if offset+compressed>len(payload):raise ValueError('Truncated payload')
            return inflate(payload[offset:offset+compressed],expected)
        cursor+=size
    raise FileNotFoundError(requested)


def sections(data):
    pe=pefile.PE(data=data)
    return {s.Name.rstrip(b'\0').decode('ascii'):s.get_data() for s in pe.sections}


def compare(data, reference):
    actual,base=sections(data),sections(reference);result={}
    for name in actual.keys() & base.keys():
        a,b=actual[name],base[name]
        changed=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
        spans=[]
        for i in changed:
            if spans and spans[-1][1]==i:spans[-1][1]=i+1
            else:spans.append([i,i+1])
        result[name]={'size':len(a),'reference_size':len(b),'identical':a==b,
                      'different_overlapping_bytes':len(changed),'different_spans':spans,
                      'sha256':hashlib.sha256(a).hexdigest(),'reference_sha256':hashlib.sha256(b).hexdigest()}
    return result


if __name__=='__main__':
    refs={}
    with zipfile.ZipFile('../downloads/LF2-Starterkit.zip') as z:
        for name in ['LF2v1.9.exe','LF2v1.9c.exe']:
            refs[name]=z.read('---------/LF2/'+name)
    refs['LF2v2.0a.exe']=read_resource('../downloads/LF2_v2.0a.exe','lf2.exe')
    inputs={name:embedded_program('../games/'+name+'/LF2_'+name+'.exe',program)
            for name,program in [('Kate','Kate-LF2.exe'),('Reinforced','lf2.exe')]}
    inputs['Bleach']=Path('../games/Bleach-static-recovery-2026-10-28/BBR 2.0a_unpacked.exe').read_bytes()
    report={'scope':'Static section bytes only; equality does not prove full runtime compatibility. No EXE/DLL executed.',
            'comparisons':{name:{ref:compare(data,base) for ref,base in refs.items()} for name,data in inputs.items()}}
    Path('validation/pack-compatibility-2026-10-29/executable-sections.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,comparisons in report['comparisons'].items():
        for ref,rows in comparisons.items():
            print(name,ref,'text identical',rows['.text']['identical'],'text differences',rows['.text']['different_overlapping_bytes'])
