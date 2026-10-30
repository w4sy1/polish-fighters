-- Local rewards; network sessions retain shared roster rules.
local progress={suspended=false}
local cache={}
function progress.invalidate() cache={} end
function progress.profile(document,id)
    local root=type(document)=="table" and document.polish_fighters_progress
    local value=type(root)=="table" and root[id]
    return type(value)=="table" and value or {}
end
function progress.earned(profile,id)
    if progress.suspended or type(profile)~="string" then return false end
    if not cache[profile] then cache[profile]=progress.profile(engine.read_settings(),profile) end
    local value=cache[profile]
    return type(value.unlocked)=="table" and value.unlocked[tostring(id)]==true
end
function progress.summary(profile,fighters)
    local value=progress.profile(engine.read_settings(),profile)
    local count=0
    if type(value.completed)=="table" then for _,done in pairs(value.completed) do if done==true then count=count+1 end end end
    local next_fighter
    local settings=require("polish-fighters/settings")
    local permitted={};for _,id in ipairs(settings.allowed_ids) do permitted[id]=true end
    for _,fighter in ipairs(fighters) do
        if fighter.hidden and (#settings.allowed_ids==0 or permitted[fighter.id])
            and not (type(value.unlocked)=="table" and value.unlocked[tostring(fighter.id)]) then
            next_fighter=fighter.name;break
        end
    end
    return count,next_fighter
end
function progress.award(document,entry,fighters)
    if not entry.campaign_clear or entry.network or type(entry.chapter)~="number"
        or entry.chapter%1~=0 or entry.chapter<0 or entry.chapter>59 then return end
    local human=false
    for _,player in ipairs(entry.players or {}) do if player.kind=="human" then human=true;break end end
    if not human then return end
    if type(document.polish_fighters_progress)~="table" then document.polish_fighters_progress={} end
    local value=progress.profile(document,entry.profile)
    value.completed=type(value.completed)=="table" and value.completed or {}
    value.unlocked=type(value.unlocked)=="table" and value.unlocked or {}
    local chapter=(entry.campaign and entry.campaign..":" or "")..tostring(math.floor(entry.chapter/10))
    if value.completed[chapter] then return end
    value.completed[chapter]=true
    local settings=require("polish-fighters/settings")
    local permitted={}
    for _,id in ipairs(settings.allowed_ids) do permitted[id]=true end
    for _,fighter in ipairs(fighters) do
        local id=tostring(fighter.id)
        if fighter.hidden and not value.unlocked[id] and (#settings.allowed_ids==0 or permitted[fighter.id]) then
            value.unlocked[id]=true;entry.reward={id=fighter.id,name=fighter.name};break
        end
    end
    document.polish_fighters_progress[entry.profile]=value
end
return progress
