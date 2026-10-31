return function(base)
    local runtime = require("polish-originals/runtime")
    local objects = require("base/game/objects")
    local before, after, physics = base.before_advance, base.after_control, base.after_physics
    function base.before_advance(state,index,value)
        before(state,index,value)
        runtime.advance(state,index,value,objects)
    end
    function base.after_control(state,index,value)
        after(state,index,value)
        runtime.after_control(state,index,value)
    end
    function base.after_physics(state,index,value)
        local removed = physics(state,index,value)
        if not removed then runtime.after_physics(state,index,value) end
        return removed
    end
    return base
end
