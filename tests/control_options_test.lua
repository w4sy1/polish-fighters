local root=arg[1]
local document={unrelated={keep=true}}
local writes=0
engine={read_settings=function() return document end,write_settings=function(value)
    document=value;writes=writes+1;return true
end}
local controls=require('base/ui/controls')
local constants=require('base/game/constants')
local keyboard=constants.input_devices.keyboard
local settings={sets={},names={}}
for index=1,4 do
    settings.sets[index]={device=keyboard,keys={index*10+1,index*10+2,index*10+3,index*10+4,index*10+5,index*10+6,index*10+7},buttons={0,1,2}}
    settings.names[index]='Player '..index
end
assert(#controls.conflicts(settings)==0)
assert(controls.save(settings))
assert(document.unrelated.keep)
local before=writes
settings.sets[1].keys[2]=settings.sets[1].keys[1]
assert(#controls.conflicts(settings)==1)
assert(not controls.save(settings))
assert(writes==before,'conflict must not overwrite configuration')
settings.sets[1].keys[1]=0;settings.sets[1].keys[2]=0
assert(#controls.conflicts(settings)==0,'unassigned keys may repeat')
settings.sets[1].device=constants.input_devices.controller_one
settings.sets[1].buttons={0,0,2}
assert(#controls.conflicts(settings)==1,'button zero is assigned')

local options=require('base/game/options')
local layout=options.default_gamepad()
layout.c.radius=100
assert(options.default_gamepad().c.radius==44,'defaults must be independent')
local values=options.current()
values.gamepad.appearance.opacity=0.25
assert(options.save(values))
assert(options.load().gamepad.appearance.opacity==0.25)
values.gamepad.appearance.opacity=0/0
assert(options.save(values))
assert(options.current().gamepad.appearance.opacity==0.66,'NaN must be rejected')
assert(document.unrelated.keep)

local pad=require('base/ui/touch_gamepad')
local config=options.default_gamepad()
config.appearance.opacity=0.25
local state=pad.create(config,true)
local held=pad.update(state,{touch_active=true,touches={
    {id=1,x=125,y=405},{id=2,x=606,y=458}
}})
assert(held:find('u') and held:find('c'),'move and attack must work simultaneously')
local alphas={}
local context={overlay=function() end,fill=function(x,y,w,h,r,g,b,a) alphas[a]=true end}
-- Avoid text rendering dependencies; shapes still use the real renderer path.
package.loaded['base/ui/font'].draw=function() end
pad.draw(state,context)
assert(alphas[64] and alphas[32],'configured opacity must affect buttons and stick')
assert(pad.update(state,{touch_active=false})=='','hiding must release held input')
print('PASS: conflicts, save preservation, layout defaults, opacity and multitouch')
