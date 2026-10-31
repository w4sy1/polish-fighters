local root=arg[1]
local runtime=assert(loadfile(root.."/content-packs/polish-originals/runtime.lua"))()
local function actor(id,team)
    return {record={id=id,kind=id>=420 and 3 or 0},hp=500,dark_hp=500,max_hp=500,
      x=100,y=0,z=300,x_int=100,y_int=0,z_int=300,vx=0,vy=0,vz=0,facing=0,team=team or 1,
      frame=0,damage_dealt=0}
end
local function world(id)
    return {items={[0]=actor(id),[10]=actor(1,2)},frame_number=0,stage={width=800,zboundary={200,400}}}
end
do
    local state=world(411);local value=state.items[0]
    value.record.frames={[300]={mp=55},[320]={mp=50},[340]={mp=180},[350]={mp=100}}
    value.mp=60;state.items[10].x=350
    assert(runtime.ai_move(state,value,state.items[10])==300,'AI ignored affordable ranged move')
    value.mp=0;assert(not runtime.ai_move(state,value,state.items[10]),'AI selected unaffordable special')
    value.mp=500;state.items[10].z=400
    assert(not runtime.ai_move(state,value,state.items[10]),'AI attacked across lanes')
    state.items[10].z=300;value.pf_clone=true
    assert(not runtime.ai_move(state,value,state.items[10]),'clone selected special')
    value.pf_clone=nil
    state.items[20]=actor(2,2);state.items[20].x=350
    assert(runtime.ai_target(state,value)==state.items[10],'equal distance target must use lower slot')
end
local objects={}
function objects.free_slot(state)
    for n=50,399 do if not state.items[n] then return n end end
    return -1
end
function objects.place(state,slot,id)
    local value=actor(id);state.items[slot]=value;return value
end
function objects.create(state,id,owner,frame,team,x,y,z,vx,vy,vz,facing)
    local slot=objects.free_slot(state)
    if slot<0 then return -1 end
    local value=objects.place(state,slot,id)
    value.owner,value.frame,value.team=owner,frame,team
    value.x,value.y,value.z=x,y,z;value.x_int,value.y_int,value.z_int=x,y,z
    value.vx,value.vy,value.vz,value.facing=vx,vy,vz,facing
    return slot
end
function objects.remove(state,index) state.items[index]=nil end
local function cast(state,frame)
    local value=state.items[0]
    value.frame=0;runtime.advance(state,0,value,objects)
    value.frame=frame;runtime.advance(state,0,value,objects)
end
do
    local state=world(411);local sz=state.items[0];sz.frame=60
    runtime.advance(state,0,sz,objects);assert(state.pf_events.basic_shots==1 and state.items[50].record.id==426)
    runtime.advance(state,0,sz,objects);assert(state.pf_events.basic_shots==1,"duplicate basic shot while frame held")
    sz.frame=61;runtime.advance(state,0,sz,objects)
    sz.frame=60;runtime.advance(state,0,sz,objects);assert(state.pf_events.basic_shots==2,"next attack did not fire")
end
for _,id in ipairs({410,411}) do
    local state=world(id)
    cast(state,310)
    local twin=assert(state.items[50]);assert(twin.hp==250 and twin.pf_clone and twin.owner==0)
    cast(state,310);assert(state.items[51]==nil,"duplicate clone")
    twin.frame=310;runtime.advance(state,50,twin,objects);assert(state.items[51]==nil,"recursive clone")
    for n=1,900 do state.frame_number=n;runtime.advance(state,50,twin,objects) end
    assert(state.items[50]==twin and twin.hp==250,"clone expired")
    twin.hp=0;cast(state,310);assert(state.items[51] and state.pf_events.clones==2,"cannot replace defeated clone")
end
do
    local state=world(410);local v=state.items[0]
    runtime.advance(state,0,v,objects);v.hp=460;runtime.advance(state,0,v,objects)
    assert(v.hp==468 and state.pf_events.healed==8)
    v.hp=0;runtime.advance(state,0,v,objects);assert(v.hp==0,"healing revived dead fighter")
