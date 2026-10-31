local document={controls={keep=true}}
local response,wire,clock={},nil,0
engine={read_settings=function() return document end,write_settings=function(d)document=d;return true end,
 json_encode=function(value) wire=value;return '{}' end,json_decode=function()return response end,
 account=function(action,endpoint,op,body,bearer)
  if action=='start' then wire={payload=wire,endpoint=endpoint,operation=op,bearer=bearer};return true end
  return 'json'
 end,network_time=function()return clock end}
local client=require('polish-fighters/online_client')
assert(client.request('https://accounts.example','login',{name='test',password='never-store-this'}))
assert(not client.request('https://accounts.example','login',{}),'concurrent request allowed')
response={token=string.rep('x',32),name='test'};client.tick()
assert(client.token and document.account_server=='https://accounts.example' and document.controls.keep)
assert(not document.password and not document.token and not document.name,'credentials persisted')
assert(not client.request('https://other.example','list-rooms',{}),'bearer sent to another origin')
assert(client.request(client.origin,'list-rooms',{}))
response={rooms={{host='127.0.0.1',port=12345,profile='lf2-classic',name='Room'}}};client.tick()
assert(#client.rooms==1)
client.publish_port=12345
assert(client.request(client.origin,'publish-room',{}));response={id='room1'};client.tick()
assert(client.pending_join.host and client.pending_join.port==12345 and client.navigate)
assert(client.logout());response={ok=true};client.tick()
assert(not client.token and #client.rooms==0 and not client.room)
assert(client.request('https://accounts.example','login',{}));response={error='Invalid credentials'};client.tick()
assert(not client.token and client.notice:find('Invalid credentials'))
client.token=string.rep('y',32);client.origin='https://accounts.example'
assert(client.request(client.origin,'publish-room',{}));client.cancel_publish=true
response={id='cancelled'};client.tick()
assert(client.cleanup_room and not client.navigate and not client.pending_join)
client.tick();assert(client.pending.operation=='delete-room')
response={ok=true};client.tick();assert(not client.room)
print('PASS: actual account response state, origin binding, room list, publish, logout and no persisted credentials')
