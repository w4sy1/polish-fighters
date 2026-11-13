engine={new_array=function() return {} end,random=function() return 0 end}
local heroes=dofile(arg[1]..'/content-packs/polish-originals/heroes.lua')
local objects=require('base/game/objects')
local constants=require('base/game/constants')
local blank={state=0,center_x=0,center_y=0,opoint={kind=0,oid=0},mp=0}
local record={id=411,kind=0,data={weapon={hp=0}},frame=function() return blank end}
local effect={id=437,kind=3,data={weapon={hp=0}},frame=function() return blank end}
local function world()
 local s={items={},records={[411]=record,[437]=effect},frame_number=0}
 local v=objects.place(s,0,411);v.owner=0;v.max_hp=500;v.hp=500
 return s,v
end
local function alive(s,root)
 local n=0
 for _,v in pairs(s.items) do if v.pf_clone and v.pf_root==root and v.hp>0 then n=n+1 end end
 return n
end
local s,v=world()
assert(heroes.clone(s,0,v,objects))
local child=s.items[50]
assert(child and child.pf_clone)
for _=1,100 do
 assert(not heroes.clone(s,0,v,objects),'root exceeded one active clone')
 assert(not heroes.clone(s,50,child,objects),'clone created a descendant')
end
assert(alive(s,0)==1)
child.hp=0;assert(heroes.clone(s,0,v,objects),'dead clone was not replaceable')
assert(alive(s,0)==1)
local replacement
for i,t in pairs(s.items) do if t.pf_clone and t.hp>0 then replacement=i end end
objects.remove(s,replacement)
assert(heroes.clone(s,0,v,objects),'removed clone was not replaceable')
assert(alive(s,0)==1)
v.hp=0;assert(not heroes.clone(s,0,v,objects),'dead owner summoned a clone')
local fresh,owner=world()
assert(heroes.clone(fresh,0,owner,objects),'new match retained old clone count')
for root=1,7 do
 local caster=objects.place(fresh,root,411);caster.owner=root
 assert(heroes.clone(fresh,root,caster,objects));assert(alive(fresh,root)==1)
end
assert(alive(fresh,0)==1,'eight owners share a clone limit')
print('PASS Szymonoko: one clone per owner, no descendants, death/removal/reentry, eight independent owners')
