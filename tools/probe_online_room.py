"""Real local account directory -> host/join -> two native game processes.

Uses scripted UI actions and auto-ready QA helpers, not physical mouse/device input.
"""
import json
import re
import secrets
import socket
import subprocess
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from account_service import Service,handler

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/online-room-2026-10-31'
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 service=Service(':memory:');server=ThreadingHTTPServer(('127.0.0.1',0),handler(service))
 server.daemon_threads=True;threading.Thread(target=server.serve_forever,daemon=True).start()
 endpoint='http://127.0.0.1:'+str(server.server_address[1])
 fixture=OUT/'fixture';fixture.mkdir(exist_ok=True)
 (fixture/'package.manifest').write_text('id=online-room-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=polish-originals@1\nmodule=config|config.lua\nextend=base/ui/flow|flow.lua\nextend=base/ui/network|network.lua\n')
 (fixture/'config.lua').write_text('return {players=2}\n')
 (fixture/'network.lua').write_text((ROOT/'tools/room-check/network.lua').read_text().replace('room-check/config','online-room-probe/config'))
 (fixture/'flow.lua').write_text('''return function(base)
 local create,update,describe=base.create,base.update,base.describe
 local client=require('polish-fighters/online_client')
 local settings,phase,finished
 function base.create(options)
  settings=engine.read_settings().online_probe
  require('polish-fighters/dashboard_model').current().room_capacity=2
  local s=create(options)
  assert(client.request(settings.endpoint,'register',{name=settings.name,password=settings.password}))
  phase=1;return s
 end
 local function connect(s)
  s.network=require('base/ui/network').create(s.options)
  s.active='network';s.network_cli=true
 end
 function base.update(s,input,context)
  if finished then return end
  local result=update(s,input,context)
  if phase==1 and not client.pending then
   assert(client.token,client.notice)
   if settings.host then
    client.publish_port=settings.port
    assert(client.request(settings.endpoint,'publish-room',{host='127.0.0.1',port=settings.port,
      name='QA directory room',capacity=2,profile='polish-originals'}))
   else assert(client.request(settings.endpoint,'list-rooms',{})) end
   phase=2
  elseif phase==2 and not client.pending then
   if settings.host then
    assert(client.room,client.notice);client.navigate=nil;connect(s);phase=3
   elseif #client.rooms>0 then
    require('polish-fighters/online_screen').open(s.launch)
    require('polish-fighters/online_screen').activate(s.launch,'join:1',{
      action=function(action) assert(action=='network');connect(s) end})
    phase=3
   else assert(client.request(settings.endpoint,'list-rooms',{})) end
  end
  if s.session and s.session.room and not s.test_match then
   s.test_match=true
   local catalog=require('base/game/catalog');local fighters=catalog.load();local slots={}
   for _,peer in ipairs(s.session.peers) do slots[peer.slot]={kind='human',fighter=peer.slot+1,team=peer.slot+1} end
   s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,
    fighters=fighters,backgrounds=catalog.backgrounds(),slots=slots,network=true})
   s.active='match';s.wait_release=nil
  end
  if s.test_match and s.match.match.frame_number>=120 then
   finished=require('polish-fighters/sync_state').digest(s)
  end
  return result
 end
 function base.describe(s)
  assert(finished,'account-directory game did not reach 120 frames: '..client.notice)
  return describe(s)..' directory_room_digest='..finished
 end
 return base
end
''')
 stage=ROOT/'engine/out/LittleFighters-mixed-online-2026-10-31'
 processes=[];logs=[]
 try:
  for index in range(2):
   config=OUT/str(index);config.mkdir(exist_ok=True)
   (config/'config.json').write_text(json.dumps({'online_probe':{'endpoint':endpoint,'host':index==0,
    'port':port,'name':'qa_'+secrets.token_hex(5),'password':secrets.token_urlsafe(24)}}))
   cmd=[str(stage/'LittleFighters.exe'),'--installer',str(stage/'LF2_v2.0a.exe'),
    '--scripts',str(ROOT/'engine/scripts'),'--mod',str(ROOT/'content-packs/polish-originals'),
    '--mod',str(fixture),'--config-dir',str(config),'--seed','42','--input-trace','*5000']
   processes.append(subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True))
   if index==0:
    deadline=time.monotonic()+30
    while True:
     if processes[0].poll() is not None:raise RuntimeError('Host exited before opening room: '+''.join(processes[0].communicate()))
     try:
      with socket.create_connection(('127.0.0.1',port),timeout=.1):break
     except OSError:
      if time.monotonic()>deadline:raise TimeoutError('Directory host listener unavailable')
      time.sleep(.025)
  for index,process in enumerate(processes):
   stdout,stderr=process.communicate(timeout=60);log=stdout+stderr
   (OUT/f'{index}.log').write_text(log,encoding='utf8');logs.append(log)
   assert process.returncode==0,(index,process.returncode,log[-1800:])
  digests=[re.search(r'directory_room_digest=([a-f0-9]{64})',log)[1] for log in logs]
  assert digests[0]==digests[1],digests
  result={'pass':True,'native_processes':2,'match_frames':120,'digests':digests,
   'scope':'local HTTP account directory and direct TCP loopback; scripted actions/auto-ready; no public HTTPS or cross-device proof'}
  (OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 finally:
  for process in processes:
   if process.poll() is None:process.kill();process.wait()
  server.shutdown();server.server_close();service.db.close()
