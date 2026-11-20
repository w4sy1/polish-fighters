-- The simple "Play online" screen: quick login, room list, relay join, publishing and LAN.
local clock=0
local server={relay=true,rooms={}}
local inflight
local requests={}
engine={read_settings=function() return {} end,write_settings=function() return true end,
 network_time=function() return clock end,random=function() return 42 end,
 json_encode=function(value) return value end,json_decode=function(raw) return raw end,
 account=function(action,endpoint,operation)
  if action=='start' then inflight=operation;requests[#requests+1]=operation;return true end
  local operation=inflight;inflight=nil
  if operation=='login' then return {token=string.rep('x',32),name='Gosc_1'} end
  if operation=='list-rooms' then return {relay=server.relay,rooms=server.rooms} end
  if operation=='publish-room' then return {id='room1'} end
  if operation=='relay-ticket' then return {ticket=string.rep('t',20),relay={host='203.0.113.10',port=8766}} end
  return {}
 end}
package.loaded['polish-fighters/dashboard_model']={current=function() return {room_capacity=2} end}
local client=require('polish-fighters/online_client')
local screen=require('polish-fighters/online_screen')
local catalog=require('base/game/catalog')
local actions={}
local context={action=function(id) actions[#actions+1]=id end,text_input=function() end}
local function run(state,frames)
 for _=1,frames or 20 do
  clock=clock+100;client.tick()
  if state.hub_online then screen.update(state,{keys={},nav={}},context) end
 end
end
local function reset()
 actions,requests={},{};client.pending_join=nil;client.navigate=nil;client.notice=''
end

-- Join: logging in as a guest lists the rooms, and a relay room becomes a relay join.
server.rooms={{id='r1',host='',port=12345,relay=true,profile=catalog.profile_id,name='Pokoj'}}
local state={};screen.open(state,true)
screen.activate(state,'find',context);run(state)
assert(client.token and #client.rooms==1,'quick join did not log in and list rooms')
local join
for _,row in ipairs(screen.rows(state.hub_online)) do if row[1]:sub(1,5)=='join:' then join=row[1] end end
assert(join,'listed room has no join row')
screen.activate(state,join,context);run(state,5)
assert(actions[1]=='network' and client.pending_join.relay and not state.hub_online,'relay join did not start')

-- Publishing asks the server again, so an earlier list without the relay does not block it.
reset();server.relay=false
state={};screen.open(state,true);screen.activate(state,'publish',context);run(state)
assert(client.notice:find('Przekaźnik niedostępny',1,true) and #actions==0)
reset();server.relay=true
state={};screen.open(state,true);screen.activate(state,'publish',context);run(state)
assert(requests[1]=='list-rooms','publish used a stale relay flag instead of a fresh list')
assert(actions[1]=='network' and client.pending_join.host,'room was not published after the relay returned')
-- ...and the other way round: a relay that went away is noticed before publishing.
reset();server.relay=false;client.pending_join=nil;client.room=nil
state={};screen.open(state,true);screen.activate(state,'publish',context);run(state)
assert(#actions==0 and client.notice:find('Przekaźnik niedostępny',1,true),'published with a relay that is gone')

-- LAN: loopback is refused, IPv4:port joins directly without the internet input delay.
reset()
state={};screen.open(state,true);screen.activate(state,'local',context)
state.hub_online.address='127.0.0.1';screen.activate(state,'find',context)
assert(#actions==0 and client.notice:find('IPv4',1,true))
state.hub_online.address='192.168.1.5:12346';screen.activate(state,'find',context)
local lan=client.pending_join
assert(actions[1]=='network' and lan.address=='192.168.1.5' and lan.port==12346 and lan.internet==false)
print('PASS simple online: guest join, fresh relay check before publishing, LAN address')
