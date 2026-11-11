"""Own Windows engine checks: real input matches and explicitly scripted skill probes."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from probe_native_packs import ROOT, TRACE, probe

PACK=ROOT/'content-packs/polish-originals'
OUT=ROOT/'validation/polish-originals-2026-10-30'
PORTABLE=ROOT/'engine/out/PolishFighters-originals-2026-10-31'

def skills(id_, frames=900):
    layout=json.loads((PACK/'layout.json').read_text())
    dimensions='{'+','.join('["mods/polish-originals/'+key+'.png"]={'+str(info['width'])+','+str(info['height'])+'}' for key,info in layout.items())+'}'
    folder=OUT/'skills'/str(id_);override=folder/'override';override.mkdir(parents=True,exist_ok=True)
    (override/'package.manifest').write_text('id=originals-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=polish-originals@1\nreplace=polish-fighters/settings|settings.lua\nextend=base/game/ai|stationary.lua\nextend=base/ui/match_screen|probe.lua\n')
    # Controlled skill targets must not interrupt the human between enter_frame and
    # before_advance. Actual AI combat is covered separately by real-input probes.
    (override/'stationary.lua').write_text('''return function(base)
 function base.control(state,index)
  local v=state.items[index]
  for _,key in ipairs({'up','down','left','right','attack','jump','defend'}) do
   v.previous_keys[key]=v.keys[key];v.keys[key]=false
  end
 end
 return base
end
''')
    (override/'settings.lua').write_text(f'return {{allowed_ids={{{id_}}},allow_hidden=true}}\n')
    lua='''return function(base)
 local create,update,draw=base.create,base.update,base.draw
 local enter=require('base/game/control').enter_frame
 local seen,casts,invalid,scaled={},{},{},0
 local dimensions=DIMENSIONS
 local target_id=TARGET_ID
 function base.create(options)
  local state=create(options)
  assert(state.match.items[0].record.id==target_id)
  state.match.items[0].team=1
  for index,value in pairs(state.match.items) do
   if index~=0 and value.record.kind==0 then value.team=2 end
  end
  return state
 end
 local function place(value,x,z)
  value.x,value.x_int,value.y,value.y_int,value.z,value.z_int=x,x,0,0,z,z
  value.vx,value.vy,value.vz=0,0,0
 end
 function base.update(state,held,context)
  local current=state.match
  local n=current.frame_number
  local human=current.items[0]
  if n>=20 and n<=620 and (n-20)%100==0 then
   local frame=300+math.floor((n-20)/100)*10
   human.hp,human.dark_hp,human.mp=human.max_hp,human.max_hp,500
   human.blink,human.hit_lag,human.wait_counter=0,0,0
   local z=math.floor((current.stage.zboundary[1]+current.stage.zboundary[2])/2)
   place(human,100,z)
   for index,value in pairs(current.items) do
    if value.record.kind==0 and value.team==2 then
     value.hp,value.dark_hp,value.max_hp=5000,5000,5000
     place(value,250,z)
    end
   end
   enter(current,human,frame);assert(human.frame==frame,'skill entry rejected')
   casts[tostring(frame)]=true
  end
  if n==720 and target_id==413 then human.hp=700 end
  update(state,held,context)
  for _,value in pairs(current.items) do
   seen[tostring(value.record.id)]=true
   if not value.record.frames[value.frame] then invalid[tostring(value.record.id)..':'..value.frame]=true end
  end
 end
 function base.draw(state,context,bounds)
  local original=context.scaled_sprite
  context.scaled_sprite=function(resource,rect,x,y,w,h,...)
   local size=dimensions[resource]
   if size then assert(rect[1]>=0 and rect[2]>=0 and rect[1]+rect[3]<=size[1] and rect[2]+rect[4]<=size[2]) end
   assert(w>0 and h>0 and x==math.floor(x) and y==math.floor(y))
   scaled=scaled+1
   return original(resource,rect,x,y,w,h,...)
  end
  draw(state,context,bounds);context.scaled_sprite=original
  if state.match.frame_number==900 then
   local doc=engine.read_settings() or {}
   doc.originals_probe={id=target_id,frame=900,casts=casts,seen=seen,events=state.match.pf_events,
    invalid_frames=invalid,scaled_draws=scaled,phase2=state.match.items[0].pf_phase2 or false,final_record=state.match.items[0].record.id}
   assert(engine.write_settings(doc))
  end
 end
 return base
end
'''.replace('TARGET_ID',str(id_)).replace('DIMENSIONS',dimensions).replace('==900', '=='+str(frames)).replace('frame=900', 'frame='+str(frames))
    (override/'probe.lua').write_text(lua)
    command=[str(PORTABLE/'openlf2.exe'),'--installer',str(PORTABLE/'LF2_v2.0a.exe'),'--scripts',str(ROOT/'engine/scripts'),
      '--mod',str(ROOT/'engine/scripts/polish-fighters'),'--mod',str(PACK),'--mod',str(override),
      '--seed','42','--input-trace',TRACE.rsplit('*300',1)[0]+'*'+str(frames+1),'--config-dir',str(folder/'config')]
    result=subprocess.run(command,capture_output=True,text=True,timeout=40)
    (folder/'run.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    settings=folder/'config/config.json'
    evidence=json.loads(settings.read_text()).get('originals_probe',{}) if settings.exists() else {}
    events=evidence.get('events',{})
    passed=result.returncode==0 and evidence.get('frame')==frames and len(evidence.get('casts',{}))==7
    passed=passed and not evidence.get('invalid_frames') and evidence.get('scaled_draws',0)>0
    passed=passed and all(events.get(f'skill_{id_}_{frame}',0)>0 for frame in range(300,361,10))
    if id_ in [410,411]: passed=passed and events.get('clones',0)>0
    if id_==412: passed=passed and events.get('spawn_421',0)>=8 and events.get('spawn_422',0)>0
    if id_==413: passed=passed and evidence.get('phase2') and events.get('boss_toilets',0)>0 and events.get('boss_ultimate_charge',0)>0
    return {'id':id_,'pass':bool(passed),'exit_code':result.returncode,'evidence':evidence}

def render():
    layout=json.loads((PACK/'layout.json').read_text());lines=[]
    for n,(key,info) in enumerate(layout.items()):
        for col,row in enumerate(range(8)):
            rect=info['rectangles'][row*8];w,h=int(rect[2]*info['scale']),int(rect[3]*info['scale'])
            for flip in [0,1]:
                values=[f'mods/polish-originals/{key}.png',*rect,col*145+int(70-w/2),n*175+flip*77+78-h,w,h,flip]
                lines.append(' '.join(map(str,values)))
    commands=OUT/'render-commands.txt';commands.write_text('\n'.join(lines))
    env=dict(os.environ);env['PATH']=str(PORTABLE)+os.pathsep+env['PATH']
    binary=ROOT/'engine/build/windows/x64/native/Release/openlf2_sprite_probe.exe'
    result=subprocess.run([str(binary),str(ROOT),str(commands),str(OUT/'render.bmp')],env=env,capture_output=True,text=True,timeout=20)
    (OUT/'render.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stderr

def main():
    shutil.copytree(ROOT/'engine/scripts',PORTABLE/'scripts',dirs_exist_ok=True)
    shutil.copytree(PACK,PORTABLE/'content-packs/polish-originals',dirs_exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        real=list(pool.map(lambda id_:probe('polish-originals',id_,OUT/'native',runs=2,geometry=True,combat=True,binary=PORTABLE/'openlf2.exe'),range(410,414)))
        scripted=list(pool.map(skills,range(410,414)))
    render()
    result={'scope':'900-frame real input matches twice per fighter; controlled native skill entry probes separately; SDL software sprite render',
      'binary_sha256':hashlib.sha256((PORTABLE/'openlf2.exe').read_bytes()).hexdigest(),
      'real_input':real,'controlled_skills':scripted,'pass':all(x['pass'] for x in real+scripted)}
    (OUT/'native-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'real_input':[(x['fighter'],x['pass']) for x in real],
       'controlled_skills':[(x['id'],x['pass']) for x in scripted],'pass':result['pass']},indent=2))
    if not result['pass']: raise SystemExit(1)

if __name__=='__main__':main()
