-- Scene geometry and layer selectors from the author's data/bg/*.dat.
return function(base)
    local scenes = require("dbz/scene-modes")
    local load = base.load
    local selected = {}
    function base.reset_scene_modes() selected = {} end
    function base.select_mode(path, index)
        assert(scenes[path] and scenes[path].modes[index + 1], "unknown DBZ scene mode")
        selected[path] = index
    end
    function base.load(path)
        local raw = load(path)
        local scene = scenes[path]
        if not scene then return raw end
        local mode = scene.modes[(selected[path] or 0) + 1]
        local data = {}
        for key, value in pairs(raw) do data[key] = value end
        data.width, data.zboundary = mode.width, {mode.zboundary[1], mode.zboundary[2]}
        if mode.shadow_resource then data.shadow = mode.shadow_resource end
        data.layers, data.groups_ready = {}, nil
        local enabled = {}
        for _, value in ipairs(mode.respond or {0}) do enabled[value] = true end
        for index, layer in ipairs(raw.layers) do
            if enabled[scene.layer_respond[index] or 0] then
                local copy = {}
                for key, value in pairs(layer) do copy[key] = value end
                copy.group, copy.bitmap_width = nil, nil
                data.layers[#data.layers + 1] = copy
            end
        end
        data.dbz_scene, data.dbz_mode = scene, mode
        return data
    end
    return base
end
