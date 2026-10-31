return function(base)
    local draw = base.draw
    local render = require("polish-originals/render")
    function base.draw(state,context,...)
        return draw(state,render.wrap(context),...)
    end
    return base
end
