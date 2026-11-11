local root=arg[1]
package.preload['polish-originals/heroes']=function() return assert(loadfile(root..'/content-packs/polish-originals/heroes.lua'))() end
local rn=assert(loadfile(root..'/content-packs/polish-originals/remonoko.lua'))()
local records={}
for _,id in ipairs({1,414,415,427,428,429,430,431,432,433,434,435,436,437,438,439}) do
 records[id]={id=id,kind=id>=427 and 3 or 0,frames={}}
 for n=300,360,10 do records[id].frames[n]={mp=n==360 and 200 or 55,state=3} end
 records[id].frame=function(n) return records[id].frames[n] or {state=n==212 and 4 or 0} end
end
local function actor(id,team,x)
 return {record=records[id],hp=500,dark_hp=500,max_hp=500,mp=500,armor=100,
 x=x or 100,x_int=x or 100,y=0,y_int=0,z=300,z_int=300,vx=0,vy=0,vz=0,
 facing=0,team=team or 1,frame=0,keys={},previous_keys={}}
end
local function world()
 return {items={[0]=actor(414),[1]=actor(1,2,170)},frame_number=0,stage={width=800,zboundary={200,400}}}
end
local objects={record=function(s,id) return records[id] end}
function objects.create(s,id,owner,frame,team,x,y,z,vx,vy,vz,facing)
 local index=10
 while s.items[index] do index=index+1 end
 local p=actor(id,team,x);p.owner,p.frame,p.y,p.z,p.vx,p.vy,p.vz,p.facing=owner,frame,y,z,vx,vy,vz,facing
 s.items[index]=p;return index
end
function objects.remove(s,i) s.items[i]=nil end
local function cast(s,n)
 local v=s.items[0];v.frame=0;rn.advance(s,0,v,objects)
 v.frame=n;rn.advance(s,0,v,objects)
end
do
 local s=world();local v=s.items[0];v.frame=60
 rn.advance(s,0,v,objects);rn.advance(s,0,v,objects)
 assert(s.pf_events.spawn_427==1,'held frame fires more than one basic bullet')
 v.frame=61;rn.advance(s,0,v,objects);v.frame=65;rn.advance(s,0,v,objects)
 assert(s.pf_events.spawn_427==2 and v.mp==500,'basic combo/MP')
end
do
 local s=world();cast(s,300);assert(s.items[1].hp==458 and s.items[0].vx==15)
 for n=1,15 do rn.advance(s,0,s.items[0],objects) end
 assert(s.items[1].hp==458,'dash damages same opponent repeatedly')
end
do
 local s=world();cast(s,310);assert(s.pf_events.spawn_428==1)
 assert(s.items[10].vx==11 and s.items[10].rn_ttl==75)
 cast(s,320);assert(s.items[1].hp==462,'metal kick does not damage')
 s.items[1].team=1;cast(s,320);assert(s.items[1].hp==462,'friendly fire')
 cast(s,330)
 for n=1,25 do rn.advance(s,0,s.items[0],objects) end
 assert(s.pf_events.rn_flame==5,'fire stream pulse count')
end
do
 local s=world();s.items[1].x,s.items[1].z=2000,900
 cast(s,340);assert(s.items[0].x==780 and s.items[0].z==400,'teleport outside arena')
end
do
 local s=world();s.items[1].x=600;cast(s,350)
 local trap=s.items[10];assert(trap and trap.record.id==429 and trap.y==0 and trap.vx==0)
 rn.advance(s,10,trap,objects);assert(s.items[10],'trap fired outside range')
 s.items[1].x=110;rn.advance(s,10,trap,objects)
 assert(not s.items[10] and s.items[1].hp==452 and s.pf_events.rn_trap_trigger==1)
 cast(s,350);trap=s.items[10];trap.rn_ttl=1;rn.advance(s,10,trap,objects);assert(not s.items[10],'trap never expires')
end
do
 local s=world();local v=s.items[0];cast(s,360)
 assert(v.record.id==415 and not v.rn_mech_until and v.hp==500,'mech missing or heals for free')
 s.frame_number=299;rn.advance(s,0,v,objects);assert(v.record.id==415)
 s.frame_number=9000;rn.advance(s,0,v,objects);assert(v.record.id==415,'mech expired automatically')
 cast(s,360);assert(v.record.id==414,'manual cancellation did not work')
 cast(s,360);v.hp=0;rn.advance(s,0,v,objects);assert(v.record.id==414 and v.hp==0,'death reverted/HP')
end
do
 local s=world();local v=s.items[0];v.y,v.vy,v.frame=-40,-3,212
 for n=1,3 do
  v.keys.jump=true;v.previous_keys.jump=false;rn.after_control(s,0,v)
 end
 assert(v.rn_air_jumps==2 and s.pf_events.rn_air_jump==2,'extra jumps not limited to two')
 v.previous_keys.jump=true;rn.after_control(s,0,v);assert(v.rn_air_jumps==2)
 v.y,v.vy=0,0;rn.after_control(s,0,v);assert(v.rn_air_jumps==0,'landing did not reset jumps')
end
do
 local s=world();local v,a=s.items[0],s.items[1]
 assert(rn.armor(v,a,{y=-60,h=10})==125,'front armor')
 a.x=80;assert(rn.armor(v,a,{y=-60,h=10})==80,'rear weak point')
 a.x=170;assert(rn.armor(v,a,{y=-35,h=15})==80,'belly weak point')
 v.record=records[415];assert(rn.armor(v,a,{y=-35,h=15})==160,'mech armor')
 v.record=records[414];v.mp=0;assert(not rn.ai_move(s,v,a),'AI uses unaffordable skills')
 local original=actor(1);original.frame=300;rn.advance(s,1,original,objects)
 assert(not original.rn_action and original.hp==500,'other fighters changed')
end
do
 package.preload['polish-originals/remonoko']=function() return rn end
 local decorate=assert(loadfile(root..'/content-packs/polish-originals/remonoko_combat.lua'))()
 local s=world();local victim,attacker=s.items[0],s.items[1]
 attacker.record={id=1,kind=0,frame=function() return {centery=79,interactions={{y=15,height=10}}} end}
 attacker.hit_list_count,attacker.hit_list,attacker.hit_list_itr=1,{0},{1}
 attacker.frame_at_pass=60
 local calls=0
 local combat=decorate({apply=function(state,index)
  calls=calls+1;assert(state.items[0].armor==125,'combat did not use front armor')
 end})
 combat.apply(s,1);assert(calls==1 and victim.armor==100,'combat leaked temporary armor')
 combat=decorate({apply=function() error('expected test failure') end})
 assert(not pcall(combat.apply,s,1) and victim.armor==100,'exception leaked temporary armor')
end
print('PASS Remonoko: basic/MP, dash once, mega, kick/teams, flame, bounded teleport, trap trigger/expiry, persistent mech/manual cancellation/death, triple jump/landing, rear/belly armor, AI, combat restoration and isolation')
