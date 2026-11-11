local document={version=1,options={unlock_characters=false},private_control='preserved'}
engine={read_settings=function() return document end,
    write_settings=function(value) document=value;return true end}
package.preload['polish-fighters/dashboard_model']=function() return {} end
local options=require('base/game/options')
local unlock=require('base/game/unlock')
local screen=require('polish-fighters/classic_shell')({
    create=function() return {page='menu'} end,
    update=function() end,draw=function() end,describe=function() return '' end})
local state=screen.create({})
local function type_code(value)
    state.pf_panel='unlock';state.pf_message=nil;state.pf_code=''
    screen.update(state,{text=value,keys={},nav={},presses={}},
        {text_input=function() end})
end
options.start()
type_code('polishfighters')
assert(document.options.unlock_characters and unlock.flags.characters==1)
assert(document.private_control=='preserved')
assert(state.pf_message[1]=='POSTACIE ODBLOKOWANE')
-- Android writes this same option before the engine starts; no second cheat flag.
local values=options.current();values.unlock_characters=false;options.save(values)
assert(unlock.flags.characters==0)
document.options.unlock_characters=true
options.start()
assert(unlock.flags.characters==1)
assert(document.private_control=='preserved')
print('PASS: desktop polishfighters code and Android saved unlock option share real engine policy')
