-- Ordered contacts are delivered independently of LF2's slower input sampling.
local layout = require("base/ui/hybrid_layout")
local hybrid = require("base/ui/hybrid_input")
local controls = require("base/ui/controls")
local bounds = {left = 0, top = 0, right = 1280, bottom = 720}
local config = layout.copy()
local geometry = layout.geometry(config, bounds)

local function contact(phase, id, name, dx, dy, ms)
    local target = geometry[name or "stick"]
    return {phase = phase, id = id, x = target.x + (dx or 0), y = target.y + (dy or 0), ms = ms or 1}
end
local function update(state, events, consume, screen, fighter, key)
    return hybrid.update(state, {contacts = events or {}, screen = screen or bounds, touch_active = true},
        "match", fighter, key, consume ~= false)
end

local paused = hybrid.create(config)
local _, pause = update(paused, {contact("d", 1, "pause")}, false)
assert(not pause, "pause waits for a simulation sample")
_, pause = update(paused)
assert(pause, "tap between frames must still pause")
_, pause = update(paused)
assert(not pause, "one tap must toggle only once")

local directions = {{70, 0, "r"}, {70, 70, "rd"}, {0, 70, "d"}, {-70, 70, "ld"}, {-70, 0, "l"},
    {-70, -70, "lu"}, {0, -70, "u"}, {70, -70, "ru"}}
for _, direction in ipairs(directions) do
    local s = hybrid.create(config)
    assert(update(s, {contact("d", 3), contact("m", 3, "stick", direction[1], direction[2])}) == direction[3])
    assert(update(s, {contact("u", 3)}) == "")
    assert(s.knob_x == 0 and s.knob_y == 0)
end

local s = hybrid.create(config)
assert(update(s, {contact("d", 1), contact("m", 1, "stick", 10, 0)}) == "", "deadzone")
assert(update(s, {contact("d", 2, "attack"), contact("m", 2, "stick", 80, 0)}, false) == "")
assert(update(s, {contact("u", 2, "attack"), contact("m", 1, "stick", -75, 0)}, false) == "")
assert(update(s) == "c", "brief attack disappeared")
assert(update(s) == "")
assert(update(s) == "l")
assert(update(s, {contact("d", 3, "jump"), contact("d", 4, "attack")}) == "lb")
assert(update(s) == "lbc")
assert(update(s, {{phase = "x"}}) == "")
assert(update(s, {contact("m", 1, "stick", 75, 0)}) == "", "cancelled contact was revived")
assert(update(s, {contact("d", 7, "defend")}) == "f")
assert(update(s, {contact("d", 8), contact("m", 8, "stick", 0, -80)}) == "uf")
assert(update(s, {contact("d", 9, "attack")}) == "ufc")

s = hybrid.create(config)
assert(update(s, {contact("d", 1, "stick", 70, 0)}) == "r")
assert(update(s, {contact("u", 1), contact("d", 2, "stick", 70, 0)}) == "")
assert(update(s) == "r", "double tilt")
s = hybrid.create(layout.copy({run = "strong"}))
assert(update(s, {contact("d", 1), contact("m", 1, "stick", 120, 0)}) == "r")
assert(update(s) == "" and update(s) == "r", "strong tilt")
assert(update(s, {contact("d", 7, "attack")}, true, {left = 0, top = 0, right = 720, bottom = 1280}) == "")
assert(update(s, {contact("m", 1, "stick", 80, 0)}, true, {left = 0, top = 0, right = 720, bottom = 1280}) == "")

s = hybrid.create(config)
assert(update(s, {contact("d", 1, "defend", 0, 0, 1)}) == "f")
assert(update(s, {contact("d", 2, "stick", 80, 0, 100)}) == "rf")
assert(update(s, {contact("d", 3, "attack", 0, 0, 302)}) == "rfcq", "expired combo must reset on its attack tick")
local recording = require("base/game/recording")
assert(recording.unpack_keys(recording.pack_keys("rfcq")) == "rcfq")
assert(recording.pack_keys("udlrcbfq") == 254)
assert(recording.unpack_keys(recording.pack_keys("rfc")) == "rcf")

local function hits(values) return {hits = values or {}} end
local fighter = {facing = 0, record = {frames = {[0] = hits({Fa = 40, Ua = 41, Da = 42}), [40] = hits(),
    [41] = hits(), [42] = hits()}}}
for index, letter in ipairs({"r", "u", "d"}) do
    s = hybrid.create(config)
    assert(update(s, {contact("d", 1, "s" .. index)}, true, nil, fighter, "pack:fighter") == "f")
    assert(update(s) == "f" .. letter)
    assert(update(s) == "f" .. letter .. "c")
    assert(update(s) == "")
end
fighter.facing = 1
s = hybrid.create(config)
assert(update(s, {contact("d", 1, "s1")}, true, nil, fighter, "pack:fighter") == "f")
assert(update(s) == "fl")
assert(update(s) == "flc")

