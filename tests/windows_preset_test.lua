local saved={}
engine={read_settings=function() return saved end,read_resource=function()
 return '0 104 98 100 102 101 96 107 0 1 3\n0 87 88 65 68 83 9 192 0 1 3\n0 38 40 37 39 13 16 17 0 1 2\n0 73 188 74 76 75 32 190 0 1 3\nP1 P2 P3 P4\n1 0\nname\nemail\ninfo\n'
end,write_settings=function(doc) saved=doc;return true end}
local controls=require('base/ui/controls')
local pc=controls.load(false,true)
assert(table.concat(pc.sets[1].keys,',')=='87,83,65,68,103,105,104')
local raw=controls.read(pc,'k83 m0,0,0')
assert(raw[0]=='d' and raw[1]=='','WASD must not also join/control another player')
assert(table.concat(controls.load().sets[1].keys,',')=='87,83,65,68,103,105,104','cancel/reload lost desktop preset')
pc.sets[1].keys[5]=74;assert(controls.save(pc))
assert(controls.load(false,true).sets[1].keys[5]==74,'saved custom controls overwritten')
saved={};assert(controls.load(false,false).sets[1].keys[5]==101,'Android/original defaults changed')
print('PASS Windows preset: W/S/A/D, Num7 attack/8 defend/9 jump, no shared keys, saved custom controls preserved')
