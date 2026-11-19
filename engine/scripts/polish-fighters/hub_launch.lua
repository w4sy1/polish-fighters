return function(base)
 local create,update,draw,describe=base.create,base.update,base.draw,base.describe
 local nav=require("base/ui/navigation")
 local hub=require("polish-fighters/hub")
 local input_settings=require("polish-fighters/input_settings")
 local catalog=require("base/game/catalog")
 local font=require("base/ui/font")
 local variants=require("base/game/constants").font_variants
 local options=require("base/game/options")
 local packs=require("polish-fighters/pack_preferences")
 local locale=require('polish-fighters/menu_locale')
 local layout=require('polish-fighters/menu_layout')
 local sounds=require('base/game/sounds')
 local online=require('polish-fighters/online_screen')
 local mods=require('polish-fighters/mod_browser')
 function base.create(value)
  local state=create(value);state.hub_navigation=nav.create()
  local selected,problem=packs.read(hub.profiles)
  state.hub_selected=selected;state.hub_note=problem
  return state
 end
 local function activate(state,id,context)
  state.hub_note=nil;state.message=nil
  if id=='battle' or id=='settings' or id=='online' or id=='credits' or id=='language' or id=='status' then
   state.hub_mode=id
  elseif id:sub(1,5)=='lang_' then
   local saved,problem=locale.select(id:sub(6))
   if not saved then state.hub_note=locale.text('save_error')..tostring(problem) end
  elseif id:sub(1,7)=='status_' then
   local item=require('polish-fighters/module_inventory')[id:sub(8)]
   state.hub_note=locale.text('assets')..item.assets..' / '..locale.text('missing_files')..item.missing
  elseif id=='resume_campaign' then
   local saved,problem=require('base/game/campaign_save').options(catalog.profile_id)
   if saved then context.action(id) else state.hub_note=tostring(problem) end
  elseif id=='training' then context.action(id)
  elseif id=='diagnostics' then state.page='diagnostics';state.diagnostics=require('base/ui/diagnostics').create()
  elseif id=='unavailable' then state.hub_note=locale.text('offline')
  elseif id=='account' then online.open(state)
  elseif id=='mods' then mods.open(state)
  elseif id:sub(1,5)=='mode_' then
   local mode=id:sub(6)
   if mode=='demo' or mode=='replay' then context.action(mode)
   else state.hub_pending_mode=mode;state.hub_mode=state.hub_preselected and 'players' or 'library' end
  elseif id=='start_mode' then context.action(state.hub_pending_mode=='battle_setup' and 'battle' or state.hub_pending_mode or 'versus')
  elseif id=="packs" then
   local hide,problem=packs.hide_duplicates()
   if problem then state.hub_note=tostring(problem);return end
   state.hub_hide_duplicates=hide
   state.hub_pack_edit={}
   for _,entry in ipairs(hub.profiles) do state.hub_pack_edit[entry.id]=not state.hub_selected or state.hub_selected[entry.id]~=false end
   state.hub_mode="packs"
  elseif id:sub(1,7)=="toggle_" then
   local tag=id:sub(8);state.hub_pack_edit[tag]=not state.hub_pack_edit[tag]
  elseif id=="packs_all" then
   for _,entry in ipairs(hub.profiles) do state.hub_pack_edit[entry.id]=true end
  elseif id=="packs_duplicates" then state.hub_hide_duplicates=not state.hub_hide_duplicates
  elseif id=="packs_save" then
   local saved,problem=packs.save(hub.profiles,state.hub_pack_edit,state.hub_hide_duplicates)
   if saved then state.hub_selected=state.hub_pack_edit;state.hub_pack_edit=nil;state.hub_mode="library"
   else state.hub_note=tostring(problem) end
  elseif id=="packs_cancel" then state.hub_pack_edit=nil;state.hub_mode="library"
  elseif id=="root" or id=="library" then state.hub_mode=id;if id=="root" then state.hub_pending_mode=nil end
  elseif id=='profile_current' and state.hub_custom_profile then
   state.hub_preselected=true;state.hub_mode=state.hub_pending_mode and 'players' or 'profile'
  elseif id:sub(1,8)=="profile_" then
   local tag=id:sub(9)
   local audit=require('polish-fighters/module_inventory')[tag]
   if (audit and audit.missing>0) or (state.hub_available and state.hub_available[tag]==false) then
    state.hub_note="Brak lokalnego pakietu. Uruchom pełną paczkę Little Fighters.";return
   end
   if tag=='mixed' then
    local doc,problem=engine.read_settings()
    if problem then state.hub_note=tostring(problem);return end
    doc=type(doc)=='table' and doc or {};doc.little_fighters_pending_mode=state.hub_pending_mode
    local saved,problem=engine.write_settings(doc)
    if not saved then state.hub_note=tostring(problem);return end
    context.action(id)
    return
   end
   for _,entry in ipairs(hub.profiles) do
    if entry.id==tag then
     if catalog.profile_id==entry.profile then state.hub_preselected=true;state.hub_mode=state.hub_pending_mode and 'players' or 'profile'
     else
      local doc,problem=engine.read_settings()
      if problem then state.hub_note=tostring(problem);return end
      doc=type(doc)=='table' and doc or {}
      doc.little_fighters_pending_mode=state.hub_pending_mode
      local saved,problem=engine.write_settings(doc)
      if not saved then state.hub_note=tostring(problem);return end
      context.action(id)
     end
     return
    end
   end
  elseif id=="network" and catalog.profile_id=='mixed-all' then
   state.hub_note='Wspólna pula: najpierw testy lokalne. Sieć uruchom w osobnym profilu.'
  elseif id=='network' then
   require('base/game/network').next_room=true
   context.action('network')
  elseif id=="controls" then input_settings.open(state)
  elseif id=="options" then
   state.page="options";state.options=options.current();state.options_focus=1
  elseif id=="recording" then
   local values=require("base/ui/controls").current()
   state.page="recording";state.record={record=values.record,author=values.author,email=values.email,info=values.info}
  elseif id=="extras" or id=="maps" or id=="fighters" then
   state.hub_classic=true
   if id=="extras" then state.pf_panel="extras"
   elseif id=="maps" then state.pf_panel="maps"
   else state.pf_panel="combo-guide" end
  else context.action(id) end
 end
 function base.update(state,input,context)
  if not state.hub_enabled then return update(state,input,context) end
  if state.hub_wait_release then
   local pad=input.gamepad or {}
   if input.button or input.keys[13] or pad.a or pad.s then return end
   state.hub_wait_release=nil
  end
  if state.hub_edit then return input_settings.update(state,input) end
  if state.hub_online then return online.update(state,input,context) end
  if state.hub_mods then return mods.update(state,input,context) end
  if state.page~="menu" then return update(state,input,context) end
  if state.hub_classic then
   update(state,input,context)
   if not state.pf_panel then state.hub_classic=nil end
   return
  end
  local rows=hub.rows(state);local targets={}
  for index in ipairs(rows) do
   local x,y,w,h=layout.box(index,#rows);targets[#targets+1]=nav.target(x,y,x+w,y+h)
  end
  for index=1,2 do
   local x,y,w,h=layout.language(index);targets[#targets+1]=nav.target(x,y,x+w,y+h)
  end
  local mapped=nav.apply(state.hub_navigation,input,{page='hub:'..state.hub_mode,targets=targets,default=1,remember=true,autofocus=not input.click})
  local previous=state.hub_hover;state.hub_hover=nil
  for index,box in ipairs(targets) do
   if mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then
    state.hub_hover=index
    if mapped.click then
     activate(state,rows[index] and rows[index][1] or (index==#rows+1 and 'lang_pl' or 'lang_en'),context)
     sounds.direct(state,'ok');break
    end
   end
  end
  if previous and previous~=state.hub_hover and state.hub_hover then sounds.direct(state,'pass') end
  if mapped.nav.cancel and state.hub_mode~='root' then
   if state.hub_mode=='packs' then state.hub_pack_edit=nil;state.hub_mode='library'
   elseif state.hub_mode=='status' then state.hub_note=locale.text('audit_note')
  elseif state.hub_mode=='players' then state.hub_mode='library'
   elseif state.hub_mode=='library' and state.hub_pending_mode then state.hub_mode='battle'
   else state.hub_mode='root';state.hub_pending_mode=nil end
   sounds.direct(state,'cancel')
  end
  for _,sound in ipairs(sounds.flush(state)) do context.sound(sound.resource,sound.volume,sound.pan) end
 end

 local function text(context,value,x,y,variant,align)
  -- Lua menu positions can be half pixels (an odd-width language button).
  -- The native frame protocol requires integral text and sprite coordinates.
  font.draw(context,value,math.floor(x+0.5),math.floor(y+0.5),variant or variants.white,nil,align)
 end
 function base.draw(state,context)
  if state.hub_enabled and state.hub_mods then return mods.draw(state,context) end
  if not state.hub_enabled or state.page~="menu" or state.hub_classic then return draw(state,context) end
  if state.hub_online then return online.draw(state,context) end
  -- Use the same scenic backdrop, logo art, and bitmap font as LF2's own
  -- launch menu. Keep the artwork bright; the old blue wash and modern cards
  -- obscured the original interface.
  context.viewport(794,550,16,32,108)
  context.image('pe/menu_back'..(state.background or 0),0,0,true)
  context.sprite('pe/menu_clip',{0,41,434,80},155,96,true)
  context.sprite('pe/menu_clip',{434,41,62,68},589,96,true)
  local heading=state.hub_edit and locale.text('controls') or
   locale.text(({root='battle',profile='battle',library='modules',packs='modules',players='players'})[state.hub_mode] or state.hub_mode or 'battle')
  if state.hub_mode~='root' and not state.hub_edit then text(context,heading,397,181,variants.blue,'center') end
  if state.hub_edit then
   local set=state.hub_edit.sets[state.hub_player]
   text(context,"Wybierz gracza, urządzenie i kliknij akcję do przypisania.",397,199,variants.blue,"center")
   for index,row in ipairs(input_settings.rows(state,{})) do
    local selected=row[1]=="player:"..state.hub_player or index==state.hub_input_hover
    text(context,row[2],row[3]+row[5]/2,row[4]+4,selected and variants.white or variants.blue,"center")
   end
   local message=state.hub_control_message
   if state.hub_capture then message="Naciśnij nowy klawisz / przycisk. ESC anuluje."
   elseif set.device>0 then
    message="Pad "..set.device..": "..(state.hub_connected_pads and state.hub_connected_pads[set.device] and "WYKRYTY" or "NIEWYKRYTY - podłącz kontroler")
   end
   if not message and #input_settings.shared_keys(state)>0 then message="Wspólne klawisze graczy. Użyj USUŃ KOLIZJE Z INNYMI." end
   if message then text(context,message,397,480,variants.yellow,"center") end
   return
  end
  local rows=hub.rows(state)
  for index,row in ipairs(rows) do
   local x,y,w,h=layout.box(index,#rows)
   text(context,row[2],x+w/2,y+3,index==state.hub_hover and variants.white or variants.blue,'center')
  end
  for index,id in ipairs({'pl','en'}) do
   local x,y,w,h=layout.language(index)
   text(context,id:upper(),x+w/2,y+4,locale.id()==id and variants.white or variants.blue,'center')
  end
  text(context,locale.text('active')..hub.title(catalog.profile_id),16,492,variants.blue)
  if state.hub_mode=='credits' then
   text(context,locale.text('credit_text'),397,235,variants.white,'center')
   text(context,locale.text('credit_packs'),397,280,variants.white,'center')
  elseif state.hub_mode=='online' then text(context,locale.text('offline'),397,416,variants.yellow,'center')
  elseif state.hub_mode=='library' then text(context,locale.text('absent_turbo'),397,479,variants.yellow,'center')
  elseif state.hub_mode=='status' then text(context,locale.text('audit_note'),397,479,variants.yellow,'center')
  elseif state.hub_mode=='players' then text(context,locale.text('local_players'),397,370,variants.white,'center') end
  local message=state.hub_note or state.message
  text(context,tostring(message or locale.text('navigation')):sub(1,92),16,520,message and variants.yellow or variants.blue)

 end
 function base.describe(state)
  return describe(state).." hub="..tostring(state.hub_enabled==true)..":"..tostring(state.hub_mode)..
    " input_settings="..tostring(state.hub_edit~=nil).." input_capture="..tostring(state.hub_capture and state.hub_capture.row or 0)..
    " online="..tostring(state.hub_online~=nil)
 end
 return base
end
