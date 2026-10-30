return function(base)
    local settings = require("polish-fighters/settings")
    local roster = require("polish-fighters/roster")
    roster.validate(settings)
    local selectable, load = base.selectable, base.load
    function base.selectable(fighter)
        return roster.permits(settings, fighter, function(value)
            return selectable(value) or require("polish-fighters/progression").earned(base.profile_id,value.id)
        end)
    end
    local random_eligible = base.random_eligible
    function base.random_eligible(fighter)
        if #settings.allowed_ids > 0 then return base.selectable(fighter) end
        return random_eligible(fighter)
    end
    function base.load()
        local fighters = load()
        -- Do not remove/reorder records: recordings and references depend on their IDs.
        local found = false
        for _, fighter in ipairs(fighters) do
            if base.selectable(fighter) then found = true; break end
        end
        assert(found, "Polish Fighters: no selectable fighters; change settings.lua")
        return fighters
    end
    return base
end
