local messages={}
local now=0
engine={read_settings=function() return {} end,network_time=function() return now end,network=function(op)
 if op=='poll' then return '' end
 return true
end,json_encode=function(v) messages[#messages+1]=v;return '{}' end}
local legacy={create=function() return {} end,start=function() end,poll=function() end,close=function() end,exchange=function() end}
local network=dofile(arg[1]..'/engine/scripts/polish-fighters/room_network.lua')(legacy)
local function inputs(frame) local list={};for _,m in ipairs(messages) do if m.op=='input' and (not frame or m.frame==frame) then list[#list+1]=m end end;return list end
local function tick(s,frame,first) s.ticks[frame]={frame=frame,inputs={first or '','','','','','','',''}} end
local function session(slot,delay)
 network.next_room=true
 local s=network.create({network_profile=string.rep('a',64)})
 s.phase='ready';s.slot=slot;s.delay=delay or 0;s.ticks={};s.sent_frame=0
 return s
end

-- Input delay: frames 0..delay-1 are submitted empty, local input targets frame+delay.
messages={}
local s=session(0,3)
assert(not network.exchange(s,{[0]='r',functions=''},0,'digest'))
local sent=inputs()
assert(#sent==4 and sent[1].frame==0 and sent[3].frame==2 and sent[1].keys=='' and sent[4].frame==3 and sent[4].keys=='r',
 'delay prefill or first delayed input wrong')
assert(not network.exchange(s,{[0]='r',functions=''},0,'digest'))
assert(#inputs()==4,'waiting redraw resent an input')
tick(s,0);tick(s,1)
assert(network.exchange(s,{[0]='',functions=''},0,'digest') and s.frames==1)
assert(#inputs()==4,'frame 0 sample sent twice')
-- First sample of frame 1 targets frame 4, and the already-buffered tick 1 is used at once.
assert(network.exchange(s,{[0]='l',functions=''},0,'digest') and s.frames==2,'buffered tick not consumed without waiting')
assert(inputs(4)[1] and inputs(4)[1].keys=='l','next input not sent ahead')
assert(not network.exchange(s,{[0]='',functions=''},0,'digest') and s.frames==2,'missing tick advanced')
print('PASS room input: delay prefill, one input per frame, ticks buffered ahead')

-- Checksums are sent in the background every interval and never block.
messages={}
s=session(0,0);s.checksum_interval=30
for frame=0,59 do tick(s,frame);assert(network.exchange(s,{[0]='',functions=''},0,'d'..frame)) end
local checks={};for _,m in ipairs(messages) do if m.op=='checksum' then checks[#checks+1]=m.frame end end
assert(#checks==2 and checks[1]==0 and checks[2]==30,'checksum interval wrong: '..table.concat(checks,','))
print('PASS room checksum: every 30 frames, non-blocking')

-- Short taps and aim survive frames where the tick is still missing.
messages={}
s=session(1,0)
assert(not network.exchange(s,{[0]='',functions=''},0,'digest')) -- frame 0 sent empty, waiting
assert(not network.exchange(s,{[0]='rc',functions=''},0,'digest')) -- tap while waiting
tick(s,0)
assert(network.exchange(s,{[0]='',functions=''},0,'digest'))
assert(not network.exchange(s,{[0]='',functions=''},0,'digest'))
sent=inputs(1)[1]
assert(sent and sent.keys:find('c') and sent.keys:find('r'),'short aimed tap lost across network wait')
assert(next(s.queued_actions)==nil,'tap repeated after sending')
network.close(s);assert(next(s.queued_actions)==nil and not s.queued_action_directions)
print('PASS room input: tap and aim survive pending frame, send once, clear on disconnect')

messages={}
s=session(0,0)
assert(not network.exchange(s,{[0]='',functions=''},0,'digest'))
assert(not network.exchange(s,{[0]='',functions='4'},0,'digest'))
tick(s,0)
assert(network.exchange(s,{[0]='',functions=''},0,'digest'))
assert(not network.exchange(s,{[0]='',functions=''},0,'digest'))
assert(inputs(1)[1].functions=='4','short F4 lost across pending network frame')
assert(not s.queued_back,'F4 repeated after sending')
print('PASS short F4 survives a pending network frame')

messages={}
s=session(1,0)
assert(not network.exchange(s,{[0]='',functions=''},0,'digest'))
network.exchange(s,{[0]='f',functions=''},0,'digest')
network.exchange(s,{[0]='udlrc',functions=''},0,'digest')
tick(s,0)
assert(network.exchange(s,{[0]='',functions=''},0,'digest'))
network.exchange(s,{[0]='',functions=''},0,'digest')
assert(inputs(1)[1].keys=='udlrc','network wait corrupted queued command')

-- A peer that stops answering times out instead of freezing the match.
messages={}
s=session(1,2);now=0
assert(not network.exchange(s,{[0]='',functions=''},0,'digest'))
now=31000
local ok,problem=network.exchange(s,{[0]='',functions=''},0,'digest')
assert(not ok and problem and s.phase=='failed','stalled room did not time out')
now=0

-- The leader announces the chosen delay; LAN and internet defaults differ.
messages={}
network.next_room=true
s=network.create({network_profile=string.rep('a',64)});network.room_begin(s)
assert(messages[#messages].op=='start' and messages[#messages].delay==2,'LAN delay default')
network.next_room=true
s=network.create({network_profile=string.rep('a',64),network_internet=true});network.room_begin(s)
assert(messages[#messages].delay==6,'internet delay default')
print('PASS room start: leader announces LAN/internet input delay')

-- The flow computes the costly state digest only on frames that report it.
s=session(0,0);s.checksum_interval=30
local due={}
for frame=0,61 do
 if network.room_checksum_due(s) then due[#due+1]=s.frames end
 tick(s,frame);assert(network.exchange(s,{[0]='',functions=''},0,network.room_checksum_due(s) and 'd' or nil))
end
assert(#due==3 and due[1]==1 and due[2]==31 and due[3]==61,'digest due on wrong frames: '..table.concat(due,','))
print('PASS room checksum: digest needed only every 30 frames')
