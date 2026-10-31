-- Generated PNGs stay byte-for-byte intact. The renderer scales source rectangles.
local layout = require("polish-originals/layout")
local render = {}
local function key_for(resource)
    return resource:match("^mods/polish%-originals/([wsjb])%.png$")
end
function render.wrap(context)
    local wrapped = {}
    for name,method in pairs(context) do wrapped[name]=method end
    local function portrait(resource,x,y,mirrored,tint)
        local key,kind=resource:match("^mods/polish%-originals/([wsjb])_([hs])%.png$")
        if not key then return false end
        local width,height=120,120
        if kind=="s" then width,height=40,45 end
        context.scaled_sprite("mods/polish-originals/"..key..".png",layout[key].portrait,x,y,width,height,mirrored,tint or 0xffffff)
        return true
    end
    local function scaled(resource, source, x, y, mirrored, tint)
        local info = layout[key_for(resource)]
        if not info then return false end
        local picture = math.floor(source[1]/80) + math.floor(source[2]/80)*8
        local rect = assert(info.rectangles[picture+1], "invalid original character picture")
        local width, height = math.max(1,math.floor(rect[3]*info.scale)), math.max(1,math.floor(rect[4]*info.scale))
        local destination_y=picture>=61 and (y+40-height/2) or (y+79-height)
        if picture<61 then destination_y=destination_y+(info.bottom_padding[picture+1] or 0)*info.scale end
        context.scaled_sprite(resource,rect,math.floor(x+40-width/2),math.floor(destination_y),width,height,mirrored,tint)
        return true
    end
    function wrapped.sprite(resource,source,x,y,color_key,mirrored,flipped,tint)
        if not portrait(resource,x,y,mirrored,tint) and not scaled(resource,source,x,y,mirrored,tint) then
            return context.sprite(resource,source,x,y,color_key,mirrored,flipped,tint)
        end
    end
    function wrapped.world_sprite(resource,source,x,y,mirrored,...)
        if not scaled(resource,source,x,y,mirrored) then
            return context.world_sprite(resource,source,x,y,mirrored,...)
        end
    end
    function wrapped.image(resource,x,y,...)
        if portrait(resource,x,y,false,0xffffff) then return end
        return context.image(resource,x,y,...)
    end
    return wrapped
end
return render
