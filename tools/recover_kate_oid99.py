"""Recover the exact oid99 actor from Kate author's V1.00 Ver2 data, additively.
Keeps existing catalog order and every original source file. No EXE is executed.
"""
import hashlib
import json
import re
from pathlib import Path
from import_legacy import RESOURCE,canonical,decode,encode

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE_SHA='e71fdc5332eb88b2eb9dd5414909cb84c8809c84957e59c076ff4af2d88ab7b8'
def recover(reference,package):
    reference=Path(reference).resolve();package=Path(package).resolve()
    files={canonical(p.relative_to(reference).as_posix()):p for p in reference.rglob('*') if p.is_file() and re.fullmatch(r'[A-Za-z0-9_./\\-]+',p.relative_to(reference).as_posix())}
    catalog=files['data/data.txt'].read_text(encoding='latin1')
    match=re.search(r'id:\s*99\s+type:\s*(\d+)\s+file:\s*(\S+)',catalog)
    if not match or match[1]!='0':raise ValueError('Author catalog lacks expected character oid99')
    source=canonical(match[2]);text=decode(files[source].read_bytes())
    if not all(re.search(r'<frame>\s*'+str(action)+r'\b',text) for action in [390,392]):raise ValueError('Missing required original actions')
    manifest=package/'package.manifest';before=manifest.read_text();assets={v:package/r for v,r in [line[6:].split('|',1) for line in before.splitlines() if line.startswith('asset=')]}
    target=next(p for p in assets.values() if p.suffix=='.txt');current=target.read_text(encoding='latin1')
    if re.search(r'id:\s*99\s+type:',current):raise ValueError('oid99 already present; do not overwrite')
    current_ids=set(map(int,re.findall(r'id:\s*(\d+)\s+type:',current)))
    missing={int(i) for i in re.findall(r'oid:\s*(\d+)',text) if int(i)>0 and int(i) not in current_ids}
    if missing:raise ValueError('Actor requires additional missing object IDs: '+str(missing))
    staged={};aliases={};evidence=[]
    def register(path):
        key=canonical(path)
        if key in staged:return aliases[key]
        virtual='mods/kate/r99/'+str(len(staged)).zfill(4)+Path(key).suffix
        aliases[key]=virtual
        original=files[key].read_bytes();staged[key]=None
        converted=encode(RESOURCE.sub(lambda m:register(m[0]),decode(original)),original) if key.endswith('.dat') else original
        staged[key]=converted
        evidence.append({'source':key,'source_sha256':hashlib.sha256(original).hexdigest(),'output_sha256':hashlib.sha256(converted).hexdigest()})
        return virtual
    virtual=register(source)
    for key,blob in staged.items():
        dest=package/'assets'/aliases[key].removeprefix('mods/kate/')
        if dest.exists():raise ValueError('Recovery output already exists')
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob)
    manifest.write_text(before+''.join('asset='+aliases[key]+'|assets/'+aliases[key].removeprefix('mods/kate/')+'\n' for key in sorted(staged)))
    target.write_text(current.replace('<object_end>','id: 99 type: 0 file: '+virtual+'\n<object_end>'),encoding='latin1')
    proof={'archive_sha256':ARCHIVE_SHA,'author_page':'https://hcyang1227.blogspot.com/2019/11/lf2-kate.html',
           'version':'Author V1.00, LF2_Kate_Ver2','id':99,'kind':0,'actions':[390,392],'assets':evidence,
           'existing_record_indices_preserved':True,'scope':'Exact authored dependency recovery; cross-version full compatibility unverified'}
    (package/'recovered-oid99.json').write_text(json.dumps(proof,indent=2)+'\n')
    return proof
if __name__=='__main__':
    archive=ROOT/'../downloads/Kate-author-v1.00-reference.exe'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA:raise ValueError('Unexpected author archive')
    reference=next(p.parent for p in (ROOT/'../games/Kate-author-reference-2026-10-30').rglob('data') if p.parent.name=='LF2_Kate_Ver2')
    result=recover(reference,ROOT/'content-packs/kate');print('Recovered oid99 with',len(result['assets']),'original assets')
