-- Drives base/game/control.lua's defend-combo recognizer directly, with a synthetic
-- character record, to check both input styles a real player can produce:
--  * the classic keyboard timing (tap Defend, tap a direction, tap Attack/Jump as three
--    separate presses) -- this must keep working exactly as before;
--  * a single-tick chord where Defend and Attack (or Jump) land together while a direction
--    is already held, as a fast keyboard or controller press can produce.
-- There was no existing test exercising control.lua's combo state machine at all.
engine = {new_array = function() return {} end, random = function() return 0 end}
local root = arg[1]
package.path = root .. "/engine/scripts/?.lua;" .. package.path

local constants = require("base/game/constants")
local item = require("base/game/item")
local control = require("base/game/control")
local character_frames = constants.character_frames
local frame_states = constants.frame_states

-- Minimal frame: defend (hit_d) works from any frame so holding a direction while walking
-- still reaches the defend stance; the defend stance (110) itself carries the actual combos.
local function make_frame(state, hits)
    local base = {name = "", picture = 0, state = state, wait = 1, next = 0, dvx = 0, dvy = 0, dvz = 0,
        center_x = 0, center_y = 0, mp = 0,
        hits = {a = 0, d = character_frames.defend, j = 0, Fa = 0, Ua = 0, Da = 0, Fj = 0, Uj = 0, Dj = 0, ja = 0},
        opoint = {kind = 0, x = 0, y = 0, action = 0, dvx = 0, dvy = 0, oid = 0, facing = 0},
        bpoint = {x = 0, y = 0},
        cpoint = {kind = 0, x = 0, y = 0, injury = 0, cover = 0, vaction = 0, aaction = 0, jaction = 0,
            daction = 0, taction = 0, throwvx = 0, throwvy = 0, hurtable = 0, decrease = 0, dircontrol = 0},
        wpoint = {kind = 0, x = 0, y = 0, weaponact = 0, attacking = 0, cover = 0, dvx = 0, dvy = 0, dvz = 0},
        interactions = {}, bodies = {}}
    for k, v in pairs(hits or {}) do base.hits[k] = v end
    return base
end

