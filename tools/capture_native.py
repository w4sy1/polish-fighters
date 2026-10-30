#!/usr/bin/env python3
"""Capture classic native menu views on Linux. Requires Pillow and the capture shim.
Temporarily changes startup panels: do not run together with other tests/gameplay.
"""
import argparse,os,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--installer',required=True);p.add_argument('--capture-library',required=True);a=p.parse_args()
 source=ROOT/'engine/scripts/polish-fighters/classic_shell.lua';original=source.read_text()
 try:
  for panel in ['classic','extras','maps','packs','connection','account']:
   edited=original
   if panel!='classic':edited=edited.replace('s.pf_navigation=nav.create();return s','s.pf_navigation=nav.create();s.pf_panel="'+panel+'";return s')
   source.write_text(edited);bmp=ROOT/f'preview/classic-{panel}.bmp';bmp.parent.mkdir(exist_ok=True)
   env=os.environ.copy();env.update(PF_CAPTURE=str(bmp),PF_CAPTURE_FRAME='12',LD_PRELOAD=str(Path(a.capture_library).resolve()),SDL_VIDEODRIVER='offscreen',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
   command=[str(Path(a.engine).resolve()),'--installer',str(Path(a.installer).resolve()),'--scripts',str(ROOT/'engine/scripts'),'--mod',str(source.parent),'--renderer','software','--config-dir',str(ROOT/'userdata/classic-visual-qa')]
   result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=30)
   if result.returncode:raise RuntimeError(result.stdout+result.stderr)
   Image.open(bmp).save(bmp.with_suffix('.png'));bmp.unlink();print('CAPTURED',panel)
 finally:source.write_text(original)
if __name__=='__main__':main()
