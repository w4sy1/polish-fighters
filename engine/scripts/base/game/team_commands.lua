-- Commands travel as reserved combinations of existing LF2 input bits. This
-- keeps room transport and recordings deterministic without a second channel.
local constants=require('base/game/constants')
local commands={signals={come='udlrc',stay='udlrb',attack='udlrf',defend='udlrcb'}}
function commands.decode(keys)
 for _,d in ipairs({'u','d','l','r'}) do if not keys:find(d,1,true) then return nil end end
 local a,b,f=keys:find('c',1,true),keys:find('b',1,true),keys:find('f',1,true)
 if a and b and not f then return 'defend' end
 if a and not b and not f then return 'come' end
 if b and not a and not f then return 'stay' end
 if f and not a and not b then return 'attack' end
end
function commands.issue(state,slot,command)
 local owner=state.items[slot]
 if not owner or owner.hp<=0 or owner.record.kind~=0 or owner.team<=0 or owner.team==constants.teams.enemies then return end
 for i,v in pairs(state.items) do
  if i~=slot and not v.human and v.hp>0 and v.record.kind==0 and v.team==owner.team then
   v.team_command=command;v.team_command_owner=slot
   v.team_anchor_x,v.team_anchor_z=v.x_int,v.z_int
   v.order_x,v.order_z=constants.no_order,constants.no_order
   v.follow_order=command=='come' and 1 or 0
  end
 end
end
function commands.input(state,slot,keys)
 local command=commands.decode(keys)
 state.team_command_latch=state.team_command_latch or {}
 if command then
  if state.team_command_latch[slot]~=command then commands.issue(state,slot,command) end
  state.team_command_latch[slot]=command
  return ''
 end
 state.team_command_latch[slot]=nil
 return keys
end
function commands.control(state,index)
 local v=state.items[index];local command=v.team_command
 if not command or command=='attack' then return false end
 if v.hp<=0 or (state.stage_run and state.stage_run.last_phase==1) then return false end
 local owner=state.items[v.team_command_owner]
 if not owner or owner.hp<=0 or owner.team~=v.team then v.team_command=nil;return false end
 local x,z=v.team_anchor_x,v.team_anchor_z
 if command=='come' then x,z=owner.x_int,owner.z_int end
 local dx,dz=x-v.x_int,z-v.z_int
 -- At the anchor ordinary AI may fight nearby; it may not chase far away.
 if command~='come' and math.abs(dx)<55 and math.abs(dz)<20 then
  for _,enemy in pairs(state.items) do
   if enemy.hp>0 and enemy.record.kind==0 and enemy.team~=v.team and enemy.team~=0
      and math.abs(enemy.x_int-x)<90 and math.abs(enemy.z_int-z)<35 then return false end
  end
 end
 for _,key in ipairs({'up','down','left','right','attack','jump','defend'}) do
  v.previous_keys[key]=v.keys[key];v.keys[key]=false
 end
 local margin=command=='come' and 65 or 12
 if dx>margin then v.keys.right=true elseif dx< -margin then v.keys.left=true end
 if dz>12 then v.keys.down=true elseif dz< -12 then v.keys.up=true end
 if command=='defend' and math.abs(dx)<=margin and math.abs(dz)<=12 then v.keys.defend=true end
 return true
end
return commands
