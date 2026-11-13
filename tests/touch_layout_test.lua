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
for _,state in ipairs({classic,modern}) do
 local attack=touch(state.buttons[1],2)
 assert(state.buttons[1].radius>=56,'old saved profiles must get a larger visible attack button')
 assert(state.buttons[1].hit_radius>=78,'attack needs a forgiving touch area around the visible circle')
 assert(frame(state,{attack}):find('c'),'attack must respond on finger down')
 assert(frame(state,{attack}):find('c'),'holding attack must remain active')
 assert(not frame(state,{}):find('c'),'release must not generate a delayed attack')
 local edge=touch(state.buttons[1],3);edge.x=edge.x+state.buttons[1].radius
 assert(frame(state,{edge}):find('c'),'entire visible attack circle, including its edge, must register')
 frame(state,{})
 local forgiving=touch(state.buttons[1],4);forgiving.x=forgiving.x+state.buttons[1].radius+15
 assert(frame(state,{forgiving}):find('c'),'near-edge attack taps must be forgiving on touchscreens')
 frame(state,{})
 local x,y=state.stick.default_x,state.stick.default_y
 frame(state,{{id=1,x=x,y=y}})
 local held=frame(state,{{id=1,x=x+35,y=y},{id=2,x=attack.x,y=attack.y}})
 assert(held:find('r') and held:find('c'),'movement and attack must work together')
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
