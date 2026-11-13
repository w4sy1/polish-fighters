local document={preserved=true}
local fail=false
engine={read_settings=function() return document end,write_settings=function(v)
 if fail then return nil,'disk full' end
 document=v;return true
end}
local options=require('base/game/options')
local editor=require('base/ui/hud_editor')
local s=editor.create(options.current())
local function tap(x,y) return editor.update(s,{pointer_x=x,pointer_y=y,click=true,button=true}) end
tap(150,20);assert(s.values.touch_layout=='modern')
tap(606,458);editor.update(s,{pointer_x=680,pointer_y=430,button=true})
editor.update(s,{button=false})
assert(s.values.gamepad.c.right==114 and s.values.gamepad.c.bottom==120,'drag did not move attack')
tap(150,85);assert(s.values.gamepad.c.radius==48)
tap(260,85);assert(s.values.gamepad.appearance.opacity<.66)
tap(150,120);assert(s.values.gamepad.stick.deadzone>.25)
tap(380,120);assert(s.values.gamepad.stick.sensitivity>1)
tap(500,120);assert(s.values.gamepad.stick.fixed==1)
tap(180,50);assert(document.touch_profiles['1'].layout.c.radius==48)
tap(280,20);assert(s.values.gamepad.c.radius==44)
tap(330,50);assert(s.values.gamepad.c.radius==48 and s.values.touch_layout=='modern')
assert(tap(580,20)=='apply' and document.options.gamepad.c.radius==48 and document.preserved)
fail=true;assert(tap(580,20)==nil and s.message:find('disk full'))
local pad=require('base/ui/touch_gamepad')
local values=options.default_gamepad();values.stick.fixed=1
local p=pad.create(values,false,'modern')
local function frame(t) return pad.update(p,{touch_active=true,touches=t},'match') end
local x,y=p.stick.default_x,p.stick.default_y
assert(frame({{id=1,x=x+30,y=y}}):find('r'),'fixed joystick recentered on the finger')
assert(not frame({{id=1,x=x+5,y=y}}):find('r'),'dead zone ignored')
frame({});assert(p.knob_x==x and p.knob_y==y,'joystick did not return to center')
local a,b=p.buttons[1],p.buttons[2]
for n=0,15 do
 local angle=n*math.pi/8
 frame({})
 local held=frame({{id=1,x=x+30,y=y},{id=2,x=a.x+math.cos(angle)*(a.radius-1),y=a.y+math.sin(angle)*(a.radius-1)},
  {id=3,x=b.x,y=b.y}})
 assert(held:find('r') and held:find('c') and held:find('b'),'attack perimeter or three-finger input lost')
end
assert(frame({})=='','released fingers left movement or attack active')
print('PASS HUD: drag, resize, opacity, presets, profiles, dead zone/sensitivity/fixed stick, failed save, attack perimeter and three fingers')
