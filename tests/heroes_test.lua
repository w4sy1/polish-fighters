local root=arg[1]
local heroes=assert(loadfile(root..'/content-packs/polish-originals/heroes.lua'))()
local records={}
for _,id in ipairs({1,410,411,412,413,414,415,430,431,432,433,434,435,436,437,438,439}) do
 records[id]={id=id,kind=id>=430 and id~=433 and 3 or 0,frames={}}
 records[id].frame=function(n) return records[id].frames[n] or {state=0} end
end
local function actor(id,team,x)
 return {record=records[id],hp=500,dark_hp=500,max_hp=500,mp=500,frame=0,
 x=x or 100,x_int=x or 100,y=0,y_int=0,z=300,z_int=300,vx=0,vy=0,vz=0,
 facing=0,team=team or 1,owner=0,caught_by=0,keys={},previous_keys={}}
end
local function world(id)
 return {items={[0]=actor(id),[1]=actor(1,2,180)},frame_number=1,stage={width=800,zboundary={200,400}}}
end
local objects={}
function objects.free_slot(s) for n=10,399 do if not s.items[n] then return n end end;return -1 end
function objects.place(s,i,id) local v=actor(id);s.items[i]=v;return v end
function objects.create(s,id,owner,frame,team,x,y,z,vx,vy,vz,facing)
 local slot=objects.free_slot(s);if slot<0 then return -1 end
 local v=objects.place(s,slot,id);v.owner,v.frame,v.team=owner,frame,team
 v.x,v.y,v.z,v.vx,v.vy,v.vz,v.facing=x,y,z,vx,vy,vz,facing
 return slot
end
function objects.remove(s,i) s.items[i]=nil end
do
 local s=world(414);local v=s.items[0]
 heroes.initialize(v);assert(v.hp==600 and v.max_hp==600)
 heroes.initialize(v);assert(v.hp==600,'HP bonus applied twice')
 heroes.advance(s,0,v,objects);v.hp=560;s.frame_number=2;heroes.advance(s,0,v,objects)
 assert(v.hp==574 and s.pf_events.rn_reactive_heal==1,'RN lost reactive regeneration')
 s.frame_number=15;heroes.advance(s,0,v,objects);assert(v.hp==578,'RN passive regeneration')
 v.hp=0;heroes.advance(s,0,v,objects);assert(v.hp==0,'RN regeneration revived a dead fighter')
end
do
 local s=world(410);local v=s.items[0];heroes.advance(s,0,v,objects)
 v.hp=460;s.frame_number=2;heroes.advance(s,0,v,objects)
 assert(v.hp==484 and s.pf_events.wasyl_reactive_heal==1,'Wasyl reactive recovery')
 s.frame_number=12;heroes.advance(s,0,v,objects);assert(v.hp==486,'Wasyl recovery after hit')
 v.hp=499;heroes.heal(s,0,v,objects,40);assert(v.hp==500 and v.dark_hp>=500,'healing overflow/dark HP')
 v.hp=0;assert(heroes.heal(s,0,v,objects,40)==0 and v.hp==0)
end
do
 local s=world(412);local v=s.items[0];heroes.advance(s,0,v,objects)
 for n=1,3 do s.frame_number=n*40;v.hp=v.hp-10;heroes.advance(s,0,v,objects) end
 assert(s.pf_events.jas_counter_teleport==1 and v.x<180 and v.y==0,'third hit did not teleport')
 for n=4,6 do s.frame_number=n*40;v.hp=v.hp-10;heroes.advance(s,0,v,objects) end
 assert(s.pf_events.jas_counter_lightning==1 and s.pf_events.spawn_432==1,'sixth hit did not retaliate')
 assert(v.mp==500,'passive counter charged mana')
end
do
 local s=world(411);local v=s.items[0]
 assert(heroes.clone(s,0,v,objects));local child=s.items[10]
 assert(child.pf_clone and child.hp==500 and child.mp==500 and child.pf_clone_depth==1)
 assert(not heroes.clone(s,0,v,objects),'root summoned a second living child')
 assert(heroes.clone(s,10,child,objects));local grand=s.items[12]
 assert(grand.pf_clone_depth==2 and grand.pf_root==0 and grand.hp==500)
 assert(not heroes.clone(s,12,grand,objects),'unbounded clone recursion')
 assert(not heroes.enemy(v,child) and not heroes.enemy(v,grand),'clones attack their family')
 child.hp=0;assert(heroes.clone(s,0,v,objects),'cannot replace dead first-generation clone')
 assert(not heroes.clone_allowed(s,14,s.items[14]),'family exceeded three living units')
 local independent=world(411);independent.items[0].team=0
 assert(heroes.clone(independent,0,independent.items[0],objects))
 assert(not heroes.enemy(independent.items[0],independent.items[10]),'independent clones attack owner')
end
do
 local s=world(413);local v=s.items[0];v.hp,v.max_hp,v.dark_hp=1500,1500,1500
 heroes.summon_toilets(s,0,v,objects);assert(s.pf_events.boss_toilets==3)
 heroes.summon_toilets(s,0,v,objects);assert(s.pf_events.boss_toilets==3,'unlimited toilet summons')
 local turret=s.items[10];assert(turret.record.id==433 and turret.hp==180)
 s.frame_number=10000;heroes.advance(s,10,turret,objects)
 assert(s.items[10]==turret and s.pf_events.boss_toilet_fire==1,'turret expires or cannot fire')
 local x,z=turret.x,turret.z;turret.x,turret.y,turret.vx=600,-20,9;heroes.after_physics(s,10,turret)
 assert(turret.x==x and turret.z==z and turret.vx==0 and turret.y==0,'turret moved from placement')
 turret.hp=0;heroes.advance(s,10,turret,objects);assert(not s.items[10] and s.pf_events.boss_toilet_destroyed==1)
 heroes.summon_toilets(s,0,v,objects);assert(s.pf_events.boss_toilets==4,'cannot replace destroyed turret')
end
do
 local s=world(413);local v=s.items[0];v.frame=360
 assert(heroes.ultimate(s,0,v,objects))
 for n=1,45 do s.frame_number=n;heroes.advance(s,0,v,objects) end
 assert(not v.pf_sigma_charge and s.pf_events.boss_ultimate_blast==1 and s.pf_events.spawn_435==8)
 assert(s.items[1].hp==380,'ultimate did not damage opponent')
 assert(not heroes.ultimate(s,0,v,objects),'ultimate ignored cooldown')
 local interrupted=world(413);local b=interrupted.items[0];heroes.ultimate(interrupted,0,b,objects)
 b.frame=180;heroes.advance(interrupted,0,b,objects)
 assert(not b.pf_sigma_charge and interrupted.pf_events.boss_ultimate_interrupted==1)
end
print('PASS heroes: persistent health buffs, regeneration/death/caps, alternating ninja counters, full two-generation clones/family safety, persistent destructible turrets and charged/interruptible ultimate')
