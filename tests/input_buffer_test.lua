local buffer=require('polish-fighters/input_buffer')
for _,action in ipairs({'u','d','l','r','c','b','f'}) do
 local state={input_phase=0}
 buffer.prepare(state,{[0]=action,functions=''})
 state.input_phase=1
 assert(buffer.prepare(state,{[0]='',functions=''})[0]:find(action,1,true),'short press lost: '..action)
 state.input_phase=0;buffer.prepare(state,{[0]='',functions=''})
 state.input_phase=1;assert(buffer.prepare(state,{[0]='',functions=''})[0]=='','press became sticky: '..action)
end
local state={input_phase=0}
buffer.prepare(state,{[0]='r',functions=''})
state.input_phase=1
local reversed=buffer.prepare(state,{[0]='l',functions=''})[0]
assert(reversed:find('l') and not reversed:find('r'),'fresh direction must override queued movement')
for _,paused in ipairs({false,true}) do
 state={input_phase=0,paused=paused}
 buffer.prepare(state,{[0]='',functions='4'})
 state.input_phase=1
 assert(buffer.prepare(state,{[0]='',functions=''}).functions=='4','short F4 lost, paused='..tostring(paused))
end
print('PASS: short movement/actions survive sampling, immediate reversal, release, F4 while paused')
