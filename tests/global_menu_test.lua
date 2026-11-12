local returned,keyboard,actions=0,nil,{}
local dialog=require('base/ui/quit_dialog')
local base=dofile(arg[1]..'/engine/scripts/polish-fighters/hub_flow.lua')({
 create=function() return {launch={}} end,draw=function() end,
 return_to_modules=function(s) returned=returned+1;s.active='launch';s.session=nil end})
local context={text_input=function(v) keyboard=v end,action=function(a) actions[#actions+1]=a end}
for _,page in ipairs({'launch','title','characters','backgrounds','network','battle','championship','ending'}) do
 local s=base.create({});s.active=page
 assert(base.global_navigation_update(s,{functions='4',keys={},pointer_x=0,pointer_y=0},context))
 assert(s.active=='launch' and keyboard==false)
 assert(not base.global_navigation_update(s,{functions='4',keys={},pointer_x=0,pointer_y=0},context),'held F4 repeated')
end
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
local mobile=base.create({touch_device=true})
assert(mobile.launch.hub_mode=='profile','chosen Android module must not open the module list again')
assert(base.create({}).launch.hub_mode=='root','desktop root must remain available')
assert(#actions==0,'menu return must not exit application')
print('PASS global menu: all screen types, F4 edge, touch during fight, stalled network, no quit')
