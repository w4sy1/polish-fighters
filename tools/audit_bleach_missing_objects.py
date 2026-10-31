"""Keep missing BBR targets explicit; action coincidence is not object provenance."""
import hashlib,json,re
from pathlib import Path
from import_legacy import decode,canonical
ROOT=Path(__file__).resolve().parents[1]
def main():
    source=ROOT/'../games/Bleach-static-recovery-2026-10-28/data-files'
    raw=(source/'data/data.txt').read_bytes();catalog=raw.decode('latin1')
    records={int(i):canonical(p) for i,p in re.findall(r'id:\s*(\d+)\s+type:\s*\d+\s+file:\s*(\S+)',catalog)}
    files={canonical(p.relative_to(source).as_posix()):p for p in source.rglob('*.dat')}
    decoded={name:decode(p.read_bytes()) for name,p in files.items()}
    results=[]
    for oid,action in ((284,83),(151,30)):
        references=[]
        for name,text in decoded.items():
            for frame,body in re.findall(r'<frame>\s*(\d+)(.*?)<frame_end>',text,re.S):
                for point in re.findall(r'\bopoint:(.*?)opoint_end:',body,re.S):
                    if re.search(r'\boid:\s*'+str(oid)+r'\b',point):
                        references.append({'source':name,'frame':int(frame),'opoint':point.strip()})
        candidates=[{'source':name,'registered_ids':[i for i,p in records.items() if p==name],
                     'sha256':hashlib.sha256(files[name].read_bytes()).hexdigest()}
                    for name,text in decoded.items() if re.search(r'<frame>\s*'+str(action)+r'\s',text)]
        assert oid not in records
        results.append({'oid':oid,'action':action,'status':'unresolved: original catalog has no target; candidates do not establish intended identity',
                        'references':references,'action_candidates':candidates})
    report={'catalog_sha256':hashlib.sha256(raw).hexdigest(),'source_dat_count':len(files),'targets':results,
            'base_weapon3_frames':list(map(int,re.findall(r'<frame>\s*(\d+)',decoded['data/weapon3.dat']))),
            'author_older_versions':'https://bleachbankaibr.webnode.page/download/versoes-anteriores/',
            'older_2_0_final_link':'https://www.4shared.com/file/183420377/13a11930/BleachBankaiRevolution20_final.html',
            'older_2_0_mirror':'https://uploadmirrors.com/download/ADRFWVLI/BleachBankaiRevolution2.0_final.rar',
            'recovery_performed':False,'reason':'No authenticated original catalog/object mapping recovered; no substitute or fabricated action added.'}
    (ROOT/'content-packs/bleach/missing-object-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print([(r['oid'],len(r['references']),len(r['action_candidates'])) for r in results])
if __name__=='__main__':main()
