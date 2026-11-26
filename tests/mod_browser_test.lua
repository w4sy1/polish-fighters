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
local ctx={sprite=function() end,viewport=function() end,image=function() end,fill=function() end,text=function(value) assert(type(value)=='string') end}
screen.draw(state,ctx)
screen.activate(state,'search',context)
screen.update(state,{keys={},text='Naruto'},context)
assert(state.hub_mods.query=='no-such-modNaruto')
screen.update(state,{keys={[13]=true}},context);assert(not state.hub_mods.edit)
screen.activate(state,'back',context);assert(not state.hub_mods)

-- Polish Fighters - GitHub: catalogue, progress and install through engine.mods.
local calls={}
local sha=string.rep('a',64)
local responses={catalogue={packages={{id='lf4-turbo',name='LF4 Turbo',profile='lf_four_turbo',size_bytes=47180842,version='1.0.0',sha256=sha},
 {id='dbz',name='Dragon Ball Z',profile='dbz',size_bytes=152277588,version='1.0.0',sha256=sha}}}}
local pending=1
engine.mods=function(action,value)
 calls[#calls+1]=action..(value and (':'..value) or '')
 if action=='catalogue' or action=='install' or (action=='import' and responses.importing) then
  responses.importing=nil
  return true
 end
 if action=='receipt' and value=='lf4-turbo' and responses.installed then return '1.0.0 '..sha end
 if action=='progress' then return 50,100,1,0 end
 if action=='poll' then
  if pending>0 then pending=pending-1;return 'pending' end
  if responses.installing then responses.installed=true;return 'lf4-turbo' end
  return responses.catalogue
 end
end
local s2={hub_available={lf_four_turbo=false}}
local watch=require('polish-fighters/catalog_watch')
watch.poll(s2)
assert(s2.hub_catalog_started and calls[#calls]=='catalogue')
screen.open(s2)
local request_count=#calls
screen.activate(s2,'github',context)
assert(s2.hub_mods.github.busy=='catalogue' and s2.hub_catalog_done)
assert(#calls==request_count,'opening Mods must take over the in-flight catalogue rather than start a second request')
screen.update(s2,{keys={}},context);assert(s2.hub_mods.github.busy=='catalogue')
screen.update(s2,{keys={}},context)
assert(not s2.hub_mods.github.busy and #s2.hub_mods.github.packages==2)
local rows=screen.rows(s2.hub_mods)
assert(rows[1][1]=='gh_classic' and rows[2][1]=='gh:dbz' and rows[3][1]=='gh:lf4-turbo')
assert(rows[3][2]:find('POBIERZ',1,true) or rows[3][2]:find('DOWNLOAD',1,true))
screen.draw(s2,ctx)
pending=1;responses.installing=true
screen.activate(s2,'gh:lf4-turbo',context);assert(s2.hub_mods.github.busy=='install')
screen.activate(s2,'gh_cancel',context);assert(calls[#calls]=='cancel')
screen.update(s2,{keys={}},context);assert(s2.hub_mods.github.fraction==0.5)
screen.draw(s2,ctx)
screen.update(s2,{keys={}},context)
assert(not s2.hub_mods.github.busy and s2.hub_mods.github.packages[2].receipt=='1.0.0 '..sha)
local installed=screen.rows(s2.hub_mods)[3][2]
assert(installed:find('WYBIERZ',1,true) or installed:find('SELECT',1,true))
assert(s2.hub_available.lf_four_turbo==true)
local selected
screen.activate(s2,'gh:lf4-turbo',{action=function(action) selected=action end})
assert(selected=='profile_lf_four_turbo')
screen.activate(s2,'gh_import',{action=function(action) selected=action end})
assert(selected=='import_local_mod')
responses.importing=true
screen.update(s2,{keys={}},context)
assert(s2.hub_mods.github.busy=='install' and not s2.hub_mods.github.target)
screen.update(s2,{keys={}},context)
assert(not s2.hub_mods.github.busy and s2.hub_mods.github.target=='lf4-turbo')
screen.activate(s2,'back',context);assert(s2.hub_mods and not s2.hub_mods.github)
-- Without the native installer (Android), the screen explains where to install.
engine.mods=function() return nil,'Mods handled by platform' end
screen.activate(s2,'github',context);assert(not s2.hub_mods.github.busy)
-- Android asks Java to open the Mods screen over the current game.
local saved,actions={}, {}
engine.write_settings=function(value) saved=value;return true end
local android={hub_android=true}
screen.open(android)
screen.activate(android,'github',{text_input=function() end,action=function(name) actions[#actions+1]=name end})
assert(next(saved)==nil and actions[1]=='open_android_mods' and android.hub_mods and not android.hub_mods.github)

-- Punkt 4: multi-select batch download - toggle queue, persist it, download item by item,
-- and auto-continue to the next queued package once each install finishes.
local saved3
engine.read_settings=function() return type(saved3)=='table' and saved3 or {} end
engine.write_settings=function(value) saved3=value;return true end
local sha2=string.rep('b',64)
local installedSet,pollLeft={},0
engine.mods=function(action,value)
 if action=='catalogue' then pollLeft=1;return true end
 if action=='install' then installedSet[value]='pending';pollLeft=1;return true end
 if action=='receipt' then return installedSet[value]=='done' and ('1.0.0 '..sha2) or nil end
 if action=='progress' then return 1,1,1,0 end
 if action=='poll' then
  if pollLeft>0 then pollLeft=pollLeft-1;return 'pending' end
  for id,st in pairs(installedSet) do if st=='pending' then installedSet[id]='done';return id end end
  return {packages={{id='lf4-turbo',name='LF4 Turbo',profile='lf_four_turbo',size_bytes=1,version='1.0.0',sha256=sha2},
   {id='dbz',name='Dragon Ball Z',profile='dbz',size_bytes=1,version='1.0.0',sha256=sha2}}}
 end
end
local s3={}
screen.open(s3)
screen.activate(s3,'github',context)
screen.update(s3,{keys={}},context)
screen.update(s3,{keys={}},context)
assert(#s3.hub_mods.github.packages==2,'catalogue should resolve to two packages')
screen.activate(s3,'gh_multi',context)
assert(s3.hub_mods.github.multi==true)
local idx={};for i,row in ipairs(screen.rows(s3.hub_mods)) do idx[row[1]]=i end
screen.activate(s3,'gh:lf4-turbo',context)
screen.activate(s3,'gh:dbz',context)
assert(#s3.hub_mods.github.queue==2,'both packages should be queued, not downloaded immediately')
assert(saved3.little_fighters_prefetch['lf4-turbo']==true and saved3.little_fighters_prefetch['dbz']==true,
 'queue must be persisted so a killed app/lost network resumes with completed items skipped')
local checkedLabel=screen.rows(s3.hub_mods)[idx['gh:dbz']][2]
assert(checkedLabel:find('%[X%]'),'queued package should show a checked box')
screen.activate(s3,'gh_queue_run',context)
assert(s3.hub_mods.github.busy=='install','confirming the batch should start the first item')
screen.update(s3,{keys={}},context)
screen.update(s3,{keys={}},context)
assert(s3.hub_mods.github.busy=='install','finishing one item should auto-continue to the next queued one')
screen.update(s3,{keys={}},context)
screen.update(s3,{keys={}},context)
assert(not s3.hub_mods.github.busy,'the queue should stop once every item is installed')
assert(installedSet['lf4-turbo']=='done' and installedSet['dbz']=='done')
for _,row in ipairs(screen.rows(s3.hub_mods)) do
 if row[1]=='gh_queue_run' then
  assert(not row[2]:find('%(%d+%)'),'installed packages should not count as pending downloads')
 end
end
print('PASS multi-select batch queue: toggle, persistence, per-item progress and auto-continue')
