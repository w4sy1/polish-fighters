"""Check real menu coordinates, in-process package reload, saved bindings and SZ's basic shot."""
import hashlib
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from probe_native_packs import ROOT, TRACE, probe

OUT=ROOT/'validation/hub-controls-2026-10-31'
PORTABLE=ROOT/'engine/out/LittleFighters-hub-2026-10-31'

def run(name,trace,extra=(),capture=False,config=None):
    directory=OUT/name;directory.mkdir(parents=True,exist_ok=True)
    config=config or directory/'config'
    command=[str(PORTABLE/'LittleFighters.exe'),'--scripts',str(PORTABLE/'scripts'),
        '--mod',str(PORTABLE/'content-packs/polish-originals'),'--config-dir',str(config),
        '--seed','42','--input-trace',trace,*extra]
    env=dict(os.environ)
    if capture:
        env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
        command+=['--renderer','software','--capture-frame',str(directory/'frame.bmp')]
    result=subprocess.run(command,capture_output=True,text=True,env=env,timeout=60)
    log=result.stdout+result.stderr;(directory/'run.log').write_text(log,encoding='utf-8')
    assert result.returncode==0,(name,result.returncode,log[-2500:])
    return log,config

def click(x,y): return f'@{x}_{y}!,@{x}_{y}'

def visual_fixtures():
    override=OUT/'portraits/override';override.mkdir(parents=True,exist_ok=True)
    (override/'package.manifest').write_text('id=portrait-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=polish-originals@1\nextend=base/ui/character_select|portraits.lua\n')
    (override/'portraits.lua').write_text('''return function(base)
 local create=base.create
 function base.create(options)
  local state=create(options)
  for slot,id in ipairs({410,411,412,413,1}) do
   for row,fighter in ipairs(state.fighters) do
    if fighter.id==id then state.slots[slot-1].fighter=row;state.slots[slot-1].phase=1 end
   end
  end
  return state
 end
 return base
end
''')
    run('portraits',click(600,286)+',*2',['--hub-menu','--mod',str(override)],True)
    override=OUT/'lineup/override';override.mkdir(parents=True,exist_ok=True)
    (override/'package.manifest').write_text('id=lineup-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=polish-originals@1\nreplace=polish-fighters/settings|settings.lua\nextend=base/ui/match_screen|lineup.lua\n')
    (override/'settings.lua').write_text('return {allowed_ids={411},allow_hidden=true}\n')
    (override/'lineup.lua').write_text('''return function(base)
 local create,update=base.create,base.update
 local objects=require('base/game/objects')
 function base.create(options)
  local state=create(options)
  state.match.items[11].record=objects.record(state.match,1)
  objects.place(state.match,12,410);objects.place(state.match,13,412);objects.place(state.match,14,413)
  return state
 end
 function base.update(state,held,context)
  for n,slot in ipairs({0,11,12,13,14}) do
   local v=state.match.items[slot]
   v.x,v.x_int=80+(n-1)*150,80+(n-1)*150
   v.y,v.y_int,v.z,v.z_int=0,0,450,450
   v.vx,v.vy,v.vz,v.blink,v.frame,v.mp,v.team=0,0,0,0,0,0,n
  end
  update(state,held,context)
 end
 return base
end
''')
    run('lineup',TRACE.rsplit('*300',1)[0]+'*3',['--mod',str(override)],True)

