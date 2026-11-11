-- Remonoko's deterministic simulation. No voice recordings or original DAT edits.
local rn = {}
local heroes = require('polish-originals/heroes')
function rn.owns(v) return v.record.id==414 or v.record.id==415 end
local function event(s,name,n)
 s.pf_events=s.pf_events or {};s.pf_events[name]=(s.pf_events[name] or 0)+(n or 1)
end
local function dir(v) return v.facing==0 and 1 or -1 end
local function enemy(v,t) return heroes.enemy(v,t) end
local function move(v,x,y,z)
 v.x,v.y,v.z=x,y,z;v.x_int,v.y_int,v.z_int=math.floor(x),math.floor(y),math.floor(z)
end
local function target(s,v)
 local result,distance,slot
 for i,t in pairs(s.items) do
  if enemy(v,t) then
   local d=(v.x-t.x)^2+(v.z-t.z)^2
   if not distance or d<distance or (d==distance and i<slot) then result,distance,slot=t,d,i end
  end
 end
 return result
end
local function hit(s,v,t,damage)
 local loss=math.min(t.hp,damage)
 t.hp=t.hp-loss;t.dark_hp=math.max(t.hp,t.dark_hp-math.floor(loss/2))
 t.hp_spent=(t.hp_spent or 0)+loss
 v.damage_dealt=(v.damage_dealt or 0)+loss
 if t.hp==0 then v.kills=(v.kills or 0)+1 end
 t.frame,t.wait_counter,t.hit_lag=180,0,3;t.vx,t.vy=dir(v)*8,-5
 event(s,'rn_damage',loss)
end
local function area(s,v,range,damage,once)
 for i,t in pairs(s.items) do
  local dx=(t.x-v.x)*dir(v)
  if enemy(v,t) and dx>=-18 and dx<range and math.abs(t.z-v.z)<35 and math.abs(t.y-v.y)<90 and (not once or not once[i]) then
   hit(s,v,t,damage);if once then once[i]=true end
  end
 end
end
local function shoot(s,i,v,objects,id,speed)
 local slot=objects.create(s,id,i,0,v.team,math.floor(v.x+dir(v)*35),math.floor(v.y-44),math.floor(v.z),dir(v)*speed,0,0,v.facing)
 if slot>=0 then
  local p=s.items[slot];p.rn_ttl=id==429 and 240 or 75;p.rn_owner=i
  if id==429 then move(p,v.x,0,v.z);p.vx,p.vy,p.vz=0,0,0 end
  event(s,'spawn_'..id)
 end
 return slot
