return function(base)
 local create,draw=base.create,base.draw
 local function visible(state)
  if not state.launch or not state.launch.hub_enabled or state.quit_dialog then return false end
  return true
 end
 local function button_area(state)
  return 574,6,214,32
 end
 function base.create(options)
  local state=create(options)
  state.launch.hub_enabled=not options.legacy_menu
  state.launch.hub_available=options.profiles_available
  local saved=engine and engine.read_settings and engine.read_settings() or {}
  if type(saved)~="table" then saved={} end
  local chosen=saved.little_fighters_start_profile
  local single_mobile=options.touch_device and chosen and chosen~='all' and chosen~='custom'
  state.launch.hub_mode=(options.profile_start or single_mobile) and "profile" or "root"
  state.launch.hub_wait_release=options.profile_start==true
  return state
 end
 function base.global_navigation_update(state,input,context)
  local f4=(input.functions or ''):find('4',1,true)~=nil
  local pressed=f4 and not state.hub_f4_held
  state.hub_f4_held=f4
  -- A local disconnect must remain possible while a peer is stalled.
  if state.quit_dialog and state.quit_dialog.kind=='modules' and state.session then
   local answer=require('base/ui/quit_dialog').update(state.quit_dialog,input,context)
   if answer=='exit' then base.return_to_modules(state)
   elseif answer=='close' then state.quit_dialog=nil;state.swallow_pointer=true end
   return true
  end
  if not visible(state) then return false end
  local x,y,w,h=button_area(state)
  if pressed or (input.click and input.pointer_x>=x and input.pointer_x<=x+w and input.pointer_y>=y and input.pointer_y<=y+h) then
   if state.active=='match' then
    -- Send the back action through the same deterministic input as the fight.
    -- A local menu intercept would strand the other network participant.
    if not f4 then input.functions=(input.functions or '')..'4' end
    return false
   end
   if context.text_input then context.text_input(false) end
   local match=state.active=='match' and state.match.match
   if state.session or (match and not match.finished) then
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
  if state.active=='characters' and context.text then
   local lines=require('polish-fighters/input_settings').selection_hint(
    state.options.touch_device or (state.touch_gamepad and state.touch_gamepad.visible),
    require('base/game/options').current().touch_layout,state.session and state.session.slot or 0)
   context.fill(0,512,794,38,16,27,47,240)
   for index,line in ipairs(lines) do context.text(line,8,515+(index-1)*16,'left',12,0xffffff,nil,nil,true) end
  elseif state.session and state.session.room and context.text then
   context.text('WSPÓLNY EKRAN | TY: GRACZ '..(state.session.slot+1),8,9,'left',13,0xffffff,nil,nil,true)
  end
  context.fill(x,y,w,h,25,48,80,240)
  local label=state.active=='match' and 'POSTACIE (F4)' or 'MENU / MODUŁY (F4)'
  if context.text then context.text(label,x+w/2,y+7,'center',15,0xffffff,nil,nil,true)
  else require('base/ui/font').draw(context,state.active=='match' and 'POSTACIE (F4)' or 'MENU / MODULY (F4)',x+w/2,y+9,1,nil,'center') end
 end
 return base
end
