engine={new_array=function() return {} end,read_settings=function() return {} end}
local catalog=require('base/game/catalog')
dofile(arg[1]..'/content-packs/lf4-turbo/catalog.lua')(catalog)
local objects=require('base/game/objects')
local function record(id,kind)
 local frames={}
 local empty={state=0,center_x=0,center_y=0,opoint={kind=0,oid=0}}
 for number,target in pairs({[10]=id,[11]=5,[20]=223}) do
  frames[number]={state=0,center_x=0,center_y=0,
   opoint={kind=1,oid=target,action=0,x=0,y=0,dvx=0,dvy=0,facing=30}}
 end
 return {id=id,kind=kind or 0,data={weapon={hp=0}},frame=function(n) return frames[n] or empty end}
end
local function check(id)
 local state={items={},records={[id]=record(id),[5]=record(5),[223]=record(223,3)}}
 local actor=objects.place(state,0,id);actor.owner=0
 for _,frame in ipairs({10,11}) do
  actor.frame=frame
  for _=1,20 do objects.spawn_from_frame(state,0,actor) end
 end
 local count=0;for _ in pairs(state.items) do count=count+1 end
 assert(count==1,'LeumasEX must not summon himself or Rudolf')
 actor.frame=20;objects.spawn_from_frame(state,0,actor)
 assert(state.items[50] and state.items[50].record.id==223,'Leumas projectile spawning was disabled')
end
assert(catalog.no_character_summons[55]);check(55)
package.loaded['mixed-all/metadata']={[1001]={pack='lf4-turbo',id=55},[1347]={pack='dbz',id=55}}
dofile(arg[1]..'/content-packs/mixed-all/catalog.lua')(catalog)
assert(catalog.no_character_summons[1001] and not catalog.no_character_summons[1347], 'restriction leaked to another mod')
check(1001)
assert(not catalog.no_character_summons[5],'Rudolf was disabled')
print('PASS: LeumasEX cannot summon characters in LF4/mixed; projectiles and unrelated characters preserved')