local frames = {}
-- Standing and the whole walking cycle (5..11, covering walking+running bases used by
-- control.lua's walk_cycle/run frame math) all hand off to the defend stance on hit_d.
for _, id in ipairs({0, 5, 6, 7, 8, 9, 10, 11}) do frames[id] = make_frame(frame_states.walking, {}) end
frames[0].state = frame_states.standing
-- The defend stance: hit_d cleared (no self-loop), the six direction combos plus jump-attack.
frames[character_frames.defend] = make_frame(frame_states.defending,
    {d = 0, Fa = 300, Ua = 301, Da = 302, Fj = 310, Uj = 311, Dj = 312, ja = 320})
for _, id in ipairs({300, 301, 302, 310, 311, 312, 320}) do frames[id] = make_frame(frame_states.attacking, {}) end

local movement = {walking_speed = 0, walking_speedz = 0, heavy_walking_speed = 0, heavy_walking_speedz = 0,
    running_speed = 0, running_speedz = 0, heavy_running_speed = 0, heavy_running_speedz = 0,
    walking_frame_rate = 1, running_frame_rate = 1, dash_distance = 0, dash_height = 0, dash_distancez = 0,
    rowing_height = 0, rowing_distance = 0}
local record = item.record({id = 1, kind = 0}, {movement = movement, frames = frames})
local match = {running = true}

-- Applies one tick of held keys (a subset of up/down/left/right/attack/jump/defend) the way
-- base/game/match.lua's read_input feeds control.step: age the previous frame's keys out,
-- latch the new ones, then step.
local function press(value, held)
    for _, key in ipairs(item.keys) do value.previous_keys[key] = value.keys[key] end
    for _, key in ipairs(item.keys) do value.keys[key] = held[key] == true end
    control.step(match, value)
end

local combo_right_attack = constants.combo_indices.right_attack
local combo_idle = constants.combo_states.idle

-- A: classic three-tap timing (D, then F, then a -- each its own tick) must still work.
local a = item.create(record)
press(a, {defend = true})
assert(a.frame == character_frames.defend, "defend tap did not reach the defend stance")
press(a, {right = true})
press(a, {attack = true})
assert(a.frame == 300, "classic tap D,F,a sequence no longer executes the forward attack")

-- B: the touch "D+A" chord -- Defend and Attack pressed in the very same tick while the
-- direction is already held from the joystick, never freshly re-tapped.
local b = item.create(record)
press(b, {right = true})
press(b, {right = true, defend = true, attack = true})
assert(b.frame == 300, "D+A chord (touch button) did not execute the forward attack; sequence state = "
    .. tostring(b.sequences[combo_right_attack]))

-- C: the touch "D+J" chord, same shape, for the forward jump-special.
local c = item.create(record)
press(c, {right = true})
press(c, {right = true, defend = true, jump = true})
assert(c.frame == 310, "D+J chord (touch button) did not execute the forward jump special")

-- D: the touch "D+J+A" chord (fusion/jump-attack) already relied on all three of its own
-- expected keys landing together; confirm the fix left that path working.
local d = item.create(record)
press(d, {defend = true, jump = true, attack = true})
assert(d.frame == 320, "D+J+A chord regressed")

-- E: the chord must still require an actual direction -- Defend+Attack with no direction
-- held must not fire a move picked arbitrarily.
local e = item.create(record)
press(e, {defend = true, attack = true})
assert(e.frame ~= 300 and e.frame ~= 301 and e.frame ~= 302,
    "D+A with no direction held must not execute any attack")
assert(e.sequences[combo_right_attack] == combo_idle, "directionless D+A left a combo armed instead of idle")

print("PASS: classic D,F,a timing unaffected; touch D+A/D+J chords execute; D+J+A unaffected; directionless D+A still inert")

-- An attack frame that can be cancelled into defense. Jump is available from
-- that stance via hit_j, as defined by the fighter record.
frames[character_frames.punch] = make_frame(frame_states.attacking)
frames[character_frames.defend].hits.j = character_frames.jump
frames[character_frames.jump] = make_frame(frame_states.jumping, {d = 0})

for _, direction in ipairs({"left", "right"}) do
    local function attacking()
        local fighter = item.create(record)
        press(fighter, {attack = true})
        assert(fighter.frame == character_frames.punch)
        return fighter
    end

    local released = attacking()
    press(released, {defend = true})
    assert(released.frame == character_frames.defend)
    press(released, {[direction] = true, jump = true})
    assert(released.frame == character_frames.jump, "released attack-cancel BLOCK started a special: " .. direction)

    local staggered = attacking()
    press(staggered, {defend = true})
    press(staggered, {[direction] = true})
    press(staggered, {[direction] = true, jump = true})
    assert(staggered.frame == character_frames.jump, "released BLOCK survived a direction edge: " .. direction)

    local held = attacking()
    press(held, {defend = true})
    press(held, {defend = true, [direction] = true})
    press(held, {defend = true, [direction] = true, jump = true})
    assert(held.frame == 310, "held BLOCK did not start its special: " .. direction)

    local chord = attacking()
    press(chord, {defend = true, [direction] = true, jump = true})
    assert(chord.frame == 310, "same-tick attack-cancel chord failed: " .. direction)

    local late_chord = item.create(record)
    press(late_chord, {defend = true})
    press(late_chord, {[direction] = true, jump = true})
    assert(late_chord.frame == character_frames.jump, "released neutral BLOCK armed a later chord: " .. direction)

    local classic = item.create(record)
    press(classic, {defend = true})
    press(classic, {[direction] = true})
    press(classic, {jump = true})
    assert(classic.frame == 310, "classic three-tap jump special failed: " .. direction)
end

print("PASS: attack-cancel release, held and simultaneous specials, and classic jump specials on both sides")

-- Defend cancels drinking before the same input can arm a special.
frames[character_frames.drinking] = make_frame(frame_states.drinking)
for _, direction in ipairs({"left", "right"}) do
    for _, hold_block in ipairs({false, true}) do
        local fighter = item.create(record)
        fighter.frame = character_frames.drinking
        press(fighter, {defend = true})
        assert(fighter.frame == character_frames.defend, "block did not cancel drinking")
        press(fighter, {[direction] = true, defend = hold_block})
        press(fighter, {[direction] = true, defend = hold_block, jump = true})
        assert(fighter.frame == character_frames.jump, "drinking cancel armed a sideways special: " .. direction)
    end
    local fighter = item.create(record)
    fighter.frame = character_frames.drinking
    press(fighter, {defend = true, [direction] = true, jump = true})
    assert(fighter.frame == character_frames.defend, "same-tick jump special overrode drinking cancel")
end

local function press_letters(fighter, keys)
    local held = {}
    for key, symbol in pairs({attack = "c", defend = "f", jump = "b", left = "l", right = "r"}) do
        held[key] = keys:find(symbol, 1, true) ~= nil
    end
    press(fighter, held)
end

local controls = require("base/ui/controls")
local keyboard = {device = constants.input_devices.keyboard, keys = {87, 83, 65, 68, 103, 105, 104}}
local pad = {device = constants.input_devices.controller_one, buttons = {0, 1, 2}}
local mapping = {sets = {keyboard, pad, keyboard, keyboard}}
for _, input in ipairs({
    {slot = 0, attack = "k103", block = "k104", left = "k65,105", right = "k68,105",
        chord_left = "k65,104,105", chord_right = "k68,104,105"},
    {slot = 1, attack = "k m0,0,0 j:1", block = "k m0,0,0 j:4",
        left = "k m0,0,0 jl:2", right = "k m0,0,0 jr:2",
        chord_left = "k m0,0,0 jl:6", chord_right = "k m0,0,0 jr:6"},
}) do
    local function tick(fighter, raw)
        press_letters(fighter, controls.read(mapping, raw)[input.slot])
    end
    for _, direction in ipairs({"left", "right"}) do
        local released = item.create(record)
        tick(released, input.attack)
        tick(released, input.block)
        assert(released.frame == character_frames.defend)
        tick(released, input[direction])
        assert(released.frame == character_frames.jump, "released BLOCK through host input parser")

        local chord = item.create(record)
        tick(chord, input.attack)
        assert(chord.frame == character_frames.punch)
        tick(chord, input["chord_" .. direction])
        assert(chord.frame == 310, "intentional chord through host input parser")
    end
end

local hybrid = require("base/ui/hybrid_input")
local layout = require("base/ui/hybrid_layout")
local bounds = {left = 0, top = 0, right = 1280, bottom = 720}
local settings = layout.copy()
local geometry = layout.geometry(settings, bounds)
local function contact(phase, id, name, dx)
    local target = geometry[name]
    return {phase = phase, id = id, x = target.x + (dx or 0), y = target.y, ms = 1}
end

for _, side in ipairs({-1, 1}) do
    for _, release in ipairs({true, false}) do
        local touch = hybrid.create(settings)
        local fighter = item.create(record)
        local function tick(...)
            local keys = hybrid.update(touch, {contacts = {...}, screen = bounds, touch_active = true},
                "match", fighter, "test:fighter", true)
            press_letters(fighter, keys)
        end
        tick(contact("d", 1, "attack"))
        tick(contact("u", 1, "attack"))
        tick(contact("d", 2, "defend"))
        if release then tick(contact("u", 2, "defend")) end
        tick(contact("d", 3, "stick", side * 80))
        tick(contact("d", 4, "jump"))
        assert(fighter.frame == (release and character_frames.jump or 310), "touch BLOCK release/hold regression")
    end
end

local rapid = item.create(record)
frames[character_frames.defend].hits.a = character_frames.punch
for _ = 1, 6 do
    press(rapid, {attack = true})
    assert(rapid.frame == character_frames.punch, "rapid ATTACK failed")
    press(rapid, {attack = true, left = true})
    press(rapid, {attack = true, right = true})
    assert(rapid.frame == character_frames.punch, "quick reversal during attack triggered a special")
    press(rapid, {defend = true})
    assert(rapid.frame == character_frames.defend, "rapid BLOCK failed to enter defense")
end
press(rapid, {jump = true, right = true})
assert(rapid.frame == character_frames.jump, "rapid attack/block sequence left a special armed")
rapid.y_int = -1
press(rapid, {jump = true, attack = true})
assert(rapid.frame == character_frames.jump_attack, "ordinary airborne JUMP+ATTACK regressed")

-- The AI completes sideways jump specials directly (ai.lua) without holding Defend.
-- A block it started earlier during an attack must not cancel that decision.
local combo_right_jump = constants.combo_indices.right_jump
local combo_complete = constants.combo_states.complete
local function ai_sideways_jump(block_in_attack)
    local value = item.create(record)
    if block_in_attack then
        value.frame = 300
        press(value, {defend = true})
        assert(value.attack_block, "attack-cancel block was not recorded")
        for _ = 1, 8 do press(value, {}) end
    end
    value.frame = character_frames.defend
    value.sequences[combo_right_jump] = combo_complete
    press(value, {})
    return value.frame
end
assert(ai_sideways_jump(false) == 310, "AI sideways jump special did not execute")
assert(ai_sideways_jump(true) == 310, "an earlier attack-cancel block suppressed the AI sideways jump special")

print("PASS: host keyboard/gamepad frames, touch contact streams, rapid attack/block and reversal, ordinary jump attack and AI sideways jump")
