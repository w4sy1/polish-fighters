#!/usr/bin/env python3
"""Exercise every fighter in an imported pack. Not an exhaustive moveset test.
Mutates roster settings temporarily; run alone, never with other source-mutating tools.
"""
import argparse,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TRACE='@350_230!,@350_230,*2,c,,c,,c,,c,,c,*180,'+','.join(['c','']*6)+',u,,u,,c,*300'
def main():
 available=sorted(p.name for p in (ROOT/'content-packs').iterdir() if (p/'package.manifest').is_file())
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--installer',required=True);p.add_argument('--pack',choices=available,default='lf4-turbo');p.add_argument('--output-dir',type=Path);a=p.parse_args()
 pack=ROOT/'content-packs'/a.pack;report=json.loads((pack/'import-report.json').read_text())
 out=a.output_dir or ROOT/'validation/native-build'/('lf4' if a.pack=='lf4-turbo' else a.pack);out.mkdir(parents=True,exist_ok=True)
 settings=ROOT/'engine/scripts/polish-fighters/settings.lua';original=settings.read_bytes();results=[]
 try:
  for fighter in report['fighters']:
   settings.write_text('return {allowed_ids={'+str(fighter['id'])+'},allow_hidden=true}\n')
   command=[str(Path(a.engine).resolve()),'--installer',str(Path(a.installer).resolve()),'--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'engine/scripts/polish-fighters'),'--mod',str(pack),'--seed','42','--input-trace',TRACE]
   process=subprocess.run(command,capture_output=True,text=True,timeout=60);text=process.stdout+process.stderr
   passed=process.returncode==0 and 'screen=match frame=300' in text and ('item0{id='+str(fighter['id'])+' ') in text
   label=re.sub(r'[^A-Za-z0-9_.-]', '_',fighter['name'])[:80]
   (out/(str(fighter['id'])+'-'+label+'.log')).write_text(text)
   results.append({'id':fighter['id'],'name':fighter['name'],'passed':passed,'frames':300});print(fighter['name'],'PASS' if passed else 'FAIL',flush=True)
 finally:settings.write_bytes(original)
 (out/'all-fighters.json').write_text(json.dumps(results,indent=2)+'\n')
 return 0 if all(r['passed'] for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
