local layout = require("base/ui/hybrid_layout")
local document = {unrelated = 7}
engine = {read_settings = function() return document end, write_settings = function(value) document = value; return true end}
package.loaded["base/game/catalog"] = {
    profile_id = "test",
    load = function() return {{name = "Davis", path = "davis.dat"}, {name = "Dennis", path = "dennis.dat"}} end,
    backgrounds = function() return {{path = "arena"}} end,
    selectable = function() return true end,
}
package.loaded["base/game/background"] = {load = function() return {} end, create_state = function() return {} end}
package.loaded["base/game/object_data"] = {load = function(path)
    return {frames = {[0] = {hits = path == "davis.dat" and {Fa = 300, Ua = 300} or {Da = 300}}, [300] = {hits = {}}}}
end}
local settings = require("base/game/options")
local editor = require("base/ui/hybrid_editor")
local s = editor.create(settings.current())
local function tap(x, y)
    return editor.update(s, {pointer_x = x, pointer_y = y, click = true, button = true})
end
local function move(x, y)
    editor.update(s, {pointer_x = x, pointer_y = y, button = true})
end
local function release()
    editor.update(s, {pointer_x = 0, pointer_y = 0, button = false})
end
tap(540, 420)
local c = s.values.hybrid.controls
assert(not c.stick.enabled and c.up.enabled and c.attack.shape == "rect")
s.selected = "stick"
tap(450, 343)
tap(450, 305)
assert(c.stick.enabled and c.stick.shape == "round" and c.attack.shape == "rect")
local bounds = {left = 13, top = 87, right = 377, bottom = 435}
local stick = layout.geometry(s.values.hybrid, bounds).stick
tap(stick.x, stick.y)
move(stick.x + 29, stick.y - 26)
release()
assert(c.stick.x > 0.20 and c.stick.y < 0.75)
tap(575, 136)
tap(575, 177)
tap(575, 218)
tap(575, 258)
tap(430, 385)
assert(c.stick.size == 1.05 and c.stick.opacity > 0.69)
assert(s.values.hybrid.deadzone == 0.2 and s.values.hybrid.buffer_ms == 325 and s.values.hybrid.run == "strong")
tap(700, 182)
tap(700, 230)
assert(tap(700, 491) == "apply")
assert(document.unrelated == 7 and document.options.hybrid.bindings["test:davis.dat"].s1 == "Ua")
assert(not document.options.hybrid.controls.s2.enabled)
s = editor.create(settings.current())
tap(100, 491)
assert(s.values.hybrid.buffer_ms == 300 and s.values.hybrid.controls.s2.enabled)
assert(tap(300, 491) == "cancel" and document.options.hybrid.buffer_ms == 325)
engine.write_settings = function() return nil, "read-only" end
s = editor.create(settings.current())
tap(575, 258)
assert(not tap(700, 491) and s.error:find("read-only", 1, true))
assert(settings.current().hybrid.buffer_ms == 325 and document.options.hybrid.buffer_ms == 325)
print("PASS Hybrid Control editor: drag, mixed shapes, sizes, transparency, binding, save, cancel and reset")
