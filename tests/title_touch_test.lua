local title=require('base/ui/title')
local selected
local context={action=function(value) selected=value end,sound=function() end}
local state=title.create()
title.update(state,{[0]='',pointer_x=395,pointer_y=243,click=true},context)
assert(selected=='stage' and state.selection==1,'touch must open the original LF2 menu row')
selected=nil
state=title.create()
title.set_replay_disabled(state,true)
title.update(state,{[0]='',pointer_x=395,pointer_y=378,click=true},context)
assert(selected==nil,'disabled replay must not open on touch')
print('PASS LF2 title touch selection and disabled replay')
