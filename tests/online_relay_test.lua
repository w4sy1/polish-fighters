local response,wire,clock={},nil,0
local network_calls={}
local relay_status='0:0:'
engine={read_settings=function() return {} end,write_settings=function() return true end,
 json_encode=function(value) wire=value;return '{}' end,json_decode=function() return response end,
 account=function(action,endpoint,op,body,bearer)
  if action=='start' then wire={payload=wire,endpoint=endpoint,operation=op,bearer=bearer};return true end
  return 'json'
 end,network_time=function() return clock end,
 network=function(op,value,port)
  network_calls[#network_calls+1]={op=op,value=value,port=port}
  if op=='relay_status' then return relay_status end
  return true
 end}
local client=require('polish-fighters/online_client')
local ticket=string.rep('t',43)
assert(client.request('https://accounts.example','login',{name='test',password='long password 123'}))
response={token=string.rep('x',32),name='test'};client.tick()
-- Login refreshes the room list on its own, which reveals the relay.
client.tick();assert(client.pending and client.pending.operation=='list-rooms','no automatic room refresh after login')
response={relay=true,rooms={{id='r1',host='',relay=true,port=12345,profile='lf2-classic',name='Online'},
 {id='bad',host='',port=12345,profile='lf2-classic',name='No relay flag'}}}
client.tick()
assert(client.relay_available and #client.rooms==1 and client.rooms[1].relay,'relay room list')
-- Joining: the ticket answer becomes a relay join with the server-provided relay address.
assert(client.request(client.origin,'relay-ticket',{room='r1',role='join'},'join'))
response={ticket=ticket,relay={host='203.0.113.10',port=8766}};client.tick()
local join=client.pending_join
assert(join and not join.host and join.relay and join.relay.address=='203.0.113.10' and join.relay.port==8766 and join.relay.ticket==ticket and client.navigate)
client.pending_join=nil;client.navigate=nil
-- A malformed relay answer is refused.
assert(client.request(client.origin,'relay-ticket',{room='r1',role='join'},'join'))
response={ticket='short',relay={host='203.0.113.10',port=8766}};client.tick()
assert(not client.pending_join and client.notice:find('przekaźnika'))
assert(client.request(client.origin,'relay-ticket',{room='r1',role='join'},'join'))
response={ticket=ticket,relay={host='example.org',port=8766}};client.tick()
assert(not client.pending_join,'relay host must be numeric IPv4')
-- Hosting: publish without an address, listen on loopback, keep one relay channel waiting.
client.publish_port=12345;client.publish_relay=true
assert(client.request(client.origin,'publish-room',{}));response={id='mine'};client.tick()
assert(client.pending_join.host and client.pending_join.address=='127.0.0.1' and client.hosting_relay)
client.pending_join=nil;client.navigate=nil
clock=1000;client.maintain_relay({capacity=2})
assert(client.pending and client.pending.operation=='relay-ticket' and client.pending.purpose=='host','host channel not requested')
response={ticket=ticket,relay={host='203.0.113.10',port=8766}};client.tick()
local offer=network_calls[#network_calls]
assert(offer.op=='relay_offer' and offer.value=='203.0.113.10:'..ticket and offer.port==8766,'host channel not offered')
relay_status='1:0:';clock=3000;client.maintain_relay({capacity=2})
assert(not client.pending,'second waiting channel requested')
relay_status='0:1:';clock=5000;client.maintain_relay({capacity=2})
assert(not client.pending,'full two-device room requested another channel')
relay_status='0:1:';clock=7000;client.maintain_relay({capacity=4})
assert(client.pending and client.pending.purpose=='host','larger room did not request the next channel')
print('PASS online relay: auto refresh, relay rooms, join ticket, host channels kept at one waiting')
