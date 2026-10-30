-- UI state is local/offline. It never represents an authenticated account.
local model = {}
model.tabs = {{"home", "Pulpit"}, {"play", "Graj"}, {"maps", "Mapy"},
    {"packs", "Pakiety"}, {"connect", "Połączenia"}, {"settings", "Ustawienia"}, {"account", "Profil"}}
local profile=require("base/game/catalog").profile_id
model.packs = {{"LF2 Classic", profile=="lf2-classic", "lf2-classic"}, {"LF4 Turbo", profile=="lf4-turbo", "lf4-turbo"},
    {"Reinforced LF2", profile=="reinforced", "reinforced"}, {"LF2 Kate", profile=="kate", "kate"},
    {"Naruto: The Setting Dawn", profile=="ntsd", "ntsd"}, {"Dragon Ball", profile=="dbz", "dbz"},
    {"One Piece", profile=="one-piece", "one-piece"}, {"Bleach", profile=="bleach", "bleach"},
    {"Polish Fighters", profile=="polish-originals", "polish-originals"}}

-- Load actual catalog contents; an active profile is not a compatibility claim.
function model.contents()
    local ok,value=pcall(function()
        local catalog=require("base/game/catalog")
        local fighters={}
        for _,fighter in ipairs(catalog.load()) do
            fighters[#fighters+1]={id=fighter.id,name=fighter.name,portrait=fighter.portrait,
                hidden=fighter.hidden,selectable=catalog.selectable(fighter)}
        end
        local campaigns={}
        if catalog.campaigns then
            for _,campaign in ipairs(catalog.campaigns) do campaigns[#campaigns+1]=campaign end
        else
            local stages=engine.read_stage_data(catalog.stage_path).stages
            for id,data in pairs(stages) do
                campaigns[#campaigns+1]={id=id,phases=data.phase_count}
            end
        end
        table.sort(campaigns,function(a,b) return a.id<b.id end)
        return {profile=profile,fighters=fighters,campaigns=campaigns}
    end)
    if not ok then return nil,tostring(value) end
    return value
end
local current
local function clean(values)
    values = type(values) == "table" and values or {}
    local map = values.map
    if type(map) ~= "number" or map % 1 ~= 0 or map < 0 or map > 99 then map = 0 end
    local name = type(values.nickname) == "string" and values.nickname or "Gracz"
    name = name:gsub("[%c]", ""):sub(1, 24)
    if name == "" then name = "Gracz" end
    local capacity=values.room_capacity
    if type(capacity)~="number" or capacity%1~=0 or capacity<2 or capacity>8 then capacity=8 end
    return {map = map, nickname = name, room_capacity=capacity}
end
function model.current()
    if not current then
        local doc = engine.read_settings()
        current = clean(type(doc) == "table" and doc.polish_fighters_dashboard)
    end
    return current
end
function model.save(changes)
    local value = model.current()
    local candidate = clean({map = changes.map ~= nil and changes.map or value.map,
        nickname = changes.nickname ~= nil and changes.nickname or value.nickname,
        room_capacity=changes.room_capacity~=nil and changes.room_capacity or value.room_capacity})
    local doc = engine.read_settings()
    if type(doc) ~= "table" then doc = {} end
    doc.polish_fighters_dashboard = candidate
    local ok, problem = engine.write_settings(doc)
    if ok then current = candidate end
    return ok, problem
end
local map_cache
function model.maps()
    if map_cache then return map_cache end
    local result = {}
    local catalog = require("base/game/catalog")
    local background = require("base/game/background")
    for index, entry in ipairs(catalog.backgrounds()) do
        local name=background.load(entry.path).name or ("Arena "..index)
        if not name:lower():match("^template") then
            result[#result + 1] = {row=index-1, path=entry.path, name=name}
        end
    end
    map_cache=result
    return result
end
function model.selected_map()
    local maps = model.maps()
    for _,map in ipairs(maps) do if map.row==model.current().map then return map end end
    return maps[1]
end
return model
