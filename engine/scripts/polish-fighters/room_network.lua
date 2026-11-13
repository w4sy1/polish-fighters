-- SPDX-License-Identifier: MIT
-- One local control set per device. The legacy two-endpoint session remains available.
return function(legacy)
 local room={}
 local timeout=30000
 local function fail(s,message)
  if tostring(message)=='simulation desynchronized' then
   message='Rozbieżny stan gry (simulation desynchronized). Sesja została bezpiecznie przerwana.'
  elseif tostring(message):lower():find('desynchronized',1,true) then
   message='Rozłączono: utrata połączenia, limit czasu lub różny stan gry (simulation desynchronized).'
  elseif tostring(message):lower():find('profile',1,true) then
   message='Niezgodny silnik, moduł lub dane gry. Użyj tej samej paczki testowej na obu urządzeniach.'
  elseif tostring(message):lower():find('timed out',1,true) then
   message='Brak odpowiedzi pokoju. Sprawdź IP, port TCP '..s.port..', wspólną sieć i zaporę gospodarza.'
  end
  engine.network("close");s.phase,s.error="failed",message;return nil,message
 end
 local function send(s,value)
  local encoded,problem=engine.json_encode(value)
  if not encoded then return fail(s,problem) end
  local ok;ok,problem=engine.network("send",encoded:gsub("\n","").."\n")
  if not ok then return fail(s,problem) end
  return true
 end
 function room.create(options)
  if not options.network_profile then
   local profile,problem=engine.network('profile');assert(profile,problem);options.network_profile=profile
  end
  return {room=true,phase="idle",profile=options.network_profile,port=options.network_port or 12345,
   capacity=require("polish-fighters/dashboard_model").current().room_capacity,
   received="",frames=0,sequence=0,version=options.recording_version}
 end
 function room.start(s,host,address)
  room.close(s);s.host=host;s.error=nil;s.names=nil;s.peers={};s.slot=nil;s.frames=0;s.sequence=0;s.sent_checksum=nil
  local value=host and (s.capacity..":"..s.profile..":"..address) or address
  local ok,problem=engine.network(host and "room_host" or "join",value,s.port)
  if not ok then return fail(s,problem) end
  s.phase="connecting";s.deadline=engine.network_time()+timeout;return true
 end
 function room.close(s)
  engine.network("close");s.phase="idle";s.pending=nil;s.received="";s.frame=nil;s.checked=nil;s.queued_unlock=0;s.queued_actions={};s.observed_actions={};s.queued_action_directions=nil;s.queued_back=nil;s.observed_back=nil
 end
 function room.ready(s,value) return send(s,{op="ready",value=value}) end
 function room.begin(s) return send(s,{op="start"}) end
 local function message(s,m)
  if m.op=="welcome" then s.slot=m.slot;s.capacity=m.capacity;s.phase="lobby"
  elseif m.op=="lobby" then s.peers=m.peers;s.capacity=m.capacity
  elseif m.op=="start" then
   -- Shared table independent of each device's boot time and local menu RNG draws.
   local seed=m.seed;local bytes={}
   for i=1,3000 do seed=(seed*16807)%2147483647;bytes[i]=string.char(seed%255+1) end
   engine.set_random_state(table.concat(bytes),0);engine.reset_random_sequence()
   s.names={};for i=1,8 do s.names[i]="" end
   for _,p in ipairs(s.peers) do s.names[p.slot+1]=p.name end
   s.phase="ready"
  elseif m.op=="frame" then
   if m.frame~=s.frames or s.frame then return fail(s,"Invalid room frame sequence") end
   s.frame=m
  elseif m.op=="checked" then
   if m.frame~=s.frames-1 then return fail(s,"Invalid room checksum sequence") end
   s.checked=m.frame
  elseif m.op=="abort" then return fail(s,m.reason)
  elseif m.op=="error" then
   if s.phase=="lobby" then s.notice=m.reason else return fail(s,m.reason) end
  end
  return true
 end
 function room.poll(s)
  if s.phase=="failed" then return nil,s.error end
  local bytes,problem=engine.network("poll");if not bytes then return fail(s,problem) end
  s.received=s.received..bytes
  if #s.received>16384 then return fail(s,"Room receive buffer exceeded") end
  if s.phase=="connecting" and engine.network("status")=="connected" then
   if not send(s,{op="hello",protocol=1,profile=s.profile,name=require("base/ui/controls").current().names[1]:sub(1,24)}) then return nil,s.error end
   s.phase="greeting"
  end
  while true do
   local line=s.received:find("\n",1,true);if not line then break end
   local decoded;decoded,problem=engine.json_decode(s.received:sub(1,line-1));s.received=s.received:sub(line+1)
   if not decoded then return fail(s,problem) end
   if not message(s,decoded) then return nil,s.error end
  end
  if s.phase=="connecting" or s.phase=="greeting" then
   if engine.network_time()>s.deadline then return fail(s,"Room connection timed out") end
  elseif s.phase=="lobby" and engine.network_time()>(s.ping or 0) then
   send(s,{op="ping"});s.ping=engine.network_time()+5000
  end
  return s.phase=="ready"
 end
 function room.exchange(s,input,hp,digest)
  -- Rendering keeps polling while a network frame is pending. Preserve short taps
  -- until the next packet is sent instead of losing them between two barriers.
  s.queued_actions=s.queued_actions or {}
  s.observed_actions=s.observed_actions or {}
  local command=require('base/game/team_commands').decode(input[0] or '')
  if command then s.queued_command=require('base/game/team_commands').signals[command] end
  local back=(input.functions or ''):find('4',1,true)~=nil
  if back and not s.observed_back then s.queued_back=true end
  s.observed_back=back
  for _,action in ipairs({'c','b','f'}) do
   local held=(input[0] or ''):find(action,1,true)~=nil
   if held and not s.observed_actions[action] then
    s.queued_actions[action]=true;s.queued_action_directions=(input[0] or ''):gsub('[^udlr]','')
   end
   s.observed_actions[action]=held
  end
  -- Preserve unlock events while the previous checksum barrier is still pending.
  local marks=input.unlock_bits or 0
  s.queued_unlock=s.queued_unlock or 0
  for _,bit in ipairs({1,2}) do
   if math.floor(marks/bit)%2==1 and math.floor(s.queued_unlock/bit)%2==0 then s.queued_unlock=s.queued_unlock+bit end
  end
  -- Report the completed previous simulation tick before submitting the next input.
  if s.frames>0 and s.sent_checksum~=s.frames-1 then
   if not send(s,{op="checksum",frame=s.frames-1,state=digest}) then return nil,s.error end
   s.sent_checksum=s.frames-1;s.deadline=engine.network_time()+timeout
  end
  local ok,problem=room.poll(s);if not ok then return nil,problem end
  if not s.pending then
   s.pending=true;s.deadline=engine.network_time()+timeout
   local functions=s.slot==0 and input.functions or ""
   if s.slot==0 and s.queued_back and not functions:find('4',1,true) then functions=functions..'4' end
   local keys=input[0] or ''
   for _,action in ipairs({'c','b','f'}) do
    if s.queued_actions[action] and not keys:find(action,1,true) then keys=keys..action end
   end
   if not keys:find('[udlr]') then keys=keys..(s.queued_action_directions or '') end
   keys=s.queued_command or keys
   if not send(s,{op="input",frame=s.frames,keys=keys,functions=functions,unlock=s.slot==0 and s.queued_unlock or 0}) then return nil,s.error end
   s.queued_command=nil
   s.queued_actions={};s.queued_action_directions=nil;s.queued_back=nil
   s.queued_unlock=0
  end
  -- The server queues this input behind the previous checksum barrier. Avoid a
  -- separate round trip before sending it, while retaining per-frame validation.
  if s.frames>0 and s.checked~=s.frames-1 then
   if engine.network_time()>s.deadline then return fail(s,"Room checksum timed out") end
   return nil
  end
  if not s.frame then
   if engine.network_time()>s.deadline then return fail(s,"Room input timed out") end
   return nil
  end
  local m=s.frame
  local combined={functions=m.functions or "",unlock_bits=m.unlock or 0,keys={},pointer_x=0,pointer_y=0,button=false,network=true}
  for i=0,7 do combined[i]=m.inputs[i+1] or "" end
  s.frame=nil;s.pending=nil;s.frames=s.frames+1;return combined
 end
 local create=legacy.create
 function legacy.create(options)
  if legacy.next_room or options.network_room then legacy.next_room=nil;return room.create(options) end
  return create(options)
 end
 for _,name in ipairs({"start","poll","close","exchange"}) do
  local original=legacy[name]
  legacy[name]=function(s,...) if s and s.room then return room[name](s,...) end;return original(s,...) end
 end
 legacy.room_ready=room.ready;legacy.room_begin=room.begin
 return legacy
end
