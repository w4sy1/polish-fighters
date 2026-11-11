engine={new_array=function() return {} end}
local objects=require('base/game/objects')
local constants=require('base/game/constants')
local function record(id,kind)
 local frames={}
 local base={state=0,center_x=0,center_y=0,opoint={kind=0,oid=0}}
 frames[0]=base
 frames[10]={state=0,center_x=0,center_y=0,
  opoint={kind=1,oid=id,action=0,x=0,y=0,dvx=0,dvy=0,facing=30}}
 frames[20]={state=0,center_x=0,center_y=0,
  opoint={kind=1,oid=202,action=0,x=0,y=0,dvx=0,dvy=0,facing=1}}
 return {id=id,kind=kind or 0,data={weapon={hp=0}},frame=function(n) return frames[n] or base end}
end
local function world(id)
 local s={items={},records={[id]=record(id),[202]=record(202,3)}}
 local root=objects.place(s,0,id);root.owner=0;root.frame=10
 return s,root
end
for _,id in ipairs({5,55,1001,1019}) do
 local s,root=world(id)
 for _=1,10 do objects.spawn_from_frame(s,0,root) end
 local children={}
 for n=50,399 do if s.items[n] then children[#children+1]=n end end
 assert(#children==3,'root cloning is not bounded for record '..id)
 for _,n in ipairs(children) do
  local child=s.items[n];child.frame=10
  assert(child.record.id==id and child.spawn_clone_generation==1)
  objects.spawn_from_frame(s,n,child)
 end
 local count=0;for _ in pairs(s.items) do count=count+1 end
 assert(count==4,'clone descendants can create more clones')
 local child=s.items[children[1]];child.frame=20
 objects.spawn_from_frame(s,children[1],child)
 assert(s.items[53] and s.items[53].record.id==202,'clone projectile ability was removed')
 child.hp=0;root.frame=10;objects.spawn_from_frame(s,0,root)
 local alive=0
 for _,value in pairs(s.items) do if value.hp>0 and value.spawn_clone_generation then alive=alive+1 end end
 assert(alive==3,'lost clone cannot be replaced')
 if id==5 then assert(s.items[children[2]].hp==10 and s.items[children[2]].mp==5,'vanilla Rudolf clone stats changed') end
end
local s,root=world(55)
local other=objects.place(s,1,55);other.frame=10
objects.spawn_from_frame(s,0,root);objects.spawn_from_frame(s,1,other)
assert(root.spawn_clone_family~=other.spawn_clone_family,'independent casters share one limit')
print('PASS: Leumas/Rudolf/remapped clone families capped at 3; descendants blocked, projectiles and replacement allowed, vanilla stats preserved')
