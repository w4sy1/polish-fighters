-- Both phones have explicitly joined the Bluetooth game, so start when both are ready.
return function(base)
 local update=base.update
 function base.update(s,...)
  local result=update(s,...)
  local session=s.network and s.network.session
  if session and session.room and session.phase=='lobby' then
   local network=require('base/game/network')
   if not session.bt_ready then network.room_ready(session,true);session.bt_ready=true end
   if session.host and not session.bt_started and #session.peers==2 then
    local ready=true
    for _,peer in ipairs(session.peers) do if not peer.ready then ready=false end end
    if ready then network.room_begin(session);session.bt_started=true end
   end
  end
  return result
 end
 return base
end
