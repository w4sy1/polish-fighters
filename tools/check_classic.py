#!/usr/bin/env python3
import argparse,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ADD='#121,,*2,'
TRACES={
 'original_menu':('*3','pf_panel=classic'),
 'extras':(ADD,'pf_panel=extras'),
 'maps':(ADD+'@420_248!,@420_248,@420_300!,@420_300,*3','pf_map=3'),
 'packs':(ADD+'@420_275!,@420_275,*3','pf_panel=packs'),
 'connection':(ADD+'@420_300!,@420_300,*3','pf_panel=connection'),
 'capacity_min':(ADD+'@420_300!,@420_300,@420_275!,@420_275,*3','pf_room_capacity=2'),
 'room_entry':(ADD+'@420_300!,@420_300,@420_220!,@420_220,*3','screen=network'),
 'account':(ADD+'@420_325!,@420_325,*3','pf_panel=account'),
 'options':(ADD+'@420_350!,@420_350,*3','launch_page=options'),
 'return':(ADD+'#27,,*3','pf_panel=classic'),
 'match':('@350_230!,@350_230,*2,c,,c,,c,,c,,c,*180,'+','.join(['c','']*6)+',u,,u,,c,*300','screen=match frame=300'),
}
def main():
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--installer',required=True);p.add_argument('--output-dir',type=Path,default=ROOT/'validation/classic');a=p.parse_args()
 temp=tempfile.TemporaryDirectory(prefix='pf-classic-')
 cmd=[str(Path(a.engine).resolve()),'--installer',str(Path(a.installer).resolve()),'--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'engine/scripts/polish-fighters'),'--seed','42','--config-dir',temp.name,'--input-trace']
 out=a.output_dir;out.mkdir(parents=True,exist_ok=True);results=[]
 for name,(trace,expected) in TRACES.items():
  r=subprocess.run(cmd+[trace],text=True,capture_output=True,timeout=45);text=r.stdout+r.stderr
  (out/(name+'.log')).write_text(text);passed=r.returncode==0 and expected in text
  results.append({'test':name,'passed':passed,'expected':expected});print(name,'PASS' if passed else 'FAIL')
  if not passed:print(text)
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 return 0 if all(v['passed'] for v in results) else 1
if __name__=='__main__':raise SystemExit(main())
