"""Native diagnostic: execute the actual two formerly broken Treature opoints.
Starts source frames directly in an isolated QA package; not a natural-input test.
"""
import json
import subprocess
from pathlib import Path
from probe_native_packs import ROOT,TRACE

def probe(frame):
    folder=ROOT/'validation/maps-build-2026-10-30/kate-oid99'/str(frame);override=folder/'qa';override.mkdir(parents=True,exist_ok=True)
    (override/'package.manifest').write_text('id=kate-recovery-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=kate@1\nreplace=polish-fighters/settings|settings.lua\nextend=base/ui/match_screen|probe.lua\n')
    (override/'settings.lua').write_text('return {allowed_ids={30},allow_hidden=true}\n')
    (override/'probe.lua').write_text('''return function(base)
 local create=base.create
 local objects=require('base/game/objects')
 function base.create(options)
  local state=create(options)
  local parent=objects.place(state.match,50,300)
  parent.frame='''+str(frame)+''';parent.wait_counter=0;parent.hit_lag=0
  local source=parent.record.frame(parent.frame).opoint
  assert(source.oid==99)
  assert(objects.spawn_from_frame(state.match,50,parent))
  local found=false
  for _,entry in pairs(state.match.items) do
   if entry.record.id==99 then
    assert(entry.frame==source.action and not entry.record.frame(entry.frame).undefined)
    found=true
   end
  end
  assert(found,'Recovered actor did not spawn')
  local doc=engine.read_settings() or {}
  doc.kate_recovery={source_frame=parent.frame,target=99,action=source.action,spawned=true}
  assert(engine.write_settings(doc))
  return state
 end
 return base
end
''')
    binary=ROOT/'engine/out/PolishFighters-2026-10-30/openlf2.exe'
    command=[str(binary),'--installer',str(ROOT/'../downloads/LF2_v2.0a.exe'),'--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'engine/scripts/polish-fighters'),'--mod',str(ROOT/'content-packs/kate'),'--mod',str(override),'--seed','42','--config-dir',str(folder/'config'),'--input-trace',TRACE]
    result=subprocess.run(command,capture_output=True,text=True,timeout=45)
    log=result.stdout+result.stderr;(folder/'native.log').write_text(log)
    config=folder/'config/config.json';proof=json.loads(config.read_text()).get('kate_recovery') if config.exists() else None
    row={'source_frame':frame,'exit_code':result.returncode,'proof':proof,'pass':result.returncode==0 and proof is not None and proof.get('spawned') and 'screen=match frame=300' in log}
    (folder/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    return row
if __name__=='__main__':
    results=[probe(frame) for frame in [174,180]]
    (ROOT/'validation/maps-build-2026-10-30/kate-oid99/summary.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
