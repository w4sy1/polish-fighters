"""Warm up each authored DBZ arena mode with its real scene objects."""
import concurrent.futures,hashlib,json
from pathlib import Path
import audit_maps_adventures as audit
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    audit.OUT=ROOT/'validation/remaining-mechanics-2026-10-30/dbz-modes'
    binary=ROOT/'engine/out/PolishFighters-remaining-2026-10-30/openlf2.exe'
    scenes=json.loads((ROOT/'content-packs/dbz/scene-modes.json').read_text())['scenes']
    targets=[(scene['row'],index,mode['name']) for scene in scenes.values() for index,mode in enumerate(scene['modes'])]
    def run(target):
        row,index,name=target
        result=audit.probe('dbz','mode',str(row)+'-'+str(index),row,engine=binary,scene_mode=index)
        result['mode']=index;result['mode_name']=name
        result['pass']=result['pass'] and result['proof'].get('scene_mode')==name
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=[]
        for result in pool.map(run,targets):
            results.append(result);print(result['key'],result['mode_name'],'PASS' if result['pass'] else 'FAIL',flush=True)
    (audit.OUT/'summary.json').write_text(json.dumps({'scope':'120 rendered headless frames per authored mode; not visual parity or complete quest/campaign behavior.','binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'tests':results},indent=2)+'\n')
