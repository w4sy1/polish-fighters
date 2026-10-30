-- Pure policy shared by the catalog decorator and tests.
local roster = {}
function roster.validate(settings)
    assert(type(settings) == "table", "settings must be a table")
    assert(type(settings.allowed_ids) == "table", "allowed_ids must be a list")
    assert(type(settings.allow_hidden) == "boolean", "allow_hidden must be boolean")
    local seen = {}
    for index, id in pairs(settings.allowed_ids) do
        assert(type(index) == "number" and index >= 1 and index <= #settings.allowed_ids and index % 1 == 0, "allowed_ids must be dense")
        assert(type(id) == "number" and id >= 0 and id % 1 == 0, "invalid fighter ID")
        assert(not seen[id], "duplicate fighter ID")
        seen[id] = true
    end
    return seen
end
function roster.permits(settings, fighter, original_selectable)
    local allowed = roster.validate(settings)
    if #settings.allowed_ids > 0 and not allowed[fighter.id] then return false end
    return settings.allow_hidden or original_selectable(fighter)
end
return roster
