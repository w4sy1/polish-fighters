-- Coordinates follow the original LF2 start menu's narrow centred text column.
local layout={}
function layout.box(index,count)
 if count<=10 then return 147,207+(index-1)*28,500,23 end
 local column=math.floor((index-1)/10)
 return 133+column*285,207+(index-1)%10*28,260,23
end
function layout.language(index) return 653+(index-1)*65,510,59,25 end
return layout
