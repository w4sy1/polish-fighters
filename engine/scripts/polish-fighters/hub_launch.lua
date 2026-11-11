return function(base)
 local create,update,draw,describe=base.create,base.update,base.draw,base.describe
 local nav=require("base/ui/navigation")
 local hub=require("polish-fighters/hub")
 local input_settings=require("polish-fighters/input_settings")
 local catalog=require("base/game/catalog")
 local font=require("base/ui/font")
 local options=require("base/game/options")
 local packs=require("polish-fighters/pack_preferences")
 local online=require('polish-fighters/online_screen')
 function base.create(value)
  local state=create(value);state.hub_navigation=nav.create()
  local selected,problem=packs.read(hub.profiles)
  state.hub_selected=selected;state.hub_note=problem
  return state
 end
 local function activate(state,id,context)
  state.hub_note=nil
  if id=="packs" then
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
  elseif id=="root" or id=="library" then state.hub_mode=id
  elseif id:sub(1,8)=="profile_" then
   local tag=id:sub(9)
   if state.hub_available and state.hub_available[tag]==false then
    state.hub_note="Brak lokalnego pakietu. Uruchom pełną paczkę Little Fighters.";return
   end
   if tag=='mixed' then
    context.action(id)
    return
   end
   for _,entry in ipairs(hub.profiles) do
    if entry.id==tag then
     if catalog.profile_id==entry.profile then state.hub_mode="profile"
     else context.action(id) end
     return
    end
   end
  elseif id=="network" and catalog.profile_id=='mixed-all' then
   state.hub_note='Wspólna pula: najpierw testy lokalne. Sieć uruchom w osobnym profilu.'
  elseif id=='network' then online.open(state)
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
  if state.page~="menu" then return update(state,input,context) end
  if state.hub_classic then
   update(state,input,context)
   if not state.pf_panel then state.hub_classic=nil end
   return
  end
  local rows=hub.rows(state);local targets={}
  for index in ipairs(rows) do
   local column=math.floor((index-1)/9);local row=(index-1)%9
   targets[#targets+1]=nav.target(35+column*385,160+row*37,405+column*385,192+row*37)
  end
  local mapped=nav.apply(state.hub_navigation,input,{page="hub:"..state.hub_mode,targets=targets,default=1})
  state.hub_hover=nil
  for index,box in ipairs(targets) do
   if mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then
    state.hub_hover=index
    if mapped.click then activate(state,rows[index][1],context);break end
   end
  end
  if mapped.nav.cancel and state.hub_mode~="root" then state.hub_mode="root" end
 end
 local function text(context,value,x,y,size,color,align)
  if context.text then context.text(value,x,y,align or "left",size,color,nil,nil,true)
  else font.draw(context,value,x,y,1,nil,align) end
 end
 function base.draw(state,context)
  if not state.hub_enabled or state.page~="menu" or state.hub_classic then return draw(state,context) end
  if state.hub_online then return online.draw(state,context) end
  context.viewport(794,550,12,18,35)
  -- Reuse the owner's original LF2 menu illustration; no extra download is needed.
  context.image("pe/menu_back"..(state.background or 0),0,0,true)
  context.fill(0,0,794,550,8,13,27,75)
  context.fill(0,0,794,78,20,35,66)
  context.fill(0,76,794,2,224,72,92)
  context.fill(24,151,389,346,16,27,47,105)
  context.fill(416,151,365,346,16,27,47,105)
  local title=state.hub_edit and "USTAWIENIA STEROWANIA" or
      (state.hub_mode=="profile" and hub.title(catalog.profile_id):upper() or "LITTLE FIGHTERS")
  text(context,title,397,20,29,0xf0f5ff,"center")
  if state.hub_edit then
   local set=state.hub_edit.sets[state.hub_player]
   text(context,"Wybierz gracza, urządzenie i kliknij akcję do przypisania.",397,56,14,0xaac0dd,"center")
   for index,row in ipairs(input_settings.rows(state,{})) do
    local selected=row[1]=="player:"..state.hub_player or index==state.hub_input_hover
    context.fill(row[3],row[4],row[5],row[6],selected and 42 or 22,selected and 80 or 42,selected and 120 or 68)
    text(context,row[2],row[3]+10,row[4]+7,14,0xffffff)
   end
   local message=state.hub_control_message
   if state.hub_capture then message="Naciśnij nowy klawisz / przycisk. ESC anuluje."
   elseif set.device>0 then
    message="Pad "..set.device..": "..(state.hub_connected_pads and state.hub_connected_pads[set.device] and "WYKRYTY" or "NIEWYKRYTY - podłącz kontroler")
   end
   if not message and #input_settings.shared_keys(state)>0 then message="Wspólne klawisze graczy. Użyj USUŃ KOLIZJE Z INNYMI." end
   if message then text(context,message,397,440,14,0xffdc82,"center") end
   return
  end
  text(context,"AKTYWNY ZESTAW: "..hub.title(catalog.profile_id),397,89,17,0x9bcbff,"center")
  local subtitle=state.hub_mode=="library" and "Uruchom jeden zestaw lub wspólną pulę zaznaczonych modów (tryb testowy)." or
    "Mysz: kliknij    Klawiatura: strzałki / Enter    Pad: D-pad / A"
  if state.hub_mode=="profile" then subtitle=input_settings.hint()
  elseif state.hub_mode=="packs" then subtitle="Wybierz pakiety do wspólnej puli oraz widoczne w menu. Zapisz, aby zastosować." end
  text(context,subtitle,397,121,13,0xaac0dd,"center")
  for index,row in ipairs(hub.rows(state)) do
   local column=math.floor((index-1)/9);local y=160+(index-1)%9*37;local x=35+column*385
   local selected=index==state.hub_hover
   context.fill(x,y,370,32,selected and 42 or 22,selected and 80 or 42,selected and 120 or 68,selected and 230 or 180)
   context.fill(x,y,3,32,selected and 255 or 160,selected and 102 or 54,selected and 115 or 74)
   text(context,row[2],x+12,y+7,15,0xf3f7ff)
  end
  if state.hub_note then text(context,state.hub_note,397,515,13,0xffdc82,"center") end
  if not state.hub_note then text(context,"WYBIERZ ZESTAW  /  ZAPROŚ GRACZY  /  ROZPOCZNIJ WALKĘ",397,521,12,0x889dbb,"center") end
 end
 function base.describe(state)
  return describe(state).." hub="..tostring(state.hub_enabled==true)..":"..tostring(state.hub_mode)..
    " input_settings="..tostring(state.hub_edit~=nil).." input_capture="..tostring(state.hub_capture and state.hub_capture.row or 0)..
    " online="..tostring(state.hub_online~=nil)
 end
 return base
end
