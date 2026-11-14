local dialog=require('base/ui/quit_dialog')
local state=dialog.create('exit')
local context={sound=function() end}
dialog.update(state,{keys={},gamepad={},pointer_x=450,pointer_y=300},context)
assert(state.ready)
local result=dialog.update(state,{keys={},gamepad={},pointer_x=450,pointer_y=300,
    click=true,button=true},context)
assert(result=='close','first direct touch must close the new dialog')
print('PASS first touch closes a newly focused dialog')
