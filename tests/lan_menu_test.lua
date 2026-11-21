local calls={}
engine={network_time=function() return 0 end,network=function(op)
 calls[#calls+1]=op
 if op=='profile' then return string.rep('a',64) end
 return true
end,read_settings=function() return {} end}
local transport=require('base/game/network')
local options={recording_version=1}
local session=transport.create(options)
assert(#session.profile>64 and calls[1]=='profile','deferred identity must be requested before networking')
transport.create(options);assert(#calls==1,'identity must be reused within the profile')
local started
transport.create=function() return {port=12345} end
transport.start=function(s,host,address) started={host=host,address=address,port=s.port};return true end
local screen=require('base/ui/network')
local state=screen.create({})
for _,address in ipairs({'','127.0.0.1','0.0.0.0','256.1.1.1','1.2.3','1.2.3.4:0','1.2.3.4:65536'}) do
 started=nil;screen.begin(state,false,address)
 assert(not started and state.message,'invalid target accepted: '..address)
end
screen.begin(state,false,'192.168.1.82:23456')
assert(started.address=='192.168.1.82' and started.port==23456 and state.page=='waiting')
screen.begin(state,true,'0.0.0.0');assert(started.host and started.address=='0.0.0.0')
-- The LAN host sees its own addresses; a relay host (loopback) does not ask for them.
local real_network=engine.network
engine.network=function(op) if op=='addresses' then return '192.168.1.82 10.0.0.5' end return real_network(op) end
screen.begin(state,true,'0.0.0.0');assert(state.host_addresses=='192.168.1.82, 10.0.0.5','LAN host lost its own IP')
local drawn={}
local font=require('base/ui/font')
local gdi=font.gdi
font.gdi=function(_,text) drawn[#drawn+1]=text end
local draw_context={viewport=function() end,image=function() end,sprite=function() end,fill=function() end}
state.session.host,state.session.slot,state.session.peers,state.session.capacity=true,0,{},2
for _,page in ipairs({'waiting','lobby'}) do
 state.page=page;drawn={};screen.draw(state,draw_context)
 assert(table.concat(drawn,'|'):find('192.168.1.82, 10.0.0.5',1,true),'host IP missing on '..page)
end
local headings={}
local draw=font.draw
font.draw=function(_,text) headings[#headings+1]=text end
state.session.internet=true
screen.begin(state,true,'127.0.0.1')
state.session.slot,state.session.peers,state.session.capacity=0,{},2
for _,page in ipairs({'waiting','lobby','internet_error'}) do
 state.page=page;drawn={};headings={}
 state.message='Przekroczono czas oczekiwania na przekaźnik.'
 screen.draw(state,draw_context)
 local labels=table.concat(drawn,'|')
 for _,lan_only in ipairs({'TCP','IP:','wspólną sieć','hotspot'}) do
  assert(not labels:find(lan_only,1,true),'Internet screen leaked LAN instructions: '..lan_only)
 end
 if page=='lobby' then assert(headings[1]:find('INTERNETOWY',1,true)) end
end
local action
screen.update(state,{keys={[27]=true},pointer_x=0,pointer_y=0},{action=function(name) action=name end,sound=function() end})
assert(action=='launch','Esc must return from an Internet error')
state.session.relay={address='127.0.0.1',ticket='test-ticket'}
screen.begin(state,false,'127.0.0.1')
assert(state.page=='waiting' and not started.host and started.address=='127.0.0.1')
state.session.relay=nil
font.draw=draw
state.session.internet=nil
font.gdi=gdi
screen.begin(state,true,'127.0.0.1');assert(not state.host_addresses,'relay host showed LAN addresses')
engine.network=function(op) if op=='addresses' then return '' end return real_network(op) end
screen.begin(state,true,'0.0.0.0');assert(not state.host_addresses)
engine.network=real_network
print('PASS LAN: lazy identity, reuse, IPv4/port validation, remote target, wildcard host, host IP shown')
