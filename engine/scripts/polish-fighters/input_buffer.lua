-- LF2 samples human input every other tick. Preserve short attack/jump/block taps
-- until that sample; long holds and direction timing retain their original behavior.
local buffer={}
function buffer.prepare(state,held)
 if state.replay or state.paused then state.pf_input_pending=nil;return held end
 state.pf_input_pending=state.pf_input_pending or {}
 local sampled=state.input_phase==1
 local copy={};for key,value in pairs(held) do copy[key]=value end
 for slot=0,7 do
  local pending=state.pf_input_pending[slot] or {}
  local keys=held[slot] or ""
  for _,action in ipairs({"c","b","f"}) do
   if keys:find(action,1,true) then pending[action]=true end
   if sampled and pending[action] and not keys:find(action,1,true) then keys=keys..action end
  end
  copy[slot]=keys
  if sampled then state.pf_input_pending[slot]=nil else state.pf_input_pending[slot]=pending end
 end
 return copy
end
return buffer
