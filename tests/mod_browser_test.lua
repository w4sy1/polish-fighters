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

-- Polish Fighters - GitHub: catalogue, progress and install through engine.mods.
local calls={}
local responses={catalogue={packages={{id='lf4-turbo',name='LF4 Turbo',profile='lf_four_turbo',size_bytes=47180842},
 {id='dbz',name='Dragon Ball Z',profile='dbz',size_bytes=152277588}}}}
local pending=1
engine.mods=function(action,value)
 calls[#calls+1]=action..(value and (':'..value) or '')
 if action=='catalogue' or action=='install' then return true end
 if action=='progress' then return 50,100,1,0 end
 if action=='poll' then
  if pending>0 then pending=pending-1;return 'pending' end
  if calls[#calls-1]=='install:lf4-turbo' or responses.installing then return 'lf4-turbo' end
  return responses.catalogue
 end
end
local s2={hub_available={lf_four_turbo=false}}
screen.open(s2)
screen.activate(s2,'github',context)
assert(s2.hub_mods.github.busy=='catalogue')
screen.update(s2,{keys={}},context);assert(s2.hub_mods.github.busy=='catalogue')
screen.update(s2,{keys={}},context)
assert(not s2.hub_mods.github.busy and #s2.hub_mods.github.packages==2)
local rows=screen.rows(s2.hub_mods);assert(rows[1][1]=='gh:dbz' and rows[2][1]=='gh:lf4-turbo')
screen.draw(s2,ctx)
pending=1;responses.installing=true
screen.activate(s2,'gh:lf4-turbo',context);assert(s2.hub_mods.github.busy=='install')
screen.update(s2,{keys={}},context);assert(s2.hub_mods.github.fraction==0.5)
screen.draw(s2,ctx)
screen.update(s2,{keys={}},context)
assert(not s2.hub_mods.github.busy and s2.hub_mods.github.installed['lf4-turbo'])
assert(s2.hub_available.lf_four_turbo==true)
screen.activate(s2,'back',context);assert(s2.hub_mods and not s2.hub_mods.github)
-- Without the native installer (Android), the screen explains where to install.
engine.mods=function() return nil,'Mods handled by platform' end
screen.activate(s2,'github',context);assert(not s2.hub_mods.github.busy)
