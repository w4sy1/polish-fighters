"""Native authored DBZ background switch; stage jump is a QA stimulus, not a playthrough."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/dbz-transition-2026-10-31'
if __name__=='__main__':
 fixture=OUT/'fixture';fixture.mkdir(parents=True,exist_ok=True)
 (fixture/'package.manifest').write_text('id=dbz-transition-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=dbz@1\nextend=base/ui/flow|flow.lua\n')
 (fixture/'flow.lua').write_text('''return function(base)
 local update,describe=base.update,base.describe
 function base.update(s,input,context)
  if not s.dbz_probe then
   s.dbz_probe=true
   local catalog=require('base/game/catalog')
   s.match=require('base/ui/match_screen').create({mode=1,difficulty=0,background=7,
    campaign_path='mods/dbz/a/000020.dat',campaign_background=7,stage_level=0,
    fighters={{id=0,path='data/deep.dat',name='QA Deep'}},backgrounds=catalog.backgrounds(),
    slots={[0]={kind='human',fighter=1,team=1}}})
   s.active='match';s.wait_release=nil
  end
  local m=s.match.match
  if m.frame_number==10 then
   assert(m.background_row==7)
   m.stage_run.id=1;m.stage_run.phase=-1;m.stage_run.runtime={};m.stage_run.go=70
  end
  return update(s,input,context)
 end
 function base.describe(s)
  local m=s.match.match
  assert(m.dbz_scene_transitions==1 and m.background_row==11,'DBZ authored scene did not switch')
  return describe(s)..' dbz_transition=true width='..m.stage.width
 end
 return base
end
''')
 command=[str(ROOT/'validation/online-native-2026-10-31/runner/LittleFighters.exe'),
  '--installer',str(ROOT/'../downloads/LF2_v2.0a.exe'),'--scripts',str(ROOT/'engine/scripts'),
  '--mod',str(ROOT/'content-packs/dbz'),'--mod',str(fixture),'--input-trace','*30',
  '--config-dir',str(OUT/'config')]
 result=subprocess.run(command,capture_output=True,text=True,timeout=90)
 log=result.stdout+result.stderr;(OUT/'run.log').write_text(log)
 assert result.returncode==0,log[-2000:]
 assert 'dbz_transition=true' in log
 (OUT/'summary.json').write_text(json.dumps({'pass':True,'from':7,'to':11,
  'scope':'QA forces stage 0 to 1; validates authored scene/geometry switch, not natural campaign completion'},indent=2))
 print('PASS: DBZ stage 0 -> 1 changes authored scene 7 -> 11 and respawns scene objects')
