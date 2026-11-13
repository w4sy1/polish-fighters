-- LF2 samples human input every other tick. Preserve short attack/jump/block taps
-- until that sample; long holds and direction timing retain their original behavior.
local buffer={}
function buffer.prepare(state,held)
 if state.replay then state.pf_input_pending=nil;state.pf_back_pending=nil;return held end
 local sampled=state.input_phase==1
 local copy={};for key,value in pairs(held) do copy[key]=value end
 -- Function keys, too, are consumed only every other simulation tick. Keep a
 -- short back press through the next sample, including while paused.
 local functions=held.functions or ''
 if functions:find('4',1,true) then state.pf_back_pending=true end
 if sampled and state.pf_back_pending and not functions:find('4',1,true) then functions=functions..'4' end
 copy.functions=functions
 if sampled then state.pf_back_pending=nil end
 if state.paused then state.pf_input_pending=nil;return copy end
 state.pf_input_pending=state.pf_input_pending or {}
 for slot=0,7 do
  local pending=state.pf_input_pending[slot] or {}
  local keys=held[slot] or ""
  local command=require('base/game/team_commands').decode(keys)
  if command then pending={command=keys} end
  if pending.command then
   copy[slot]=pending.command
   if sampled then state.pf_input_pending[slot]=nil else state.pf_input_pending[slot]=pending end
  else
  local directions=keys:gsub('[^udlr]','')
  if directions~='' then pending.directions=directions end
  if sampled and directions=='' and pending.directions then keys=keys..pending.directions end
  for _,action in ipairs({"c","b","f"}) do
   if keys:find(action,1,true) then pending[action]=true end
   if sampled and pending[action] and not keys:find(action,1,true) then keys=keys..action end
  end
  copy[slot]=keys
  if sampled then state.pf_input_pending[slot]=nil else state.pf_input_pending[slot]=pending end
  end
 end
 return copy
end
return buffer
