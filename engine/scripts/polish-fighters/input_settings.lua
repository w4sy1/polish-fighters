local controls=require("base/ui/controls")
local nav=require("base/ui/navigation")
local screen={}
local actions={"GÓRA","DÓŁ","LEWO","PRAWO","ATAK / STRZAŁ","SKOK","BLOK"}
local mouse_names={[1]="MYSZ: LEWY",[2]="MYSZ: PRAWY",[4]="MYSZ: ŚRODKOWY",[5]="MYSZ: BOCZNY 1",[6]="MYSZ: BOCZNY 2"}
function screen.key_label(code)
 if code>=96 and code<=105 then return "Num "..(code-96) end
 return mouse_names[code] or controls.key_label(code)
end
function screen.hint()
 local set=controls.current().sets[1]
 if set.device~=0 then
  return "GRACZ 1 / PAD "..set.device..": ATAK "..(set.buttons[1]+1).."   SKOK "..(set.buttons[2]+1).."   BLOK "..(set.buttons[3]+1)
 end
 return "GRACZ 1: ATAK "..screen.key_label(set.keys[5]).."   SKOK "..screen.key_label(set.keys[6]).."   BLOK "..screen.key_label(set.keys[7])
end
function screen.selection_hint(touch,slot)
 local who='TY: GRACZ '..((slot or 0)+1)
 if touch then
  return {who..' | HYBRID CONTROL', 'Ruch: joystick lub strzałki | ATAK: wybór | SKOK: wstecz'}
 end
 local set=controls.current().sets[1]
 if set.device~=0 then
  return {who..' | PAD '..set.device..': RUCH D-PAD / LEWY ANALOG',
   'ATAK / OK '..(set.buttons[1]+1)..' | SKOK / WSTECZ '..(set.buttons[2]+1)..' | BLOK '..(set.buttons[3]+1)}
 end
 return {who..' | RUCH '..screen.key_label(set.keys[1])..' / '..screen.key_label(set.keys[2])..' / '..screen.key_label(set.keys[3])..' / '..screen.key_label(set.keys[4]),
  'ATAK / OK '..screen.key_label(set.keys[5])..' | SKOK / WSTECZ '..screen.key_label(set.keys[6])..' | BLOK '..screen.key_label(set.keys[7])}
