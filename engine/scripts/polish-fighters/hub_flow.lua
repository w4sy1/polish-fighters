return function(base)
 local create,draw=base.create,base.draw
 local function visible(state)
  if not state.launch or not state.launch.hub_enabled or state.quit_dialog then return false end
  if state.active=='launch' then return false end
  if state.active=='match' then
   local match=state.match and state.match.match
   if state.session and match and not match.finished and (match.round_counter or 0)<101 then return false end
   return match and match.mode~=require('base/game/constants').modes.demo and
     (match.paused or match.finished or (match.round_counter or 0)>=101)
  end
  return state.active=='title' or state.active=='characters' or state.active=='ending' or
    state.active=='battle' or state.active=='championship'
 end
 local function button_area(state)
  if state.active=='match' then return 247,507,300,36 end
  if state.active=='characters' then return 247,0,300,30 end
  return 247,6,300,36
 end
 function base.create(options)
  local state=create(options)
  state.launch.hub_enabled=not options.legacy_menu
  state.launch.hub_available=options.profiles_available
  state.launch.hub_mode=options.profile_start and "profile" or "root"
  state.launch.hub_wait_release=options.profile_start==true
  return state
 end
 function base.overlay_update(state,input,context)
  if not visible(state) then return false end
  local x,y,w,h=button_area(state)
  if input.click and input.pointer_x>=x and input.pointer_x<=x+w and input.pointer_y>=y and input.pointer_y<=y+h then
   local match=state.active=='match' and state.match.match
   if match and not match.finished then
    state.quit_dialog=require('base/ui/quit_dialog').create('modules')
   else base.return_to_modules(state) end
   return true
  end
  return false
 end
 function base.draw(state,context)
  draw(state,context)
  if not visible(state) then return end
  local x,y,w,h=button_area(state)
  context.fill(x,y,w,h,25,48,80,240)
  if context.text then context.text('MODUŁY / MENU GŁÓWNE',397,y+7,'center',17,0xffffff,nil,nil,true)
  else require('base/ui/font').draw(context,'MODULY / MENU GLOWNE',397,y+9,1,nil,'center') end
 end
 return base
end
