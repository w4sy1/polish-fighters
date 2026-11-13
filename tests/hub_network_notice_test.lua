engine={read_settings=function() return {} end}
local locale=require('base/i18n/i18n');locale.use('polish');locale.host(true)
local shell=dofile(arg[1]..'/engine/scripts/polish-fighters/hub_launch.lua')({
 create=function() return {} end,update=function() end,draw=function() end,describe=function() return '' end})
local seen={}
shell.draw({hub_enabled=true,page='menu',hub_mode='root',message='Network connection lost'},
 {viewport=function() end,image=function() end,sprite=function() end,fill=function() end,text=function(value) seen[value]=true end})
assert(seen['Network connection lost'],'network failure was hidden behind module launcher')
print('PASS hub: disconnect reason remains visible on module launcher')