for _, size in ipairs({{1600, 900}, {2400, 1080}, {720, 1280}}) do
    local screen = {left = -20, right = size[1] - 20, top = -10, bottom = size[2] - 10}
    local g = layout.geometry(config, screen)
    for _, name in ipairs(layout.order) do
        local o = g[name]
        assert(o.x - o.rx >= screen.left - 0.001 and o.x + o.rx <= screen.right + 0.001)
        assert(o.y - o.ry >= screen.top - 0.001 and o.y + o.ry <= screen.bottom + 0.001)
    end
end
local doc = {other = true, options = {show_fps = true}}
engine = {read_settings = function() return doc end, write_settings = function(v) doc = v; return true end}
local options = require("base/game/options")
local values = options.load()
values.hybrid.controls.attack.shape = "rect"
values.hybrid.controls.attack.opacity = 0.3
values.hybrid.controls.up.enabled = true
values.hybrid.controls.s2.enabled = false
values.hybrid.bindings["pack:fighter"] = {s2 = "Da"}
assert(options.save(values))
local saved = options.load()
assert(doc.other and saved.show_fps and saved.hybrid.controls.attack.shape == "rect")
assert(saved.hybrid.controls.attack.opacity == 0.3 and saved.hybrid.controls.up.enabled)
assert(not saved.hybrid.controls.s2.enabled and saved.hybrid.bindings["pack:fighter"].s2 == "Da")
local parsed = controls.read({sets = {{device = 1}, {device = 1}, {device = 1}, {device = 1}}}, "k m0,0,0 h1 vd1:5:30:50,m1:-2:20:51,u1:-2:20:53,")
assert(#parsed.contacts == 3 and parsed.contacts[2].x == -2 and parsed.contacts[3].phase == "u")
print("PASS Hybrid Control: eight directions, holds, fast taps, multitouch, cancel, resize, run, shortcuts, settings and transport")

-- Seven command families share three controls over three pages. Touch shortcuts
-- still emit ordinary LF2 inputs, including the final-page transform command.
local seven = {facing = 0, record = {frames = {
    [0] = hits({Fa = 40, Ua = 40, Da = 40, Fj = 40, Uj = 40, Dj = 40, ja = 40}),
    [5] = hits({ja = -41}), [40] = hits(), [41] = hits(),
}}}
local moves = hybrid.moves(seven.record)
assert(#moves == 7 and hybrid.pages(moves) == 3)
assert(#moves[7].variants == 2 and moves[7].variants[1].target == -41)
assert(moves[7].variants[1].sources[1] == 5)
local extended = layout.copy({bindings = {["pack:fighter"] = {s1 = "Ua", s4 = "Dj", s7 = "ja"}}})
assert(extended.bindings["pack:fighter"].s4 == "Dj" and extended.bindings["pack:fighter"].s7 == "ja")
s = hybrid.create(extended)
assert(update(s, {contact("d", 20, "skills")}, true, nil, seven, "pack:fighter") == "")
assert(s.page == 2)
assert(update(s, {contact("d", 21, "s1")}, true, nil, seven, "pack:fighter") == "f")
assert(update(s, nil, true, nil, seven) == "fd")
assert(update(s, nil, true, nil, seven) == "fdb")
assert(update(s, {contact("u", 20, "skills"), contact("u", 21, "s1")}, true, nil, seven) == "")
assert(update(s, {contact("d", 22, "skills")}, true, nil, seven, "pack:fighter") == "")
assert(s.page == 3)
assert(update(s, {contact("d", 23, "s1")}, true, nil, seven, "pack:fighter") == "f")
assert(update(s, nil, true, nil, seven) == "fb")
assert(update(s, nil, true, nil, seven) == "fbc")
assert(update(s, nil, true, nil, fighter) == "" and s.page == 1)
print("PASS: seven move families, conditional targets, extended bindings, transport and fighter page change")

-- The classic TCP offset is unrelated to the replay/room combo reset bit.
local network = require("base/game/network")
local local_peer = {host = true, phase = "ready", version = 1, sequence = 0, checksum = 42, frames = 0, received = ""}
local remote_peer = {host = false, version = 1, sequence = 1, checksum = 42}
local packets = {network.packet(remote_peer, {[0] = "bq", functions = ""}, 0)}
engine.network_time = function() return 0 end
engine.network = function(action, sent)
    if action == "poll" then return table.remove(packets, 1) or "" end
    assert(action == "send" and sent:byte(1) % 2 == 1)
    return true
end
local merged = assert(network.exchange(local_peer, {[0] = "fbcq", functions = ""}, 0))
assert(merged[0] == "cbf" and merged[4] == "b" and merged[1] == "")
print("PASS: legacy TCP preserves shortcut input without injecting combo resets")
