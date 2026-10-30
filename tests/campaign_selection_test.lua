local catalog={profile_id='dbz',campaigns={{id=1,name='Namek',path='mods/dbz/namek.dat',start_id=0,background=8}},
    load=function() return {} end,selectable=function() return true end}
package.preload['base/game/catalog']=function() return catalog end
engine={read_settings=function() return {} end}
local model=require('polish-fighters/dashboard_model')
assert(model.contents().campaigns[1].name=='Namek','custom catalog must not be parsed as ordinary stage data')
model.pending_campaign=catalog.campaigns[1]
local selection=dofile(arg[1]..'/engine/scripts/polish-fighters/selection.lua')({
    create=function() return {options={}} end,match_options=function() return {} end})
local state=selection.create({mode='stage'})
assert(state.options.stage_level==0 and not model.pending_campaign)
local options=selection.match_options(state)
assert(options.campaign_path=='mods/dbz/namek.dat' and options.campaign_background==8)
local continued=selection.create({mode='stage',previous=state})
assert(selection.match_options(continued).campaign_path==options.campaign_path)
local versus=selection.create({mode='versus',previous=state})
assert(not selection.match_options(versus).campaign_path,'campaign must not leak into versus mode')
local reads={}
engine.read_stage_data=function(path) reads[path]=(reads[path] or 0)+1;return {stages={}} end
local stage=require('base/game/stage')
local run=stage.create(0,'mods/dbz/namek.dat')
run.result=3;run.shutter=20
stage.update({round_counter=0},run)
assert(run.ending and not run.next_group,'standalone campaign must end instead of entering missing chapter')
local second=stage.create(0,'mods/dbz/buu.dat');second.result=3;second.shutter=20
stage.update({round_counter=0},second)
assert(reads['mods/dbz/namek.dat']==1 and reads['mods/dbz/buu.dat']==1,'campaign caches must be isolated')
package.loaded['base/ui/navigation']={create=function() return {} end,
    target=function(l,t,r,b) return {left=l,top=t,right=r,bottom=b} end,
    apply=function(s,input) return input end}
local shell=dofile(arg[1]..'/engine/scripts/polish-fighters/classic_shell.lua')({
    create=function() return {page='menu'} end,update=function() end,draw=function() end,describe=function() return '' end})
local menu=shell.create({});menu.pf_panel='campaigns';menu.pf_contents={campaigns=catalog.campaigns}
local action
local context={action=function(value) action=value end}
shell.update(menu,{keys={},nav={},click=true,pointer_x=420,pointer_y=219},context)
assert(action=='stage' and model.pending_campaign.id==1,'campaign click must enter actual stage setup')
menu.pf_panel='campaigns';catalog.campaigns[1].requires_custom_unlock=true;action=nil
shell.update(menu,{keys={},nav={},click=true,pointer_x=420,pointer_y=219},context)
assert(not action and menu.pf_message[1]=='KAMPANIA ZABLOKOWANA','unknown author unlock rules must not be bypassed')
print('PASS: campaign catalog, selection, continued options, versus isolation, ending and independent data caches')
