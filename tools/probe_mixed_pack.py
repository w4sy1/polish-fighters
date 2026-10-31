"""Run mixed-roster selection and eight-source combat in the actual native engine."""
import json
import os
import subprocess
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/mixed-2026-10-31'
BINARY=OUT/'runner/LittleFighters.exe'
def run(name,trace,fixture=None,capture=False,render=False):
 folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
 cmd=[str(BINARY),'--installer',str(ROOT/'../downloads/LF2_v2.0a.exe'),
      '--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'content-packs/polish-originals'),
      '--mod',str(ROOT/'content-packs/mixed-all'),'--config-dir',str(folder/'config'),
      '--seed','42','--hub-menu','--input-trace',trace]
 if fixture:cmd+=['--mod',str(fixture)]
 env=dict(os.environ)
 if capture:
  env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
  cmd+=['--renderer','software','--capture-frame',str(folder/'frame.bmp')]
  if render:cmd+=['--render-trace']
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=120,env=env)
 log=result.stdout+result.stderr;(folder/'run.log').write_text(log,encoding='utf8')
 assert result.returncode==0,(name,result.returncode,log[-3000:])
 return log

if __name__=='__main__':
 BINARY.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/'engine/build/windows/x64/native/Release/openlf2.exe',BINARY)
 for dll in (ROOT/'engine/out/LittleFighters-pack-ai-2026-10-31').glob('*.dll'):shutil.copy2(dll,BINARY.parent/dll.name)
 run('menu','*2',capture=True)
 run('selection','@600_286!,@600_286,*8',capture=True)
 fixture=OUT/'fixture';fixture.mkdir(exist_ok=True)
 (fixture/'package.manifest').write_text('id=mixed-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=mixed-all@1\nextend=base/ui/flow|flow.lua\n')
 (fixture/'flow.lua').write_text('''return function(base)
 local update,describe=base.update,base.describe
 local packs={'polish-originals','lf4-turbo','dbz','one-piece','kate','reinforced','ntsd','bleach'}
 function base.update(s,input,context)
  if not s.mixed_probe then
   s.mixed_probe=true
   local catalog=require('base/game/catalog');local fighters=catalog.load();local slots={}
   for slot,pack in ipairs(packs) do
    local selected
    for row,fighter in ipairs(fighters) do
     if (pack=='polish-originals' and fighter.id==410) or
       (fighter.pack==pack and catalog.selectable(fighter) and not fighter.name:lower():find('template',1,true)) then
      selected=row;break
     end
    end
    assert(selected,'no fighter for '..pack)
    slots[slot-1]={kind='human',fighter=selected,team=slot%2+1}
   end
   s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,
     fighters=fighters,backgrounds=catalog.backgrounds(),slots=slots})
   s.active='match';s.wait_release=nil
   for slot=0,7 do local v=s.match.match.items[slot];v.x=70+slot*90;v.x_int=v.x;v.z=400;v.z_int=400 end
  end
  return update(s,input,context)
 end
 function base.describe(s)
  return describe(s)..' mixed_digest='..require('polish-fighters/sync_state').digest(s)
 end
 return base
end
''')
 logs=[run('fight-'+str(n),'c/c/c/c/c/c/c/c*15,*30,r/l/r/l/r/l/r/l*40,c/c/c/c/c/c/c/c*25,*190',fixture,capture=True) for n in range(2)]
 # Capture advertises text rendering; digest excludes local presentation fields.
 import re
 digests=[re.search('mixed_digest=([a-f0-9]{64})',log)[1] for log in logs]
 assert digests[0]==digests[1],digests
 # Exercise a DBZ scene from the mixed namespace, including remapped global opoints.
 source=(fixture/'flow.lua').read_text()
 source=source.replace("s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,",
   "local bgrow;for row,entry in ipairs(catalog.backgrounds()) do if entry.path:match('^mods/mixed%-all/2/') then bgrow=row-1;break end end;assert(bgrow);s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=bgrow,")
 map_fixture=OUT/'map-fixture';map_fixture.mkdir(exist_ok=True)
 shutil.copy2(fixture/'package.manifest',map_fixture/'package.manifest')
 (map_fixture/'flow.lua').write_text(source)
 run('dbz-map','*5',map_fixture,True)
 all_maps=OUT/'all-maps-fixture';all_maps.mkdir(exist_ok=True)
 shutil.copy2(fixture/'package.manifest',all_maps/'package.manifest')
 (all_maps/'flow.lua').write_text('''return function(base)
 local update,describe=base.update,base.describe
 local counter=0;local tested={}
 function base.update(s,input,context)
  local catalog=require('base/game/catalog');local maps=catalog.backgrounds()
  local index=math.floor(counter/4)+1
  if index<=#maps and counter%4==0 then
   s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=index-1,
     fighters={{id=0,path='data/deep.dat',name='QA Deep'}},backgrounds=maps,
     slots={[0]={kind='human',fighter=1,team=1}}})
   assert(s.match.match.background_row==index-1,'map selector collision')
   s.active='match';s.wait_release=nil;tested[index]=true
  end
  counter=counter+1
  return update(s,input,context)
 end
 function base.describe(s)
  assert(#tested==#require('base/game/catalog').backgrounds(),'not all maps reached')
  return describe(s)..' mixed_maps='..#tested
 end
 return base
end
''')
 map_count=json.loads((ROOT/'content-packs/mixed-all/build-report.json').read_text())['maps']
 map_log=run('all-maps','*'+str(map_count*4),all_maps,True,True)
 assert 'mixed_maps='+str(map_count) in map_log
 summary={'pass':True,'frames':300,'sources':8,'digests':digests,'maps_rendered':map_count,
  'scope':'short mixed combat and 4 SDL software frames per map; not exhaustive moves or campaign completion'}
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary))
