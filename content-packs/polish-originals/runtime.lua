-- Additive mechanics, scoped to IDs 410-426; no original fighter data is changed.
local runtime = {}
local function own(value) return value.record.id>=410 and value.record.id<=413 end
local function event(state,name,count)
    state.pf_events=state.pf_events or {}
    state.pf_events[name]=(state.pf_events[name] or 0)+(count or 1)
end
local function enemy(a,b)
    return a~=b and b.hp>0 and b.record.kind==0 and (a.team==0 or a.team~=b.team)
end
local function direction(value) return value.facing==0 and 1 or -1 end
local function relocate(value,x,y,z)
    value.x,value.y,value.z=x,y,z
    value.x_int,value.y_int,value.z_int=math.floor(x),math.floor(y),math.floor(z)
end
function runtime.initialize(value)
    if value.record.id==413 and not value.pf_initialized then
        value.hp,value.dark_hp,value.max_hp=1500,1500,1500
    end
    if own(value) then value.pf_initialized=true end
end
local function nearest(state,value)
    local selected,distance,selected_index
    for target_index,target in pairs(state.items) do
        if enemy(value,target) and target_index~=value.pf_master and
           not (target.pf_clone and state.items[target.pf_master]==value) then
            local current=(target.x-value.x)^2+(target.z-value.z)^2
            if not distance or current<distance or (current==distance and target_index<selected_index) then
                selected,distance,selected_index=target,current,target_index
            end
        end
    end
    return selected
end
local function shoot(state,index,value,objects,id,count,speed)
    for n=1,count do
        local offset=(n-(count+1)/2)
        local muzzle_height=value.record.id==413 and 60 or 44
        local slot=objects.create(state,id,index,0,value.team,math.floor(value.x+direction(value)*35),
            math.floor(value.y-muzzle_height),math.floor(value.z+offset*8),direction(value)*speed,0,offset*.6,value.facing)
        if slot>=0 then
            local effect=state.items[slot]
            effect.pf_ttl=id==422 and 180 or (id==423 and 240 or 90)
            effect.pf_master=index
            event(state,"spawn_"..id)
        end
    end
end
local function rain(state,index,value,objects)
    local target=nearest(state,value) or value
    for n=1,9 do
        local width=state.stage and state.stage.width or 2400
        local x=math.max(20,math.min(width-20,target.x+(n-5)*22))
        local slot=objects.create(state,424,index,0,value.team,math.floor(x),-180,
            math.floor(target.z),0,8,0,value.facing)
        if slot>=0 then
            state.items[slot].pf_ttl=70;state.items[slot].pf_master=index
            event(state,"spawn_424");event(state,"rain_orbs")
        end
    end
end
local function clone(state,index,value,objects)
    if value.pf_clone then return end
    for _,other in pairs(state.items) do
        if other.pf_clone and other.pf_master==index and other.hp>0 then return end
    end
    local slot=objects.free_slot(state)
    if slot<0 then return end
    local twin=objects.place(state,slot,value.record.id)
    if not twin then return end
    twin.pf_initialized,twin.pf_clone,twin.pf_master=true,true,index
    twin.team,twin.owner,twin.human=value.team,index,false
    twin.follow=index
    twin.hp=math.floor(value.max_hp/2);twin.max_hp,twin.dark_hp=twin.hp,twin.hp
    twin.facing=value.facing
    relocate(twin,value.x-direction(value)*45,0,value.z+12)
    event(state,"clones")
