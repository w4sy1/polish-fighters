-- Shared, deterministic additions for the custom roster. Original mod records are untouched.
local heroes={}
local function event(s,name,n)
 s.pf_events=s.pf_events or {};s.pf_events[name]=(s.pf_events[name] or 0)+(n or 1)
end
heroes.event=event
local function direction(v) return v.facing==0 and 1 or -1 end
local function family(a,b) return a.pf_family~=nil and a.pf_family==b.pf_family end
heroes.family=family
local function enemy(a,b)
 return a~=b and b.hp>0 and b.record.kind==0 and not family(a,b) and (a.team==0 or a.team~=b.team)
end
heroes.enemy=enemy
local function relocate(v,x,y,z)
 v.x,v.y,v.z=x,y,z;v.x_int,v.y_int,v.z_int=math.floor(x),math.floor(y),math.floor(z)
end
heroes.relocate=relocate
local function caught(s,i,v)
 local frame=v.record.frame(v.frame)
 local catcher=s.items[v.caught_by]
 return frame.cpoint and frame.cpoint.kind==2 and catcher and catcher.catching==i
end
function heroes.nearest(s,v)
 local best,dist,slot
 for i,t in pairs(s.items) do
  if enemy(v,t) then
   local d=(t.x-v.x)^2+(t.z-v.z)^2
   if not dist or d<dist or (d==dist and i<slot) then best,dist,slot=t,d,i end
  end
 end
 return best
end
function heroes.projectile(s,i,v,objects,id,vx,vz,y)
 local owner=v.pf_root or i
 local slot=objects.create(s,id,owner,0,v.team,math.floor(v.x+direction(v)*38),
  math.floor(v.y-(y or 48)),math.floor(v.z),vx,0,vz or 0,v.facing)
 if slot>=0 then
  local p=s.items[slot];p.pf_ttl=75;p.pf_master=i;p.pf_family=v.pf_family
  event(s,'spawn_'..id)
 end
 return slot
end
function heroes.effect(s,i,v,objects,id,frame,y)
 local slot=objects.create(s,id,i,frame or 0,v.team,math.floor(v.x),math.floor(v.y-(y or 42)),math.floor(v.z),0,0,0,v.facing)
 if slot>=0 then
  local p=s.items[slot];p.pf_visual=true;p.pf_anchor=i;p.pf_anchor_y=y or 42;p.pf_ttl=16
  event(s,'effect_'..id)
 end
 return slot
end
function heroes.heal(s,i,v,objects,amount)
 if v.hp<=0 or v.hp>=v.max_hp then return 0 end
 local gain=math.min(amount,v.max_hp-v.hp)
 v.hp=v.hp+gain;v.dark_hp=math.max(v.dark_hp,v.hp)
 event(s,'heal_'..v.record.id,gain)
 if (s.frame_number or 0)>=(v.pf_next_aura or 0) then
  heroes.effect(s,i,v,objects,436);v.pf_next_aura=(s.frame_number or 0)+24
 end
 return gain
end
function heroes.area(s,i,v,range,damage,front,once)
 for j,t in pairs(s.items) do
  local dx=t.x-v.x
  if enemy(v,t) and math.abs(dx)<range and (not front or dx*direction(v)>-18)
    and math.abs(t.z-v.z)<(front and 40 or 75) and math.abs(t.y-v.y)<110 and (not once or not once[j]) then
   local loss=math.min(t.hp,damage)
   t.hp=t.hp-loss;t.dark_hp=math.max(t.hp,t.dark_hp-math.floor(loss/2));t.hp_spent=(t.hp_spent or 0)+loss
   local source=s.items[v.pf_root or v.pf_master] or v
   source.damage_dealt=(source.damage_dealt or 0)+loss
   if t.hp==0 and (t.follow==nil or t.follow==-1) then source.kills=(source.kills or 0)+1 end
   t.frame,t.wait_counter,t.hit_lag=180,0,3;t.vx,t.vy=(dx>=0 and 8 or -8),-5
   if once then once[j]=true end
   event(s,'hero_area_damage',loss)
  end
 end
end
function heroes.initialize(v)
 if (v.record.id==414 or v.record.id==415) and not v.rn_initialized then
  local gain=100
  v.hp,v.dark_hp,v.max_hp=v.hp>0 and v.hp+gain or 0,v.dark_hp+gain,v.max_hp+gain
  v.rn_initialized=true
 end