def main():
    OUT.mkdir(exist_ok=True)
    binary=ROOT/'engine/build/windows/x64/native/Release/openlf2.exe'
    for name in ['openlf2.exe','LittleFighters.exe']:shutil.copy2(binary,PORTABLE/name)
    shutil.copytree(ROOT/'engine/scripts',PORTABLE/'scripts',dirs_exist_ok=True)
    shutil.copytree(ROOT/'content-packs/polish-originals',PORTABLE/'content-packs/polish-originals',dirs_exist_ok=True)
    log,_=run('main','*2',['--hub-menu'],True)
    assert 'hub=true:root' in log
    log,_=run('options',click(600,250)+',*2',['--hub-menu'],True)
    assert 'launch_page=options' in log
    log,_=run('recording',click(600,398)+',*2',['--hub-menu'],True)
    assert 'launch_page=recording' in log
    log,_=run('classic-controls',click(600,212)+','+click(620,414)+',*2',['--hub-menu'],True)
    assert 'launch_page=controls' in log
    log,_=run('held-switch','@220_250!*3,@220_250,*2',['--hub-menu'])
    assert 'Profile loaded: lf2-classic' in log and 'hub=true:profile' in log and 'screen=characters' not in log
    profiles=['polish-originals','lf2-classic','lf4-turbo','dbz','one-piece','kate','reinforced','ntsd','bleach']
    def profile_case(pair):
        n,profile=pair
        column,row=divmod(n-1,9)
        log,_=run('profile-'+profile,click(220+column*385,175+row*37)+',*2',['--hub-menu'])
        assert 'hub=true:profile' in log,(profile,log)
        if profile!='polish-originals': assert 'Profile loaded: '+profile in log
        return {'profile':profile,'pass':True}
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(profile_case,enumerate(profiles,2)))
    config=OUT/'input/config';config.mkdir(parents=True,exist_ok=True)
    (config/'config.json').write_text(json.dumps({'marker':'preserve-me'}))
    controls=click(600,212)
    configure=controls+','+click(620,285)+','+click(620,371)
    log,_=run('input',configure+',*2',['--hub-menu'],True,config)
    assert 'input_settings=true' in log
    run('save-input',configure+','+click(300,495)+',*2',['--hub-menu'],config=config)
    settings=json.loads((config/'config.json').read_text())
    player=settings['controls']['players'][0]
    assert player['mouse_mode'] and player['attack']==1 and player['defend']==2 and player['jump']==32
    assert settings['marker']=='preserve-me'
    # Reopen the real screen and capture a physical virtual-key assignment.
    remap=controls+','+click(230,330)+',#70,*1,'+click(300,495)+',*2'
    run('remap',remap,['--hub-menu'],config=config)
    assert json.loads((config/'config.json').read_text())['controls']['players'][0]['attack']==70
    # Restore mouse attack for the subsequent gameplay probe.
    run('restore-mouse',configure+','+click(300,495),['--hub-menu'],config=config)
    override=OUT/'basic-shot/override';override.mkdir(parents=True,exist_ok=True)
    (override/'package.manifest').write_text('id=basic-shot-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=polish-originals@1\nreplace=polish-fighters/settings|settings.lua\nextend=base/ui/match_screen|probe.lua\n')
    (override/'settings.lua').write_text('return {allowed_ids={411},allow_hidden=true}\n')
    (override/'probe.lua').write_text('''return function(base)
 local create,update,draw=base.create,base.update,base.draw
 local objects=require('base/game/objects')
 function base.create(options)
  local state=create(options)
  assert(state.match.items[0].record.id==411)
  local human=state.match.items[0];human.team=1;human.blink=0
  local target=state.match.items[11];target.record=objects.record(state.match,1);target.team=2
  target.hp,target.dark_hp,target.max_hp=5000,5000,5000
  return state
 end
 function base.update(state,held,context)
  local human,target=state.match.items[0],state.match.items[11]
  if state.match.frame_number<120 then
   target.x,target.x_int=human.x+180,math.floor(human.x+180)
   target.y,target.y_int,target.z,target.z_int=0,0,human.z,human.z_int
   target.vx,target.vy,target.vz,target.blink,target.frame,target.mp=0,0,0,0,0,0
   human.facing=0
  end
  update(state,held,context)
 end
 function base.draw(state,context,bounds)
  draw(state,context,bounds)
  if state.match.frame_number>=75 then
   local h=state.match.items[0];local doc=engine.read_settings() or {}
   doc.basic_shot={shots=h.pf_basic_shots or 0,damage=h.damage_dealt,mp_spent=h.mp_spent,frame=state.match.frame_number}
   assert(engine.write_settings(doc))
  end
 end
 return base
end
''')
    prefix=TRACE.rsplit('*300',1)[0]
    log,_=run('basic-shot',prefix+'*70,#1,*40',['--mod',str(override)],config=config)
    evidence=json.loads((config/'config.json').read_text())['basic_shot']
    assert evidence['shots']>0 and evidence['damage']>0 and evidence['mp_spent']==0,evidence
    run('shot-visual',prefix+'*70,#1,*6',['--mod',str(override)],True,config)
    # Actual new control screen, controller capture waits for release before accepting button 5.
    pad_config=OUT/'pad/config'
    pad_trace=controls+','+click(220,156)+','+click(220,156)+','+click(230,330)+',*1,$15,*1,'+click(300,495)+',*2'
    run('pad',pad_trace,['--hub-menu'],True,pad_config)
    pad=json.loads((pad_config/'config.json').read_text())['controls']['players'][0]
    assert pad['device']==1 and pad['buttons'][0]==5,pad
    visual_fixtures()
    with ThreadPoolExecutor(max_workers=2) as pool:
        fights=list(pool.map(lambda id_:probe('polish-originals',id_,OUT/'fighters',runs=2,geometry=True,combat=True,
          binary=PORTABLE/'LittleFighters.exe',scripts=PORTABLE/'scripts',content_root=PORTABLE/'content-packs'),range(410,414)))
    assert all(row['pass'] for row in fights)
    import probe_polish_originals as skills_probe
    skills_probe.PORTABLE=PORTABLE;skills_probe.OUT=OUT/'skill-regression'
    with ThreadPoolExecutor(max_workers=2) as pool:skills=list(pool.map(skills_probe.skills,range(410,414)))
    assert all(row['pass'] for row in skills),skills
    report={'binary_sha256':hashlib.sha256((PORTABLE/'LittleFighters.exe').read_bytes()).hexdigest(),
      'profiles':results,'mouse_bindings_saved':True,'remap_reload':True,'controller_binding_saved':True,
      'physical_controller_tested':False,'basic_shot':evidence,'fighters':fights,'controlled_skills':skills,'pass':True}
    (OUT/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'profiles':len(results),'basic_shot':evidence,'fighters':[(r['fighter'],r['pass']) for r in fights],'pass':True},indent=2))

if __name__=='__main__':main()
