return function(base)
    local create = base.create
    local runtime = require("polish-originals/runtime")
    function base.create(options)
        local state = create(options)
        for _,value in pairs(state.items) do runtime.initialize(value) end
        return state
    end
    return base
end
