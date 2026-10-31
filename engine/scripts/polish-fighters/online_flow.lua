return function(base)
 local update=base.update
 local client=require('polish-fighters/online_client')
 function base.update(state,...)
  client.tick()
  local result=update(state,...)
  local session=state.network and state.network.session
  if client.host_started and client.room and not client.pending and session and
    (session.phase=='idle' or session.phase=='failed') then
   client.host_started=false
   client.request(client.origin,'delete-room',{})
  end
  return result
 end
 return base
end
