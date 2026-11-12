-- Small project-owned 5 x 7 capitals. Integer rectangles keep pixels crisp at logical resolution.
local font={}
local shapes={
 A={14,17,17,31,17,17,17},B={30,17,17,30,17,17,30},C={14,17,16,16,16,17,14},D={30,17,17,17,17,17,30},
 E={31,16,16,30,16,16,31},F={31,16,16,30,16,16,16},G={14,17,16,23,17,17,15},H={17,17,17,31,17,17,17},
 I={14,4,4,4,4,4,14},J={7,2,2,2,18,18,12},K={17,18,20,24,20,18,17},L={16,16,16,16,16,16,31},
 M={17,27,21,21,17,17,17},N={17,25,21,19,17,17,17},O={14,17,17,17,17,17,14},P={30,17,17,30,16,16,16},
 Q={14,17,17,17,21,18,13},R={30,17,17,30,20,18,17},S={15,16,16,14,1,1,30},T={31,4,4,4,4,4,4},
 U={17,17,17,17,17,17,14},V={17,17,17,17,17,10,4},W={17,17,17,21,21,21,10},X={17,17,10,4,10,17,17},
 Y={17,17,10,4,4,4,4},Z={31,1,2,4,8,16,31},
 ['0']={14,17,19,21,25,17,14},['1']={4,12,4,4,4,4,14},['2']={14,17,1,2,4,8,31},['3']={30,1,1,14,1,1,30},
 ['4']={2,6,10,18,31,2,2},['5']={31,16,16,30,1,1,30},['6']={14,16,16,30,17,17,14},['7']={31,1,2,4,8,8,8},
 ['8']={14,17,17,14,17,17,14},['9']={14,17,17,15,1,1,14},
 [' ']={},['/']={1,2,2,4,8,8,16},['-']={0,0,0,31},[':']={0,4,4,0,4,4},['.']={0,0,0,0,0,4,4},
 ['[']={14,8,8,8,8,8,14},[']']={14,2,2,2,2,2,14},['+']={0,4,4,31,4,4},['?']={14,17,1,2,4,0,4},
}
local accents={['Ą']='A',['Ć']='C',['Ę']='E',['Ł']='L',['Ń']='N',['Ó']='O',['Ś']='S',['Ź']='Z',['Ż']='Z'}
local lower={['ą']='Ą',['ć']='Ć',['ę']='Ę',['ł']='Ł',['ń']='Ń',['ó']='Ó',['ś']='Ś',['ź']='Ź',['ż']='Ż'}
local function characters(value)
 return value:gsub('[%z\1-\127\194-\244][\128-\191]*',function(c) return lower[c] or c:upper() end)
end
function font.draw(context,value,x,y,scale,color,align)
 value=characters(value);scale=scale or 2
 local count=0;for _ in value:gmatch('[%z\1-\127\194-\244][\128-\191]*') do count=count+1 end
 local width=(count*6-1)*scale
 if align=='center' then x=x-width/2 elseif align=='right' then x=x-width end
 x=math.floor(x);y=math.floor(y)
 -- One sprite per character avoids exceeding the engine's command budget on long module lists.
 if context.sprite then
  local atlas=require('polish-fighters/menu_font_index')
  local offset=({[1]=0,[2]=12,[4]=36})[scale]
  if offset then
   for c in value:gmatch('[%z\1-\127\194-\244][\128-\191]*') do
    context.sprite('mods/polish-fighters/menu-font.png',{(atlas[c] or atlas['?'])*scale,offset,5*scale,12*scale},x,y-3*scale,true,false,false,color)
    x=x+6*scale
   end
   return
  end
 end
 local r=math.floor(color/65536)%256;local g=math.floor(color/256)%256;local b=color%256
 local function pixel(px,py) context.fill(x+px*scale,y+py*scale,scale,scale,r,g,b) end
 for c in value:gmatch('[%z\1-\127\194-\244][\128-\191]*') do
  local rows=shapes[accents[c] or c] or shapes['?']
  for row,bits in ipairs(rows) do
   for column=0,4 do if math.floor(bits/2^(4-column))%2==1 then pixel(column,row-1) end end
  end
  if c=='Ł' then pixel(1,4);pixel(3,2)
  elseif c=='Ą' or c=='Ę' then pixel(3,7);pixel(4,8)
  elseif c=='Ż' then pixel(2,-2)
  elseif accents[c] then pixel(2,-2);pixel(3,-3) end
  x=x+6*scale
 end
end
font.glyphs=shapes
font.accents=accents
return font
