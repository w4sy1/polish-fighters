return function(base)
 local create=base.create
 local client=require('polish-fighters/online_client')
 local transport=require('base/game/network')
 function base.create(options)
  local join=client.pending_join
  -- Rooms found or published through the account server are internet matches: the
  -- room leader then picks the larger input delay that hides a long round trip.
  if join or client.room then
   local copy={};for key,value in pairs(options) do copy[key]=value end
   copy.network_internet=not join or join.internet~=false;options=copy
  end
  if join then
   client.pending_join=nil;transport.next_room=true
   options.network_port=join.port;options.network_relay=join.relay
  end
  local state=create(options)
  if join then
   base.begin(state,join.host,join.address)
   if join.host and join.internet~=false then client.host_started=true end
  end
  return state
 end
 return base
end
