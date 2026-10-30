local document={}
engine={read_settings=function() return document end,write_settings=function(v) document=v;return true end}
local targets
package.preload['base/ui/navigation']=function() return {
    create=function() return {} end,
    target=function(l,t,r,b) return {left=l,top=t,right=r,bottom=b} end,
    apply=function(state,input,page) targets=page.targets;return input end} end
local options=require('base/game/options')
local screen=require('base/ui/launch')
local state=screen.create({})
state.page='options';state.options=options.current();state.options.language='polish'
local function update(x,y,click)
    screen.update(state,{filters={text=true,window=true,xbrz=true},pointer_x=x,pointer_y=y,
        click=click,nav={},keys={},text=''}, {action=function() end,text_input=function() end,sound=function() end})
end
update(-1,-1,false)
for _,box in ipairs(targets) do assert(box.top>=0 and box.bottom<=550,'settings target outside viewport') end
assert(targets[1].top>=205,'settings panel must remain below the classic logo')
local first=targets[1]
update(first.left+5,first.top+5,true)
assert(state.option_open=='touch_layout')
update(-1,-1,false)
local modern=targets[3]
update(modern.left+5,modern.top+5,true)
assert(state.options.touch_layout=='modern')
update(-1,-1,false)
local ok=targets[#targets-1]
update(ok.left+5,ok.top+5,true)
assert(state.page=='menu' and document.options.touch_layout=='modern')
assert(not options.current().digipad)
print('PASS: actual settings dropdown, visible targets and saved modern layout')
