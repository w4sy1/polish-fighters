-- In a network game the title menu is shared and reads only player keys (taps on menu items
-- are local). Touch players need the Hybrid Control stick and buttons there.
engine=setmetatable({},{__index=function() return function() return nil end end})
local flow=require('base/ui/flow')
assert(flow.hybrid_mode({active='title'})==nil,'local title must keep tap navigation')
assert(flow.hybrid_mode({active='title',session={room=true}})=='selection','network title has no touch controls')
assert(flow.hybrid_mode({active='title',session={room=true},quit_dialog={}})==nil,'controls shown over the quit dialog')
assert(flow.hybrid_mode({active='characters'})=='selection')
print('PASS network title: touch players get Hybrid Control to choose the mode')
