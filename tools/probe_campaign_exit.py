"""Native campaign exit regression: a cleared fixture stage, real AI and movement.

The human starts at the exit; the computer must walk there without repositioning.
An empty two-stage fixture isolates passage logic, not combat or a full campaign.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOW = '''return function(base)
 local update,describe=base.update,base.describe
 function base.update(s,input,context)
  if s.qa_exit_done then return end
  if not s.qa_exit_started then
   s.qa_exit_started=true
   local catalog=require('base/game/catalog');local fighters=catalog.load();local human,computer
   for row,f in ipairs(fighters) do
    if f.id==0 then human=row end
    if f.id==ACTOR then computer=row end
   end
   assert(human and computer,'fixture fighters unavailable')
   s.match=require('base/ui/match_screen').create({mode=1,difficulty=0,background=0,
    campaign_path='mods/qa-campaign-exit/exit.txt',stage_level=0,fighters=fighters,backgrounds=catalog.backgrounds(),
    slots={[0]={kind='human',fighter=human,team=1},[1]={kind='computer',fighter=computer,team=1}}})
   s.active='match';s.wait_release=nil
   local m=s.match.match
   assert(m.items[0] and m.items[11],'human and computer slots missing')
   m.items[0].x,m.items[0].x_int=350,350
   m.items[11].x,m.items[11].x_int=150,150
   s.qa_start_x=m.items[11].x;s.qa_max_x=s.qa_start_x
  end
  local result=update(s,input,context)
  local m=s.match.match;local v=m.items[11]
  s.qa_max_x=math.max(s.qa_max_x,v.x)
  s.qa_exit_done=m.stage_run.id>=1
  local doc=engine.read_settings() or {}
  doc.qa_campaign_exit={actor=ACTOR,start_x=s.qa_start_x,max_x=s.qa_max_x,
   current_x=v.x,stage=m.stage_run.id,phase=m.stage_run.phase,
   last_phase=m.stage_run.last_phase,passed=s.qa_exit_done}
  assert(engine.write_settings(doc))
  return result
 end
 function base.describe(s) return describe(s)..' qa_exit='..tostring(s.qa_exit_done) end
 return base
end
'''


def run(stage, output, actor):
    folder = output / str(actor)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'campaign.txt').write_text(''.join(
        f'<stage>\nid: {n}\n<phase>\nbound: 350\n<phase_end>\n<stage_end>\n' for n in (0, 1)))
    (folder / 'package.manifest').write_text(
        'id=qa-campaign-exit\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\n'
        'extend=base/ui/flow|flow.lua\nasset=mods/qa-campaign-exit/exit.txt|campaign.txt\n')
    (folder / 'flow.lua').write_text(FLOW.replace('ACTOR', str(actor)))
    command = [str(stage / 'LittleFighters.exe'), '--installer', str(stage / 'LF2_v2.0a.exe'),
               '--scripts', str(stage / 'scripts'), '--mod', str(stage / 'content-packs/polish-originals'),
               '--mod', str(folder), '--config-dir', str(folder / 'config'), '--input-trace', '*350']
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    (folder / 'run.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2500:])
    report = json.loads((folder / 'config/config.json').read_text())['qa_campaign_exit']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--actors', default='0,410,411,412,413,414,415')
    args = parser.parse_args()
    reports = [run(args.stage.resolve(), args.output.resolve(), int(n)) for n in args.actors.split(',')]
    (args.output / 'summary.json').write_text(json.dumps(reports, indent=2))
    print(json.dumps(reports, indent=2))
    assert all(r['passed'] for r in reports), 'Computer allies blocked campaign passage'
