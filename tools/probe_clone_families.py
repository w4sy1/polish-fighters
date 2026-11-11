"""Controlled native opoint tests using the actual LF4 LeumasEX/Rudolf files."""
import argparse
import json
import subprocess
from pathlib import Path

LUA = '''return function(base)
 local create=base.create
 function base.create(options)
  local s=create(options);local catalog=require('base/game/catalog');local fighters=catalog.load();local row
  for n,f in ipairs(fighters) do if f.id==ACTOR then row=n end end
  assert(row,'fixture actor missing')
  local m=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,
   fighters=fighters,backgrounds=catalog.backgrounds(),slots={[0]={kind='human',fighter=row,team=1}}}).match
  local objects=require('base/game/objects');local root=m.items[0]
  root.frame=FRAME;root.wait_counter=0;root.hit_lag=0
  for n=1,10 do objects.spawn_from_frame(m,0,root) end
  local children={}
  for n=50,399 do if m.items[n] and m.items[n].record.kind==0 then children[#children+1]=n end end
  local first=#children
  for _,n in ipairs(children) do
   local child=m.items[n];child.frame=FRAME;child.wait_counter=0;child.hit_lag=0
   objects.spawn_from_frame(m,n,child)
  end
  local total=0;local identities={}
  for n=50,399 do
   local child=m.items[n]
   if child and child.record.kind==0 then total=total+1;identities[tostring(child.record.id)]=true end
  end
  local doc=engine.read_settings() or {}
  doc.qa_clone_family={actor=ACTOR,root_name=fighters[row].name,first_generation=first,
   all_descendants=total,identities=identities,passed=first==3 and total==3 and identities[tostring(ACTOR)]==true}
  assert(engine.write_settings(doc));return s
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
    for profile, actor, frame in [('lf4-turbo', 55, 274), ('lf4-turbo', 5, 271),
                                   ('mixed-all', 1001, 274), ('mixed-all', 1019, 271)]:
        folder = output / (profile + '-' + str(actor))
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'package.manifest').write_text('id=qa-clone-family\nversion=1\napi=1\nrequires=base@1\n'
            'requires=polish-fighters@1\nextend=base/ui/flow|flow.lua\n')
        (folder / 'flow.lua').write_text(LUA.replace('ACTOR', str(actor)).replace('FRAME', str(frame)))
        mods = [stage / 'content-packs' / profile]
        if profile == 'mixed-all': mods.insert(0, stage / 'content-packs/polish-originals')
        command = [str(stage / 'LittleFighters.exe'), '--installer', str(stage / 'LF2_v2.0a.exe'),
                   '--scripts', str(stage / 'scripts'), '--config-dir', str(folder / 'config')]
        for mod in mods + [folder]: command += ['--mod', str(mod)]
        process = subprocess.run(command + ['--input-trace', '*1'], capture_output=True, text=True, timeout=120)
        (folder / 'run.log').write_text(process.stdout + process.stderr, encoding='utf-8')
        assert process.returncode == 0, process.stderr[-1500:]
        report = json.loads((folder / 'config/config.json').read_text())['qa_clone_family']
        report['profile'] = profile
        results.append(report)
        print(json.dumps(report), flush=True)
    (output / 'summary.json').write_text(json.dumps(results, indent=2))
    assert all(r['passed'] for r in results), 'Native clone families are not bounded'
