"""Actual native peers through production Java relay; radio is replaced by loopback."""
import json
import re
import socket
import subprocess
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/hero-update-2026-11-06/bluetooth'

def main(mixed=False,data_root=None,stage_root=None):
    OUT.mkdir(parents=True,exist_ok=True)
    java=ROOT/'engine/build/studio-jdk17/jdk-17.0.18+8/bin'
    classes=OUT/'classes';classes.mkdir(exist_ok=True)
    source=ROOT/'engine/android/app/src/main/java/io/github/openlf2/openlf2/StreamRelay.java'
    subprocess.run([str(java/'javac.exe'),'-d',str(classes),str(source),
        str(ROOT/'tests/StreamRelayTest.java'),str(ROOT/'tests/StreamRelayServer.java')],check=True)
    unit=subprocess.run([str(java/'java.exe'),'-cp',str(classes),'StreamRelayTest'],capture_output=True,text=True,check=True,timeout=30)
    (OUT/'byte-tests.log').write_text(unit.stdout+unit.stderr)
    stage=Path(stage_root).resolve() if stage_root else ROOT/'engine/out/LittleFighters-Heroes-2026-11-06'
    data=Path(data_root).resolve() if data_root else stage
    fixture=OUT/'fixture';fixture.mkdir(exist_ok=True)
    (fixture/'package.manifest').write_text('id=relay-diagnostic\nversion=1\napi=1\nrequires=base@1\nextend=base/ui/flow|flow.lua\n')
    (fixture/'flow.lua').write_text('''return function(base)
 local update,describe=base.update,base.describe
 function base.update(s,...)
  local result=update(s,...)
  if s.active=='network' and s.network and s.network.session.phase=='failed' then
   error('RELAY_NETWORK_FAILURE: '..tostring(s.network.session.error))
  end
  if s.session and not s.bt_test_match then
   s.bt_test_match=true
   local catalog=require('base/game/catalog');local fighters=catalog.load();local slots={}
   for _,peer in ipairs(s.session.peers) do
    for row,f in ipairs(fighters) do if f.id==414-peer.slot*3 then
     slots[peer.slot]={kind='human',fighter=row,team=peer.slot+1};break
    end end
   end
   s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,
    fighters=fighters,backgrounds=catalog.backgrounds(),slots=slots,network=true})
   s.active='match';s.wait_release=nil
  end
  return result
 end
 function base.describe(s)
  return describe(s)..' relay_digest='..require('polish-fighters/sync_state').digest(s)
 end
 return base
end
''')
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
    common=[str(stage/'LittleFighters.exe'),'--installer',str(data/'LF2_v2.0a.exe'),
        '--scripts',str(data/'scripts'),'--mod',str(data/'scripts/polish-fighters'),
        '--mod',str(data/'content-packs/polish-originals'),
        '--seed','42','--input-trace','rbc*120', '--mod',str(data/'scripts/bluetooth-room')]
    if mixed: common+=['--mod',str(data/'content-packs/mixed-all')]
    common+=['--mod',str(fixture)]
    processes=[]
    try:
        host_log=(OUT/'host.log').open('w')
        host=subprocess.Popen(common+['--host','127.0.0.1','--port',str(port),'--config-dir',str(OUT/'host-config')],stdout=host_log,stderr=subprocess.STDOUT,text=True)
        processes.append(host)
        relay=subprocess.Popen([str(java/'java.exe'),'-cp',str(classes),'StreamRelayServer',str(port)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        processes.append(relay)
        proxy_port=int(relay.stdout.readline().strip())
        guest=subprocess.Popen(common+['--join','127.0.0.1','--port',str(proxy_port),'--config-dir',str(OUT/'guest-config')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        processes.append(guest)
        peer_out,peer_err=guest.communicate(timeout=90)
        host.wait(timeout=90);host_log.close()
        relay_out,relay_err=relay.communicate(timeout=10)
        host_out=(OUT/'host.log').read_text();peer_out+=peer_err
        (OUT/'host.log').write_text(host_out);(OUT/'guest.log').write_text(peer_out)
        (OUT/'relay.log').write_text(relay_out+relay_err)
        assert all(p.returncode==0 for p in processes),(host_out[-2000:],peer_out[-2000:],relay_err)
        counts=[int(re.findall(r'network_frames=(\d+)',log)[-1]) for log in (host_out,peer_out)]
        assert counts==[120,120],counts
        digests=[re.findall(r'relay_digest=([a-f0-9]{64})',log)[-1] for log in (host_out,peer_out)]
        assert digests[0]==digests[1],digests
        assert all(re.search(r'screen=match frame=1[12]\d',log) for log in (host_out,peer_out)),(host_out[-1500:],peer_out[-1500:])
        report=dict(pass_=True,production_java_relay=True,native_peers=2,
            synchronized_frames=counts,simulation_digest=digests[0],actual_match=True,
            custom_heroes_profile=True,full_mixed_profile=mixed,byte_integrity_tests=3,
            data_root=str(data),
            physical_bluetooth_tested=False,android_activity_tested=False)
        (OUT/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))
    finally:
        for process in processes:
            if process.poll() is None:process.kill();process.wait()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mixed',action='store_true')
    parser.add_argument('--data-root',type=Path)
    parser.add_argument('--stage-root',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.output: OUT=args.output.resolve()
    main(args.mixed,args.data_root,args.stage_root)
