-- Loaded only by Android Bluetooth startup. Normal LAN/legacy sessions are unchanged.
return function(base)
 local create=base.create
 function base.create(options)
  require('base/game/network').next_room=true
  local state=create(options)
  state.session.capacity=2
  return state
 end
 return base
end
