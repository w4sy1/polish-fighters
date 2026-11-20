-- Local command selection. Only the accepted choice enters match input.
local hybrid_layout = require("base/ui/hybrid_layout")
local commands = require("base/game/team_commands")
local menu = {}
local choices = {"attack", "stay", "come", "defend"}

function menu.layout(screen, touch, controls)
    screen = screen or hybrid_layout.screen
    local right, top, bottom = screen.right, screen.top, screen.bottom
    local width, height = screen.right - screen.left, bottom - top
    local scale = math.min(width / 794, height / 550)
    if scale <= 0 then return nil end
    local radius, w, h, gap = 20 * scale, 101 * scale, 37 * scale, 6 * scale
    local x = right - radius - 16 * scale
    local y = touch and top + height * 0.35 or bottom - radius - 30 * scale
    local function at(cx, cy)
        local trigger = {x = cx - radius, y = cy - radius, w = 2 * radius, h = 2 * radius}
        local left = touch and trigger.x - 2 * (w + gap) or right - 2 * w - gap - 16 * scale
        local upper = touch and cy - h - gap / 2 or trigger.y - 2 * (h + gap)
        local result = {trigger = trigger, scale = scale, touch = touch}
        for i, command in ipairs(choices) do
            result[i] = {x = left + (i - 1) % 2 * (w + gap), y = upper + math.floor((i - 1) / 2) * (h + gap),
                w = w, h = h, command = command}
        end
        return result
    end
    if not touch then return at(x, y) end
    for _, offset in ipairs({0, 0.09, -0.09, 0.18, -0.15, 0.27}) do
        for _, shift in ipairs({0, 0.15, 0.30, 0.45}) do
            local result = at(x - width * shift, y + height * offset)
            local clear = true
            for _, box in pairs({result.trigger, result[1], result[2], result[3], result[4]}) do
                if box.x < screen.left or box.y < top or box.y + box.h + 5 * scale > bottom then clear = false end
                for _, control in pairs(controls or {}) do
                    if control.enabled and box.x < control.x + control.rx and box.x + box.w > control.x - control.rx
                        and box.y < control.y + control.ry and box.y + box.h + 5 * scale > control.y - control.ry then
                        clear = false
                    end
                end
            end
            if clear then return result end
        end
    end
end

local function hit(box, x, y)
    return x and y and x >= box.x and x < box.x + box.w and y >= box.y and y < box.y + box.h
end

local function activate(s, x, y)
    if not s.layout then return false end
    local trigger = s.layout.trigger
    local radius = trigger.w / 2
    if hit(trigger, x, y) and (x - trigger.x - radius)^2 + (y - trigger.y - radius)^2 <= radius^2 then
        s.open = not s.open
        return true
    end
    if s.open then
        for _, box in ipairs(s.layout) do
            if hit(box, x, y) then
                s.pending = commands.signals[box.command]
                s.open = false
                return true
            end
        end
    end
    return false
end

function menu.update(s, input, enabled, layout, v, escape, touch)
    s.layout = enabled and layout or nil
    if not s.layout then s.open, s.pending, s.progress = false, nil, 0 end
    local close = s.open and escape
    if close then s.open = false
    elseif s.layout and v then s.open = not s.open end

    if touch and touch.contacts then
        local contacts = {}
        for _, contact in ipairs(touch.contacts) do
            local id = contact.id
            if contact.phase == "d" then s.owned[id] = activate(s, contact.x, contact.y) or nil end
            if not s.owned[id] then contacts[#contacts + 1] = contact end
            if contact.phase == "u" or contact.phase == "x" then s.owned[id] = nil end
        end
        touch.contacts = contacts
    elseif touch and touch.touch_active then
        local previous, touches = s.owned, {}
        s.owned = {}
        for _, point in ipairs(touch.touches or {}) do
            local owned = previous[point.id]
            if owned == nil then owned = activate(s, point.x, point.y) end
            s.owned[point.id] = owned
            if not owned then touches[#touches + 1] = point end
        end
        touch.touches = touches
    elseif input.click then
        activate(s, input.pointer_x, input.pointer_y)
    end
    if s.layout then
        s.progress = math.max(0, math.min(1, (s.progress or 0) + (s.open and 0.25 or -0.25)))
    end
    return close
end

return menu