end
function runtime.ai_target(state,value) return nearest(state,value) end
-- Pick useful, affordable moves instead of cycling through every skill irrespective of range.
function runtime.ai_move(state,value,target)
    if value.pf_clone or value.hp<=0 or value.y<0 or not target then return nil end
    local dx,dz=math.abs(target.x-value.x),math.abs(target.z-value.z)
    local choices
    if dz>45 then return nil end
    local id=value.record.id
    if id==410 then choices=dx<95 and {330,300} or (dx>260 and {320,300} or {300,340})
    elseif id==411 then choices=dx<95 and {320,300} or {340,300,350}
    elseif id==412 then choices=dx<100 and {310,300} or (dx>260 and {330,320,300} or {300,350})
    elseif id==413 then choices=dx<160 and {310,330,300} or {350,340,300}
    else return nil end
    local first=(value.pf_ai_cycle or 0)%#choices
    for offset=0,#choices-1 do
        local number=choices[(first+offset)%#choices+1]
        local frame=value.record.frames and value.record.frames[number]
        if frame and frame.mp>=0 and frame.mp<=999 and (value.mp or 0)>=frame.mp then return number end
    end
end
local function blink(state,value)
    local target=nearest(state,value)
    local x=target and target.x-direction(value)*45 or value.x+direction(value)*150
    -- Use the stage bounds when available; physics still enforces passable geometry.
    local width=state.stage and state.stage.width or 2400
    local bounds=state.stage and state.stage.zboundary
    local z=target and target.z or value.z
    if bounds then z=math.max(bounds[1],math.min(bounds[2],z)) end
    relocate(value,math.max(20,math.min(width-20,x)),math.min(0,value.y),z)
    value.vx,value.vz=0,0
    event(state,"teleports")
end
local function area(state,index,value,range,damage,slow)
    for target_index,target in pairs(state.items) do
        if target_index~=index and target_index~=value.pf_master and
           not (target.pf_clone and target.pf_master==index) and enemy(value,target)
           and math.abs(target.x-value.x)<range and math.abs(target.z-value.z)<45 then
            local loss=math.min(target.hp,damage)
            target.hp=target.hp-loss
            target.dark_hp=math.max(target.hp,target.dark_hp-math.floor(loss/2))
            local source=state.items[value.pf_master] or value
            source.damage_dealt=(source.damage_dealt or 0)+loss
            if target.hp==0 and not target.pf_clone then source.kills=(source.kills or 0)+1 end
            if not slow or target.hp==0 then
                target.frame,target.wait_counter,target.hit_lag=180,0,3
                target.vx,target.vy=(target.x>=value.x and 6 or -6),-5
            end
            event(state,"area_damage",loss)
            if slow then
                state.pf_slows=state.pf_slows or {}
                state.pf_slows[target_index]=(state.frame_number or 0)+35
            end
        end
    end
end
local function action(state,index,value,objects,frame)
    local id=value.record.id
    if value.pf_clone then
        -- Clones use basic attacks and a small shot, never recursively clone/ultimate.
        if frame==300 then shoot(state,index,value,objects,id==410 and 420 or 426,1,9) end
        return
    end
    if id==410 then
        if frame==310 then clone(state,index,value,objects)
        elseif frame==320 then blink(state,value)
        elseif frame==330 then area(state,index,value,95,35,false)
        else shoot(state,index,value,objects,420,frame>=340 and 5 or 3,10) end
    elseif id==411 then
        if frame==310 then clone(state,index,value,objects)
        else
            if frame==320 or frame==350 then blink(state,value) end
            shoot(state,index,value,objects,426,frame>=340 and 8 or 3,13)
            if frame==340 then
                for other_index,other in pairs(state.items) do
                    if other.pf_clone and other.pf_master==index and other.hp>0 then shoot(state,other_index,other,objects,426,5,13) end
                end
            end
        end
    elseif id==412 then
        if frame==310 or frame==350 then shoot(state,index,value,objects,422,1,3)
        elseif frame==320 then blink(state,value)
        elseif frame==330 then
            value.pf_surf=24;value.vx=direction(value)*12;value.vy=-6
            shoot(state,index,value,objects,421,1,12)
        else shoot(state,index,value,objects,421,8,11) end
    elseif id==413 then
        if frame==310 then area(state,index,value,170,55,false)
        elseif frame==330 then shoot(state,index,value,objects,425,1,5)
        elseif frame==340 then shoot(state,index,value,objects,423,3,2)
        elseif frame==350 then rain(state,index,value,objects)
        else shoot(state,index,value,objects,424,value.pf_phase2 and 5 or 3,8) end
    end
    event(state,"skill_"..id.."_"..frame)
end
function runtime.advance(state,index,value,objects)
    local id=value.record.id
    if own(value) then
        runtime.initialize(value)
        if id==411 then
            local attack_start=value.frame==60 or value.frame==65 or value.frame==70 or
                value.frame==80 or value.frame==85 or value.frame==90
            if attack_start and value.hp>0 then
                if value.pf_basic_shot~=value.frame then
                    value.pf_basic_shot=value.frame
                    shoot(state,index,value,objects,426,1,13)
                    value.pf_basic_shots=(value.pf_basic_shots or 0)+1
                    event(state,"basic_shots")
                end
            else value.pf_basic_shot=nil end
        end
        if id==410 and value.hp>0 and value.pf_previous_hp and value.hp<value.pf_previous_hp then
            local amount=math.min(8,math.floor((value.pf_previous_hp-value.hp)/4))
            value.hp=math.min(value.dark_hp,value.max_hp,value.hp+amount)
            if amount>0 then event(state,"healed",amount) end
        end
        value.pf_previous_hp=value.hp
        if id==413 and value.hp>0 and value.hp<value.max_hp/2 and not value.pf_phase2 then
            value.pf_phase2=true;event(state,"boss_phase2")
        end
        if value.hp>0 and value.frame>=300 and value.frame<=360 and value.frame%10==0 then
            if value.pf_action~=value.frame then
                value.pf_action=value.frame
                action(state,index,value,objects,value.frame)
            end
        else value.pf_action=nil end
    elseif id>=420 and id<=426 and value.pf_ttl then
        value.pf_ttl=value.pf_ttl-1
        if value.pf_ttl<=0 then objects.remove(state,index);return end
        if id==422 and value.pf_ttl%15==0 then area(state,index,value,85,4,true) end
        if id==423 and value.pf_ttl%35==0 then shoot(state,index,value,objects,424,1,8) end
    end
end
function runtime.after_control(state,index,value)
    local until_frame=state.pf_slows and state.pf_slows[index]
    if until_frame then
        if (state.frame_number or 0)<=until_frame then value.vx,value.vz=value.vx*.60,value.vz*.60
        else state.pf_slows[index]=nil end
    end
    if value.pf_phase2 then value.vx=math.max(-13,math.min(13,value.vx*1.1)) end
end
function runtime.after_physics(state,index,value)
    if value.record.id==422 and value.pf_ttl then
        relocate(value,value.x,0,value.z);value.vx,value.vy,value.vz=0,0,0
    elseif value.record.id==423 and value.pf_ttl then
        relocate(value,value.x,-25,value.z);value.vx,value.vy,value.vz=0,0,0
    elseif value.record.id==425 and value.pf_ttl then
        relocate(value,value.x,-20,value.z);value.vy=0
    elseif value.pf_surf and value.pf_surf>0 then
        value.pf_surf=value.pf_surf-1;value.vy=0;value.vx=direction(value)*12
    end
end
return runtime
