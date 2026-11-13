-- Local-only editor. Live controls and preview share the same geometry.
local options=require('base/game/options')
local pad=require('base/ui/touch_gamepad')
local font=require('base/ui/font')
local editor={}
local names={'stick','dpad','c','b','f','da','dj','daj','pause','fast','commands'}
local labels={stick='JOYSTICK',dpad='KIERUNKI',c='ATAK',b='SKOK',f='BLOK',da='D+A',dj='D+J',daj='D+J+A',pause='PAUZA',fast='TEMPO',commands='KOMENDY'}
local function clone(v)
 if type(v)~='table' then return v end
 local out={};for k,x in pairs(v) do out[k]=clone(x) end;return out
end
local function clamp(v,lo,hi) return math.max(lo,math.min(hi,v)) end
function editor.create(values)
 return {values=clone(values),selected='c',slot=1,message='Przeciagnij przycisk lub joystick'}
end
function editor.rebuild(s)
 s.pad=pad.create(s.values.gamepad,s.values.touch_layout=='classic',s.values.touch_layout)
 pad.set_available(s.pad,{da=true,dj=true,daj=true})
 pad.update(s.pad,{touch_active=true,touches={},screen={left=0,top=190,right=794,bottom=550}},'match');s.pad.visible=true
end
local function controls(s)
 local result={}
 local function b(label,action,x,y,w) result[#result+1]={label=label,action=action,x=x,y=y,w=w or 94,h=27} end
 b('KLASYCZNY','classic',8,8,122);b('MOBILNY','modern',136,8,112)
 b('DOMYSLNE','reset',254,8,112);b('ZASTOSUJ','apply',552,8,112);b('ANULUJ','cancel',670,8,112)
 b('PROFIL '..s.slot,'slot',8,42,122);b('ZAPISZ PROFIL','save_profile',136,42,150);b('WCZYTAJ PROFIL','load_profile',292,42,158)
 b('ROZMIAR -','smaller',8,76,110);b('ROZMIAR +','bigger',124,76,110)
 b('ALFA -','opacity_down',240,76);b('ALFA +','opacity_up',340,76)
 b('MARTWA -','deadzone_down',8,110,110);b('MARTWA +','deadzone_up',124,110,110)
 b('CZULOSC -','sensitivity_down',240,110,110);b('CZULOSC +','sensitivity_up',356,110,110)
 b(s.values.gamepad.stick.fixed==1 and 'STALY' or 'DYNAMICZNY','fixed',472,110,134)
 b(s.values.auto_advance and 'AUTO PRAWO: TAK' or 'AUTO PRAWO: NIE','auto',456,42,194)
 return result
end
function editor.update(s,input)
 local x,y=input.pointer_x or -1,input.pointer_y or -1
 if input.nav and input.nav.cancel then return 'cancel' end
 if input.click then
  for _,b in ipairs(controls(s)) do
   if x>=b.x and x<=b.x+b.w and y>=b.y and y<=b.y+b.h then
    local action=b.action;local layout=s.values.gamepad
    if action=='apply' then
     local ok,problem=options.save(s.values)
     if ok then return 'apply' end
     s.message='Blad zapisu: '..tostring(problem)
    elseif action=='cancel' then return 'cancel'
    elseif action=='classic' or action=='modern' then s.values.touch_layout=action
    elseif action=='reset' then s.values.gamepad=options.default_gamepad()
    elseif action=='slot' then s.slot=s.slot%3+1
    elseif action=='save_profile' then
     local doc=engine.read_settings() or {};doc.touch_profiles=type(doc.touch_profiles)=='table' and doc.touch_profiles or {}
     doc.touch_profiles[tostring(s.slot)]={layout=clone(layout),style=s.values.touch_layout}
     local ok,problem=engine.write_settings(doc);s.message=ok and 'Profil zapisany' or 'Blad: '..tostring(problem)
    elseif action=='load_profile' then
     local doc=engine.read_settings() or {};local p=type(doc.touch_profiles)=='table' and doc.touch_profiles[tostring(s.slot)]
     if type(p)=='table' and type(p.layout)=='table' and (p.style=='classic' or p.style=='modern') then
      s.values.gamepad=options.normalize_gamepad(p.layout);s.values.touch_layout=p.style;s.message='Profil wczytany'
     else s.message='Brak poprawnego profilu w tym miejscu' end
    elseif action=='smaller' or action=='bigger' then
     local v=layout[s.selected];v.radius=clamp(v.radius+(action=='bigger' and 4 or -4),12,130)
    elseif action=='opacity_down' or action=='opacity_up' then
     layout.appearance.opacity=clamp(layout.appearance.opacity+(action=='opacity_up' and .05 or -.05),.15,1)
    elseif action=='deadzone_down' or action=='deadzone_up' then
     layout.stick.deadzone=clamp(layout.stick.deadzone+(action=='deadzone_up' and .05 or -.05),.05,.9)
    elseif action=='sensitivity_down' or action=='sensitivity_up' then
     layout.stick.sensitivity=clamp(layout.stick.sensitivity+(action=='sensitivity_up' and .1 or -.1),.25,3)
    elseif action=='fixed' then layout.stick.fixed=1-layout.stick.fixed end
    if action=='auto' then s.values.auto_advance=not s.values.auto_advance end
    editor.rebuild(s);return
   end
  end
  local best,distance
  for _,name in ipairs(names) do
   if not (name=='stick' and s.values.touch_layout=='classic') and not (name=='dpad' and s.values.touch_layout~='classic') then
    local v=s.values.gamepad[name]
    local cx=v.left or 794-v.right;local cy=v.top and 190+v.top or 550-v.bottom
    local d=math.sqrt((x-cx)^2+(y-cy)^2)
    if d<=v.radius and (not distance or d<distance) then best,distance=name,d end
   end
  end
  if best then s.selected=best;s.drag=true end
 end
 if s.drag and input.button then
  local v=s.values.gamepad[s.selected]
  x,y=clamp(x,v.radius,794-v.radius),clamp(y,190+v.radius,550-v.radius)
  if v.left then v.left=x else v.right=794-x end
  if v.top then v.top=y-190 else v.bottom=550-y end
  editor.rebuild(s)
 elseif not input.button then s.drag=nil end
end
function editor.draw(s,context)
 if not s.pad then editor.rebuild(s) end
 context.viewport(794,550,12,20,40)
 context.fill(0,195,794,2,40,65,90,255)
 pad.draw(s.pad,context)
 for _,b in ipairs(controls(s)) do
  context.fill(b.x,b.y,b.w,b.h,34,60,100,255)
  font.draw(context,b.label,b.x+b.w/2,b.y+7,nil,nil,'center')
 end
 local l=s.values.gamepad
 font.draw(context,string.format('%s R=%d ALFA=%.2f MARTWA=%.2f CZULOSC=%.1f',
  labels[s.selected],l[s.selected].radius,l.appearance.opacity,l.stick.deadzone,l.stick.sensitivity),397,150,nil,nil,'center')
 font.draw(context,s.message,397,179,nil,nil,'center')
end
return editor