end
do
    local state=world(412);cast(state,300)
    assert(state.pf_events.spawn_421==8,"not exactly eight swords")
    runtime.advance(state,0,state.items[0],objects);assert(state.pf_events.spawn_421==8,"repeated action on same frame")
    for n=50,57 do assert(state.items[n].vx>0 and state.items[n].record.id==421) end
    cast(state,310);local slime=state.items[58];assert(slime.record.id==422)
    slime.x,slime.z=100,300;state.items[0].team=0;slime.team=0
    state.frame_number=1;slime.pf_ttl=166
    runtime.advance(state,58,slime,objects)
    assert(state.items[10].hp==496 and state.items[0].hp==500,"slime damage or owner protection")
    state.items[10].vx,state.items[10].vz=10,5
    runtime.after_control(state,10,state.items[10]);assert(state.items[10].vx==6 and state.items[10].vz==3)
    state.frame_number=40;state.items[10].vx=10;runtime.after_control(state,10,state.items[10]);assert(state.items[10].vx==10)
    slime.pf_ttl=1;runtime.advance(state,58,slime,objects);assert(state.items[58]==nil)
end
do
    local state=world(413);local boss=state.items[0];runtime.initialize(boss)
    assert(boss.hp==1500);boss.hp=700;runtime.advance(state,0,boss,objects)
    assert(boss.pf_phase2 and state.pf_events.boss_phase2==1)
    runtime.advance(state,0,boss,objects);assert(boss.hp==700 and state.pf_events.boss_phase2==1)
    cast(state,340);assert(state.pf_events.spawn_423==3)
    local helper=state.items[50];helper.pf_ttl=211;runtime.advance(state,50,helper,objects)
    assert(state.pf_events.spawn_424==1,"helper does not fire")
    cast(state,310);assert(state.items[10].hp==445,"stomp has no damage")
    assert(state.items[10].frame==180 and state.items[10].vy<0,"stomp has no knockdown reaction")
    cast(state,350);assert(state.pf_events.rain_orbs==9,"orb rain count")
    local falling=0
    for _,value in pairs(state.items) do
        if value.record.id==424 and value.y==-180 and value.vy==8 then falling=falling+1 end
    end
    assert(falling==9,"orb rain does not fall from above")
end
do
    local state=world(410);state.items[10].x=900;state.items[10].z=500
    cast(state,320);assert(state.items[0].x==780 and state.items[0].z==400,"teleport escaped stage")
    local original=state.items[10];original.frame=310;runtime.advance(state,10,original,objects)
    assert(not original.pf_initialized and original.hp==500,"original fighter changed")
end
do
    package.preload['polish-originals/layout']=function() return assert(loadfile(root..'/content-packs/polish-originals/layout.lua'))() end
    local render=assert(loadfile(root..'/content-packs/polish-originals/render.lua'))()
    local calls,legacy,last_width,last_height=0,0,0,0
    local context={scaled_sprite=function(resource,rect,x,y,w,h,mirrored,tint)
        calls=calls+1;assert(rect[1]>=0 and rect[2]>=0 and w>0 and h>0)
        last_width,last_height=w,h
        assert(x==math.floor(x) and y==math.floor(y))
    end,sprite=function(resource,rect,x,y,keyed,mirrored,flipped,tint)
        assert(keyed and not mirrored and flipped and tint==0x123456,"legacy sprite fields changed")
        legacy=legacy+1
    end,image=function() legacy=legacy+1 end,
    world_sprite=function() legacy=legacy+1 end}
    local wrapped=render.wrap(context)
    for _,key in ipairs({'w','s','j','b'}) do
        for pic=0,63 do wrapped.sprite('mods/polish-originals/'..key..'.png',{pic%8*80,math.floor(pic/8)*80,79,79},0,0,true,false) end
        wrapped.image('mods/polish-originals/'..key..'_h.png',10,10,false)
        assert(last_width==120 and last_height==120,"selection portrait must match LF2's 120x120 face")
        wrapped.sprite('mods/polish-originals/'..key..'_h.png',{0,0,55,55},10,10,false,false)
        assert(last_width==120 and last_height==120)
        wrapped.image('mods/polish-originals/'..key..'_s.png',10,10,false)
        assert(last_width==40 and last_height==45,"HUD portrait must match LF2's 40x45 face")
    end
    wrapped.sprite('sprite/sys/deep_0.bmp',{0,0,79,79},0,0,true,false,true,0x123456)
    wrapped.image('pe/frame',0,0,false)
    wrapped.world_sprite('sprite/sys/deep_0.bmp',{0,0,79,79},0,0,false)
    assert(calls==268 and legacy==3,"renderer changed original assets")
end
print('PASS: one persistent clone, no recursion, eight swords, bounded healing, slime damage/slow/expiry, boss phase/helpers, teleport bounds and original renderer delegation')
