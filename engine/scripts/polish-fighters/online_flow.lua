return function(base)
 local update=base.update
 local client=require('polish-fighters/online_client')
 function base.update(state,...)
  client.tick()
  local result=update(state,...)
  local session=state.network and state.network.session
  if session and session.host and session.phase=='lobby' then
   client.maintain_relay(session)
  end
  -- Leaving the lobby (POWRÓT/F4 drops state.network) or a closed/failed session ends
  -- the hosted room: withdraw its listing and stop the heartbeat. A running match keeps
  -- state.session, so the listing stays while the match is played.
  if client.host_started and client.room and not state.session and
    (not session or session.phase=='idle' or session.phase=='failed') then
   client.host_started=false;client.hosting_relay=nil;client.cleanup_room=true
  end
  return result
 end
 return base
end
