#!/usr/bin/env python3
"""Actual two-peer engine handshakes: matching builds/data pass, mismatches fail."""
import argparse,json,socket,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def available_port():
 with socket.socket() as server:server.bind(('127.0.0.1',0));return server.getsockname()[1]
def case(server_binary,client_binary,installer,label,server_mod=None,client_mod=None):
 port=available_port();common=['--installer',str(Path(installer).resolve()),'--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'engine/scripts/polish-fighters'),'--seed','42','--port',str(port),'--input-trace','*3']
 server_command=[str(Path(server_binary).resolve()),*common,'--host','127.0.0.1']
 if server_mod:server_command+=['--mod',str(server_mod)]
 host=subprocess.Popen(server_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  line=host.stdout.readline();assert 'Network listening' in line,line
  command=[str(Path(client_binary).resolve()),*common,'--join','127.0.0.1']
  if client_mod:command+=['--mod',str(client_mod)]
  peer=subprocess.run(command,capture_output=True,text=True,timeout=10)
  output,errors=host.communicate(timeout=10);host_output=line+output+errors;peer_output=peer.stdout+peer.stderr
  expected=label=='matching'
  passed=(host.returncode==0 and peer.returncode==0 and 'screen=title' in host_output and 'screen=title' in peer_output) if expected else ('profile mismatch' in host_output.lower() or 'profile mismatch' in peer_output.lower())
  out=ROOT/'validation/native-build/network';out.mkdir(parents=True,exist_ok=True)
  (out/(label+'-host.log')).write_text(host_output);(out/(label+'-client.log')).write_text(peer_output)
  print(label,'PASS' if passed else 'FAIL')
  if not passed:print(host_output,peer_output)
  return {'case':label,'passed':passed,'host_exit':host.returncode,'client_exit':peer.returncode}
 finally:
  if host.poll() is None:host.kill();host.wait()
def main():
 p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--old-engine',required=True);p.add_argument('--installer',required=True);a=p.parse_args()
 temp=ROOT/'userdata/profile-checks';temp.mkdir(parents=True,exist_ok=True)
 for name,value in [('a',b'A'),('b',b'B')]:
  path=temp/name;path.mkdir(exist_ok=True);(path/'probe.bin').write_bytes(value)
  (path/'package.manifest').write_text('id=profile-check\nversion=1\napi=1\nrequires=base@1\nasset=mods/profile-check/probe.bin|probe.bin\n')
 results=[case(a.engine,a.engine,a.installer,'matching'),case(a.engine,a.old_engine,a.installer,'native_mismatch'),case(a.engine,a.engine,a.installer,'asset_mismatch',temp/'a',temp/'b')]
 (ROOT/'validation/native-build/network/results.json').write_text(json.dumps(results,indent=2)+'\n')
 return 0 if all(r['passed'] for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
