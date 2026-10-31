"""Assisted DBZ traversal: removes spawned phase entries and moves QA player.

This tests progression and resources, not natural difficulty, AI balance or EXE-only mechanics.
"""
import json
import re
import subprocess
import argparse
from types import SimpleNamespace
from pathlib import Path
from lupa.luajit21 import LuaRuntime
from import_legacy import decode

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/campaign-traversal-2026-10-31'
def definitions(pack_name):
 pack=ROOT/'content-packs'/pack_name
 lua=LuaRuntime();catalog=lua.execute((pack/'catalog.lua').read_text())(lua.table())
 resources=dict(line[6:].split('|',1) for line in (pack/'package.manifest').read_text().splitlines() if line.startswith('asset='))
 if catalog.campaigns is not None:
  campaigns=[SimpleNamespace(path=c.path,name=c.name,background=c.background,start_id=c.start_id) for _,c in catalog.campaigns.items()]
 else:
  stages=decode((pack/resources[catalog.stage_path]).read_bytes())
  ids=[int(i) for i in re.findall(r'<stage>\s*id:\s*(\d+)',stages)]
  groups=sorted({i//10 for i in ids})
  count=len(re.findall(r'id:\s*\d+\s+file:',(pack/resources[catalog.source_path]).read_text()))
  campaigns=[SimpleNamespace(path=catalog.stage_path,name='chapter-'+str(group+1),
    background=min(group+1,count-1),start_id=min(i for i in ids if i//10==group)) for group in groups]
 return pack,catalog,resources,campaigns

def case(index,pack_name='dbz'):
 pack,catalog,resources,campaigns=definitions(pack_name)
 campaign=campaigns[index]
 source=decode((pack/resources[campaign.path]).read_bytes())
 declared={int(i) for i in re.findall(r'id:\s*(\d+)\s+type:',(pack/resources[catalog.source_path]).read_text())}
 referenced={int(i) for i in re.findall(r'\bid:\s*(\d+)',source)}
 # Stage IDs are <stage> header values; only phase entry lines are object references.
 referenced={int(i) for phase in re.findall(r'<phase>(.*?)<phase_end>',source,re.S) for i in re.findall(r'\bid:\s*(\d+)',phase)}
 missing=sorted(referenced-declared-{1000,3000,3001})
 folder=OUT/pack_name/str(index);folder.mkdir(parents=True,exist_ok=True)
 if missing:
  result={'campaign':index,'name':campaign.name,'status':'blocked_source_ids','ids':missing}
  (folder/'result.json').write_text(json.dumps(result,indent=2));return result
 (folder/'package.manifest').write_text('id=campaign-traversal-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires='+pack_name+'@1\nextend=base/ui/flow|flow.lua\n')
 script='''return function(base)
 local update,describe=base.update,base.describe
 local visited={};local done=false
 function base.update(s,input,context)
  if not s.campaign_probe then
   s.campaign_probe=true
   local catalog=require('base/game/catalog')
   s.match=require('base/ui/match_screen').create({mode=1,difficulty=0,background=0,
    campaign_path=CAMPAIGN,campaign_background=BG,stage_level=START,
    fighters={{id=0,path='data/deep.dat',name='QA Deep'}},backgrounds=catalog.backgrounds(),
    slots={[0]={kind='human',fighter=1,team=1}}})
   s.active='match';s.wait_release=nil
  end
  local m=s.match and s.match.match
  if m then
   local run=m.stage_run
   visited[tostring(run.id)..':'..tostring(run.phase)]=true
   if run.result==1 or run.ending then done=true end
   if not done then
    for _,entry in pairs(run.runtime[run.phase] or {}) do
     for _,slot in pairs(entry.ids or {}) do
      if slot>=20 and m.items[slot] then require('base/game/objects').remove(m,slot) end
     end
    end
    for slot,value in pairs(m.items) do
     if slot==0 then value.hp=5000;value.dark_hp=5000;value.max_hp=5000
      value.x=m.stage.width;value.x_int=value.x
     elseif value.team==require('base/game/constants').teams.enemies and value.record.kind==0 then value.hp=0;value.dark_hp=0 end
    end
   end
  end
  return update(s,input,context)
 end
 function base.describe(s)
  local count=0;for _ in pairs(visited) do count=count+1 end
  local m=s.match.match;local run=m.stage_run
  local phase=engine.read_stage_data(run.source_path).stages[run.id].phases[run.phase]
  return describe(s)..' traversal_done='..tostring(done)..' visited='..count..
   ' target_bound='..tostring(phase and phase.bound or -1)
 end
 return base
end
'''.replace('CAMPAIGN',json.dumps(campaign.path)).replace('BG',str(campaign.background or 0)).replace('START',str(campaign.start_id or 0))
 (folder/'flow.lua').write_text(script)
 cmd=[str(ROOT/'validation/online-native-2026-10-31/runner/LittleFighters.exe'),
  '--installer',str(ROOT/'../downloads/LF2_v2.0a.exe'),'--scripts',str(ROOT/'engine/scripts'),
  '--mod',str(pack),'--mod',str(folder),'--input-trace','*20000','--config-dir',str(folder/'config')]
 try:
  completed=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
  log=completed.stdout+completed.stderr;(folder/'run.log').write_text(log)
  result={'campaign':index,'name':campaign.name,'exit':completed.returncode,
   'assisted_completed':completed.returncode==0 and 'traversal_done=true' in log,
   'visited':int(re.search(r'visited=(\d+)',log)[1]) if re.search(r'visited=(\d+)',log) else None}
 except subprocess.TimeoutExpired:
  result={'campaign':index,'name':campaign.name,'status':'timeout','assisted_completed':False}
 (folder/'result.json').write_text(json.dumps(result,indent=2));return result

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--all',action='store_true')
 parser.add_argument('--packs',default='dbz')
 args=parser.parse_args()
 results=[]
 for pack_name in args.packs.split(','):
  for index in (range(len(definitions(pack_name)[3])) if args.all else [0,10,11]):
   result=case(index,pack_name);result['pack']=pack_name;results.append(result);print(json.dumps(result),flush=True)
 (OUT/'summary.json').write_text(json.dumps({'scope':'QA removes authored phase entries; progression/resource test only, not deaths, difficulty or natural playthrough','results':results},indent=2))
