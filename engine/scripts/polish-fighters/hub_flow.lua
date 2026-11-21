return function(base)
 local create,draw=base.create,base.draw
 local function visible(state)
  if not state.launch or not state.launch.hub_enabled or state.quit_dialog then return false end
  return true
 end
 local function button_area(state)
  return 574,6,214,32
 end
 local function paused_locally(state)
  return not state.session and state.active=='match' and state.match and state.match.view and state.match.view.paused
 end
 local function show_button(state)
  if not visible(state) then return false end
  if state.active~='launch' then return true end
  local launch=state.launch
  return launch.page=='menu' and (launch.hub_mode=='profile' or launch.hub_mode=='battle')
 end
 function base.create(options)
  local state=create(options)
  state.launch.hub_enabled=not options.legacy_menu
  state.launch.hub_available=options.profiles_available
  state.launch.hub_android=options.touch_device
  local saved=engine and engine.read_settings and engine.read_settings() or {}
  if type(saved)~="table" then saved={} end
  if options.profile_load_failed then
   saved.little_fighters_pending_mode=nil
   if options.touch_device then saved.little_fighters_start_profile='lf_two' end
   engine.write_settings(saved)
   state.launch.hub_note=require('polish-fighters/menu_locale').text('profile_load_failed')
  end
  local chosen=saved.little_fighters_start_profile
  local single_mobile=options.touch_device and chosen and chosen~='all' and chosen~='custom'
  local active_profile=require('base/game/catalog').profile_id
  local managed_profile=type(active_profile)=='string' and active_profile:match('^mod%-')~=nil
  state.launch.hub_custom_profile=managed_profile and active_profile or nil
  state.launch.hub_mode=(options.profile_start or single_mobile or managed_profile) and "profile" or "root"
  state.launch.hub_preselected=options.profile_start or single_mobile or managed_profile
  if state.launch.hub_android and not options.profile_start then state.launch.hub_mode="root" end
  state.launch.hub_wait_release=options.profile_start==true
  local menu=saved.little_fighters_start_menu
  if menu=='battle' or menu=='settings' or menu=='online' or menu=='controls' or menu=='options' then
   state.launch.hub_mode=menu;saved.little_fighters_start_menu=nil;engine.write_settings(saved)
   if menu=='controls' then state.launch.hub_mode='settings';require('polish-fighters/input_settings').open(state.launch)
   elseif menu=='options' then state.launch.hub_mode='settings';state.launch.page='options';state.launch.options=require('base/game/options').current();state.launch.options_focus=1 end
  end
  local pending=saved.little_fighters_pending_mode
  local valid={versus=true,stage=true,championship=true,team_championship=true,battle_setup=true}
  if valid[pending] then
   state.launch.hub_pending_mode=pending;state.launch.hub_mode='players'
   saved.little_fighters_pending_mode=nil;engine.write_settings(saved)
  end
  if state.launch.hub_enabled and options.profiles_available and not options.profile_start
   and not saved.controls_guide_seen and state.launch.hub_mode=='root' and state.launch.page=='menu' then
   state.launch.hub_intro_guide=true
   state.launch.hub_classic=true
   state.launch.pf_panel='combo-guide'
   state.launch.pf_guide_message=true
   state.launch.pf_message=require('polish-fighters/combo_guide').basics
  end
  return state
 end
 local function return_to_main(state)
  base.return_to_modules(state)
  state.launch.hub_mode='root'
 end
 function base.global_navigation_update(state,input,context)
  local f4=(input.functions or ''):find('4',1,true)~=nil
  local pressed=f4 and not state.hub_f4_held
  state.hub_f4_held=f4
  -- A local disconnect must remain possible while a peer is stalled.
  if state.quit_dialog and state.quit_dialog.kind=='modules' and state.session then
   local answer=require('base/ui/quit_dialog').update(state.quit_dialog,input,context)
   if answer=='exit' then return_to_main(state)
   elseif answer=='close' then state.quit_dialog=nil;state.swallow_pointer=true end
   return true
  end
  if not visible(state) then return false end
  if not paused_locally(state) then state.paused_guide=nil end
  if state.paused_guide then
   if pressed or (input.keys and input.keys[27]) or (input.click and input.pointer_y and input.pointer_y>=460) then
    state.paused_guide=nil
   end
   return true
  end
  if paused_locally(state) and input.click and input.pointer_x and input.pointer_y
   and input.pointer_x>=10 and input.pointer_x<=240 and input.pointer_y>=6 and input.pointer_y<=38 then
   state.paused_guide=true
   return true
  end
  if pressed and state.active=='launch' and not state.session then
   local launch=state.launch
   if launch.hub_mode=='root' and (launch.page==nil or launch.page=='menu') and
    not launch.hub_edit and not launch.hub_online and not launch.hub_mods and not launch.pf_panel then
    return true
   end
   input.keys=input.keys or {}
   input.keys[27]=true
   return false
  end
  local escape=input.keys and input.keys[27]
  local back=escape and not state.hub_escape_held
  state.hub_escape_held=escape
  if back and not state.session and (state.active=='characters' or state.active=='battle' or state.active=='championship') then
   state.active='launch';state.launch.page='menu';state.launch.hub_mode='players';state.wait_release=true
   return true
  end
  local x,y,w,h=button_area(state)
  if pressed or (show_button(state) and input.click and input.pointer_x>=x and input.pointer_x<=x+w and input.pointer_y>=y and input.pointer_y<=y+h) then
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
   else return_to_main(state) end
   return true
  end
  return false
 end
 function base.draw(state,context)
  if context.text then
   local original=context;context={};for key,value in pairs(original) do context[key]=value end
   function context.text(value,...) return original.text(require('polish-fighters/menu_locale').translate(value),...) end
  end
  context.pf_selection_hint=state.launch and state.launch.hub_enabled and state.active=='characters'
  draw(state,context)
  if paused_locally(state) then
   local font=require('base/ui/font')
   local ascii=require('base/ui/hybrid_hud').ascii
   local function text(label,x,y,align)
    if context.text then context.text(label,x,y,align,14,0xffffff,nil,nil,true)
    else font.draw(context,ascii(label),x,y,1,nil,align) end
   end
   if state.paused_guide then
    context.fill(60,70,674,440,16,27,47,250)
    for index,line in ipairs(require('polish-fighters/combo_guide').basics) do
     text(line,80,88+(index-1)*29,'left')
    end
    context.fill(300,460,194,35,25,48,80,255)
    text('POWRÓT',397,468,'center')
    return
   end
   context.fill(10,6,230,32,25,48,80,240)
   text('STEROWANIE I PORADNIK',125,13,'center')
  end
  if not show_button(state) then return end
  local x,y,w,h=button_area(state)
  if state.active=='characters' and context.text then
   local lines=require('polish-fighters/input_settings').selection_hint(
    state.options.touch_device or state.hybrid.visible,state.session and state.session.slot or 0)
   context.fill(0,512,794,38,16,27,47,240)
   for index,line in ipairs(lines) do context.text(line,8,515+(index-1)*16,'left',12,0xffffff,nil,nil,true) end
  elseif state.session and state.session.room and context.text then
   context.text('WSPÓLNY EKRAN | TY: GRACZ '..(state.session.slot+1),8,9,'left',13,0xffffff,nil,nil,true)
  end
  context.fill(x,y,w,h,25,48,80,240)
  local label=state.active=='match' and 'POSTACIE (F4)' or 'POWRÓT (F4)'
  if context.text then context.text(label,x+w/2,y+7,'center',15,0xffffff,nil,nil,true)
  else require('base/ui/font').draw(context,state.active=='match' and 'POSTACIE (F4)' or 'POWROT (F4)',x+w/2,y+9,1,nil,'center') end
 end
 return base
end
