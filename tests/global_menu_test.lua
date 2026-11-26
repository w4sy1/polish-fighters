local returned,keyboard,actions=0,nil,{}
local dialog=require('base/ui/quit_dialog')
local base=dofile(arg[1]..'/engine/scripts/polish-fighters/hub_flow.lua')({
 create=function() return {launch={}} end,draw=function() end,
 return_to_modules=function(s) returned=returned+1;s.active='launch';s.session=nil end})
local context={text_input=function(v) keyboard=v end,action=function(a) actions[#actions+1]=a end}
for _,page in ipairs({'title','characters','backgrounds','network','battle','championship','ending'}) do
 local s=base.create({});s.active=page
 assert(base.global_navigation_update(s,{functions='4',keys={},pointer_x=0,pointer_y=0},context))
 assert(s.active=='launch' and s.launch.hub_mode=='root' and keyboard==false)
 assert(not base.global_navigation_update(s,{functions='4',keys={},pointer_x=0,pointer_y=0},context),'held F4 repeated')
end
local main=base.create({});main.active='launch';main.launch.page='menu'
engine={read_settings=function() return {} end}
local rows=require('polish-fighters/hub').rows(main.launch)
assert(rows[1][1]=='library' and rows[2][1]=='battle')
local count=returned
assert(base.global_navigation_update(main,{functions='4',keys={}},context))
assert(returned==count and main.launch.hub_mode=='root','F4 must leave the main menu in place')
base.global_navigation_update(main,{functions='',keys={}},context)
main.launch.hub_mode='library'
local press={functions='4',keys={}}
assert(not base.global_navigation_update(main,press,context) and press.keys[27],
 'F4 inside the modules list must use the normal back action')
local s=base.create({});s.active='match';s.match={match={finished=false,paused=false}}
local touch={functions='',click=true,pointer_x=600,pointer_y=20}
assert(not base.global_navigation_update(s,touch,context))
assert(touch.functions=='4' and not s.quit_dialog,'fight back must reach synchronized match input')
assert(not base.global_navigation_update(s,{functions='4'},context),'F4 in fight must not open modules')
s.active='title';s.session={}
base.global_navigation_update(s,{functions=''},context)
assert(base.global_navigation_update(s,{functions='4'},context))
assert(s.quit_dialog.kind=='modules')
local update=dialog.update
dialog.update=function() return 'exit' end
assert(base.global_navigation_update(s,{functions='',keys={}},context))
assert(not s.session and s.active=='launch','stalled network must allow local return from menus')
dialog.update=update
engine={read_settings=function() return {little_fighters_start_profile='lf_four_turbo'} end}
local hub=require('polish-fighters/hub')
local initial=base.create({touch_device=true})
assert(initial.launch.hub_mode=='root' and initial.launch.hub_preselected,'Android starts at the game menu with its chosen module')
initial.launch.hub_mode='settings'
local found_tools=false
for _,row in ipairs(hub.rows(initial.launch)) do
 if row[1]=='android_tools' then found_tools=true end
end
assert(found_tools,'Android tools must be reachable from the settings menu')
local settings={little_fighters_start_profile='lf_four_turbo'}
engine.read_settings=function() return settings end
engine.write_settings=function(document)
 assert(document==settings and document.little_fighters_open_android_tools==true)
 return true
end
assert(hub.open_android_tools(context) and actions[1]=='quit')
actions={}
local mobile=base.create({touch_device=true,profile_start=true})
assert(mobile.launch.hub_mode=='profile','chosen Android module must not open the module list again')
mobile.active='launch';mobile.launch.page='menu'
assert(base.global_navigation_update(mobile,{keys={},click=true,pointer_x=600,pointer_y=20},context))
assert(base.create({}).launch.hub_mode=='root','desktop root must remain available')
assert(#actions==0,'menu return must not exit application')
print('PASS global menu: all screen types, F4 edge, touch during fight, stalled network, no quit')

local paused=base.create({});paused.active='match';paused.match={view={paused=true}}
local open_help={functions='',keys={},click=true,pointer_x=120,pointer_y=20}
assert(not base.global_navigation_update(paused,open_help,context) and not paused.paused_guide)
paused.session={}
assert(not base.global_navigation_update(paused,open_help,context) and not paused.paused_guide)
print('PASS: removed pause tutorial no longer intercepts clicks')

-- Etap 1.14 / Etap 2: GRAJ LOKALNIE (battle) must never lead into a network hub_mode.
local hub=require('polish-fighters/hub')
for _,row in ipairs(hub.rows({hub_mode='battle'},'battle')) do
 local id=row[1]
 assert(id:sub(1,7)~='network' and id:sub(1,7)~='account' and id:sub(1,3)~='lan' and id:sub(1,6)~='remote',
  'GRAJ LOKALNIE must not expose a network row: '..id)
end
assert(require('polish-fighters/menu_locale').text('play_main')=='GRAJ LOKALNIE')
print('PASS: GRAJ LOKALNIE has no network row, label pinned')

-- Etap 1.14 / Etap 3: GRAJ ZDALNIE replaces SIECI (online), gates BLUETOOTH by availability.
do
 local root=hub.rows({hub_mode='root'})
 local remote_id
 for _,row in ipairs(root) do if row[1]=='remote' then remote_id=row end if row[1]=='online' then error('online row must be removed') end end
 assert(remote_id and remote_id[2]=='GRAJ ZDALNIE','root must expose remote with GRAJ ZDALNIE label')

 local android=hub.rows({hub_mode='remote',hub_android=true,hub_bluetooth_available=true})
 assert(#android==5,'android remote menu must have SERWER/BLUETOOTH/WIFI/HOTSPOT/WSTECZ')
 local ids={} for i,row in ipairs(android) do ids[row[1]]=i end
 assert(ids.remote_server and ids.remote_bluetooth and ids.remote_wifi and ids.remote_hotspot and ids.root)

 local desktop=hub.rows({hub_mode='remote',hub_android=false,hub_bluetooth_available=false})
 assert(#desktop==4,'desktop without bluetooth must have SERWER/WIFI/HOTSPOT/WSTECZ only')
 for _,row in ipairs(desktop) do assert(row[1]~='remote_bluetooth','no bluetooth row without availability') end

 -- settings no longer exposes the old standalone LAN row
 for _,row in ipairs(hub.rows({hub_mode='settings'})) do assert(row[1]~='lan','settings must not duplicate WIFI/HOTSPOT via lan row') end
end
print('PASS: GRAJ ZDALNIE menu replaces SIECI, gates BLUETOOTH by availability, settings drop duplicate lan row')

-- Etap 1.14 / Zadanie 4A.1: BLUETOOTH on Android routes through the same
-- quit+relaunch pattern as the existing android_tools restart flow.
do
 local bt_settings={}
 engine.read_settings=function() return bt_settings end
 engine.write_settings=function(document)
  assert(document==bt_settings and document.little_fighters_open_bluetooth==true)
  return true
 end
 local bt_actions={}
 local bt_context={action=function(a) bt_actions[#bt_actions+1]=a end}
 assert(hub.open_android_bluetooth(bt_context) and bt_actions[1]=='quit',
  'remote_bluetooth must write the restart flag and quit, like open_android_tools')
end
print('PASS: BLUETOOTH routes through the quit+relaunch restart pattern')
