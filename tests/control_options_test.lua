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

print('PASS: keyboard and controller conflicts, save preservation')
