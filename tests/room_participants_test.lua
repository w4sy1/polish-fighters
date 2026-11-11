package.loaded['base/game/catalog']={load=function() return {} end,backgrounds=function() return {} end}
local select=require('base/ui/character_select')
local phases=require('base/game/constants').character_slot_phases
local s=select.create({mode='versus',participants={{slot=0},{slot=1},{slot=7}}})
for _,i in ipairs({0,1,7}) do assert(s.slots[i].phase==phases.choosing_fighter) end
assert(s.slots[2].phase==phases.empty,'unconnected slot must stay empty')
local offline=select.create({mode='versus'})
assert(offline.slots[0].phase==phases.empty,'local join behavior changed')
assert(not pcall(select.create,{mode='versus',participants={{slot=8}}}))
print('PASS room participants: separate reserved slots, unused slots empty, offline preserved')
