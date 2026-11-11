"""Run every installed profile with both saved touch layouts and return via F4."""
import argparse
import json
import subprocess
from pathlib import Path

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();stage=args.stage.resolve();output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    probe=output/'probe';probe.mkdir(exist_ok=True)
    (probe/'package.manifest').write_text('id=qa-layout-menu\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nextend=base/ui/flow|flow.lua\n')
    (probe/'flow.lua').write_text('''return function(base)
 local describe=base.describe
 function base.describe(s) return describe(s)..' touch='..s.touch_gamepad.style end
 return base
end''')
    results=[]
    for pack in ['', 'polish-originals','lf4-turbo','dbz','one-piece','kate','reinforced','ntsd','bleach','mixed-all']:
        for style in ['classic','modern']:
            name=(pack or 'lf2')+'-'+style;config=output/name;config.mkdir(exist_ok=True)
            saved={'version':1,'options':{'touch_layout':style},'qa_keep':{'progress':7}}
            (config/'config.json').write_text(json.dumps(saved))
            command=[str(stage/'LittleFighters.exe'),'--installer',str(stage/'LF2_v2.0a.exe'),
                '--scripts',str(stage/'scripts'),'--hub-menu','--config-dir',str(config),'--input-trace','4,,*4']
            if pack=='mixed-all':command+=['--mod',str(stage/'content-packs/polish-originals')]
            if pack:command+=['--mod',str(stage/'content-packs'/pack)]
            command+=['--mod',str(probe)]
            run=subprocess.run(command,capture_output=True,text=True,timeout=90)
            log=run.stdout+run.stderr;(config/'run.log').write_text(log,encoding='utf-8')
            document=json.loads((config/'config.json').read_text())
            passed=run.returncode==0 and 'screen=launch' in log and 'hub=true:root' in log and 'touch='+style in log
            passed=passed and document['qa_keep']==saved['qa_keep'] and document['options']['touch_layout']==style
            results.append(dict(pack=pack or 'lf2',style=style,passed=passed,exit=run.returncode))
            print(name,'PASS' if passed else 'FAIL',flush=True)
    (output/'results.json').write_text(json.dumps(results,indent=2))
    raise SystemExit(0 if all(r['passed'] for r in results) else 1)
