-- A hosted room listing must disappear when the host leaves the lobby (POWRÓT/F4 drops
-- state.network), must stay while the match runs, and the heartbeat must stop.
local response,clock={},0
local requests={}
engine={read_settings=function() return {} end,write_settings=function() return true end,
 json_encode=function(value) return '{}' end,json_decode=function() return response end,
 account=function(action,endpoint,op)
  if action=='start' then requests[#requests+1]=op;return true end
  return 'json'
 end,network_time=function() return clock end,network=function() return '0:0:' end}
local client=require('polish-fighters/online_client')
local frame_update
local flow=dofile(arg[1]..'/engine/scripts/polish-fighters/online_flow.lua')({update=function(state) if frame_update then frame_update(state) end end})
local function hosting()
 requests={};client.pending=nil;client.cleanup_room=nil
 client.token=string.rep('t',32);client.origin='https://accounts.example';client.room='room1'
 client.host_started=true;client.hosting_relay=true;client.heartbeat=clock+30000
 return {network={session={host=true,phase='lobby',capacity=2}}}
end
local function count(op) local n=0;for _,v in ipairs(requests) do if v==op then n=n+1 end end;return n end

-- Lobby: the listing stays and nothing is deleted.
local state=hosting()
for _=1,3 do flow.update(state) end
assert(count('delete-room')==0,'listing deleted while the lobby is open')

-- A running match keeps the listing even though the lobby screen is gone.
state.session=state.network.session;state.network.session.phase='ready';state.network=nil
for _=1,3 do flow.update(state) end
assert(count('delete-room')==0,'listing deleted during a match')
state.session=nil

-- POWRÓT (F4): flow.return_to_modules clears state.network. The next frames withdraw the room.
state=hosting()
flow.update(state);state.network=nil
flow.update(state);flow.update(state)
assert(count('delete-room')==1,'leaving the lobby did not delete the listing')
assert(not client.hosting_relay,'relay channel still offered after leaving')
response={ok=true};flow.update(state)
assert(client.room==nil,'room id kept after delete-room')
clock=clock+60000
for _=1,3 do flow.update(state) end
assert(count('heartbeat-room')==0,'heartbeat continued after leaving the lobby')
assert(count('delete-room')==1,'delete-room repeated')

-- A closed or failed session (Esc in the lobby) withdraws the listing too.
state=hosting();state.network.session.phase='failed'
flow.update(state);flow.update(state)
assert(count('delete-room')==1,'failed session kept the listing')
print('PASS online: leaving the lobby deletes the room listing, a match keeps it')

-- The list shows the host's nick: published names carry it, newer servers report the owner.
assert(client.listing_name('kuba','Pokój Polish Fighters')=='kuba: Pokój Polish Fighters')
assert(client.listing_name('kuba','kuba: Arena')=='kuba: Arena','nick added twice')
local long=client.listing_name('kuba',string.rep('ż',40))
assert(#long<=48 and long:sub(-2)=='ż','UTF-8 character split by the 48 byte limit')
assert(client.room_title({name='kuba: Arena',profile='lf2-classic'})=='kuba: Arena / lf2-classic')
assert(client.room_title({name='Arena',owner='ola',profile='lf2-classic'})=='ola: Arena / lf2-classic')
assert(client.room_title({name='ola: Arena',owner='ola',profile='lf2-classic'})=='ola: Arena / lf2-classic')
print('PASS online: room list shows the host nick')
