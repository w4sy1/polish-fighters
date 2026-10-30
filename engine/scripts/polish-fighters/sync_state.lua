-- SPDX-License-Identifier: MIT
-- Simulation fingerprint, excluding local rendering, audio and recording state.
local sync={}
local omit={capture=true,display=true,view=true,stage=true,recording=true,record=true,
 sounds=true,sound_events=true,rumble=true,backgrounds=true,fighters=true,
 pointer_x=true,pointer_y=true,nav=true,sparks=true,direct_sounds=true}
local function serialize(value,seen)
 local kind=type(value)
 if kind=="nil" then return "n" end
 if kind=="boolean" then return value and "t" or "f" end
 if kind=="number" then return "d"..string.format("%.17g",value)..";" end
 if kind=="string" then return "s"..#value..":"..value end
 if kind~="table" then return "x" end
 if seen[value] then error("Cycle in simulation snapshot") end
 seen[value]=true
 local keys={}
 for key,v in pairs(value) do
  if (type(key)=="number" or type(key)=="string") and type(v)~="function" and not omit[key] then keys[#keys+1]=key end
 end
 table.sort(keys,function(a,b) if type(a)~=type(b) then return type(a)<type(b) end;return a<b end)
 local result={"{"}
 if value.record then result[#result+1]="record:"..tostring(value.record.id)..":"..tostring(value.record.kind)..";" end
 for _,key in ipairs(keys) do
  result[#result+1]=serialize(key,seen);result[#result+1]=serialize(value[key],seen)
 end
 result[#result+1]="}";seen[value]=nil;return table.concat(result)
end
function sync.digest(flow)
 local random,index=engine.random_state()
 local fighters,stage_index=require("base/game/stage").random_list()
 local state={active=flow.active,random=random,index=index,stage_fighters=fighters,stage_index=stage_index,unlock=require("base/game/unlock").flags}
 if flow.active=="match" then state.match=flow.match.match
 elseif flow.active=="characters" then
  local c=flow.characters;state.selection={slots=c.slots,menu=c.menu,options=c.options,countdown=c.countdown,order=c.order,cursor=c.cursor,computers=c.computers}
 elseif flow.active=="title" then state.selection={selected=flow.title.selection,input=flow.title.input}

 elseif flow.active=="battle" or flow.active=="championship" then state.selection=flow[flow.active]
 end
 return assert(engine.state_digest(serialize(state,{})))
end
return sync
