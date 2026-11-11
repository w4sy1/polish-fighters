"""Real loopback TCP test, not physical device or game integration.
Run: python tests/test_room_tcp.py --runner /path/to/room-host-runner
"""
import argparse,json,platform,socket,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROFILE='a'*64
class Client:
 def __init__(self,port):
  self.socket=socket.create_connection(('127.0.0.1',port),timeout=3);self.socket.settimeout(3);self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1);self.stream=self.socket.makefile('rb')
 def send(self,**message):self.socket.sendall(json.dumps(message,separators=(',',':')).encode()+b'\n')
 def until(self,op,predicate=lambda x:True):
  deadline=time.monotonic()+3
  while time.monotonic()<deadline:
   line=self.stream.readline(8192)
   if not line:raise AssertionError('Connection closed waiting for '+op)
   value=json.loads(line)
   if value.get('op')=='error' and op!='error':raise AssertionError(value)
   if value.get('op')==op and predicate(value):return value
  raise AssertionError('No matching message: '+op)
 def close(self):
  self.stream.close();self.socket.close()
def run(runner,count):
 process=subprocess.Popen([str(Path(runner).resolve()),str(count)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 clients=[];extra=[]
 try:
  line=process.stdout.readline();assert line.startswith('LISTEN '),line+process.stderr.read()
  port=int(line.rsplit(':',1)[1])
  bad=Client(port);extra.append(bad);bad.send(op='hello',protocol=1,profile='b'*64,name='wrong');assert 'mismatch' in bad.until('error')['reason']
  malformed=Client(port);extra.append(malformed);malformed.socket.sendall(b'not-json\n');assert 'JSON' in malformed.until('error')['reason']
  oversize=Client(port);extra.append(oversize);oversize.socket.sendall(b'x'*4100+b'\n');assert 'exceed' in oversize.until('error')['reason']
  # Fragment the first greeting across TCP writes; the host must not treat reads as messages.
  first=Client(port);clients.append(first);hello=json.dumps({'op':'hello','protocol':1,'profile':PROFILE,'name':'player0'}).encode()+b'\n'
  for start in range(0,len(hello),7):
   first.socket.sendall(hello[start:start+7]);time.sleep(0.002)
  assert first.until('welcome')['slot']==0
  first.send(op='start');assert 'two devices' in first.until('error')['reason']
  for index in range(1,count):
   peer=Client(port);clients.append(peer);peer.send(op='hello',protocol=1,profile=PROFILE,name=('Player \"Two\" \\ name' if index==1 else 'player'+str(index)));assert peer.until('welcome')['slot']==index
  ninth=Client(port);extra.append(ninth);ninth.send(op='hello',protocol=1,profile=PROFILE,name='extra');assert 'full' in ninth.until('error')['reason']
  for client in clients:client.send(op='ready',value=True)
  snapshot=first.until('lobby',lambda m:len(m['peers'])==count and all(p['ready'] for p in m['peers']))
  assert snapshot['peers'][1]['name']=='Player \"Two\" \\ name'
  first.send(op='start')
  for client in clients:assert client.until('start')['seed']==42
  expected=['rc' if i%2 else 'l' for i in range(count)]+['']*(8-count)
  first_queued=False
  for frame in range(30):
   for index in reversed(range(count)):
    if index!=0 or not first_queued:clients[index].send(op='input',frame=frame,keys=expected[index],slot=7-index,functions='15' if index==0 else '',unlock=3 if index==0 else 0)
   first_queued=False
   for client in clients:
    tick=client.until('frame');assert tick['frame']==frame and tick['inputs']==expected and tick['functions']=='15' and tick['unlock']==3,tick
   for index,client in enumerate(clients):
    client.send(op='checksum',frame=frame,state='c'*64)
    if index==0 and frame<29:
     client.send(op='input',frame=frame+1,keys=expected[0],functions='15',unlock=3)
     first_queued=True;time.sleep(0.003)
   for client in clients:assert client.until('checked')['frame']==frame
  # Divergent state must stop the room; it cannot be accepted silently.
  for index,client in enumerate(clients):client.send(op='input',frame=30,keys=expected[index],slot=7-index)
  for client in clients:client.until('frame')
  first.send(op='checksum',frame=30,state='c'*64)
  clients[1].send(op='checksum',frame=30,state='d'*64)
  assert first.until('abort')['reason']
  return {'devices_as_tcp_clients':count,'frames':30,'fragmented_greeting':True,'full_room_rejected':True,'wrong_profile_rejected':True,'malformed_rejected':True,'oversize_rejected':True,'desync_aborted':True}
 finally:
  for client in clients+extra:
   try:client.close()
   except OSError:pass
  process.terminate()
  try:process.wait(timeout=3)
  except subprocess.TimeoutExpired:process.kill();process.wait()
def interruption_case(runner,timeout=False,unauthorized=False,queued=None):
 process=subprocess.Popen([str(Path(runner).resolve()),'2','150' if timeout else '5000'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 clients=[]
 try:
  line=process.stdout.readline();assert line.startswith('LISTEN ');port=int(line.rsplit(':',1)[1])
  for slot in range(2):
   peer=Client(port);clients.append(peer);peer.send(op='hello',protocol=1,profile=PROFILE,name='peer'+str(slot));peer.until('welcome');peer.send(op='ready',value=True)
  clients[0].until('lobby',lambda v:len(v['peers'])==2 and all(p['ready'] for p in v['peers']))
  clients[0].send(op='start')
  for peer in clients:peer.until('start')
  if queued:
   for peer in clients:peer.send(op='input',frame=0,keys='')
   for peer in clients:peer.until('frame')
   clients[0].send(op='checksum',frame=0,state='c'*64)
   clients[0].send(op='input',frame=2 if queued=='order' else 1,keys='r')
   if queued=='duplicate':clients[0].send(op='input',frame=1,keys='r')
   assert ('out-of-order' if queued=='order' else 'duplicate queued') in clients[0].until('error')['reason']
  elif unauthorized:
   clients[1].send(op='input',frame=0,keys='',functions='1')
   assert 'only the host' in clients[1].until('error')['reason']
   clients[0].until('abort')
  elif timeout:
   # Keep one endpoint alive; the missing endpoint must abort the waiting frame.
   clients[0].send(op='input',frame=0,keys='r')
   deadline=time.monotonic()+2;aborted=False
   while time.monotonic()<deadline:
    clients[0].send(op='ping')
    value=json.loads(clients[0].stream.readline())
    if value.get('op')=='abort':aborted=True;break
    assert value.get('op')=='pong',value
    time.sleep(0.025)
   assert aborted,'stalled endpoint did not abort room'
  else:
   clients[1].close();clients[0].until('abort')
  return {'test':'queued_'+queued if queued else 'unauthorized_global_command' if unauthorized else 'idle_timeout' if timeout else 'disconnect','passed':True}
 finally:
  for peer in clients:
   try:peer.close()
   except OSError:pass
  process.terminate()
  try:process.wait(timeout=3)
  except subprocess.TimeoutExpired:process.kill();process.wait()

def main():
 p=argparse.ArgumentParser();p.add_argument('--runner',required=True);p.add_argument('--output',type=Path,default=ROOT/'validation/network/tcp-results.json');a=p.parse_args();results=[]
 for count in range(2,9):
  results.append(run(a.runner,count));print('PASS:',count,'separate TCP clients, 30 synchronized frames')
 interruptions=[interruption_case(a.runner),interruption_case(a.runner,timeout=True),interruption_case(a.runner,unauthorized=True),interruption_case(a.runner,queued='duplicate'),interruption_case(a.runner,queued='order')]
 print('PASS: disconnect and stalled-peer timeout abort')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'scope':'real OS loopback sockets on one '+platform.system()+' machine; not a physical-device/gameplay test','results':results,'interruptions':interruptions},indent=2)+'\n')
if __name__=='__main__':main()
