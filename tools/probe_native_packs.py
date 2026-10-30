"""Run the existing own native EXE with isolated roster overrides; no build.
Never changes production/source settings or invokes original game programs.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import subprocess
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
TRACE='@350_230!,@350_230,*2,c,,c,,c,,c,,c,*180,'+','.join(['c','']*6)+',u,,u,,c,*300'


def probe(pack, fighter, output, runs=2, geometry=False, combat=False, binary=None, scripts=None, content_root=None):
    binary=Path(binary) if binary else ROOT/'engine/out/PolishFighters-Windows-x64-portable/openlf2.exe'
    scripts=Path(scripts) if scripts else ROOT/'engine/scripts'
    content_root=Path(content_root) if content_root else ROOT/'content-packs'
    target_frames=900 if combat else 300
    trace=TRACE
    if combat:
        # Real input sequences, no forced frames/health/MP or simulation shortcuts.
        actions=['f','','r','','c','','*24','f','','u','','c','','*24',
                 'f','','d','','c','','*24','f','','r','','b','','*24',
                 'f','','u','','b','','*24','f','','d','','b','','*24',
                 'f','','b','','c','','*24','r*10','c','','b','','c','','*24']
        expanded=[]
        for token in actions:
            command,sep,count=token.partition('*')
            expanded.extend([command]*(int(count) if sep else 1))
        expanded=(expanded*5)[:900]
        # The first actionable input participates in the menu-to-match transition.
        # Add an idle input so the measured match reaches 900 simulation frames.
        trace=TRACE.rsplit('*300',1)[0]+','.join(command or '*1' for command in expanded)+',*1'
    folder=output/pack/str(fighter);folder.mkdir(parents=True,exist_ok=True)
    override=folder/'roster';override.mkdir(exist_ok=True)
    (override/'package.manifest').write_text('id=compat-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires='+pack+'@1\nreplace=polish-fighters/settings|settings.lua\nextend=base/ui/match_screen|probe.lua\n')
    (override/'settings.lua').write_text('return {allowed_ids={'+str(fighter)+'},allow_hidden=true}\n')
    dimensions=[]
    if geometry:
        for line in (content_root/pack/'package.manifest').read_text().splitlines():
            if line.startswith('asset='):
                virtual,relative=line[6:].split('|',1)
                path=content_root/pack/relative
                if path.suffix in ['.bmp','.png']:
                    with Image.open(path) as image:
                        dimensions.append('['+json.dumps(virtual)+']={'+str(image.width)+','+str(image.height)+'},')
    (override/'probe.lua').write_text('''return function(base)
 local dimensions={'''+''.join(dimensions)+'''}
 local outside,observed={},{}
 local visited,missing,creations={},{},0
 local catalog=require('base/game/catalog')
 local function observe(resource,rect)
  local size=dimensions[resource]
  if size and (rect[1]<0 or rect[2]<0 or rect[1]+rect[3]>size[1] or rect[2]+rect[4]>size[2]) then
   local key=resource..":"..table.concat(rect,",")
   if not observed[key] then
    observed[key]=true
    outside[#outside+1]={resource=resource,rect={rect[1],rect[2],rect[3],rect[4]},dimensions=size}
   end
  end
 end
 local create,draw,outcome=base.create,base.draw,base.outcome
 local function persist(state,finished)
   local doc=engine.read_settings() or {}
   doc.compat_probe=doc.compat_probe or {}
   doc.compat_probe.geometry={outside=outside,frame=state.match.frame_number,
    human_record_frames=visited,observed_missing_opoints=missing}
   if finished then doc.compat_probe.finished={frame=state.match.frame_number,winner=state.match.winner} end
   assert(engine.write_settings(doc))
 end
 function base.outcome(state)
  local result=outcome(state)
  if state.match.finished then persist(state,true) end
  return result
 end
 function base.create(options)
  local state=create(options)
  assert(state.match.items[0].record.id=='''+str(fighter)+''',"Probe selected wrong human")
  local doc=engine.read_settings() or {}
  creations=creations+1
  if creations==1 then doc.compat_probe={} end
  doc.compat_probe.fighter=state.match.items[0].record.id
  doc.compat_probe.created=true
  doc.compat_probe.match_creations=creations
  assert(engine.write_settings(doc))
  return state
 end
 local function validate(label,values)
  for i,v in ipairs(values) do
   assert(type(v)=="number" and v==v and v>=-8192 and v<=8192 and v==math.floor(v),
    "Probe invalid draw field "..label.." #"..i.."="..tostring(v))
  end
 end
 function base.draw(state,context,bounds)
  local human=state.match.items[0]
  if human then visited[tostring(human.record.id)..":"..tostring(human.frame)]=true end
  for _,entry in pairs(state.match.items) do
   local point=entry.record.frame(entry.frame).opoint
   if point and point.kind>0 and point.oid>0 and entry.wait_counter==0
      and not catalog.objects().by_id[point.oid] then
    missing[tostring(entry.record.id)..":"..tostring(entry.frame)..":"..tostring(point.oid)]=true
   end
  end
  local sprite,world=context.sprite,context.world_sprite
  context.sprite=function(resource,rect,x,y,...)
   validate(resource,{rect[1],rect[2],rect[3],rect[4],x,y})
   observe(resource,rect)
   return sprite(resource,rect,x,y,...)
  end
  context.world_sprite=function(resource,rect,x,y,...)
   validate(resource,{rect[1],rect[2],rect[3],rect[4],x,y})
   observe(resource,rect)
   return world(resource,rect,x,y,...)
  end
  draw(state,context,bounds)
  context.sprite,context.world_sprite=sprite,world
  if state.match.frame_number=='''+str(target_frames)+''' then
   persist(state,false)
  end
 end
 return base
end
''')
    command=[str(binary),
             '--installer',str(ROOT/'../downloads/LF2_v2.0a.exe'),'--scripts',str(scripts),
             '--mod',str(scripts/'polish-fighters'),'--mod',str(content_root/pack),
             '--mod',str(override),'--seed','42','--input-trace',trace]
    logs=[];results=[]
    for run in range(runs):
        try:
            p=subprocess.run(command+['--config-dir',str(folder/('config-'+str(run)))],capture_output=True,text=True,timeout=35)
            log=p.stdout+p.stderr;code=p.returncode
        except subprocess.TimeoutExpired:
            log='Timeout after 35 seconds';code=-1
        (folder/('run-'+str(run)+'.log')).write_text(log,encoding='utf-8')
        config=folder/('config-'+str(run))/'config.json'
        selection=json.loads(config.read_text()).get('compat_probe',{}) if config.exists() else {}
        results.append({'exit_code':code,'match300':('screen=match frame='+str(target_frames)) in log,
                        'expected_match_frames':target_frames,
                        'requested_human_confirmed':selection.get('created') is True and selection.get('fighter')==fighter,
                        'natural_match_finished':selection.get('finished'),
                        'geometry':selection.get('geometry')})
        logs.append(log)
    row={'pack':pack,'fighter':fighter,'runs':results,'deterministic_output':len(set(logs))==1,
         'pass':all(r['exit_code']==0 and (r['match300'] or (combat and r['natural_match_finished'])) and r['requested_human_confirmed'] for r in results) and len(set(logs))==1}
    (folder/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    return row


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pack',choices=['bleach','kate','reinforced']);p.add_argument('--fighter',type=int);p.add_argument('--runs',type=int,default=2);p.add_argument('--geometry',action='store_true');p.add_argument('--combat',action='store_true');a=p.parse_args()
    output=ROOT/'validation/native-fixes-2026-10-29'/('fighters-combat' if a.combat else ('fighters-geometry' if a.geometry else 'fighters'));output.mkdir(exist_ok=True)
    targets=[]
    for pack in ([a.pack] if a.pack else ['bleach','kate','reinforced']):
        report=json.loads((ROOT/'content-packs'/pack/'import-report.json').read_text())
        targets.extend((pack,f['id']) for f in report['fighters'] if a.fighter is None or f['id']==a.fighter)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(probe,pack,fighter,output,a.runs,a.geometry,a.combat) for pack,fighter in targets]
        for future in concurrent.futures.as_completed(futures):
            row=future.result();rows.append(row);print(row['pack'],row['fighter'],'PASS' if row['pass'] else 'FAIL',flush=True)
    (output/'summary.json').write_text(json.dumps({'binary_sha256':hashlib.sha256((ROOT/'engine/out/PolishFighters-Windows-x64-portable/openlf2.exe').read_bytes()).hexdigest(),
        'scope':str(900 if a.combat else 300)+'-frame seeded native matches, selected fighter confirmed, no visual/exhaustive move verification',
        'tests':sorted(rows,key=lambda r:(r['pack'],r['fighter']))},indent=2)+'\n')
