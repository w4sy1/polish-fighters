return function(base)
 local draw=base.draw
 local settings=require("polish-fighters/input_settings")
 local catalog=require('base/game/catalog')
 function base.draw(state,context,...)
  local styled=context.text and (catalog.profile_id=='polish-originals' or catalog.profile_id=='mixed-all')
  local wrapped=context
  if styled then
   wrapped={};for key,value in pairs(context) do wrapped[key]=value end
   function wrapped.image(resource,x,y,...)
    if resource=='pe/charmenu' then
     context.image('pe/menu_back1',0,0,true)
     context.fill(0,0,794,550,8,13,27,125)
     context.fill(30,38,734,48,18,30,53,230)
     context.fill(30,84,734,2,224,72,92)
     context.text('POLISH FIGHTERS  /  WYBÓR POSTACI',397,50,'center',23,0xf0f5ff,nil,nil,true)
     for slot=0,7 do
      local col,row=slot%4*153,math.floor(slot/4)*212
      context.fill(col+144,row+91,126,192,19,32,53,225)
      context.fill(col+144,row+91,126,3,slot<4 and 100 or 224,slot<4 and 168 or 72,slot<4 and 230 or 92)
     end
     for row=0,1 do
      for index,label in ipairs({'Gracz:','Postać:','Drużyna:'}) do
       context.text(label,139,219+row*212+(index-1)*22,'right',12,0xadc3df,nil,nil,true)
      end
     end
     return
    elseif resource=='pe/cma' or resource=='pe/cma2' then
     context.text('DOŁĄCZ DO WALKI',x+60,y+7,'center',12,0xdbe9ff,nil,nil,true)
     context.text('Naciśnij atak',x+60,y+29,'center',13,0x8fb9e8,nil,nil,true)
     return
    end
    return context.image(resource,x,y,...)
   end
  end
  draw(state,wrapped,...)
  if context.text then context.text(settings.hint(),397,529,"center",13,0xd4e4ff,nil,nil,true) end
 end
 return base
end
