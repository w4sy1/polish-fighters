return function(base)
 local create=base.create
 local client=require('polish-fighters/online_client')
 local transport=require('base/game/network')
 function base.create(options)
  local join=client.pending_join
  if join then
   client.pending_join=nil;transport.next_room=true
   local copy={};for key,value in pairs(options) do copy[key]=value end
   copy.network_port=join.port;options=copy
  end
  local state=create(options)
  if join then base.begin(state,join.host,join.address);client.host_started=join.host end
  return state
 end
 return base
end
