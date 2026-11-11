engine={random=function() return 0 end}
package.loaded['polish-originals/runtime']={ai_target=function() return nil end}
local constants=require('base/game/constants')
local original=require('base/game/ai')
local ai=dofile(arg[1]..'/content-packs/polish-originals/ai.lua')({control=original.control})
local function actor(id,team)
 return {record={id=id},keys={},previous_keys={},hp=500,team=team or constants.teams.player_one}
end
for id=410,415 do
 local value=actor(id)
 local state={items={[10]=value},stage_run={last_phase=1},frame_number=100}
 ai.control(state,10,constants.modes.stage,{})
 assert(value.keys.right,'Campaign exit: hero '..id..' stays still after the last enemy')
 assert(not value.keys.attack,'A clear exit must not trigger combat abilities')
end
local value=actor(433)
ai.control({items={[50]=value},stage_run={last_phase=1}},50,constants.modes.stage,{})
assert(not value.keys.right,'Stationary turret must not start walking')
value=actor(410,constants.teams.enemies)
ai.control({items={[20]=value},stage_run={last_phase=1}},20,constants.modes.stage,{})
assert(not value.keys.right,'Enemy must not receive allied exit orders')
value=actor(410)
ai.control({items={[10]=value},stage_run={last_phase=0}},10,constants.modes.stage,{})
assert(not value.keys.right,'Combat phase must retain its own AI')
print('PASS: all six hero forms use shared campaign-exit movement; combat, enemies and stationary turrets unchanged')
