"""Check complete native catalogs and duplicate policy without deleting object records."""
import argparse
import json
import subprocess
from pathlib import Path

FLOW = '''return function(base)
 local create=base.create
 function base.create(options)
  local s=create(options);local catalog=require('base/game/catalog');local all=catalog.load()
  local selected={};local deep=0
  for _,f in ipairs(all) do
   if catalog.selectable(f) then
    selected[#selected+1]={id=f.id,name=f.name,pack=f.pack or (f.id>=410 and 'polish-originals' or 'lf2')}
    if (f.pf_source_name or f.name):lower()=='deep' then deep=deep+1 end
   end
  end
  local doc=engine.read_settings() or {}
  doc.qa_roster={profile=catalog.profile_id,records=#catalog.objects().list,
   total_fighters=#all,selected=selected,deep_count=deep}
  assert(engine.write_settings(doc));return s
 end
 return base
end
'''
IDS = ['polish_fighters', 'lf_two', 'lf_four_turbo', 'dbz', 'one_piece', 'kate', 'reinforced', 'ntsd', 'bleach']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stage, output = args.stage.resolve(), args.output.resolve()
    cases = [('all-clean', None, True), ('all-variants', None, False),
             ('lf4-only', ['lf_four_turbo'], True), ('polish-only', ['polish_fighters'], True)]
    results = []
    for case, enabled, hide in cases:
        folder = output / case
        config = folder / 'config'
        config.mkdir(parents=True, exist_ok=True)
        (folder / 'package.manifest').write_text('id=qa-roster-selection\nversion=1\napi=1\nrequires=base@1\n'
            'requires=polish-fighters@1\nextend=base/ui/flow|flow.lua\n')
        (folder / 'flow.lua').write_text(FLOW)
        (config / 'config.json').write_text(json.dumps({'version': 1, 'options': {'unlock_characters': True},
            'little_fighters_packs': {name: enabled is None or name in enabled for name in IDS},
            'little_fighters_hide_duplicates': hide}))
        command = [str(stage / 'LittleFighters.exe'), '--installer', str(stage / 'LF2_v2.0a.exe'),
                   '--scripts', str(stage / 'scripts'), '--mod', str(stage / 'content-packs/polish-originals'),
                   '--mod', str(stage / 'content-packs/mixed-all'), '--mod', str(folder),
                   '--config-dir', str(config), '--input-trace', '*1']
        process = subprocess.run(command, capture_output=True, text=True, timeout=120)
        (folder / 'run.log').write_text(process.stdout + process.stderr, encoding='utf-8')
        assert process.returncode == 0, process.stderr[-1500:]
        result = json.loads((config / 'config.json').read_text())['qa_roster']
        result['case'] = case
        results.append(result)
        print(json.dumps({k: v for k, v in result.items() if k != 'selected'}), flush=True)
    (output / 'summary.json').write_text(json.dumps(results, indent=2))
    assert len({r['records'] for r in results}) == 1, 'Object records were removed'
    assert results[0]['deep_count'] == results[2]['deep_count'] == 1
    assert results[1]['deep_count'] > 1, 'Opt-out no longer restores variants'
    assert results[3]['deep_count'] == 0 and len(results[3]['selected']) == 5
    assert all(f['pack'] == 'lf4-turbo' for f in results[2]['selected'])
