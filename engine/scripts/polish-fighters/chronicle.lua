-- Local history; contains no account credentials and never changes simulation state.
local chronicle={}
local function read()
    local document,problem=engine.read_settings()
    if problem then return nil,problem end
    if type(document)~="table" then document={} end
    local saved=document.polish_fighters_chronicle
    if type(saved)~="table" then saved={} end
    local entries={}
    if type(saved.entries)=="table" then
        for _,entry in ipairs(saved.entries) do
            if type(entry)=="table" and type(entry.id)=="number" and type(entry.profile)=="string"
                and type(entry.players)=="table" and type(entry.mode)=="number" then
                entries[#entries+1]=entry
            end
        end
    end
    while #entries>50 do table.remove(entries,1) end
    local serial=tonumber(saved.serial) or 0
    if serial~=serial or serial<0 or serial>2000000000 then serial=0 end
    return document,{entries=entries,serial=math.floor(serial)}
end
function chronicle.entries()
    local document,value=read()
    if not document then return {},value end
    return value.entries
end
function chronicle.append(entry)
    local document,value=read()
    if not document then return nil,value end
    value.serial=value.serial+1
    entry.id=value.serial
    value.entries[#value.entries+1]=entry
    if #value.entries>50 then table.remove(value.entries,1) end
    document.polish_fighters_chronicle=value
    if entry.campaign_clear then
        require("polish-fighters/progression").award(document,entry,require("base/game/catalog").load())
    end
    local ok,problem=engine.write_settings(document)
    if ok and entry.campaign_clear then require("polish-fighters/progression").invalidate() end
    return ok,problem
end
return chronicle
