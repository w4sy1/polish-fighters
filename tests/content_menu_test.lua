local document={}
engine={read_settings=function() return document end,write_settings=function(value) document=value;return true end,
    read_stage_data=function() return {stages={[0]={phase_count=3},[10]={phase_count=5}}} end}
local fighters,maps={},{}
for index=1,42 do fighters[index]={id=index,name='Fighter'..index,portrait='head.bmp',hidden=false} end
for index=1,17 do maps[index]={path='arena'..index} end
package.preload['base/game/catalog']=function() return {profile_id='ntsd',stage_path='stage.dat',
    load=function() return fighters end,backgrounds=function() return maps end,selectable=function() return true end} end
package.preload['base/game/background']=function() return {load=function(path) return {name=path} end} end
package.preload['base/ui/hybrid_editor']=function() return {
    create=function(values, destination) return {values=values,destination=destination} end} end
local drawn={}
package.preload['base/ui/font']=function() return {draw=function(c,text) drawn[#drawn+1]=text end,gdi=function() end} end
package.preload['base/ui/navigation']=function() return {create=function() return {} end,
    target=function(l,t,r,b) return {left=l,top=t,right=r,bottom=b} end,
    apply=function(s,input) return input end} end
local model=require('polish-fighters/dashboard_model')
assert(model.packs[5][2] and not model.packs[1][2],'active Naruto must be identified')
local content=assert(model.contents())
assert(#content.fighters==42 and #content.campaigns==2)
local shell=dofile(arg[1]..'/engine/scripts/polish-fighters/classic_shell.lua')({
    create=function() return {page='menu',background=1} end,update=function() end,
    draw=function() end,describe=function() return 'test' end})
local state=shell.create({})
local keyboard=false
local context={action=function() end,viewport=function() end,image=function() end,sprite=function() end,fill=function() end,
    text_input=function(active) keyboard=active end}
local function click(index)
    shell.update(state,{keys={},click=true,pointer_x=420,pointer_y=219+(index-1)*25,nav={}},context)
end
state.pf_panel='packs'
click(5)
assert(state.pf_panel=='pack-content')
click(1)
assert(state.pf_panel=='fighters')
shell.draw(state,context)
assert(#drawn==11,'one title, eight fighters, next and back')
click(9)
assert(state.pf_content_page==2)
click(1)
assert(state.pf_message[1]=='Fighter9')
click(1) -- dismiss detail
assert(not state.pf_message)
state.pf_panel='maps'
click(9)
assert(state.pf_map_page==2)
click(1)
assert(model.current().map==8,'second page retains original map indices')
state.pf_panel='extras'
click(6)
assert(state.page=='menu' and state.pf_panel=='history' and not state.hud,'the extras menu must not open the HUD editor')
state.pf_message=nil;state.pf_panel='unlock'
local presses={}
for letter in ('POLISHFIGHTERS'):gmatch('.') do presses[#presses+1]=letter:byte() end
shell.update(state,{presses=presses,keys={},nav={}},context)
assert(state.pf_message[1]=='POSTACIE ODBLOKOWANE')
assert(document.options.unlock_characters==true,'code must persist through existing options')
require('base/game/unlock').flags.characters=0 -- network session may have reset the live flag
state.pf_message=nil
shell.update(state,{presses=presses,keys={},nav={}},context)
assert(require('base/game/unlock').flags.characters==1,'reusing code must restore a reset live flag')
state.pf_message=nil;state.pf_panel='unlock'
click(1)
assert(keyboard and state.pf_typing)
shell.update(state,{text='POLISH',presses={80,79,76,73,83,72},keys={},nav={}},context)
assert(state.pf_code=='polish','text input must not duplicate hardware presses')
shell.update(state,{text='fighters',presses={},keys={},nav={}},context)
assert(state.pf_message[1]=='POSTACIE ODBLOKOWANE' and not keyboard)
state.pf_message=nil;click(1)
shell.update(state,{text='wrong',keys={},presses={},nav={}},context)
click(2)
assert(state.pf_message[1]=='NIEPRAWIDLOWY KOD' and not keyboard)
state.pf_message=nil;state.pf_panel='history'
shell.draw(state,context)
click(1)
assert(state.pf_message[1]=='HISTORIA','empty history must be readable')
engine.read_stage_data=function() error('invalid campaign') end
local value,problem=model.contents()
assert(not value and problem:find('invalid campaign'),'corrupt package must return a readable error')

-- Etap 1.14 / Zadanie 3.4: the old "connection" panel (room/tcp/capacity/
-- lan/bluetooth) is retired; the separate "account" panel (native-account/
-- guest, the only other entry point into the full non-simple online
-- screen) must survive untouched.
state.pf_message=nil;state.pf_panel='extras';drawn={}
shell.draw(state,context)
for _,label in ipairs(drawn) do
    assert(not label:find('POLACZENIA',1,true),'retired connection row must not be drawn: '..label)
end
local saw_account=false
for _,label in ipairs(drawn) do if label=='KONTO / GOSC' then saw_account=true end end
assert(saw_account,'account row must survive the connection-panel removal')
state.pf_panel='account';drawn={}
shell.draw(state,context)
assert(drawn[1]=='KONTO / GOŚĆ' and drawn[2]=='ZALOGUJ / UTWÓRZ KONTO' and drawn[3]=='GRAJ BEZ LOGOWANIA',
    'account panel rows (native-account/guest) must be unaffected')
local opened_online=false
package.loaded['polish-fighters/online_screen']={open=function() opened_online=true end}
click(1) -- native-account
assert(opened_online and not state.pf_panel,'native-account must still open the full online screen')
print('PASS: active Naruto, real catalogs, pagination, map indices, touch GUI, package errors')
print('PASS: connection panel retired, account panel (native-account/guest) preserved')
