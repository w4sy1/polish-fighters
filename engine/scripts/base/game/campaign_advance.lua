local constants=require('base/game/constants')
local advance={}
function advance.ready(state)
 local run=state.stage_run
 if state.mode~=constants.modes.stage or not run or run.result~=0 or run.shutter~=0 or run.phase_done~=1 then return false end
 for _,v in pairs(state.items) do
  if v.record.kind==0 and v.team==constants.teams.enemies then return false end
 end
 for _,entry in pairs(run.runtime[run.phase] or {}) do
  if (entry.count or 0)<(entry.total or 0) then return false end
 end
 local list=require('base/game/stage').list(run.source_path)
 local data=list[run.id];local phase=data and data.phases[run.phase]
 if not phase then return false end
 if run.last_phase==1 then return run.id%10~=9 and list[run.id+1]~=nil end
 local next_index=phase.when_clear_goto_phase~=-1 and phase.when_clear_goto_phase or run.phase+1
 local following=data.phases[next_index]
 return following~=nil and following.bound>phase.bound
end
function advance.input(driver,state,keys,enabled)
 local run=state and state.stage_run
 if not run or not enabled or state.paused or state.replay or state.finished then return keys end
 local token=tostring(run.id)..':'..tostring(run.phase)
 if driver.token~=token then driver.token=token;driver.cancelled=nil end
 if keys~='' then driver.cancelled=true;return keys end
 if not driver.cancelled and advance.ready(state) then return 'r' end
 return keys
end
function advance.follow(state,index)
 local v=state.items[index]
 if not state.stage_run or state.stage_run.last_phase==1 or v.hp<=0 or
    v.team_command=='stay' or v.team_command=='defend' or not advance.ready(state) then return false end
 local leader
 for slot=0,7 do
  local candidate=state.items[slot]
  if candidate and candidate.hp>0 and candidate.team==v.team and candidate.x_int>v.x_int+50 then
   if not leader or candidate.x_int>leader.x_int then leader=candidate end
  end
 end
 if not leader then return false end
 for _,key in ipairs({'up','down','left','right','attack','jump','defend'}) do
  v.previous_keys[key]=v.keys[key];v.keys[key]=false
 end
 v.keys.right=true
 if leader.z_int>v.z_int+12 then v.keys.down=true elseif leader.z_int<v.z_int-12 then v.keys.up=true end
 return true
end
return advance
