"""Exercise actual native mouse/touch-equivalent clicks back to the module launcher."""
import argparse
import json
import subprocess
from pathlib import Path

FLOW = '''return function(base)
 local create=base.create
 function base.create(options)
  local s=create(options);s.launch.hub_enabled=true;s.launch.hub_mode='profile'
  local which='CASE'
  if which=='characters' then
   s.characters=require('base/ui/character_select').create({mode='stage'});s.active='characters'
  elseif which=='ending' then s.ending=require('base/ui/ending').create(0);s.active='ending'
  elseif which=='paused' or which=='finished' then
   local catalog=require('base/game/catalog');local fighters=catalog.load()
   s.characters=require('base/ui/character_select').create({mode='versus'})
   s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,
    fighters=fighters,backgrounds=catalog.backgrounds(),slots={[0]={kind='human',fighter=1,team=1},
    [1]={kind='computer',fighter=2,team=2}}})
   s.active='match';s.match.match.paused=which=='paused'
   if which=='finished' then s.match.match.finished=true;s.match.match.round_counter=150 end
  end
  return s
 end
 return base
end
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stage, output = args.stage.resolve(), args.output.resolve()
    results = []
    for case in ('profile', 'characters', 'ending', 'paused', 'finished'):
        folder = output / case
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'package.manifest').write_text('id=qa-module-navigation\nversion=1\napi=1\n'
            'requires=base@1\nrequires=polish-fighters@1\nextend=base/ui/flow|flow.lua\n')
        (folder / 'flow.lua').write_text(FLOW.replace('CASE', case))
        point = {'profile': '@60_470', 'characters': '@397_16', 'ending': '@397_24',
                 'paused': '@397_523', 'finished': '@397_523'}[case]
        trace = point + ',!,*4' if case != 'paused' else point + ',!,@0_0,@300_300,!,*8'
        command = [str(stage / 'LittleFighters.exe'), '--installer', str(stage / 'LF2_v2.0a.exe'),
                   '--scripts', str(stage / 'scripts'), '--mod', str(stage / 'content-packs/polish-originals'),
                   '--mod', str(folder), '--config-dir', str(folder / 'config'), '--hub-menu', '--input-trace', trace]
        process = subprocess.run(command, capture_output=True, text=True, timeout=90)
        log = process.stdout + process.stderr
        (folder / 'run.log').write_text(log, encoding='utf-8')
        result = dict(case=case, exit=process.returncode,
                      returned_to_modules=process.returncode == 0 and 'hub=true:root' in log and 'screen=launch' in log)
        results.append(result)
        print(json.dumps(result), flush=True)
    (output / 'summary.json').write_text(json.dumps(results, indent=2))
    assert all(r['returned_to_modules'] for r in results), 'Native module navigation failed'
