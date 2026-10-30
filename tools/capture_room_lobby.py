#!/usr/bin/env python3
"""Capture the actual native lobby with eight connected local game processes.
Temporarily changes developer test configuration. Run separately from other game tests.
"""
import argparse,os,socket,subprocess,time
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--installer',required=True);p.add_argument('--capture-library',required=True);a=p.parse_args()
 config=ROOT/'tools/room-check/config.lua';original=config.read_bytes();processes=[]
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 bmp=ROOT/'preview/room-eight-native.bmp'
 common=[str(Path(a.engine).resolve()),'--installer',str(Path(a.installer).resolve()),'--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'engine/scripts/polish-fighters'),'--mod',str(ROOT/'tools/room-check'),'--port',str(port)]
 try:
  config.write_text('return {players=8,damage_probe=false,hold_lobby=true}\n')
  env=os.environ.copy();env.update(PF_CAPTURE=str(bmp),PF_CAPTURE_FRAME='150',LD_PRELOAD=str(Path(a.capture_library).resolve()),SDL_VIDEODRIVER='offscreen',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
  host=subprocess.Popen(common+['--host','127.0.0.1','--renderer','software'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);processes.append(host)
  time.sleep(1)
  for i in range(7):processes.append(subprocess.Popen(common+['--join','127.0.0.1','--input-trace','*1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
  stdout,stderr=host.communicate(timeout=30)
  if host.returncode:raise RuntimeError(stdout+stderr)
  Image.open(bmp).save(bmp.with_suffix('.png'));bmp.unlink();print('CAPTURED',bmp.with_suffix('.png'))
 finally:
  for process in processes:
   if process.poll() is None:process.kill();process.wait()
  config.write_bytes(original)
if __name__=='__main__':main()
