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
print('PASS LAN: lazy identity, reuse, IPv4/port validation, remote target, wildcard host')
