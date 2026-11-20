-- SPDX-License-Identifier: MIT
local layout = {}
layout.order = {"stick", "left", "down", "right", "up", "defend", "attack", "jump", "s1", "s2", "s3", "pause"}
layout.screen = {left = 0, top = 0, right = 794, bottom = 550}
layout.labels = {stick = "Joystick", left = "←", right = "→", up = "↑", down = "↓",
    attack = "ATAK", jump = "SKOK", defend = "OBRONA", s1 = "S1", s2 = "S2", s3 = "S3", pause = "II"}
local defaults = {
    stick = {171, 551, 124, true}, left = {97, 630, 46, false}, down = {205, 630, 46, false},
    right = {315, 630, 46, false}, up = {205, 523, 46, false},
    defend = {873, 595, 56, true}, attack = {1021, 595, 81, true}, jump = {1169, 595, 56, true},
    s1 = {959, 456, 39, true}, s2 = {1061, 456, 39, true}, s3 = {1161, 456, 39, true},
    pause = {640, 44, 26, true},
}
local arrows = {left = true, right = true, up = true, down = true}
layout.arrows = arrows

function layout.number(value, fallback, low, high)
    if type(value) ~= "number" or value ~= value then return fallback end
    return math.max(low, math.min(high, value))
end

function layout.copy(value)
    value = type(value) == "table" and value or {}
    local result = {controls = {}, bindings = {},
        deadzone = layout.number(value.deadzone, 0.15, 0.05, 0.75),
        buffer_ms = layout.number(value.buffer_ms, 300, 100, 900),
        run = value.run == "strong" and "strong" or "double"}
    for _, name in ipairs(layout.order) do
        local default = defaults[name]
        local item = type(value.controls) == "table" and value.controls[name]
        item = type(item) == "table" and item or {}
        result.controls[name] = {
            x = layout.number(item.x, default[1] / 1280, 0, 1),
            y = layout.number(item.y, default[2] / 720, 0, 1),
            size = layout.number(item.size, 1, 0.55, 1.85),
            opacity = layout.number(item.opacity, 0.65, 0.15, 1),
            shape = item.shape == "round" and "round" or (item.shape == "rect" or arrows[name]) and "rect" or "round",
            enabled = item.enabled == nil and default[4] or item.enabled == true,
        }
    end
    if type(value.bindings) == "table" then
        for fighter, slots in pairs(value.bindings) do
            if type(fighter) == "string" and type(slots) == "table" then
                local checked = {}
                for _, slot in ipairs({"s1", "s2", "s3"}) do
                    local move = slots[slot]
                    if type(move) == "string" then checked[slot] = move end
                end
                result.bindings[fighter] = checked
            end
        end
    end
    return result
end

function layout.geometry(settings, screen)
    local width, height = screen.right - screen.left, screen.bottom - screen.top
    local scale = math.min(width / 1280, height / 720)
    local result = {}
    for _, name in ipairs(layout.order) do
        local entry = settings.controls[name]
        local radius = defaults[name][3] * scale * entry.size
        local rx, ry = radius, radius
        if entry.shape == "rect" and not arrows[name] and name ~= "stick" and name ~= "pause" then
            rx, ry = radius * 1.35, radius * 0.72
        end
        result[name] = {name = name, x = layout.number(screen.left + width * entry.x, 0, screen.left + rx, screen.right - rx),
            y = layout.number(screen.top + height * entry.y, 0, screen.top + ry, screen.bottom - ry),
            rx = rx, ry = ry, radius = radius, shape = entry.shape, opacity = entry.opacity, enabled = entry.enabled,
            scale = scale * entry.size}
    end
    return result
end

function layout.hit(geometry, x, y, show_disabled, paused)
    local chosen, nearest
    for _, name in ipairs(layout.order) do
        local item = geometry[name]
        if item and (item.enabled or show_disabled) and (not paused or name == "pause") then
            local dx, dy = math.abs(x - item.x) / item.rx, math.abs(y - item.y) / item.ry
            -- Both shapes use a linear, edge-normalized distance so overlapping buttons compare fairly.
            local distance = item.shape == "rect" and math.max(dx, dy) or math.sqrt(dx * dx + dy * dy)
            if distance <= 1 and (not nearest or distance <= nearest) then chosen, nearest = name, distance end
        end
    end
    return chosen
end

return layout
