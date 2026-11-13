local messages={}
engine={read_settings=function() return {} end,network_time=function() return 0 end,network=function(op)
 if op=='poll' then return '' end
 return true
end,json_encode=function(v) messages[#messages+1]=v;return '{}' end}
local legacy={create=function() return {} end,start=function() end,poll=function() end,close=function() end,exchange=function() end}
local network=dofile(arg[1]..'/engine/scripts/polish-fighters/room_network.lua')(legacy)
network.next_room=true
local s=network.create({network_profile=string.rep('a',64)})
s.phase='ready';s.slot=1;s.pending=true;s.deadline=30000
local tap={[0]='rc',functions=''}
assert(not network.exchange(s,tap,0,'digest'))
s.frame={inputs={'','', '', '', '', '', '', ''}}
assert(network.exchange(s,{[0]='',functions=''},0,'digest'))
s.sent_checksum=0;s.checked=0
assert(not network.exchange(s,{[0]='',functions=''},0,'digest'))
local sent=messages[#messages]
assert(sent.op=='input' and sent.keys:find('c') and sent.keys:find('r'),'short aimed tap lost across network wait')
assert(next(s.queued_actions)==nil,'tap repeated after sending')
network.close(s);assert(next(s.queued_actions)==nil and not s.queued_action_directions)
network.next_room=true
s=network.create({network_profile=string.rep('a',64)});s.phase='ready';s.slot=0
network.exchange(s,{[0]='c',functions=''},0,'digest')
network.exchange(s,{[0]='c',functions=''},0,'digest') -- repeated render of the same pending tick
s.frame={inputs={'c','', '', '', '', '', '', ''}}
assert(network.exchange(s,{[0]='c',functions=''},0,'digest'))
s.sent_checksum=0;s.checked=0
network.exchange(s,{[0]='',functions=''},0,'digest')
assert(messages[#messages].keys=='','waiting redraw duplicated a sent tap and swallowed release')
network.next_room=true
s=network.create({network_profile=string.rep('a',64)});s.phase='ready';s.slot=0;s.frames=1;s.sent_checksum=0;s.deadline=30000
assert(not network.exchange(s,{[0]='r',functions=''},0,'digest'))
assert(messages[#messages].op=='input' and messages[#messages].frame==1,'next input must not wait for a separate checksum acknowledgement')
assert(s.frames==1,'unconfirmed frame advanced')
s.checked=0;s.frame={inputs={'r','', '', '', '', '', '', ''}}
assert(network.exchange(s,{[0]='r',functions=''},0,'digest') and s.frames==2)
print('PASS room input: tap and aim survive pending frame, send once, clear on disconnect')

network.next_room=true
s=network.create({network_profile=string.rep('a',64)});s.phase='ready';s.slot=0;s.pending=true;s.deadline=30000
assert(not network.exchange(s,{[0]='',functions='4'},0,'digest'))
s.frame={inputs={'','', '', '', '', '', '', ''}}
assert(network.exchange(s,{[0]='',functions=''},0,'digest'))
s.sent_checksum=0;s.checked=0
assert(not network.exchange(s,{[0]='',functions=''},0,'digest'))
assert(messages[#messages].functions=='4','short F4 lost across pending network frame')
assert(not s.queued_back,'F4 repeated after sending')
print('PASS short F4 survives a pending network frame')
network.next_room=true
s=network.create({network_profile=string.rep('a',64)});s.phase='ready';s.slot=1;s.pending=true;s.deadline=30000
network.exchange(s,{[0]='f',functions=''},0,'digest')
network.exchange(s,{[0]='udlrc',functions=''},0,'digest')
s.frame={inputs={'','','','','','','',''}}
assert(network.exchange(s,{[0]='',functions=''},0,'digest'))
s.sent_checksum=0;s.checked=0
network.exchange(s,{[0]='',functions=''},0,'digest')
assert(messages[#messages].keys=='udlrc','network wait corrupted queued command')
