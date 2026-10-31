return function(base)
    base.source_path = "mods/polish-originals/catalog.txt"
    base.profile_id = "polish-originals"
    local load = base.load
    -- The classic bitmap font is ASCII. Preserve Polish names separately for TTF/UI metadata.
    local names = {[410]="Wasyl",[411]="SZ",[412]="Mega Ninja Jas",[413]="Skibidi Sigma Tata"}
    function base.load()
        local fighters = load()
        for _, value in ipairs(fighters) do
            if names[value.id] then
                value.name = names[value.id]
                value.full_name = value.id == 411 and "Szymonoko" or value.name
                if value.id == 412 then
                    value.full_name="Mega Ninja Jaś"
                    value.strength, value.difficulty = 2, 2.5
                end
            end
        end
        return fighters
    end
    return base
end
