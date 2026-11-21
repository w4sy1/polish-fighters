-- SPDX-License-Identifier: MIT
local layout = require("base/ui/hybrid_layout")
local hybrid = {}
local letters = {left = "l", right = "r", up = "u", down = "d", attack = "c", jump = "b", defend = "f"}
local axes = {{"left", "right"}, {"up", "down"}}
local actions = {"defend", "jump", "attack"}
local sectors = {"r", "dr", "d", "dl", "l", "ul", "u", "ur"}
local skills = {
    {"Fa", "Przód + atak", "forward", "c"}, {"Ua", "Góra + atak", "u", "c"},
    {"Da", "Dół + atak", "d", "c"}, {"Fj", "Przód + skok", "forward", "b"},
    {"Uj", "Góra + skok", "u", "b"}, {"Dj", "Dół + skok", "d", "b"}, {"ja", "Skok + atak", "b", "c"},
}

function hybrid.moves(record)
    local result = {}
    if not record then return result end
    local frames = record.frames
    for _, spec in ipairs(skills) do
        local variants = {}
        for source, frame in pairs(frames) do
            local target = frame.hits[spec[1]]
            if target and target ~= 0 and frames[math.abs(target)] then
                local variant = variants[target]
                if not variant then
                    variant = {frame = frames[math.abs(target)], target = target, sources = {}}
                    variants[target] = variant
                end
                variant.sources[#variant.sources + 1] = source
            end
        end
        if next(variants) then
            local move = {spec[1], spec[2], spec[3], spec[4], variants = {}}
            for _, variant in pairs(variants) do
                table.sort(variant.sources)
                move.variants[#move.variants + 1] = variant
            end
            table.sort(move.variants, function(left, right) return left.target < right.target end)
            result[#result + 1] = move
        end
    end
    return result
end

-- Profiles can extend this function via package.manifest to annotate a parsed
-- target. The annotation is presentation data and never changes match input.
function hybrid.move_details(profile, fighter, move, variant)
    if profile ~= "polish-originals" then return end
    local known = require("polish-fighters/combo_guide").moves(fighter.id)
    for _, entry in ipairs(known or {}) do
        if entry[3] == math.abs(variant.target) then return entry[2] end
    end
end

-- Alternate targets share an input chord but use their own animation windows.
-- Require the original frame names so only matching Tiger data receives these shortcuts.
local tiger_variants = {
    {216, "tiger_genkidama", "Genkidama", "Po zwykłym ryku (S5)."},
    {320, "roar5", "Dalszy ryk", "Po dodatkowym bloku podczas ryku."},
}

function hybrid.shortcuts(record)
    local moves = hybrid.moves(record)
    for _, move in ipairs(moves) do
        if move[1] == "Uj" then
            for _, spec in ipairs(tiger_variants) do
                for _, variant in ipairs(move.variants) do
                    if variant.target == spec[1] and variant.frame.name == spec[2] then
                        variant.caption, variant.condition = spec[3], spec[4]
                        moves[#moves + 1] = {move[1] .. ":" .. variant.target,
                            variant.caption, move[3], move[4], variant = variant}
                    end
                end
            end
            break
        end
    end
    return moves
end

function hybrid.describe(record)
    local moves = hybrid.shortcuts(record)
    local rows = {}
    for _, move in ipairs(moves) do
        for _, variant in ipairs(move.variants or {}) do
            rows[#rows + 1] = {move = move, variant = variant}
        end
    end
    return moves, rows
end

function hybrid.pages(moves)
    return math.max(1, math.ceil(#moves / layout.slots_per_page))
end

function hybrid.binding(settings, key, moves, slot)
    local bindings = key and settings.bindings[key]
    local configured = bindings and bindings[slot]
    if configured then
        for _, move in ipairs(moves) do
            if move[1] == configured then return move end
        end
        return nil
    end
    return moves[tonumber(slot:sub(2))]
end

function hybrid.create(settings)
    return {settings = settings, fingers = {}, counts = {}, queue = {}, direction = "",
        output = "", clock = 0, knob_x = 0, knob_y = 0, visible = false, page = 1, pages = 1}
end

function hybrid.reset(s)
    s.fingers, s.counts, s.queue = {}, {}, {}
    s.stick, s.guard, s.strong, s.pause, s.trace = nil, nil, nil, false, nil
    s.direction, s.output, s.knob_x, s.knob_y = "", "", 0, 0
    s.jump_at, s.attack_at, s.follow_up = nil, nil, nil
end

local function contains(value, letter) return value:find(letter, 1, true) ~= nil end
local function append(value, letter) return contains(value, letter) and value or value .. letter end
local function held(s)
    local result = s.direction
    for _, axis in ipairs(axes) do
        local negative, positive = letters[axis[1]], letters[axis[2]]
        local n = contains(result, negative) or (s.counts[axis[1]] or 0) > 0
        local p = contains(result, positive) or (s.counts[axis[2]] or 0) > 0
        result = result:gsub("[" .. negative .. positive .. "]", "")
        if n ~= p then result = result .. (n and negative or positive) end
    end
    for _, name in ipairs(actions) do
        if (s.counts[name] or 0) > 0 then result = result .. letters[name] end
    end
    return result
end

local function enqueue(s, value)
    if value == (s.queue[#s.queue] or s.output) then return end
    if #s.queue < 96 then s.queue[#s.queue + 1] = value end
end

local function enter_direction(s, value, now)
    local previous = s.direction
    s.direction = value
    if previous == value then return end
    if s.guard and now - s.guard.start <= s.settings.buffer_ms and value ~= "" then s.guard.direction = value end
    enqueue(s, held(s))
end

local function move_stick(s, event, now)
    local item = s.geometry.stick
    local dx, dy = (event.x - item.x) / item.radius, (event.y - item.y) / item.radius
    local distance = math.sqrt(dx * dx + dy * dy)
    local limit = math.max(1, distance)
    s.knob_x, s.knob_y = dx / limit, dy / limit
    if distance <= s.settings.deadzone then
        s.strong = false
        enter_direction(s, "", now)
        return
    end
    local direction = sectors[1 + math.floor(math.atan2(dy, dx) / (math.pi / 4) + 0.5) % 8]
    if s.settings.run == "strong" and distance >= 0.86 and not s.strong and direction:find("[lr]") then
        s.strong = true
        local base = held(s):gsub("[lr]", "")
        local horizontal = direction:match("[lr]")
        enqueue(s, base)
        enqueue(s, base .. horizontal)
        enqueue(s, base)
        enqueue(s, base .. horizontal)
    elseif distance < 0.65 then
        s.strong = false
    end
    enter_direction(s, direction, now)
end

local function shortcut(s, name, fighter, record_key)
    if not fighter then return end
    local move = hybrid.binding(s.settings, record_key, s.moves, layout.slot(name, s.page))
    if not move then return end
    local direction = move[3]
    if direction == "forward" then direction = fighter.facing == 0 and "r" or "l" end
    -- Feed the ordinary LF2 recognizer and the ordinary recorded/networked input stream.
    -- The fighter's frame selects the target and control.enter_frame enforces its cost.
    if move.variant then
        -- Arm only from a frame whose ordinary animation leads to the move.
        local frame, frames, seen = fighter.frame, fighter.record.frames, {}
        while frames[frame] and not seen[frame] do
            if frames[frame].hits.Uj == move.variant.target then
                s.follow_up = {record = fighter.record, frame = frame, path = seen}
                return
            end
            -- Do not wait through a return to neutral or an unrelated looping animation.
            seen[frame] = true
            frame = frames[frame].next
            if not frame or frame <= 0 or frame >= 999 then break end
        end
        return
    end
    s.follow_up = nil
    local base = held(s)
    enqueue(s, "")
    enqueue(s, "f")
    enqueue(s, "f" .. direction)
    enqueue(s, "f" .. direction .. move[4])
    enqueue(s, base)
    s.guard = nil
end

local function button_down(s, name, now)
    local before = held(s)
    local previous_direction = before:match("[udlr]+")
    s.counts[name] = (s.counts[name] or 0) + 1
    if s.counts[name] ~= 1 then return end
    if not s.guard then
        if name == "attack" then s.attack_at = now end
        if name == "jump" then
            s.jump_at = now
            if s.attack_at and now - s.attack_at <= 35 and contains(before, "c") and s.queue[#s.queue] == before then
                table.remove(s.queue)
                enqueue(s, (held(s):gsub("c", "")))
            end
        end
    end
    if name == "defend" then
        s.jump_at, s.attack_at = nil, nil
        s.guard = {start = now, direction = previous_direction, initial = previous_direction}
    elseif (name == "attack" or name == "jump") and s.guard then
        local guard = s.guard
        if now - guard.start <= s.settings.buffer_ms then
            -- A direction already held when defense began needs a fresh edge for LF2.
            if guard.direction and guard.initial == guard.direction then
                enqueue(s, (before:gsub("[udlr]", "")))
                enqueue(s, before:gsub("[udlr]", "") .. guard.direction)
                enqueue(s, before:gsub("[udlr]", "") .. guard.direction .. letters[name])
            end
            if name == "attack" or guard.direction then s.guard = nil end
        else
            -- Release LF2’s unfinished sequence on the same simulation tick as the late action.
            enqueue(s, held(s) .. "q")
            s.guard = nil
        end
    elseif layout.arrows[name] and s.guard and now - s.guard.start <= s.settings.buffer_ms then
        s.guard.direction = held(s):match("[udlr]+")
    end
    enqueue(s, held(s))
end

local function event(s, e, paused, fighter, key)
    local now = e.ms or s.clock
    if e.phase == "x" then
        local guard = s.guard or contains(s.output, "f")
        hybrid.reset(s)
        if guard then enqueue(s, "q") end
        return
    end
    local name = s.fingers[e.id]
    if e.phase == "d" then
        if name then return end
        name = layout.hit(s.geometry, e.x, e.y, false, paused, s.pages > 1)
        if not name or (name == "stick" and s.stick) or
            (s.mode == "selection" and (name == "pause" or name == "skills" or name:match("^s%d$"))) then return end
        s.fingers[e.id] = name
        if name == "stick" then s.stick = e.id; move_stick(s, e, now)
        elseif name == "pause" then s.pause = true
        elseif name == "skills" then s.page = s.page % s.pages + 1
        elseif name:match("^s%d$") then shortcut(s, name, fighter, key)
        else button_down(s, name, now) end
    elseif name and e.phase == "m" and name == "stick" then
        move_stick(s, e, now)
    elseif name and e.phase == "u" then
        s.fingers[e.id] = nil
        if name == "stick" then
            s.stick, s.strong, s.knob_x, s.knob_y = nil, nil, 0, 0
            enter_direction(s, "", now)
        elseif letters[name] then
            if name == "attack" and s.counts.attack == 1 and s.jump_at and s.attack_at
                and s.attack_at >= s.jump_at - 35 and now - s.jump_at <= 175 then
                -- Keep a quick jump-attack tap through the jump's takeoff frames.
                local pressed = held(s)
                enqueue(s, pressed)
                for _ = 1, 2 do
                    if #s.queue < 96 then s.queue[#s.queue + 1] = pressed end
                end
                s.jump_at = nil
            end
            s.counts[name] = s.counts[name] - 1
            enqueue(s, held(s))
        end
    end
end

function hybrid.update(s, input, mode, fighter, key, consume)
    local screen = input.screen or layout.screen
    local old = s.screen
    if not old or old.left ~= screen.left or old.top ~= screen.top or old.right ~= screen.right or old.bottom ~= screen.bottom then
        hybrid.reset(s)
        s.screen, s.geometry = screen, layout.geometry(s.settings, screen)
        if old then return "", false end
    end
    if not mode then
        hybrid.reset(s)
        s.visible, s.trace = false, {}
        return "", false
    end
    if mode ~= s.mode then hybrid.reset(s); s.mode = mode end
    local record = fighter and fighter.record
    if s.record ~= record or not s.moves then
        s.record, s.moves = record, hybrid.shortcuts(record)
        s.pages = hybrid.pages(s.moves)
        s.page = math.min(s.page, s.pages)
    end
    s.clock = s.clock + 33
    s.visible = input.touch_active == true or next(s.fingers) ~= nil
    local events = input.contacts
    if not events then
        -- Headless input traces express contact snapshots. Live SDL always sends events.
        events = {}
        local current = {}
        for _, point in ipairs(input.touches or {}) do
            local id = point.id
            current[id] = true
            events[#events + 1] = {phase = (s.trace or {})[id] and "m" or "d", id = id, x = point.x, y = point.y}
        end
        for id in pairs(s.trace or {}) do
            if not current[id] then events[#events + 1] = {phase = "u", id = id} end
        end
        s.trace = current
    end
    for _, contact in ipairs(events) do event(s, contact, mode == "pause", fighter, key) end
    if not consume then return s.output, false end
    local follow = s.follow_up
    if follow then
        local frame = record == follow.record and record.frames[fighter.frame]
        if not frame or (fighter.frame ~= follow.frame and not follow.path[fighter.frame]) then
            s.follow_up = nil
        elseif fighter.frame == follow.frame then
            s.follow_up = nil
            if not contains(s.output, "f") then
                s.output = "fub"
                s.guard = nil
                return s.output, false
            end
        end
    end
    s.output = table.remove(s.queue, 1) or held(s)
    local pause = s.pause
    s.pause = false
    return s.output, pause
end

return hybrid
