-- SPDX-License-Identifier: MIT
local layout = require("base/ui/hybrid_layout")
local font = require("base/ui/font")
local hud = {}
local has_locale, locale = pcall(require, "polish-fighters/menu_locale")
-- Translates the editor's and the buttons' Polish labels when the game runs in English.
function hud.tr(text)
    if has_locale then
        local translated, value = pcall(locale.translate, text)
        if translated and type(value) == "string" then return value end
    end
    return text
end
-- The bitmap font draws one byte per glyph, so UTF-8 letters and symbols need ASCII stand-ins.
local ascii = {["ą"] = "a", ["ć"] = "c", ["ę"] = "e", ["ł"] = "l", ["ń"] = "n", ["ó"] = "o", ["ś"] = "s",
    ["ź"] = "z", ["ż"] = "z", ["Ą"] = "A", ["Ć"] = "C", ["Ę"] = "E", ["Ł"] = "L", ["Ń"] = "N", ["Ó"] = "O",
    ["Ś"] = "S", ["Ź"] = "Z", ["Ż"] = "Z", ["−"] = "-", ["›"] = ">", ["←"] = "<", ["→"] = ">", ["↑"] = "^",
    ["↓"] = "v", ["↖"] = "<", ["↙"] = "<", ["↗"] = ">", ["↘"] = ">"}
function hud.ascii(text)
    return (text:gsub("[\xC2-\xF4][\x80-\xBF]+", function(character) return ascii[character] or "?" end))
end
local colors = {
    attack = {133, 21, 48, 255, 141, 168}, jump = {161, 74, 4, 255, 194, 125},
    defend = {15, 75, 147, 133, 205, 255}, special = {80, 25, 133, 209, 155, 255},
    neutral = {42, 40, 59, 194, 182, 223}, knob = {115, 112, 143, 223, 216, 242},
}

local function plate(context, x, y, rx, ry, shape, color, opacity, pressed)
    local bands = math.max(8, math.min(52, math.ceil(ry * 1.35)))
    local height = 2 * ry / bands
    local inset = math.max(1, math.min(rx, ry) * 0.035)
    local alpha = math.floor(255 * opacity)
    for row = 0, bands - 1 do
        local offset = (row + 0.5) * height - ry
        local fraction = math.abs(offset) / ry
        local half = rx * math.sqrt(math.max(0, 1 - fraction ^ 2))
        if shape == "rect" then
            local corner = math.min(rx, ry) * 0.25
            local rise = math.max(0, math.abs(offset) - ry + corner)
            half = rx - corner + math.sqrt(corner ^ 2 - rise ^ 2)
        end
        local top = math.floor(y - ry + row * height)
        local bottom = math.floor(y - ry + (row + 1) * height)
        if bottom > top then
            local border = math.max(inset, half * (fraction > 0.96 and 1 or 0))
            local glow = math.floor(24 * (1 - fraction) + (pressed and 38 or 0))
            local left, right = math.floor(x - half), math.floor(x + half)
            local width = right - left
            local line = math.min(width, math.ceil(border))
            if line > 0 then
                context.fill(left, top, line, bottom - top, color[4], color[5], color[6], alpha)
                if width > line then
                    local edge = math.min(line, width - line)
                    context.fill(right - edge, top, edge, bottom - top, color[4], color[5], color[6], alpha)
                    if width > line + edge then
                        context.fill(left + line, top, width - line - edge, bottom - top,
                            color[1] + glow, color[2] + glow, color[3] + glow, alpha)
                    end
                end
            end
        end
    end
end

local function label(context, text, x, y, size, native_text)
    text = hud.tr(text)
    if native_text and context.text then
        context.text(text, math.floor(x), math.floor(y - size * 0.57), "center", size, 0xffffff, 0x262032)
    else
        font.draw(context, hud.ascii(text), math.floor(x), math.floor(y - 8), nil, nil, "center")
    end
end

local compass = {"→", "↘", "↓", "↙", "←", "↖", "↑", "↗"}
function hud.draw(context, geometry, state, preview, selected)
    if not preview and not state.visible then return end
    if not preview then context.overlay(true) end
    for _, name in ipairs(layout.order) do
        local item = geometry[name]
        if (item.enabled or preview and selected == name) and (preview or state.mode ~= "pause" or name == "pause")
            and (preview or state.mode ~= "selection" or (name ~= "pause" and not name:match("^s%d$")))
            and (preview or name ~= "skills" or (state.pages or 1) > 1) then
            local color = colors[name] or (name:sub(1, 1) == "s" and name ~= "stick" and colors.special or colors.neutral)
            local opacity = item.enabled and item.opacity or 0.22
            if selected == name then
                local x, y = math.floor(item.x - item.rx - 3), math.floor(item.y - item.ry - 3)
                local w, h = math.ceil(item.rx * 2 + 6), math.ceil(item.ry * 2 + 6)
                context.fill(x, y, w, 1, 192, 133, 255, 255)
                context.fill(x, y + h, w, 1, 192, 133, 255, 255)
                context.fill(x, y, 1, h, 192, 133, 255, 255)
                context.fill(x + w, y, 1, h, 192, 133, 255, 255)
            end
            plate(context, item.x, item.y, item.rx, item.ry, item.shape, color, opacity,
                state.counts and (state.counts[name] or 0) > 0)
            if name == "stick" then
                for index, arrow in ipairs(compass) do
                    local angle = (index - 1) * math.pi / 4
                    label(context, arrow, item.x + math.cos(angle) * item.rx * 0.73,
                        item.y + math.sin(angle) * item.ry * 0.73, math.max(8, math.floor(item.radius * 0.24)), state.text)
                end
                local knob = item.radius * 0.29
                plate(context, item.x + (state.knob_x or 0) * item.radius * 0.61,
                    item.y + (state.knob_y or 0) * item.radius * 0.61, knob, knob, "round", colors.knob, opacity, false)
            else
                local size = math.max(8, math.floor(math.min(item.ry * 0.66, item.rx * 2.85 / #layout.labels[name])))
                local caption = name:match("^s%d$") and layout.slot(name, state.page):upper() or layout.labels[name]
                label(context, caption, item.x, item.y, size, state.text)
            end
        end
    end
    if not preview then context.overlay(false) end
end

return hud
