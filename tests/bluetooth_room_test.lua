local root=arg[1]
local transport={next_room=false,ready_calls=0,start_calls=0}
function transport.room_ready(session,value) assert(value);transport.ready_calls=transport.ready_calls+1 end
function transport.room_begin(session) transport.start_calls=transport.start_calls+1 end
package.loaded['base/game/network']=transport
local network=assert(loadfile(root..'/engine/scripts/bluetooth-room/network.lua'))()({
 create=function(options) assert(transport.next_room);return {session={room=true,capacity=8}} end})
assert(network.create({}).session.capacity==2)
local update_calls=0
local flow=assert(loadfile(root..'/engine/scripts/bluetooth-room/flow.lua'))()({
 update=function() update_calls=update_calls+1;return true end})
local s={network={session={room=true,phase='lobby',host=true,peers={{ready=true},{ready=false}}}}}
assert(flow.update(s)==true);assert(transport.ready_calls==1 and transport.start_calls==0)
s.network.session.peers[2].ready=true
flow.update(s);flow.update(s)
assert(transport.ready_calls==1 and transport.start_calls==1)
s.network.session={room=true,phase='lobby',host=false,peers={{ready=true},{ready=true}}}
flow.update(s);assert(transport.ready_calls==2 and transport.start_calls==1)
s.network.session={room=false,phase='lobby',host=true,peers={{ready=true},{ready=true}}}
flow.update(s);assert(transport.ready_calls==2 and transport.start_calls==1)
assert(update_calls==5)
print('PASS: Bluetooth opts into existing two-player room, auto-readies once, host starts only with both ready; legacy untouched')
