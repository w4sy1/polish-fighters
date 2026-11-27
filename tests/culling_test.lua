local c=require('base/ui/culling')
assert(c.visible(10,130,20,20,0,128,794,550))
assert(not c.visible(10,25394,20,20,0,128,794,550))
assert(not c.visible(800,130,20,20,0,128,794,550))
assert(c.visible(-10,130,20,20,0,128,794,550))
assert(not c.visible(-20,130,20,20,0,128,794,550))
assert(c.visible(-100,130,20,20,-200,128,1000,550))
assert(not c.visible(10,130,0,20,0,128,794,550))
print('PASS: effect culling, exact edges, partial visibility and wide windows')

local background = require("base/game/background")
local function paint_tiles(layer, camera, bounds, wide)
    engine = {
        read_resource = function()
            return "BM" .. string.rep("\0", 16) .. string.char(layer.bitmap_width) .. string.rep("\0", 7)
        end,
    }
    local positions = {}
    local context = {image = function(_, x) positions[#positions + 1] = x end}
    local data = {width = layer.width, layers = {layer}}
    background.paint(context, data, background.create_state(data), camera, bounds, wide)
    return positions
end
local stripes = {color = 0, x = 0, y = 220, cc = 0, width = 3200, loop = 1,
    transparency = 0, resource = "stripe.bmp", bitmap_width = 1}
local classic = paint_tiles(stripes, 1000)
assert(#classic == 794 and classic[1] == 0 and classic[#classic] == 793, "classic draws only visible stripes")
local wide = paint_tiles(stripes, 500, {left = -60, right = 880}, {left = -100, right = 900, camera = 500})
assert(#wide == 940 and wide[1] == -60 and wide[#wide] == 879, "wide rendering uses clipped bounds")
local overlapping = {color = 0, x = 7, y = 220, cc = 0, width = 2400, loop = 90,
    transparency = 1, resource = "overlap.bmp", bitmap_width = 120}
local partial = paint_tiles(overlapping, 120)
assert(#partial == 11 and partial[1] == -113 and partial[#partial] == 787, "clipping preserves partial tiles and phase")
print("PASS: repeated backgrounds respect the viewport and preserve tile positions")
