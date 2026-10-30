return function(base)
    local progress=require("polish-fighters/progression")
    local create,close,start=base.create,base.close,base.start
    function base.create(...)
        progress.suspended=true
        return create(...)
    end
    function base.close(...)
        local value,problem=close(...)
        progress.suspended=false
        return value,problem
    end
    function base.start(...)
        progress.suspended=true
        local value,problem=start(...)
        -- Legacy start can call close internally; keep rewards suspended afterwards.
        progress.suspended=true
        return value,problem
    end
    return base
end
