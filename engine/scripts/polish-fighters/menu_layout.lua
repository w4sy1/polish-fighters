-- All coordinates are in the engine's existing 794 x 550 logical viewport.
local layout={}
function layout.box(index,count)
 if count<=8 then return 221,141+(index-1)*43,352,37 end
 local column=math.floor((index-1)/8)
 return 30+column*384,141+(index-1)%8*41,366,35
end
function layout.language(index) return 653+(index-1)*65,514,59,28 end
return layout
