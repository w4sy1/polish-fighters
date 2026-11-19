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
-- Nickname play: no password; the server's nick key is kept per server so this device can reclaim the nick.
client.token=nil;client.room=nil
assert(client.nick_key('https://accounts.example')==nil)
assert(client.request('https://accounts.example','login',{nick=true,name='Kuba'}))
assert(wire.payload.nick==true and wire.payload.name=='Kuba' and not wire.payload.password)
response={token=string.rep('n',32),name='kuba',nick_key=string.rep('k',43)};client.tick()
assert(client.token and client.notice:find('Grasz jako kuba'))
assert(document.online_nick=='kuba' and client.nick_key('https://accounts.example')==string.rep('k',43))
assert(not document.token and not document.password,'session persisted')
client.token=nil
assert(client.request('https://accounts.example','login',{nick=true,name='x'}));response={error='Nick in use'};client.tick()
assert(client.notice:find('zajęty'))
-- The online screen asks for the on-screen keyboard only while a field is selected, and nick typing plays on Enter.
local screen=require('polish-fighters/online_screen')
local state,typing={},nil
local context={text_input=function(active)typing=active end,action=function()end}
screen.open(state)
assert(state.hub_online.nick=='kuba','saved nick not offered')
local function frame(input)
 input.keys=input.keys or {};input.click=input.click or false;input.pointer_x=input.pointer_x or -1;input.pointer_y=input.pointer_y or -1
 screen.update(state,input,context)
end
frame({});assert(typing==false)
screen.activate(state,'field:nick',context);frame({text='_7 ź!'})
assert(typing==true and state.hub_online.nick=='kuba_7','nick typing: '..state.hub_online.nick)
frame({text='\n'})
assert(client.pending and wire.payload.nick==true and wire.payload.name=='kuba_7')
assert(wire.payload.nick_key==string.rep('k',43))
response={token=string.rep('m',32),name='kuba_7',nick_key=string.rep('k',43)};client.tick()
screen.activate(state,'back',context);assert(typing==false and state.hub_online==nil)
print('PASS: actual account response state, origin binding, room list, publish, logout, nick play and no persisted credentials')
