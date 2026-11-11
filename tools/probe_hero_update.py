"""Controlled native Windows probes using real inputs and the staged hero package.

HP reductions for reactive-passive tests are explicit fixtures, not natural combat proof.
"""
import json
import os
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'engine/out/LittleFighters-Heroes-2026-11-06'
OUT=ROOT/'validation/hero-update-2026-11-06/native'

LUA='''return function(base)
 local update=base.update
 local objects=require('base/game/objects')
 local which='CASE'
 local pictures,forms={},{}
 local before_cancel=false
 local maximum_clones=0
 function base.update(s,input,context)
  if not s.hero_fixture then
   s.hero_fixture=true
   local catalog=require('base/game/catalog');local fighters=catalog.load();local row
   for n,f in ipairs(fighters) do if f.id==TARGET then row=n end end
   assert(row)
   local opponent
   for n,f in ipairs(fighters) do if f.id==1 then opponent=n end end
   s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,
    fighters=fighters,backgrounds=catalog.backgrounds(),slots={
     [0]={kind='human',fighter=row,team=1},[1]={kind='human',fighter=opponent,team=2}}})
   s.active='match';s.wait_release=nil
   local m=s.match.match;local v=m.items[0];v.x,v.x_int,v.y,v.y_int,v.z,v.z_int=220,220,0,0,400,400
   v.mp=500;m.items[1].hp,m.items[1].dark_hp,m.items[1].max_hp=10000,10000,10000
  end
  local m=s.match.match;local n=m.frame_number;local v=m.items[0];local t=m.items[1]
  for i=50,399 do local p=m.items[i];if p and p.record.id<410 then objects.remove(m,i) end end
  t.x,t.x_int,t.y,t.y_int,t.z,t.z_int=v.x+160,math.floor(v.x+160),0,0,v.z,math.floor(v.z)
  t.frame,t.wait_counter,t.vx,t.vy,t.vz,t.facing=0,0,0,0,0,1
  local schedule={}
  if which=='mech' then
   schedule={[5]='f',[7]='b',[9]='c',[35]='c',[50]='c',[65]='c',[80]='c',
    [120]='f',[122]='r',[123]='r',[124]='b',[200]='f',[202]='r',[203]='r',[204]='c',[208]='c',[214]='c',
    [1100]='f',[1102]='b',[1104]='c'}
   if n==320 then v.hp=v.hp-80 end
   if n==1000 then before_cancel=v.record.id==415 end
   if n==1099 then v.mp=0 end
  elseif which=='sz' then schedule={[5]='f',[7]='u',[9]='c'}
  elseif which=='boss' then
   schedule={[5]='f',[7]='u',[9]='b',[200]='f',[202]='b',[204]='c',[560]='f',[562]='u',[563]='u',[564]='b'}
   if n==500 then for _,p in pairs(m.items) do if p.record.id==433 and p.hp>0 then p.hp=0;break end end end
  elseif which=='jas' then
   if n==30 or n==70 or n==110 or n==160 or n==200 or n==240 then v.hp=v.hp-10 end
  elseif which=='wasyl' then
   if n==30 or n==70 then v.hp=v.hp-40 end
  end
  input=(schedule[n] or '')..'/?t'
  update(s,input,context)
  forms[tostring(v.record.id)]=true
  if v.record.id==415 then pictures[tostring(v.record.frame(v.frame).picture)]=true end
  local clones,depths=0,{}
  for _,p in pairs(m.items) do
   if p.pf_clone and p.record.id==411 and p.hp>0 then
    clones=clones+1;depths[tostring(p.pf_clone_depth)]=true
    assert(p.max_hp==500,'SZ clone lost full HP')
   end
  end
  maximum_clones=math.max(maximum_clones,clones)
  if m.frame_number==END_FRAME then
   local turrets=0
   for _,p in pairs(m.items) do if p.record.id==433 and p.hp>0 then turrets=turrets+1 end end
   local doc=engine.read_settings() or {}
   doc.hero_probe={case=which,events=m.pf_events or {},frame=m.frame_number,hp=v.hp,max_hp=v.max_hp,
    damage=v.damage_dealt,record=v.record.id,forms=forms,pictures=pictures,before_cancel=before_cancel,
    maximum_clones=maximum_clones,clone_depths=depths,turrets=turrets,mp=v.mp}
   assert(engine.write_settings(doc))
  end
 end
 return base
end
'''


def run(case,actor,frames):
    folder=OUT/(case+'-'+str(frames));override=folder/'fixture';override.mkdir(parents=True,exist_ok=True)
    (override/'package.manifest').write_text('id=hero-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=polish-originals@1\nextend=base/ui/flow|flow.lua\n')
    (override/'flow.lua').write_text(LUA.replace('CASE',case).replace('TARGET',str(actor)).replace('END_FRAME',str(frames)))
    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    command=[str(STAGE/'LittleFighters.exe'),'--installer',str(STAGE/'LF2_v2.0a.exe'),
     '--scripts',str(STAGE/'scripts'),'--mod',str(STAGE/'content-packs/polish-originals'),
     '--mod',str(override),'--config-dir',str(folder/'config'),'--seed','42',
     '--input-trace','*'+str(frames),'--renderer','software','--capture-frame',str(folder/'frame.bmp')]
    result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=90)
    (folder/'run.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    assert result.returncode==0,(case,result.stderr[-2500:])
    report=json.loads((folder/'config/config.json').read_text()).get('hero_probe',{})
    assert report.get('frame')==frames,(case,report)
    return report


def main():
    results={case:run(case,id_,frames) for case,id_,frames in (
     ('mech',414,1250),('sz',411,450),('boss',413,650),('jas',412,320),('wasyl',410,220))}
    mech=results['mech'];events=mech['events']
    assert mech['before_cancel'] and mech['record']==414 and mech['max_hp']==600,mech
    assert len(mech['pictures'])>=6 and events.get('rn_mech_basic',0)>=3,mech
    assert events.get('rn_combo_uppercut',0)>0 and events.get('rn_combo_finisher',0)>0,mech
    assert events.get('spawn_430',0)>0 and events.get('spawn_431',0)>0 and mech['damage']>50,mech
    sz=results['sz'];assert sz['maximum_clones']==2 and sz['clone_depths'].get('2') and sz['hp']==500,sz
    boss=results['boss'];events=boss['events']
    assert boss['turrets']==3 and events.get('boss_toilets')==4 and events.get('boss_toilet_destroyed')==1,boss
    assert events.get('boss_ultimate_blast')==1 and events.get('boss_toilet_fire',0)>20 and boss['hp']==1500,boss
    jas=results['jas']['events'];assert jas.get('jas_counter_teleport')==1 and jas.get('jas_counter_lightning')==1,jas
    wasyl=results['wasyl']['events'];assert wasyl.get('wasyl_reactive_heal')==2 and wasyl.get('heal_410',0)>=48,wasyl
    run('mech',414,145)
    (OUT/'summary.json').write_text(json.dumps(dict(pass_=True,cases=results),indent=2)+'\n')
    print('PASS: actual native input transform, persistent form, attacks/animation, three-step combo, free cancellation; clone family, turrets/ultimate, reactive passives')


if __name__=='__main__':main()