end
function heroes.clone_allowed(s,i,v)
 if v.record.id~=411 or v.hp<=0 or v.pf_clone or (v.pf_clone_depth or 0)>0 then return false end
 local root=v.pf_root or i
 for j,t in pairs(s.items) do
  if t.hp>0 and t.record.id==411 then
   if t.pf_clone and (t.pf_root==root or t.pf_master==i) then return false end
  end
 end
 return true
end
function heroes.clone(s,i,v,objects)
 if not heroes.clone_allowed(s,i,v) then return false end
 local slot=objects.free_slot(s);if slot<0 then return false end
 local twin=objects.place(s,slot,411);if not twin then return false end
 local root=v.pf_root or i
 v.pf_family='sz:'..root
 twin.pf_initialized,twin.pf_clone,twin.pf_master=true,true,i
 twin.pf_clone_depth=(v.pf_clone_depth or 0)+1;twin.pf_root=root;twin.pf_family=v.pf_family
 twin.pf_self_index=slot;twin.team,twin.owner,twin.human=v.team,root,false;twin.follow=root
 twin.hp,twin.max_hp,twin.dark_hp=v.max_hp,v.max_hp,v.max_hp;twin.mp=500;twin.facing=v.facing
 relocate(twin,v.x-direction(v)*50,0,v.z+12)
 heroes.effect(s,slot,twin,objects,437,20)
 event(s,'clones');event(s,'sz_clone_depth_'..twin.pf_clone_depth)
 return true
end
local function react(s,i,v,objects,loss)
 local id=v.record.id;local n=s.frame_number or 0
 if id==410 then
  heroes.heal(s,i,v,objects,math.min(40,math.ceil(loss*.60)))
  v.pf_recovery_until=n+120;event(s,'wasyl_reactive_heal')
 elseif id==414 or id==415 then
  heroes.heal(s,i,v,objects,math.min(20,math.ceil(loss*.35)))
  event(s,'rn_reactive_heal')
 elseif id==412 then
  v.pf_counter_hits=(v.pf_counter_hits or 0)+1
  if v.pf_counter_hits>=3 and n>=(v.pf_counter_ready or 0) and not caught(s,i,v) then
   v.pf_counter_hits=0;v.pf_counter_ready=n+35;v.pf_counter_cycle=(v.pf_counter_cycle or 0)+1
   local t=heroes.nearest(s,v)
   if v.pf_counter_cycle%2==1 then
    heroes.effect(s,i,v,objects,437)
    local width=s.stage and s.stage.width or 2400
    local x=t and t.x-direction(t)*75 or v.x-direction(v)*140
    local z=t and t.z+24 or v.z
    local bounds=s.stage and s.stage.zboundary
    if bounds then z=math.max(bounds[1],math.min(bounds[2],z)) end
    relocate(v,math.max(20,math.min(width-20,x)),0,z)
    if t then v.facing=v.x<t.x and 0 or 1 end
    v.frame,v.wait_counter,v.hit_lag,v.vx,v.vy,v.vz=0,0,0,0,0,0;v.blink=8
    heroes.effect(s,i,v,objects,437);event(s,'jas_counter_teleport')
   else
    if t then v.facing=t.x>=v.x and 0 or 1 end
    heroes.projectile(s,i,v,objects,432,direction(v)*15,t and math.max(-3,math.min(3,(t.z-v.z)/12)) or 0)
    heroes.effect(s,i,v,objects,437);event(s,'jas_counter_lightning')
   end
  end
 end
