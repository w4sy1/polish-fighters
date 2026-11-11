"""Open every guide page via real native menu clicks; optionally capture the UI."""
import argparse
import os
import subprocess
from pathlib import Path

FLOW = '''return function(base)
 local create,describe=base.create,base.describe
 function base.create(options)
  local s=create(options);s.launch.hub_enabled=true;s.launch.hub_mode='profile';return s
 end
 function base.describe(s)
  return describe(s)..' qa_guide='..tostring(s.launch.pf_guide_message==true)..
   ' guide_lines='..tostring(s.launch.pf_message and #s.launch.pf_message or 0)
 end
 return base
end
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--capture', action='store_true')
    args = parser.parse_args()
    stage, output = args.stage.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fixture = output / 'fixture'
    fixture.mkdir(exist_ok=True)
    (fixture / 'package.manifest').write_text('id=qa-combo-guide\nversion=1\napi=1\nrequires=base@1\n'
        'requires=polish-fighters@1\nextend=base/ui/flow|flow.lua\n')
    (fixture / 'flow.lua').write_text(FLOW)
    for row, name in enumerate(['basics', 'wasyl', 'sz', 'jas', 'tata', 'remonoko', 'mech'], 1):
        trace = '@60_360,!,@420_' + str(219 + (row - 1) * 25) + ',!,*3'
        command = [str(stage / 'LittleFighters.exe'), '--installer', str(stage / 'LF2_v2.0a.exe'),
                   '--scripts', str(stage / 'scripts'), '--mod', str(stage / 'content-packs/polish-originals'),
                   '--mod', str(fixture), '--config-dir', str(output / ('config-' + name)),
                   '--hub-menu', '--input-trace', trace]
        if args.capture: command += ['--renderer', 'software', '--capture-frame', str(output / (name + '.bmp'))]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace',
                                env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'), timeout=90)
        log = result.stdout + result.stderr
        (output / (name + '.log')).write_text(log, encoding='utf-8')
        assert result.returncode == 0 and 'qa_guide=true guide_lines=10' in log, (name, log[-1500:])
        print('PASS native guide:', name, flush=True)
