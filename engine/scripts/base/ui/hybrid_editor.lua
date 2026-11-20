-- SPDX-License-Identifier: MIT
local layout = require("base/ui/hybrid_layout")
local input_driver = require("base/ui/hybrid_input")
local hud = require("base/ui/hybrid_hud")
local options = require("base/game/options")
local catalog = require("base/game/catalog")
local background = require("base/game/background")
local object_data = require("base/game/object_data")
local font = require("base/ui/font")
local editor = {}
local preview = {left = 13, top = 87, right = 377, bottom = 435}
local function fighter_key(path) return catalog.profile_id .. ":" .. path end
editor.fighter_key = fighter_key

function editor.create(values, destination)
    values.hybrid = layout.copy(values.hybrid)
    local fighters, selected = {}, 1
    for _, fighter in ipairs(catalog.load()) do
        if fighter.name:lower() ~= "template" and catalog.selectable(fighter) then
            fighters[#fighters + 1] = fighter
            if fighter.name:lower() == "davis" then selected = #fighters end
        end
    end
    local arena = background.load(catalog.backgrounds()[1].path)
    return {values = values, fighters = fighters, fighter = selected, selected = "stick",
        arena = arena, arena_view = background.create_state(arena), destination = destination or "options"}
end

local function actions(s)
    local rows = {}
    local settings, name = s.values.hybrid, s.selected
    local entry = settings.controls[name]
    local function button(x, y, w, text, run)
        rows[#rows + 1] = {x = x, y = y, w = w, text = text, run = run}
    end
    local function adjust(y, text, target, key, delta, low, high)
        button(391, y, 31, "−", function() target[key] = math.max(low, target[key] - delta) end)
        button(556, y, 31, "+", function() target[key] = math.min(high, target[key] + delta) end)
        rows[#rows + 1] = {x = 423, y = y, w = 132, text = text}
    end
    button(391, 87, 196, layout.labels[name] .. "  ›", function()
        for i, id in ipairs(layout.order) do
            if id == name then s.selected = layout.order[i % #layout.order + 1]; break end
        end
    end)
    adjust(128, ("Rozmiar %d%%"):format(math.floor(entry.size * 100 + 0.5)), entry, "size", 0.05, 0.55, 1.85)
    adjust(169, ("Krycie %d%%"):format(math.floor(entry.opacity * 100 + 0.5)), entry, "opacity", 0.05, 0.15, 1)
    adjust(210, ("Martwa strefa %d%%"):format(math.floor(settings.deadzone * 100 + 0.5)), settings, "deadzone", 0.05, 0.05, 0.75)
    adjust(251, ("Bufor %d ms"):format(settings.buffer_ms), settings, "buffer_ms", 25, 100, 900)
    button(391, 292, 196, entry.shape == "round" and "Kształt: okrągły" or "Kształt: prostokątny",
        function() entry.shape = entry.shape == "round" and "rect" or "round" end)
    button(391, 333, 196, entry.enabled and "Widoczny" or "Ukryty", function() entry.enabled = not entry.enabled end)
    button(391, 374, 196, settings.run == "double" and "Bieg: dwa wychylenia" or "Bieg: mocne wychylenie",
        function() settings.run = settings.run == "double" and "strong" or "double" end)

    button(391, 413, 95, "Joystick", function()
        local standard = layout.copy()
        for _, id in ipairs(layout.order) do settings.controls[id] = standard.controls[id] end
        s.selected = "stick"
    end)
    button(492, 413, 95, "Strzałki", function()
        local standard = layout.copy()
        for _, id in ipairs(layout.order) do
            local control = standard.controls[id]
            settings.controls[id] = control
            control.enabled = id ~= "stick"
            control.shape = id == "pause" and "round" or "rect"
        end
        settings.controls.attack.x, settings.controls.attack.y = 1115 / 1280, 630 / 720
        settings.controls.attack.size = 1.09
        settings.controls.defend.x, settings.controls.defend.y = 905 / 1280, 588 / 720
        settings.controls.jump.x, settings.controls.jump.y = 1060 / 1280, 533 / 720
        settings.controls.s1.x, settings.controls.s2.x, settings.controls.s3.x = 973 / 1280, 1081 / 1280, 1189 / 1280
        s.selected = "up"
    end)

    local fighter = s.fighters[s.fighter]
    button(601, 87, 26, "<", function() s.fighter = (s.fighter - 2) % math.max(#s.fighters, 1) + 1 end)
    rows[#rows + 1] = {x = 628, y = 87, w = 126, text = (fighter and fighter.name or "Postać"):sub(1, 21)}
    button(757, 87, 24, ">", function() s.fighter = s.fighter % math.max(#s.fighters, 1) + 1 end)
    if fighter then
        local key = fighter_key(fighter.path)
        if s.move_fighter ~= fighter then
            s.moves = input_driver.moves(object_data.load(fighter.path))
            s.move_fighter = fighter
        end
        local moves = s.moves
        for index, slot in ipairs({"s1", "s2", "s3"}) do
            local y = 139 + (index - 1) * 79
            local control = settings.controls[slot]
            button(601, y, 180, slot:upper() .. (control.enabled and "  Włączony" or "  Wyłączony"),
                function() control.enabled = not control.enabled end)
            local active = input_driver.binding(settings, key, moves, slot)
            button(601, y + 33, 180, active and ("D + " .. active[2] .. "  ›") or "Brak przypisania  ›", function()
                local position = 0
                for i, move in ipairs(moves) do if move == active then position = i end end
                local next_move = moves[(position + 1) % (#moves + 1)]
                settings.bindings[key] = settings.bindings[key] or {}
                settings.bindings[key][slot] = next_move and next_move[1] or "none"
            end)
        end
    end
    button(13, 476, 214, "Przywróć domyślne", function() s.values.hybrid = layout.copy(); s.selected = "stick" end)
    button(238, 476, 139, "Anuluj", function() return "cancel" end)
    button(391, 476, 390, "Zapisz", function()
        local saved, problem = options.save(s.values, true)
        if saved then return "apply" end
        s.error = "Błąd zapisu: " .. tostring(problem)
    end)
    return rows
end

function editor.update(s, input)
    if (input.nav and input.nav.cancel) or (input.keys and input.keys[27]) then return "cancel" end
    local x, y = input.pointer_x, input.pointer_y
    if not x or not y then return end
    local settings = s.values.hybrid
    if input.click then
        for _, row in ipairs(actions(s)) do
            if row.run and x >= row.x and x < row.x + row.w and y >= row.y and y < row.y + 30 then return row.run() end
        end
        local geometry = layout.geometry(settings, preview)
        local name = layout.hit(geometry, x, y, false)
        if not name and not geometry[s.selected].enabled then
            name = layout.hit({[s.selected] = geometry[s.selected]}, x, y, true)
        end
        if name then
            s.selected = name
            s.drag = {x = x - geometry[name].x, y = y - geometry[name].y}
        end
    end
    if s.drag and input.button then
        local entry = settings.controls[s.selected]
        entry.x = layout.number((x - s.drag.x - preview.left) / (preview.right - preview.left), 0, 0, 1)
        entry.y = layout.number((y - s.drag.y - preview.top) / (preview.bottom - preview.top), 0, 0, 1)
    elseif not input.button then
        s.drag = nil
    end
end

function editor.draw(s, context)
    context.viewport(794, 550, 23, 23, 33)
    local native = require("base/i18n/i18n").can_draw_text() and context.text ~= nil
    local function text(label, x, y, size)
        if native then context.text(label, x, y, "center", size, 0xf6f1ff)
        else font.draw(context, label, x, y, nil, nil, "center") end
    end
    context.fill(0, 0, 794, 61, 33, 31, 46, 255)
    text("Polish Fighters", 104, 12, 21)
    text("OpenLF2", 104, 38, 12)
    context.fill(197, 14, 2, 34, 154, 76, 239, 255)
    text("Ustawienia sterowania", 461, 15, 27)
    context.fill(13, 87, 364, 348, 43, 38, 56, 255)
    context.clip(13, 87, 364, 348)
    local arena_context = {
        image = function(resource, x, y, keyed) context.image(resource, x - 212, y + 8, keyed) end,
        fill = function(x, y, w, h, r, g, b) context.fill(x - 212, y + 8, w, h, r, g, b) end,
    }
    background.paint(arena_context, s.arena, s.arena_view, 0)
    context.fill(13, 87, 364, 348, 29, 21, 43, 45)
    context.clip()
    context.fill(391, 87, 196, 348, 30, 28, 42, 255)
    context.fill(601, 87, 180, 348, 30, 28, 42, 255)
    hud.draw(context, layout.geometry(s.values.hybrid, preview), {text = native}, true, s.selected)
    text("Przeciągnij element, aby zmienić pozycję", 195, 443, 12)
    for _, row in ipairs(actions(s)) do
        local r, g, b = 50, 43, 68
        if row.text == "Zapisz" then r, g, b = 108, 48, 184 end
        if row.run then context.fill(row.x, row.y, row.w, 30, r, g, b, 255) end
        text(row.text, row.x + math.floor(row.w / 2), row.y + 7, 13)
    end
    if s.error then text(s.error:sub(1, 100), 397, 518, 13) end
end
return editor
