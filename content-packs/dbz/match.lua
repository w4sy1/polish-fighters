return function(base)
    local create,step = base.create,base.step
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
        state.dbz_campaign_scenes=definitions
        state.dbz_backgrounds=options.backgrounds
        state.dbz_scene_stage=state.stage_run and state.stage_run.id
        runtime.spawn(state, objects)
        return state
    end
    function base.step(state,...)
        local result=step(state,...)
        if state.stage_run and state.dbz_scene_stage~=state.stage_run.id then
            local selected=state.dbz_campaign_scenes and state.dbz_campaign_scenes[tostring(state.stage_run.id)]
            if selected then runtime.transition(state,selected,state.dbz_backgrounds,background,objects) end
            state.dbz_scene_stage=state.stage_run.id
        end
        return result
    end
    return base
end