end
function heroes.summon_toilets(s,i,v,objects)
 local active=0
 for _,t in pairs(s.items) do if t.record.id==433 and t.pf_master==i and t.hp>0 then active=active+1 end end
 v.pf_family='boss:'..i
 local width=s.stage and s.stage.width or 2400
 for n=active+1,3 do
  local slot=objects.free_slot(s);if slot<0 then break end
  local t=objects.place(s,slot,433);if not t then break end
  t.pf_turret,t.pf_master,t.pf_family=true,i,v.pf_family;t.owner,t.team,t.follow=i,v.team,i
  t.hp,t.max_hp,t.dark_hp,t.mp=180,180,180,0
  local z=v.z+(n-2)*28;local bounds=s.stage and s.stage.zboundary
  if bounds then z=math.max(bounds[1],math.min(bounds[2],z)) end
  relocate(t,math.max(20,math.min(width-20,v.x-direction(v)*(40+n*45))),0,z)
  t.pf_turret_x,t.pf_turret_z=t.x,t.z;t.facing=v.facing;t.pf_fire_at=(s.frame_number or 0)+n*7
  heroes.effect(s,slot,t,objects,438);event(s,'boss_toilets')
 end
end
function heroes.ultimate(s,i,v,objects)
 if v.pf_sigma_charge or (s.frame_number or 0)<(v.pf_sigma_ready or 0) then
  v.mp=math.min(500,(v.mp or 0)+230);return false
 end
 v.pf_sigma_charge=45;v.pf_sigma_ready=(s.frame_number or 0)+240
 heroes.effect(s,i,v,objects,438);event(s,'boss_ultimate_charge');return true
end
function heroes.advance(s,i,v,objects)
 local id=v.record.id;local n=s.frame_number or 0
 if id>=410 and id<=415 then
  heroes.initialize(v);v.pf_self_index=i
  if v.hp>0 then
   if v.pf_last_health and v.hp<v.pf_last_health then react(s,i,v,objects,v.pf_last_health-v.hp) end
   if (id==414 or id==415) and n%15==0 then heroes.heal(s,i,v,objects,4) end
   if id==410 and n<=(v.pf_recovery_until or -1) and n%12==0 then heroes.heal(s,i,v,objects,2) end
   if id==411 and v.pf_clone and v.mp>=150 and n%3==0 then v.mp=math.min(500,v.mp+1) end
  end
  v.pf_last_health=v.hp
  if id==413 and v.pf_sigma_charge then
   if v.hp<=0 or (v.frame>=180 and v.frame<=199) or caught(s,i,v) then
    v.pf_sigma_charge=nil;event(s,'boss_ultimate_interrupted')
   else
    v.pf_sigma_charge=v.pf_sigma_charge-1;v.vx,v.vz=0,0;v.frame,v.wait_counter=360,0
    if v.pf_sigma_charge%7==0 then heroes.effect(s,i,v,objects,438) end
    if v.pf_sigma_charge==0 then
     heroes.area(s,i,v,310,120,false,{})
     for step=0,7 do
      local angle=step*math.pi/4
      local slot=heroes.projectile(s,i,v,objects,435,math.cos(angle)*9,math.sin(angle)*4)
      if slot>=0 then s.items[slot].facing=math.cos(angle)>=0 and 0 or 1 end
     end
     heroes.effect(s,i,v,objects,439,0,5)
     v.pf_sigma_charge=nil;v.frame,v.wait_counter=361,0;s.shake=8;event(s,'boss_ultimate_blast')
    end
   end
  end
 elseif id==433 then
  if v.hp<=0 then
   heroes.effect(s,i,v,objects,438);objects.remove(s,i);event(s,'boss_toilet_destroyed');return
  end
  local t=heroes.nearest(s,v)
  if t and n>=(v.pf_fire_at or 0) then
   v.facing=t.x>=v.x and 0 or 1
   heroes.projectile(s,i,v,objects,434,direction(v)*12,math.max(-2.5,math.min(2.5,(t.z-v.z)/14)),34)
   v.pf_fire_at=n+40;v.frame,v.wait_counter=60,0;event(s,'boss_toilet_fire')
  end
 elseif id>=430 and id<=439 and v.pf_ttl then
  v.pf_ttl=v.pf_ttl-1
  if v.pf_ttl<=0 then objects.remove(s,i) end
 end
end
function heroes.after_physics(s,i,v)
 if v.record.id==433 and v.pf_turret then
  relocate(v,v.pf_turret_x,0,v.pf_turret_z);v.vx,v.vy,v.vz=0,0,0
 elseif v.pf_visual then
  local anchor=s.items[v.pf_anchor]
  if anchor then relocate(v,anchor.x,anchor.y-v.pf_anchor_y,anchor.z) end
  v.vx,v.vy,v.vz=0,0,0
 end
end
return heroes
