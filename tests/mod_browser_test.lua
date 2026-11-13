engine={read_settings=function() return {options={language='english'}} end}
local screen=require('polish-fighters/mod_browser')
local state={};local context={text_input=function() end}
screen.open(state)
assert(#screen.filtered(state.hub_mods)==103)
state.hub_mods.query='D.R. LF2 & LF3'
assert(#screen.filtered(state.hub_mods)==2)
state.hub_mods.query='[';assert(#screen.filtered(state.hub_mods)==0,'query treated as Lua pattern')
state.hub_mods.query='';screen.activate(state,'next',context);assert(state.hub_mods.page==2)
screen.activate(state,'category',context);assert(state.hub_mods.page==1)
for _,entry in ipairs(screen.filtered(state.hub_mods)) do assert(entry.category=='classic') end
screen.activate(state,'mod:little-fighter-2-original',context)
assert(state.hub_mods.detail.name=='Little Fighter 2 Original')
assert(#screen.rows(state.hub_mods)==1)
screen.activate(state,'back',context);assert(not state.hub_mods.detail)
state.hub_mods.query='no-such-mod';state.hub_mods.page=999;screen.rows(state.hub_mods)
assert(state.hub_mods.page==1)
local ctx={viewport=function() end,image=function() end,fill=function() end,text=function(value) assert(type(value)=='string') end}
screen.draw(state,ctx)
screen.activate(state,'search',context)
screen.update(state,{keys={},text='Naruto'},context)
assert(state.hub_mods.query=='no-such-modNaruto')
screen.update(state,{keys={[13]=true}},context);assert(not state.hub_mods.edit)
screen.activate(state,'back',context);assert(not state.hub_mods)
