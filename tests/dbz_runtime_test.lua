local root=arg[1]
local runtime=assert(loadfile(root..'/content-packs/dbz/scene_runtime.lua'))()
local state={stage={dbz_mode={arest={0,2}},dbz_scene={opoints={
 {kind=1,oid=405,action=402,x=400,y=-20,z=360,hp=800},
 {kind=1,oid=191,action=20,x=100,arest={2}},
 {kind=1,oid=999,action=1,arest={1}}}}},items={}}
local objects={free_slot=function(s)return 50+#s.dbz_scene_objects end,
 record=function(s,id)return {frames={[20]={},[402]={}}} end,
 place=function(s,index,id)local value={};s.items[index]=value;return value end}
runtime.spawn(state,objects)
assert(#state.dbz_scene_objects==2)
assert(state.items[50].frame==402 and state.items[50].x_int==400)
assert(state.items[50].y_int==-20 and state.items[50].z_int==360)
assert(state.items[50].hp==800 and state.items[50].max_hp==800)
assert(state.items[51].frame==20)
objects.record=function()return nil end
assert(not pcall(runtime.spawn,state,objects))
