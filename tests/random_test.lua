local root = arg[1] or '.'
local base = dofile(root .. '/engine/scripts/base/game/catalog.lua')
local settings = {allowed_ids={1, 52}, allow_hidden=true}
package.preload['polish-fighters/settings'] = function() return settings end
package.preload['polish-fighters/roster'] = function()
    return dofile(root .. '/engine/scripts/polish-fighters/roster.lua')
end
local catalog = dofile(root .. '/engine/scripts/polish-fighters/catalog.lua')(base)
local fighters={{id=1,record=1},{id=2,record=2},{id=52,record=3,hidden=true}}
local list=catalog.random_candidates(fighters,{[1]=true})
assert(#list==1 and list[1]==3)
list=catalog.random_candidates(fighters,{[1]=true,[3]=true})
assert(#list==2 and list[1]==1 and list[2]==3)
for i=1,8 do
    local picks=catalog.random_candidates(fighters,{[1]=true,[3]=true})
    assert(#picks==2)
end
settings.allowed_ids={99}
assert(not pcall(catalog.random_candidates,fighters,{}))
settings.allowed_ids = {}
settings.allow_hidden = false
package.preload['base/game/unlock'] = function() return {flags={characters=0}} end
package.preload['polish-fighters/progression'] = function() return {earned=function() return false end} end
local dbz = dofile(root .. '/content-packs/dbz/catalog.lua')(catalog)
local dbz_fighters = {{id=91,record=1},{id=93,record=2},{id=36,record=3,hidden=true},{id=94,record=0}}
list = dbz.random_candidates(dbz_fighters,{[1]=true})
assert(#list==1 and list[1]==2)
list = dbz.random_candidates(dbz_fighters,{[1]=true,[2]=true})
assert(#list==2 and list[1]==1 and list[2]==2)
print('PASS: random picks obey roster, hidden boss, small roster fallback, empty guard')
