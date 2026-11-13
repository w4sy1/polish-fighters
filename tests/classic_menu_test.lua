local document={unrelated={keep=true}}
local fail=false
engine={read_settings=function() return document end,write_settings=function(value)
 if fail then return nil,'read only' end;document=value;return true end,
 read_resource=function() return '0 104 98 100 102 101 96 107 0 1 3\n0 87 88 65 68 83 9 192 0 1 3\n0 38 40 37 39 13 16 17 0 1 2\n0 73 188 74 76 75 32 190 0 1 3\nP1 P2 P3 P4\n1 0\nname\nemail\ninfo\n' end}
local controls=require('base/ui/controls');controls.load()
local options=require('base/game/options');options.load()
local hub=require('polish-fighters/hub')
local layout=require('polish-fighters/menu_layout')
local locale=require('polish-fighters/menu_locale')
local shell=dofile(arg[1]..'/engine/scripts/polish-fighters/hub_launch.lua')({create=function() return {page='menu'} end,update=function() end,draw=function() end,describe=function() return '' end})
local state=shell.create({});state.hub_enabled=true;state.hub_mode='root'
local requested
local context={action=function(id) requested=id end,sound=function() end}
local function click(id)
 local rows=hub.rows(state);local index
 for i,row in ipairs(rows) do if row[1]==id then index=i;break end end
 assert(index,'No action '..id..' in '..state.hub_mode)
 local x,y,w,h=layout.box(index,#rows)
 shell.update(state,{keys={},gamepad={},pointer_x=x+w/2,pointer_y=y+h/2,click=true},context)
end
local function back()
 shell.update(state,{keys={[27]=true},gamepad={},pointer_x=0,pointer_y=0},context)
 shell.update(state,{keys={},gamepad={},pointer_x=0,pointer_y=0},context)
end
assert(#hub.rows(state)==7)
click('battle');assert(#hub.rows(state)==10)
for _,mode in ipairs({'versus','stage','championship','team_championship','battle_setup'}) do
 state.hub_preselected=false;state.hub_mode='battle';click('mode_'..mode);assert(state.hub_mode=='library' and state.hub_pending_mode==mode)
 click('profile_lf_two');assert(state.hub_mode=='players')
 click('controls');assert(state.hub_edit);require('polish-fighters/input_settings').activate(state,'cancel')
 click('start_mode');assert(requested==(mode=='battle_setup' and 'battle' or mode));back();assert(state.hub_mode=='library');back();assert(state.hub_mode=='battle')
end
state.hub_mode='battle';click('mode_demo');assert(requested=='demo');click('mode_replay');assert(requested=='replay')
state.hub_mode='root';click('language');click('lang_en');assert(locale.id()=='en' and hub.rows({hub_mode='root'})[1][2]=='BATTLE')
assert(document.options.language=='english' and document.unrelated.keep)
assert(locale.translate('GRACZ 2: ATAK Num 7')=='PLAYER 2: ATTACK Num 7')
options.load();assert(locale.id()=='en');click('lang_pl');assert(locale.id()=='pl')
state.hub_mode='root';click('library');click('packs')
for _,entry in ipairs(hub.profiles) do state.hub_pack_edit[entry.id]=false end
click('packs_save');assert(state.hub_mode=='packs' and state.hub_note)
state.hub_pack_edit.lf_two=true;click('packs_save');assert(state.hub_mode=='library' and document.little_fighters_packs.lf_two)
assert(#hub.rows(state)==5,'disabled packs must not crowd a single-module selection')
click('packs');click('toggle_lf_two');back();assert(state.hub_selected.lf_two,'cancel modified saved modules')
state.hub_mode='root';click('online');click('unavailable');assert(state.hub_note==locale.text('offline'))
state.hub_mode='root';click('credits');back();assert(state.hub_mode=='root')
-- A profile reload carries the requested mode once, without another thirteen-choice menu.
state.hub_preselected=false;state.hub_mode='battle';click('mode_stage');state.hub_selected=nil;click('profile_dbz');assert(requested=='profile_dbz' and document.little_fighters_pending_mode=='stage')
local flow=dofile(arg[1]..'/engine/scripts/polish-fighters/hub_flow.lua')({create=function() return {launch={}} end})
local fresh=flow.create({profile_start=true});assert(fresh.launch.hub_mode=='players' and fresh.launch.hub_pending_mode=='stage' and document.little_fighters_pending_mode==nil)
-- Every target stays inside the fixed viewport and contains no overlapping button.
for _,mode in ipairs({'root','battle','library','packs','players','settings','online','language','credits','status'}) do
 state.hub_mode=mode;state.hub_pack_edit={};local rows=hub.rows(state)
 for i=1,#rows do local x,y,w,h=layout.box(i,#rows);assert(x>=0 and x+w<=794 and y>=0 and y+h<=490) end
end
local commands=0
state.hub_mode='status';state.hub_enabled=true;state.page='menu';state.hub_edit=nil
shell.draw(state,{viewport=function() end,image=function() commands=commands+1 end,
 fill=function() commands=commands+1 end,sprite=function() commands=commands+1 end,text=function() commands=commands+1 end})
assert(commands<4096,'module list exceeded native renderer command limit')
local edit=controls.copy(controls.current());edit.sets[1].device=1;edit.sets[1].directions={'r','d','l','u'}
assert(controls.save(edit));controls.load();assert(controls.current().sets[1].directions[1]=='r')
local held=controls.read(controls.current(),'$1r');assert(held[0]:find('u') and not held[0]:find('r'))
edit.sets[1].directions={'r','r','l','u'};assert(not controls.save(edit),'duplicate pad directions were accepted')
fail=true;local saved,problem=locale.select('en');assert(not saved and problem=='read only')
print('PASS classic menu: all modes, module handoff, back, controls, unavailable online, PL/EN persistence, target bounds, pad remapping/conflicts')
