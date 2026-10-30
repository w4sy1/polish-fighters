local root = arg[1] or "."
local path = root .. "/engine/scripts/polish-fighters/"
local roster = dofile(path .. "roster.lua")
local function normal(f) return not f.hidden end
local settings = {allowed_ids = {1, 2}, allow_hidden = false}
assert(roster.permits(settings, {id=1}, normal))
assert(not roster.permits(settings, {id=3}, normal))
assert(not roster.permits(settings, {id=2, hidden=true}, normal))
settings.allow_hidden = true
assert(roster.permits(settings, {id=2, hidden=true}, normal))
assert(not pcall(roster.validate, {allowed_ids={1,1},allow_hidden=false}))
assert(not pcall(roster.validate, {allowed_ids={-1},allow_hidden=false}))
assert(roster.permits({allowed_ids={},allow_hidden=false}, {id=9}, normal))
local list = {{id=1},{id=2,hidden=true},{id=3}}
local stub = {load=function() return list end, selectable=normal}
package.preload["polish-fighters/settings"] = function() return settings end
package.preload["polish-fighters/roster"] = function() return roster end
local catalog = dofile(path .. "catalog.lua")(stub)
assert(catalog.load() == list and #list == 3)
assert(catalog.selectable(list[2]) and not catalog.selectable(list[3]))
settings.allowed_ids = {99}
assert(not pcall(catalog.load))
local locale = dofile(root .. "/engine/scripts/base/i18n/polish.lua")
assert(locale.Options == "Opcje")
print("PASS: roster restrictions, hidden fighters, empty selection guard, stable records, Polish locale")
