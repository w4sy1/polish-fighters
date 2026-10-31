"""Materialize only overflowing NTSD integer literals as consumed by its x86 VC80 CRT.
Uses our own probe and the installed Microsoft CRT, never original game code.
"""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from import_legacy import decode,encode
ROOT=Path(__file__).resolve().parents[1]
FIELD=re.compile(r'\b([A-Za-z_]+):\s*(-?\d+)(?![\w.])')

def normalize(text,values):
    evidence=[]
    def change(match):
        value=int(match[2])
        if -2147483648<=value<=2147483647:return match[0]
        converted=values[match[2]]
        if not -2147483648<=converted<=2147483647:raise ValueError('Invalid CRT result')
        evidence.append({'line':text.count('\n',0,match.start())+1,'field':match[1],'literal':match[2],'crt_value':converted})
        return match[0][:-len(match[2])]+str(converted)
    result=FIELD.sub(change,text)
    return result,evidence

if __name__=='__main__':
    pack=ROOT/'content-packs/ntsd';sources={p:decode(p.read_bytes()) for p in (pack/'assets').rglob('*.dat')}
    tokens=sorted({m[2] for text in sources.values() for m in FIELD.finditer(text) if not -2147483648<=int(m[2])<=2147483647})
    if not tokens:raise ValueError('No overflows; preserve existing normalization evidence')
    probe=ROOT/'engine/build/vc80-probe/vc80-scan-probe.exe'
    output=subprocess.run([str(probe)],input='\n'.join(tokens)+'\n',capture_output=True,text=True,check=True)
    values={}
    for line in output.stdout.splitlines():
        original,converted,value=line.split();assert converted=='1';values[original]=int(value)
    assert set(values)==set(tokens)
    backup=ROOT/'../baseline-remaining-mechanics-2026-10-30/content-packs/ntsd'
    results=[]
    for path,text in sources.items():
        result,evidence=normalize(text,values)
        if not evidence:continue
        raw=path.read_bytes();copy=backup/path.relative_to(pack);copy.parent.mkdir(parents=True,exist_ok=True)
        if copy.exists():raise ValueError('Backup exists; do not overwrite')
        shutil.copy2(path,copy);encoded=encode(result,raw);assert encoded[:123]==raw[:123]
        path.write_bytes(encoded)
        results.append({'asset':path.relative_to(pack).as_posix(),'before_sha256':hashlib.sha256(raw).hexdigest(),
                        'after_sha256':hashlib.sha256(encoded).hexdigest(),'fields':evidence})
    proof={'scope':'Exact observed x86 Microsoft VC80 sscanf %d conversion; not clamping/guessing values',
           'crt':'Installed Windows MSVCR80.dll 8.0.50727.9680, x86','original_game_import':'MSVCR80.dll sscanf/fscanf',
           'probe_source':'tests/vc80_scan_probe.cpp','probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),
           'unique_tokens':values,'files':results,'field_count':sum(len(x['fields']) for x in results)}
    (pack/'vc80-integer-normalization.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('Normalized',proof['field_count'],'literals in',len(results),'DATs using actual x86 VC80 results')
