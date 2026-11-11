"""Native regression: disconnect swallows the old press, then accepts a new touch."""
import argparse,json,subprocess
from pathlib import Path

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();stage=args.stage.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    probe=out/'probe';probe.mkdir(exist_ok=True)
    (probe/'package.manifest').write_text('id=qa-network-return\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nextend=base/ui/flow|flow.lua\n')
    (probe/'flow.lua').write_text('''return function(base)
 local create=base.create
 function base.create(options)
  local s=create(options);s.active='title'
  s.session={room=true,phase='failed',error='qa-disconnect',frames=0,slot=0}
  s.network={session=s.session};return s
 end
 return base
end''')
    for name,trace,expected in [('old-press','c!@200_250,*3','root'),('new-press','c!@200_250,*3,!@200_250,*3','profile')]:
        config=out/name;config.mkdir(exist_ok=True)
        (config/'config.json').write_text(json.dumps({'version':1,'qa_keep':7,'options':{'touch_layout':'modern'}}))
        run=subprocess.run([str(stage/'LittleFighters.exe'),'--installer',str(stage/'LF2_v2.0a.exe'),
            '--scripts',str(stage/'scripts'),'--mod',str(probe),'--hub-menu','--config-dir',str(config),
            '--input-trace',trace],capture_output=True,text=True,timeout=30)
        log=run.stdout+run.stderr;(config/'run.log').write_text(log,encoding='utf-8')
        document=json.loads((config/'config.json').read_text())
        assert run.returncode==0 and 'hub=true:'+expected in log,log
        assert document['qa_keep']==7 and document['options']['touch_layout']=='modern'
        assert document['last_network_error']['reason']=='qa-disconnect'
        assert bytes.fromhex(document['last_network_error']['snapshot_hex'])
        print(name,'PASS',flush=True)
