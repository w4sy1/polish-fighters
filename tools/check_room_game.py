#!/usr/bin/env python3
"""Run distinct real game processes through the integrated room and simulation."""
import argparse,json,socket,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def port():
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
def case(engine,installer,count,probe=False,menu=False,pack=None,unlock=False,output_dir=None):
 started=time.monotonic()
 config=ROOT/'tools/room-check/config.lua';config.write_text('return {players='+str(count)+',damage_probe='+str(probe).lower()+',menu='+str(menu).lower()+'}\n')
 listen_port=port()
 common=[str(Path(engine).resolve()),'--installer',str(Path(installer).resolve()),'--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'engine/scripts/polish-fighters'),'--mod',str(ROOT/'tools/room-check'),'--port',str(listen_port)]
 if pack:common+=['--mod',str(ROOT/'content-packs'/pack)]
 processes=[];out=output_dir or ROOT/'validation/room-game';out.mkdir(parents=True,exist_ok=True)
 label=f'{count}-devices'+('-desync' if probe else '')+('-menu' if menu else '')+('-'+pack if pack else '')+('-unlock' if unlock else '')
 try:
  for i in range(count):
   trace=('rbc' if i%2==0 else 'lbf')+'*120'
   if unlock and i==0:
    marks=[]
    for key in [76,70,50,190,78,69,84]:marks.extend(['#'+str(key),''])
    trace=','.join(marks+['*106'])
   if menu:trace='*3,c,,c,,c,,c,,c,*180,'+','.join(['c','']*6)+',u,,u,,c,*120'
   processes.append(subprocess.Popen(common+['--seed',str(42+i),'--host' if i==0 else '--join','127.0.0.1','--input-trace',trace],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True))
   if i==0:
    deadline=time.monotonic()+30
    while True:
     if processes[0].poll() is not None:
      stdout,stderr=processes[0].communicate();raise RuntimeError(stdout+stderr)
     try:
      with socket.create_connection(('127.0.0.1',listen_port),timeout=.1):break
     except OSError:
      if time.monotonic()>deadline:raise RuntimeError('Room listener did not open')
      time.sleep(.025)
  results=[]
  for i,p in enumerate(processes):
   stdout,stderr=p.communicate(timeout=90);text=stdout+stderr
   (out/f'{label}-{i}.log').write_text(text)
   import re
   found=re.search(r'room_digest=([a-f0-9]{64})',text)
   if menu:found=re.search(r'room_digest=([a-f0-9]{64})',text)
   match=re.search(r'screen=match frame=(\d+)',text)
   results.append({'slot':i,'exit':p.returncode,'digest':found.group(1) if found else None,'match': bool(match and int(match.group(1))>=120),'desync':'desynchronized' in text,'unlocked':('unlock_characters=true' in text or 'unlock=1:' in text)})
   if p.returncode:print(text[-2200:])
  passed=all(v['desync'] for v in results) if probe else all(v['exit']==0 and v['match'] and v['digest'] for v in results) and len({v['digest'] for v in results})==1
  if unlock:passed=passed and all(v['unlocked'] for v in results)
  print(label,'PASS' if passed else 'FAIL',flush=True)
  return {'devices':count,'probe':probe,'passed':passed,'elapsed_seconds':round(time.monotonic()-started,3),'processes':results}
 except subprocess.TimeoutExpired:
  for i,p in enumerate(processes):
   if p.poll() is None:p.kill()
   stdout,stderr=p.communicate()
   text=stdout+stderr
   (out/f'{label}-{i}-timeout.log').write_text(text)
   print(f'PROCESS {i}: {text[-1800:]}',flush=True)
  raise
 finally:
  for p in processes:
   if p.poll() is None:p.kill();p.wait()
def main():
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--installer',required=True);p.add_argument('--counts',default='2,3,4,5,6,7,8');p.add_argument('--probe',action='store_true');p.add_argument('--menu',action='store_true');p.add_argument('--pack');p.add_argument('--unlock',action='store_true');p.add_argument('--output-dir',type=Path,default=ROOT/'validation/room-game');a=p.parse_args()
 config=ROOT/'tools/room-check/config.lua';original=config.read_bytes()
 try:results=[case(a.engine,a.installer,int(n),a.probe,a.menu,a.pack,a.unlock,a.output_dir) for n in a.counts.split(',')]
 finally:config.write_bytes(original)
 (a.output_dir/('desync-results.json' if a.probe else 'unlock-results.json' if a.unlock else 'menu-results.json' if a.menu else a.pack+'-results.json' if a.pack else 'results.json')).write_text(json.dumps(results,indent=2)+'\n')
 return 0 if all(v['passed'] for v in results) else 1
if __name__=='__main__':raise SystemExit(main())