end
function rn.ai_move(s,v,t)
 if not t or v.hp<=0 or v.y<0 or math.abs(t.z-v.z)>45 then return nil end
 local dx=math.abs(t.x-v.x)
 local choices=dx<100 and {320,300,360} or {310,330,340}
 for n=1,#choices do
  local frame=choices[((v.pf_ai_cycle or 0)+n-1)%#choices+1]
  local f=v.record.frames[frame]
  if f and (v.mp or 0)>=f.mp and not (frame==360 and v.record.id==415) then return frame end
 end
end
local function transform(s,v,objects,id)
 local record=objects.record(s,id)
 if not record then return false end
 v.record=record;v.frame,v.wait_counter,v.pic_offset=0,0,0
 v.rn_dash,v.rn_flame=nil,nil
 return true
end
function rn.advance(s,i,v,objects)
 local id=v.record.id
 if rn.owns(v) then
  if id==415 and v.hp<=0 then
   if transform(s,v,objects,414) then v.rn_mech_until=nil;v.frame=180;event(s,'rn_mech_end') end
  end
  if v.hp<=0 then return end
  if v.rn_dash and v.rn_dash>0 then
   v.rn_dash=v.rn_dash-1;v.vx=dir(v)*15
   area(s,v,85,v.record.id==415 and 60 or 42,v.rn_dash_hits)
  end
  if v.rn_flame and v.rn_flame>0 then
   v.rn_flame=v.rn_flame-1
   if v.rn_flame%5==0 then
    if v.record.id==415 then
     heroes.projectile(s,i,v,objects,430,dir(v)*11,-1)
     heroes.projectile(s,i,v,objects,430,dir(v)*11,1)
    else shoot(s,i,v,objects,427,8) end
    event(s,'rn_flame')
   end
  end
  local basic=v.frame==60 or v.frame==65 or v.frame==70 or v.frame==80 or v.frame==85 or v.frame==90
  if basic and v.rn_basic~=v.frame then
   v.rn_basic=v.frame
   if v.record.id==415 then
    area(s,v,115,35,{})
    heroes.projectile(s,i,v,objects,430,dir(v)*12,0,53)
    event(s,'rn_mech_basic')
   else shoot(s,i,v,objects,427,14) end
   event(s,'rn_basic')
  elseif not basic then v.rn_basic=nil end
  local frame=v.frame
  if frame>=300 and frame<=390 and frame%10==0 then
   if v.rn_action~=frame then
    v.rn_action=frame;event(s,'skill_414_'..frame)
    if frame==300 then
     v.rn_dash,v.rn_dash_hits=12,{};v.vx=dir(v)*15
     area(s,v,85,v.record.id==415 and 60 or 42,v.rn_dash_hits)
    elseif frame==310 then
     if v.record.id==415 then
      heroes.projectile(s,i,v,objects,431,dir(v)*11,-1.2,53)
      heroes.projectile(s,i,v,objects,431,dir(v)*11,1.2,53)
     else shoot(s,i,v,objects,428,11) end
    elseif frame==320 then
     area(s,v,110,v.record.id==415 and 65 or 38,{})
     if v.record.id==415 then heroes.effect(s,i,v,objects,439,0,5) end
    elseif frame==330 then
     v.rn_flame=25
     if v.record.id==415 then heroes.projectile(s,i,v,objects,430,dir(v)*11,0,53)
     else shoot(s,i,v,objects,427,8) end
    elseif frame==340 then
     if v.record.id==415 then
      for n=0,7 do
       local angle=n*math.pi/4
       heroes.projectile(s,i,v,objects,430,math.cos(angle)*10,math.sin(angle)*4)
      end
      heroes.effect(s,i,v,objects,439,0,5);event(s,'rn_fire_ring')
     else
     local t=target(s,v);local width=s.stage and s.stage.width or 2400
     local z=t and t.z or v.z;local bounds=s.stage and s.stage.zboundary
     if bounds then z=math.max(bounds[1],math.min(bounds[2],z)) end
     move(v,math.max(20,math.min(width-20,t and t.x-dir(v)*45 or v.x+dir(v)*150)),math.min(0,v.y),z)
     v.vx,v.vz=0,0;event(s,'rn_teleport')
     end
    elseif frame==350 then shoot(s,i,v,objects,429,0)
    elseif frame==360 then
     local next_id=v.record.id==414 and 415 or 414
     if transform(s,v,objects,next_id) then
      v.rn_mech_until=nil;event(s,next_id==415 and 'rn_mech' or 'rn_mech_end')
      heroes.effect(s,i,v,objects,439,0,5)
     end
    elseif frame==380 and v.record.id==415 then
     area(s,v,120,45,{});heroes.projectile(s,i,v,objects,430,dir(v)*13,0,60)
     heroes.effect(s,i,v,objects,439,0,5);event(s,'rn_combo_uppercut')
    elseif frame==390 and v.record.id==415 then
     area(s,v,145,60,{});heroes.projectile(s,i,v,objects,431,dir(v)*13,0,53)
     heroes.effect(s,i,v,objects,439,0,5);event(s,'rn_combo_finisher')
    end
   end
  else v.rn_action=nil end
 elseif id>=427 and id<=429 and v.rn_ttl then
  v.rn_ttl=v.rn_ttl-1
  if v.rn_ttl<=0 then objects.remove(s,i);return end
  if id==429 then
   local owner=s.items[v.rn_owner]
   if owner and owner.hp>0 then
    for _,t in pairs(s.items) do
     if enemy(owner,t) and math.abs(t.x-v.x)<55 and math.abs(t.z-v.z)<32 and math.abs(t.y)<65 then
      hit(s,owner,t,48);objects.remove(s,i);event(s,'rn_trap_trigger');return
     end
    end
   end
  end
 end
end
function rn.after_control(s,i,v)
 if not rn.owns(v) or v.hp<=0 then return end
 local keys,prev=v.keys or {},v.previous_keys or {}
 local frame=v.record.frame(v.frame)
 if v.y<0 and frame.state==4 and keys.jump and not prev.jump and (v.rn_air_jumps or 0)<2 then
  v.rn_air_jumps=(v.rn_air_jumps or 0)+1
  v.vy=-9;v.frame,v.wait_counter=212,0;event(s,'rn_air_jump')
 elseif v.y>=0 and (v.vy or 0)>=0 then v.rn_air_jumps=0 end
end
function rn.after_physics(s,i,v)
 if v.record.id==429 and v.rn_ttl then move(v,v.x,0,v.z);v.vx,v.vy,v.vz=0,0,0 end
end
-- Armor is scoped to the actual attacker and contact rectangle by the combat decorator.
function rn.armor(v,a,itr)
 if v.record.id==415 then return 160 end
 local rear=(a.x-v.x)*dir(v)<0
 local top=a.y-(itr.centery or 0)+(itr.y or 0)
 local belly=v.y-30
 local low_contact=top<=belly+12 and top+(itr.h or 0)>=belly-12
 return (rear or low_contact) and 80 or 125
end
return rn
