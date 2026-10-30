-- Developer-only automation. The production lobby requires explicit Ready and Start.
return function(screen)
 local update=screen.update
 function screen.update(s,input,context)
  update(s,input,context)
  local session=s.session
  if session.room and session.phase=="lobby" then
   local own
   for _,peer in ipairs(session.peers) do if peer.slot==session.slot then own=peer end end
   local network=require("base/game/network")
   if own and not own.ready and not s.test_ready then s.test_ready=true;network.room_ready(session,true) end
   if not require("room-check/config").hold_lobby and session.slot==0 and #session.peers==require("room-check/config").players then
    local ready=true;for _,peer in ipairs(session.peers) do ready=ready and peer.ready end
    if ready and not s.test_start then s.test_start=true;network.room_begin(session) end
   end
  end
 end
 return screen
end
