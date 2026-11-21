-- POWRÓT on "Konto i pokoje" must return to the module launcher; the following frames of the
-- whole hub (update and draw) must not fail. On Android a failure here ends the engine with
-- exit code 1 and closes the game.
engine={read_settings=function() return {} end,account=function() return nil,'offline' end}
local locale=require('base/i18n/i18n');locale.use('polish');locale.host(true)
local nav=require('base/ui/navigation')
local online=require('polish-fighters/online_screen')
local shell=dofile(arg[1]..'/engine/scripts/polish-fighters/hub_launch.lua')({
 create=function() return {} end,update=function() end,draw=function() end,describe=function() return '' end})
local actions={}
-- Like the engine since 0.18.12: several text_input calls in one frame are allowed, the last wins.
local typing,frame_typing=false,{}
local context={viewport=function() end,image=function() end,sprite=function() end,fill=function() end,
 text=function() end,text_input=function(value) frame_typing[#frame_typing+1]=value end,
 action=function(id) actions[#actions+1]=id end,measure=function() return 0 end}
local state={hub_enabled=true,page='menu',hub_mode='online',hub_navigation=nav.create(),hub_selected={}}
local function frame(input)
 input.keys=input.keys or {};frame_typing={}
 local ok,problem=pcall(shell.update,state,input,context);assert(ok,'update: '..tostring(problem))
 ok,problem=pcall(shell.draw,state,context);assert(ok,'draw: '..tostring(problem))
 if #frame_typing>0 then typing=frame_typing[#frame_typing] end
end
online.open(state);frame({})
-- Focus the nick field so the keyboard is on, then leave: it must end up off.
local nick
for _,row in ipairs(online.rows(state.hub_online)) do if row[1]:sub(1,6)=='field:' then nick=nick or row end end
frame({click=true,pointer_x=nick[3]+5,pointer_y=nick[4]+5});frame({})
assert(typing==true,'focusing the nick field did not start text input')
local back
for _,row in ipairs(online.rows(state.hub_online)) do if row[1]=='back' then back=row end end
frame({click=true,pointer_x=back[3]+5,pointer_y=back[4]+5})
assert(state.hub_online==nil,'POWRÓT did not close the online screen')
assert(typing==false,'the keyboard stayed on after POWRÓT')
for _=1,5 do frame({}) end
-- The same with Android Back (Escape) instead of a tap.
online.open(state);frame({})
frame({click=true,pointer_x=nick[3]+5,pointer_y=nick[4]+5});frame({})
frame({keys={[27]=true}});frame({})
assert(state.hub_online and not state.hub_online.focus and not typing,'Back must close the keyboard first')
frame({keys={[27]=true}});frame({})
assert(state.hub_online==nil,'Back did not close the online screen')
for _=1,5 do frame({}) end
assert(#actions==0,'closing the online screen started an action: '..table.concat(actions,','))
print('PASS hub: POWRÓT and Back leave Konto i pokoje without failing the next frames')
