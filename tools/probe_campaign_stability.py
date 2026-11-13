"""Real native campaign progression with assisted clears; not a natural playthrough.

Uses installed content and isolated configuration, never edits source settings.
The QA player is invulnerable and moves to exits; authored spawns are removed.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOW = '''return function(base)
 local create,describe=base.create,base.describe
 function base.create(options)
  local s=create(options)
  local catalog=require('base/game/catalog');local fighters=catalog.load();local row
  for n,f in ipairs(fighters) do if f.id==ACTOR then row=n end end
  assert(row,'QA fighter missing')
  s.match=require('base/ui/match_screen').create({mode=1,difficulty=0,background=0,
   campaign_path=catalog.stage_path,stage_level=LEVEL,fighters=fighters,backgrounds=catalog.backgrounds(),
   slots={[0]={kind='human',fighter=row,team=1}}})
  s.active='match';s.qa_visited={};s.qa_done=false
  return s
 end
 function base.update(s,input,context)
  if s.qa_done then return end
  local m=s.match.match;local run=m.stage_run
  s.qa_visited[tostring(run.id)..':'..tostring(run.phase)]=true
  local objects=require('base/game/objects')
  if ASSIST then
   for index=20,399 do if m.items[index] then objects.remove(m,index) end end
  end
  for index=0,19 do
   local v=m.items[index]
   if v then v.hp=5000;v.dark_hp=5000;v.max_hp=5000
    if ASSIST then v.x=m.stage.width;v.x_int=v.x end end
  end
  local moves={'r','rc','','f','r','c','','b','r','c','','f','u','c','','f','d','c',''}
  local held=ASSIST and '' or moves[(m.frame_number%#moves)+1]
  require('base/game/match').step(m,{[0]=held,[1]='',[2]='',[3]='',[4]='',[5]='',[6]='',[7]='',functions=''})
  s.qa_done=run.result==1 or run.ending
  local document=engine.read_settings() or {}
  document.qa_campaign={done=s.qa_done,stage=run.id,phase=run.phase,visited=s.qa_visited,frames=m.frame_number}
  if s.qa_done or m.frame_number%30==0 then assert(engine.write_settings(document)) end
 end
 function base.describe(s)
  return describe(s)..' qa_campaign_done='..tostring(s.qa_done)
 end
 return base
end
'''


def probe(engine, output, pack, actor, level, natural_frames=0):
    folder = output / f'{pack}-{actor}-{level}'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'package.manifest').write_text(
        'id=qa-stability\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\n'
        'extend=base/ui/flow|flow.lua\n', encoding='utf-8')
    (folder / 'flow.lua').write_text(FLOW.replace('ACTOR', str(actor)).replace('LEVEL', str(level))
                                   .replace('ASSIST', 'false' if natural_frames else 'true'), encoding='utf-8')
    command = [str(engine), '--installer', str(ROOT.parent/'downloads/LF2_v2.0a.exe'),
               '--scripts', str(ROOT/'engine/scripts'), '--mod', str(ROOT/'content-packs'/pack),
               '--mod', str(folder), '--seed', '42', '--config-dir', str(folder/'config'),
               '--input-trace', '*'+str(natural_frames or 6000)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
    (folder/'run.log').write_text(completed.stdout+completed.stderr, encoding='utf-8')
    config = folder/'config/config.json'
    result = json.loads(config.read_text()).get('qa_campaign', {}) if config.exists() else {}
    result.update(pack=pack, actor=actor, level=level, exit=completed.returncode,
                  scope='combat smoke' if natural_frames else 'assisted progression',
                  passed=completed.returncode == 0 and (result.get('done') is True or
                      natural_frames>0 and result.get('frames',0)>=natural_frames-30))
    if completed.returncode:
        result['error'] = completed.stderr[-2000:]
    (folder/'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pack', default='lf4-turbo')
    parser.add_argument('--actor', type=int, default=55)
    parser.add_argument('--levels', default='0,10,20,30,40')
    parser.add_argument('--natural-frames', type=int, default=0)
    args = parser.parse_args()
    results = [probe(args.engine.resolve(), args.output.resolve(), args.pack, args.actor, int(level), args.natural_frames)
               for level in args.levels.split(',')]
    (args.output/'summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    raise SystemExit(0 if all(r['passed'] for r in results) else 1)
