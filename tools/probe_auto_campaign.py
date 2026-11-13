"""Real movement across a cleared two-section fixture, without teleporting players."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FLOW='''return function(base)
 local create,update,describe=base.create,base.update,base.describe
 function base.create(options)
  local s=create(options);local opts=require('base/game/options').current()
  opts.auto_advance=ENABLED;assert(require('base/game/options').save(opts))
  local catalog=require('base/game/catalog');local fighters=catalog.load();local human,ally
  for row,f in ipairs(fighters) do if f.id==411 then human=row end;if f.id==410 then ally=row end end
  s.match=require('base/ui/match_screen').create({mode=1,difficulty=0,background=0,
   campaign_path='mods/qa-auto/campaign.txt',campaign_background=0,stage_level=0,
   fighters=fighters,backgrounds=catalog.backgrounds(),
   slots={[0]={kind='human',fighter=human,team=1},[1]={kind='computer',fighter=ally,team=1}}})
  s.active='match';s.wait_release=nil
  assert(require('polish-originals/heroes').clone(s.match.match,0,s.match.match.items[0],require('base/game/objects')))
  return s
 end
 function base.update(s,input,context)
  if s.qa_done then return end
  local result=update(s,input,context)
  local m=s.match.match
  if m.stage_run.id>=1 then
   for _,v in pairs(m.items) do assert(not v.pf_clone,'old clone survived section transition') end
   s.qa_done=true
  end
  return result
 end
 function base.describe(s)
  return describe(s)..' qa_auto_stage='..s.match.match.stage_run.id..' qa_auto_x='..s.match.match.items[0].x_int
 end
 return base
end
'''
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);results=[]
 for name,enabled,trace,stage in [('enabled',True,'*600',1),('disabled',False,'*600',0),('manual',True,'*75,l,*600',0)]:
  folder=out/name;folder.mkdir(exist_ok=True)
  (folder/'campaign.txt').write_text(''.join(f'<stage>\nid: {n}\n<phase>\nbound: 350\n<phase_end>\n<stage_end>\n' for n in (0,1)))
  (folder/'package.manifest').write_text('id=qa-auto\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nextend=base/ui/flow|flow.lua\nasset=mods/qa-auto/campaign.txt|campaign.txt\n')
  (folder/'flow.lua').write_text(FLOW.replace('ENABLED',str(enabled).lower()))
  completed=subprocess.run([str(a.engine.resolve()),'--installer',str(ROOT.parent/'downloads/LF2_v2.0a.exe'),
   '--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'content-packs/polish-originals'),'--mod',str(folder),
   '--config-dir',str(folder/'config'),'--input-trace',trace],capture_output=True,text=True,timeout=90)
  log=completed.stdout+completed.stderr;(folder/'run.log').write_text(log,encoding='utf-8')
  result=dict(case=name,passed=completed.returncode==0 and f'qa_auto_stage={stage}' in log)
  results.append(result);print(result,flush=True)
  if not result['passed']:print(log[-1600:],flush=True)
 (out/'summary.json').write_text(json.dumps(results,indent=2))
 raise SystemExit(0 if all(r['passed'] for r in results) else 1)
