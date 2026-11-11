"""Check the real native GitHub transport and render the update modal using a future fixture."""
import argparse
import os
import subprocess
from pathlib import Path

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    stage=args.stage.resolve(); out=args.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    for mode in ['http','notice','download','dismiss']:
        fixture=out/mode;fixture.mkdir(exist_ok=True)
        (fixture/'package.manifest').write_text('id=qa-updates\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nextend=base/ui/flow|flow.lua\n')
        http="""
 assert(engine.updates('start'))
 local until_time=engine.network_time()+8000
 local raw=engine.updates('poll')
 while raw=='pending' and engine.network_time()<until_time do raw=engine.updates('poll') end
 assert(type(raw)=='table' and #raw>0,'GitHub HTTP or parsing failed')
 s.qa_http=true
""" if mode=='http' else "s.available_update={name='Polish Fighters 0.12.0'}"
        (fixture/'flow.lua').write_text('''return function(base)
 local create,describe=base.create,base.describe
 function base.create(options)
  local s=create(options)
 '''+http+'''
  return s
 end
 function base.describe(s)
  return describe(s)..' qa_http='..tostring(s.qa_http==true)..' qa_notice='..tostring(s.update_notice~=nil)
 end
 return base
end
''')
        trace={'http':'*3','notice':'*3','download':'*3,@320_300,!,*2','dismiss':'*3,@460_300,!,*2'}[mode]
        cmd=[str(stage/'LittleFighters.exe'),'--installer',str(stage/'LF2_v2.0a.exe'),
             '--scripts',str(stage/'scripts'),'--mod',str(fixture),'--hub-menu','--input-trace',trace,
             '--renderer','software','--capture-frame',str(out/(mode+'.bmp'))]
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30,
                              env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
        log=result.stdout+result.stderr;(out/(mode+'.log')).write_text(log,encoding='utf-8')
        expected='qa_http=true' if mode=='http' else 'qa_notice='+str(mode=='notice').lower()
        assert result.returncode==0 and expected in log,(mode,log[-2000:])
        print('PASS native updates:',mode,flush=True)
