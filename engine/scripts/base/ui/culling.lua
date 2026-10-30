-- Pure rectangle intersection: omitted draw commands do not alter simulation.
local culling={}
function culling.visible(x,y,w,h,left,top,right,bottom)
    return w>0 and h>0 and x<right and y<bottom and x+w>left and y+h>top
end
return culling
