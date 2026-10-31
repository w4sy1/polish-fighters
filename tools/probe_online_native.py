"""Native HTTP account client against an ephemeral real local service, no real user accounts."""
import json
import os
import secrets
import shutil
import subprocess
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from account_service import Service,handler

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/online-native-2026-10-31'
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 runner=OUT/'runner';runner.mkdir(exist_ok=True)
 shutil.copy2(ROOT/'engine/build/windows/x64/native/Release/openlf2.exe',runner/'LittleFighters.exe')
 for dll in (ROOT/'engine/out/LittleFighters-pack-ai-2026-10-31').glob('*.dll'):shutil.copy2(dll,runner/dll.name)
 service=Service(':memory:');server=ThreadingHTTPServer(('127.0.0.1',0),handler(service))
 server.daemon_threads=True
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 endpoint='http://127.0.0.1:'+str(server.server_address[1])
 username='probe_'+secrets.token_hex(4);password=secrets.token_urlsafe(24)
 fixture=OUT/'fixture';fixture.mkdir(exist_ok=True)
 (fixture/'package.manifest').write_text('id=online-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nextend=base/ui/flow|flow.lua\n')
 script='''return function(base)
 local create,update,describe=base.create,base.update,base.describe
 local client=require('polish-fighters/online_client')
 local endpoint=ENDPOINT
 local credentials={name=USERNAME,password=PASSWORD}
 local phase=0
 function base.create(options)
  local state=create(options)
  assert(client.request(endpoint,'register',credentials));return state
 end
 function base.update(state,...)
  local result=update(state,...)
  if not client.pending and phase<10 then
   phase=phase+1
   if phase==1 then assert(client.token,'native registration failed');assert(client.request(endpoint,'list-rooms',{}))
   elseif phase==2 then assert(#client.rooms==0);client.publish_port=12345
    assert(client.request(endpoint,'publish-room',{name='Native test',host='127.0.0.1',port=12345,capacity=4,profile='lf2-classic'}))
   elseif phase==3 then assert(client.room);client.navigate=nil;client.pending_join=nil;assert(client.request(endpoint,'list-rooms',{}))
   elseif phase==4 then assert(#client.rooms==1,'room count='..#client.rooms..' '..client.notice);assert(client.request(endpoint,'delete-room',{}))
   elseif phase==5 then assert(not client.room);assert(client.logout())
   elseif phase==6 then assert(not client.token);assert(client.request(endpoint,'login',credentials))
   elseif phase==7 then assert(client.token);assert(client.logout())
   elseif phase==8 then assert(not client.token);assert(client.request('http://192.0.2.1','login',credentials))
   elseif phase==9 then assert(client.notice:find('HTTPS'),'remote plaintext HTTP was not rejected');phase=10 end
  end
  return result
 end
 function base.describe(state)
  assert(phase==10,'native account workflow incomplete')
  return describe(state)..' online_probe=true'
 end
 return base
end
'''
 for key,value in {'ENDPOINT':endpoint,'USERNAME':username,'PASSWORD':password}.items():script=script.replace(key,json.dumps(value))
 (fixture/'flow.lua').write_text(script)
 command=[str(runner/'LittleFighters.exe'),'--installer',str(ROOT/'../downloads/LF2_v2.0a.exe'),
  '--scripts',str(ROOT/'engine/scripts'),'--mod',str(fixture),'--hub-menu','--input-trace','*40000',
  '--config-dir',str(OUT/'config')]
 try:
  result=subprocess.run(command,capture_output=True,text=True,timeout=90)
  log=result.stdout+result.stderr
  assert result.returncode==0,(result.returncode,log[-1500:])
  assert 'online_probe=true' in log
  settings=(OUT/'config/config.json').read_text()
  assert password not in settings and username not in settings and '"token"' not in settings
  ui_command=[str(runner/'LittleFighters.exe'),'--installer',str(ROOT/'../downloads/LF2_v2.0a.exe'),
   '--scripts',str(ROOT/'engine/scripts'),'--hub-menu','--config-dir',str(OUT/'ui-config'),
   '--input-trace','@600_323!,@600_323,@100_174!,@100_174,^d^e^m^o,@100_220!,@100_220,^d^e^m^o^p^a^s^s^w^o^r^d^1^2,*2',
   '--renderer','software','--capture-frame',str(OUT/'account.bmp')]
  env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
  ui=subprocess.run(ui_command,capture_output=True,text=True,timeout=30,env=env)
  assert ui.returncode==0 and 'online=true' in ui.stdout,ui.stderr
  (OUT/'run.log').write_text(log)
  (OUT/'summary.json').write_text(json.dumps({'pass':True,'register':True,'login':True,'list_publish_delete':True,
   'logout':True,'remote_plain_http_rejected':True,'credentials_not_persisted':True,'scope':'local HTTP service; public HTTPS deployment not tested'},indent=2))
  print('PASS: native async register/login/room list/publish/delete/logout; remote HTTP rejected; no credentials in settings')
 finally:server.shutdown();server.server_close();service.db.close()
