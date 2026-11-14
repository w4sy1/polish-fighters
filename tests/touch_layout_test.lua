local document={options={digipad=true,touch_layout='classic'},other='preserved'}
engine={read_settings=function() return document end,write_settings=function(value) document=value;return true end}
local options=require('base/game/options')
assert(options.current().touch_layout=='classic' and not options.current().digipad,'migrate saved cross profile to circular joystick')
local values=options.current();values.touch_layout='classic'
assert(options.save(values) and options.load().touch_layout=='classic' and not options.current().digipad)
values.touch_layout='modern';assert(options.save(values) and not options.current().digipad)
assert(document.other=='preserved')
local pad=require('base/ui/touch_gamepad')
local layout=options.default_gamepad()
local classic=pad.create(layout,true,'classic')
assert(not classic.stick.fixed and #classic.buttons==3,'old profiles use a circular stick and preserve base actions')
local modern=pad.create(layout,false,'modern')
assert(not modern.stick.fixed)
local function frame(state,touches,mode,screen)
    return pad.update(state,{touch_active=true,touches=touches,screen=screen},mode or 'match')
end
local function touch(button,id) return {id=id,x=button.x,y=button.y} end
-- Raptor_5G: 2436x1080 landscape, logical 794x550, centered at 1080/550 scale.
-- The viewport edges extend into both side bars and are reported to Lua.
local raptor_screen={left=-223,top=0,right=1017,bottom=550}
local scale=1080/550
local offset=(2436-794*scale)/2
local saved={}
for key,value in pairs(layout) do saved[key]=value end
for key,values in pairs({c={188,92,44},b={180,186,32},f={282,150,32},da={72,250,26},dj={72,165,26},daj={72,80,26}}) do
 saved[key]={right=values[1],bottom=values[2],radius=values[3]}
end
local phone=pad.create(saved,false,'modern',true)
frame(phone,{},'match',raptor_screen)
assert(#phone.buttons==3,'Android must show exactly attack, jump and block')
assert(phone.buttons[1].x==phone.buttons[2].x and phone.buttons[2].y<phone.buttons[1].y
 and phone.buttons[3].x<phone.buttons[1].x,'Android actions must form the approved triangle')
for i=1,#phone.buttons do for j=i+1,#phone.buttons do
 local a,b=phone.buttons[i],phone.buttons[j]
 local distance=math.sqrt((a.x-b.x)^2+(a.y-b.y)^2)
 assert(distance>a.radius+b.radius+5,'Raptor visible circles overlap after scaling')
end end
for index,letter in ipairs({'c','b','f'}) do
 local button=phone.buttons[index]
 local px,py=offset+button.x*scale,button.y*scale
 assert(px-button.radius*scale>=0 and px+button.radius*scale<=2436 and
  py-button.radius*scale>=0 and py+button.radius*scale<=1080,'Raptor action circle is clipped')
 assert(frame(phone,{touch(button,100+index)},'match',raptor_screen)==letter,
  'Raptor scaled action mapped to the wrong button')
 frame(phone,{},'match',raptor_screen)
end
for _,state in ipairs({classic,modern}) do
 local attack=touch(state.buttons[1],2)
 assert(state.buttons[1].radius==state.buttons[1].hit_radius,'attack hitbox must match its visible circle')
 for i=1,#state.buttons do for j=i+1,#state.buttons do
  local a,b=state.buttons[i],state.buttons[j]
  local distance=math.sqrt((a.x-b.x)^2+(a.y-b.y)^2)
  assert(distance>a.radius+b.radius+5,'visible action circles overlap: '..a.action..' / '..b.action)
 end end
 assert(frame(state,{attack}):find('c'),'attack must respond on finger down')
 assert(frame(state,{attack}):find('c'),'holding attack must remain active')
 assert(not frame(state,{}):find('c'),'release must not generate a delayed attack')
 local edge=touch(state.buttons[1],3);edge.x=edge.x+state.buttons[1].radius
 assert(frame(state,{edge}):find('c'),'entire visible attack circle, including its edge, must register')
 local upper=touch(state.buttons[1],31);upper.y=upper.y-state.buttons[1].radius
 assert(frame(state,{upper}):find('c'),'visible attack edge must respond')
 frame(state,{})
 for index,letter in ipairs({'c','b','f'}) do
  local button=state.buttons[index]
  local one=frame(state,{touch(button,40+index)})
  assert(one==letter,'one finger pressed the wrong action: '..letter..' -> '..one)
  assert(frame(state,{})=='','release must clear '..letter)
 end
 local jump,block=touch(state.buttons[2],52),touch(state.buttons[3],53)
 assert(frame(state,{jump,block})=='bf','jump and block must remain independent')
 assert(frame(state,{block})=='f','releasing jump must keep block only')
 assert(frame(state,{})=='','releasing block must clear it')
 local migrated=pad.create(saved,false,'modern')
 assert(migrated.buttons[1].x==state.buttons[1].x and migrated.buttons[2].y==state.buttons[2].y,
  'desktop touch layout must retain its previous positions')
 frame(state,{})
 local x,y=state.stick.default_x,state.stick.default_y
 frame(state,{{id=1,x=x,y=y}})
 local held=frame(state,{{id=1,x=x+35,y=y},{id=2,x=attack.x,y=attack.y}})
 assert(held:find('r') and held:find('c'),'movement and attack must work together')
 local triple=frame(state,{{id=1,x=x+35,y=y},jump,block})
 assert(triple:find('r') and triple:find('b') and triple:find('f') and not triple:find('c'),
  'three fingers must move, jump and block without attacking')
 local fourth=frame(state,{{id=1,x=x+35,y=y},jump,block,attack})
 assert(fourth:find('r') and fourth:find('b') and fourth:find('f') and fourth:find('c'),
  'four fingers must keep actions independent')
 local moved=touch(state.buttons[3],2)
 assert(not frame(state,{{id=1,x=x+35,y=y},jump,block,moved}):find('c'),
  'dragging the attack finger onto block must release attack without switching action')
 assert(frame(state,{attack},'pause')=='','pause must release movement and attack')
 pad.update(state,{touch_active=false})
 assert(frame(state,{})=='','hiding must not queue a delayed shot')
end
for _,style in ipairs({'classic','modern'}) do
 local menu=pad.create(layout,style=='classic',style)
 local button={id=12,x=menu.buttons[1].x,y=menu.buttons[1].y}
 assert(frame(menu,{button},'full'):find('c'),'menu attack must confirm immediately in '..style)
 assert(not menu.aim_finger and not menu.attack_pulse,'menu must not start an aiming gesture')
 assert(not frame(menu,{},'full'):find('c'),'menu release must not confirm again')
end
print('PASS: layout migration, classic multitouch, immediate attack, movement with attack and cancellation')