end
function screen.current_lines(touch)
 if not touch then return screen.selection_hint(false,0) end
 local layout=require('base/ui/hybrid_layout')
 local shown=require('base/game/options').current().hybrid.controls
 local movement={}
 for _,name in ipairs({'stick','left','up','right','down'}) do
  if shown[name].enabled then movement[#movement+1]=layout.labels[name] end
 end
 local buttons={}
 for _,name in ipairs({'attack','defend','jump','s1','s2','s3','skills'}) do
  if shown[name].enabled then buttons[#buttons+1]=layout.labels[name] end
 end
 return {'RUCH: '..(#movement>0 and table.concat(movement,' / ') or 'WYŁĄCZONY'),
  'PRZYCISKI: '..(#buttons>0 and table.concat(buttons,' / ') or 'WYŁĄCZONE')}
end
function screen.shared_keys(state)
 local set=state.hub_edit.sets[state.hub_player];local shared={}
 if set.device~=0 then return shared end
 local used={};for _,code in ipairs(set.keys) do if code~=0 then used[code]=true end end
 for player,other in ipairs(state.hub_edit.sets) do
  if player~=state.hub_player and other.device==0 then
   for row,code in ipairs(other.keys) do if used[code] then shared[#shared+1]={player=player,row=row,code=code} end end
  end
 end
 return shared
end
function screen.open(state)
 state.hub_edit=controls.copy(controls.current());state.hub_player=1
 state.hub_capture=nil;state.hub_control_message=nil;state.hub_input_nav=nav.create()
 -- Etap 1.14 / Etap 5: hybrid_layout has no single joystick/arrows "mode" field --
 -- movement is a set of independently-enabled controls (stick vs left/up/right/down).
 -- The toggle below treats them as one group, staged here and applied on save like
 -- the rest of this screen's changes.
 state.hub_hybrid_mode=require('base/game/options').current().hybrid.controls.stick.enabled and 'stick' or 'arrows'
end
local function preset(state,kind)
 local set=state.hub_edit.sets[state.hub_player]
 set.device=0;set.mouse_mode=kind=="mouse"
 if kind=="arrows" then set.keys={38,40,37,39,97,98,99}
 elseif kind=="mouse" then set.keys={87,83,65,68,1,32,2}
 elseif kind=="num789" then set.keys={87,83,65,68,103,105,104}
 else set.keys={87,83,65,68,74,75,76} end
end
function screen.rows(state,input)
 local rows={}
 for player=1,4 do rows[#rows+1]={"player:"..player,"GRACZ "..player,20+(player-1)*190,95,180,30} end
 local set=state.hub_edit.sets[state.hub_player]
 local device=set.device==0 and (set.mouse_mode and "KLAWIATURA + MYSZ" or "KLAWIATURA") or ("PAD "..set.device)
 rows[#rows+1]={"device","URZĄDZENIE: "..device,30,142,440,32}
 for row,label in ipairs(actions) do
  local binding
  if set.device==0 then binding=screen.key_label(set.keys[row])
  elseif row<=4 then binding='D-PAD / ANALOG: '..(set.directions or {'u','d','l','r'})[row]:upper()
  else binding="PRZYCISK "..(set.buttons[row-4]+1) end
  rows[#rows+1]={"bind:"..row,label..": "..binding,35,185+(row-1)*33,430,29}
 end
 rows[#rows+1]={"num789","WASD | 7 ATAK / 8 BLOK / 9 SKOK",500,149,265,31}
 rows[#rows+1]={"wasd","WASD + J / K / L",500,190,265,31}
 rows[#rows+1]={"arrows","STRZAŁKI + NUM 1 / 2 / 3",500,232,265,31}
 rows[#rows+1]={"mouse","WASD + MYSZ + SPACJA",500,274,265,31}
 rows[#rows+1]={"defaults","PRZYWRÓĆ ORYGINALNE LF2",500,316,265,31}
 rows[#rows+1]={"resolve","USUŃ KOLIZJE Z INNYMI",500,358,265,31}
 rows[#rows+1]={"classic","NAZWY GRACZY / PANEL LF2",500,400,265,31}
 if state.hub_android then
  rows[#rows+1]={"hybrid_mode","RUCH: "..(state.hub_hybrid_mode=='stick' and "JOYSTICK" or "STRZAŁKI"),30,445,215,32}
  rows[#rows+1]={"hybrid_hud","EDYTOR HUD",255,445,215,32}
 end
 rows[#rows+1]={"save","ZAPISZ",210,480,180,34}
 rows[#rows+1]={"cancel","ANULUJ",410,480,180,34}
 return rows
end
function screen.activate(state,id)
 local set=state.hub_edit.sets[state.hub_player]
 if id:sub(1,7)=="player:" then state.hub_player=tonumber(id:sub(8));state.hub_capture=nil
 elseif id=="device" then
  if set.device==0 and not set.mouse_mode then set.mouse_mode=true
  elseif set.device==0 then set.mouse_mode=false;set.device=1
  else set.device=(set.device+1)%5;set.mouse_mode=false end
 elseif id:sub(1,5)=="bind:" then
  local row=tonumber(id:sub(6))
  state.hub_capture={row=row,armed=false}
 elseif id=="wasd" or id=="arrows" or id=="mouse" or id=="num789" then preset(state,id)
 elseif id=="defaults" then state.hub_edit=controls.defaults()
 elseif id=="resolve" then
  for _,conflict in ipairs(screen.shared_keys(state)) do state.hub_edit.sets[conflict.player].keys[conflict.row]=0 end
  state.hub_control_message="Usunięto wspólne klawisze pozostałych graczy."
 elseif id=="classic" then
  state.editing=state.hub_edit;state.hub_edit=nil;state.page="controls"
  state.name_player=0;state.previous_keys={}
 elseif id=="hybrid_mode" then
  state.hub_hybrid_mode=state.hub_hybrid_mode=='stick' and 'arrows' or 'stick'
 elseif id=="hybrid_hud" then
  -- Clear hub_edit so the next frame falls through to the wrapped launch.lua base's
  -- own state.page=='hud' dispatch (hub_launch.base.update checks hub_edit first).
  -- Stash it rather than dropping it: unsaved key/pad rebinds would otherwise be
  -- silently lost while the player is in the HUD editor (Final review finding 1).
  -- hub_launch.lua restores it once the HUD editor hands state.page back to 'menu',
  -- which re-enters this screen (hub_edit non-nil) so SAVE/CANCEL stays the player's
  -- own explicit choice.
  state.hub_hybrid_pending_edit=state.hub_edit
  state.hub_edit=nil
  state.hud=require('base/ui/hybrid_editor').create(require('base/game/options').current(),'menu')
  state.page='hud'
 elseif id=="save" then
  if #screen.shared_keys(state)>0 then
   state.hub_control_message="Kolizje z innymi graczami. Najpierw użyj USUŃ KOLIZJE.";return
  end
  local saved,problem=controls.save(state.hub_edit)
  if saved and state.hub_android then
   local options=require('base/game/options')
   local values=options.current()
   local wanted=state.hub_hybrid_mode=='stick'
   if values.hybrid.controls.stick.enabled~=wanted then
    values.hybrid.controls.stick.enabled=wanted
    for _,name in ipairs({'left','right','up','down'}) do values.hybrid.controls[name].enabled=not wanted end
    saved,problem=options.save(values)
   end
  end
  if saved then state.hub_edit=nil;state.hub_note="ZAPISANO STEROWANIE"
  else state.hub_control_message="Nie zapisano: "..tostring(problem) end
 elseif id=="cancel" then state.hub_edit=nil end
end
function screen.update(state,input)
 state.hub_connected_pads=input.pads or {}
 if state.hub_escape_release then
  if input.keys[27] then return end
  state.hub_escape_release=nil
 end
 local capture=state.hub_capture
 if capture then
  if input.keys[27] then state.hub_capture=nil;state.hub_escape_release=true;return end
  local set=state.hub_edit.sets[state.hub_player]
  local pressed
  if set.device==0 then
   for code=1,249 do
    if input.keys[code] and (not mouse_names[code] or set.mouse_mode) then pressed=code;break end
   end
  else
   local pad=input.pads and input.pads[set.device]
   if capture.row<=4 then
    for _,direction in ipairs({'u','d','l','r'}) do if pad and pad.dirs and pad.dirs[direction] then pressed=direction;break end end
   else for button=0,31 do if pad and pad.buttons[button] then pressed=button;break end end end
  end
  if pressed==nil then capture.armed=true
  elseif capture.armed then
   if set.device==0 then set.keys[capture.row]=pressed
   elseif capture.row<=4 then set.directions=set.directions or {'u','d','l','r'};set.directions[capture.row]=pressed
   else set.buttons[capture.row-4]=pressed end
   state.hub_capture=nil
  end
  return
 end
 local targets={}
 local rows=screen.rows(state,input)
 for _,row in ipairs(rows) do targets[#targets+1]=nav.target(row[3],row[4],row[3]+row[5],row[4]+row[6]) end
 local mapped=nav.apply(state.hub_input_nav,input,{page="input:"..state.hub_player,targets=targets,default=5})
 state.hub_input_hover=nil
 for index,box in ipairs(targets) do
  if mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then
   state.hub_input_hover=index
   if mapped.click then screen.activate(state,rows[index][1]);break end
  end
 end
 if mapped.nav.cancel then state.hub_edit=nil end
end
return screen
