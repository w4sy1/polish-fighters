return function(base)
    local control=base.control
    local enter=require("base/game/control").enter_frame
    local runtime=require("polish-originals/runtime")
    function base.control(state,index,mode,context)
        local value=state.items[index]
        if value.record.id<410 or value.record.id>413 then return control(state,index,mode,context) end
        for _,key in ipairs({"up","down","left","right","attack","jump","defend"}) do
            value.previous_keys[key]=value.keys[key];value.keys[key]=false
        end
        if value.hp<=0 then return end
        local target=runtime.ai_target(state,value)
        if not target then return end
        local dx,dz=target.x-value.x,target.z-value.z
        local ranged=value.record.id==411
        local preferred=ranged and 190 or 50
        if math.abs(dx)>preferred then value.keys[dx>0 and "right" or "left"]=true end
        if math.abs(dz)>7 then value.keys[dz>0 and "down" or "up"]=true end
        value.facing=dx>=0 and 0 or 1
        if math.abs(dx)<(ranged and 360 or 85) and math.abs(dz)<24 then
            value.keys.attack=(state.frame_number+index)%12<5
        end
        if not value.pf_clone and state.frame_number>=(value.pf_ai_cast or 70) and
           value.record.frame(value.frame).state<=2 then
            local cycle=value.pf_ai_cycle or 0
            local move=runtime.ai_move(state,value,target)
            if move then
                enter(state,value,move)
                value.pf_ai_cycle=cycle+1;value.pf_ai_cast=state.frame_number+100
            end
        end
    end
    return base
end
