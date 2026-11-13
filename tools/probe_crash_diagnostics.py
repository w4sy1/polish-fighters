"""Inject a Lua failure in a real native runtime and check the local report."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--missing-resource',action='store_true')
    args=parser.parse_args()
    folder=args.output.resolve();folder.mkdir(parents=True,exist_ok=True)
    (folder/'package.manifest').write_text('id=qa-diagnostics\nversion=1\napi=1\nrequires=base@1\n'
        'requires=polish-fighters@1\nextend=base/ui/flow|flow.lua\n')
    injected='function base.create() engine.read_resource("mods/qa-diagnostics/missing.dat") end' if args.missing_resource else \
        'function base.update() error("QA controlled failure token=qa-sensitive-value") end'
    (folder/'flow.lua').write_text('return function(base)\n'+injected+'\nreturn base\nend\n')
    completed=subprocess.run([str(args.engine.resolve()),'--installer',str(ROOT.parent/'downloads/LF2_v2.0a.exe'),
        '--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'content-packs/lf4-turbo'),
        '--mod',str(folder),'--config-dir',str(folder/'config'),'--input-trace','*1'],
        capture_output=True,text=True,timeout=60)
    (folder/'run.log').write_text(completed.stdout+completed.stderr,encoding='utf-8')
    assert completed.returncode!=0,'failure was swallowed'
    report=json.loads((folder/'config/config.json').read_text())['polish_fighters_last_crash']
    assert ('missing.dat' if args.missing_resource else 'QA controlled failure') in report['traceback'] and 'stack traceback' in report['traceback']
    assert 'qa-sensitive-value' not in json.dumps(report)
    assert report['profile']=='lf4-turbo' and report['version'] and report['events']
    (folder/'result.json').write_text(json.dumps({'passed':True,'report':report},indent=2),encoding='utf-8')
    print('PASS: native Lua error remains fatal, local bounded report includes context/traceback and redacts token')
