return function(base)
    local create = base.create
    local runtime = require("dbz/scene_runtime")
    local objects = require("base/game/objects")
    local background = require("base/game/background")
    local stage_scenes = require("dbz/stage-scenes")
    function base.create(options)
        background.reset_scene_modes()
        local definitions = options.campaign_path and stage_scenes[options.campaign_path]
        local selected = definitions and definitions[tostring(options.stage_level)]
        if selected then options.campaign_background = selected.row end
        local row = selected and selected.row or options.background
        local entry = options.backgrounds[row + 1]
        if entry then background.select_mode(entry.path, options.scene_mode or (selected and selected.mode) or 0) end
        local state = create(options)
        runtime.spawn(state, objects)
        return state
    end
    return base
end
