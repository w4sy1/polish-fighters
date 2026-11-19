-- Account credentials and tokens live only in this Lua runtime, never in settings or replays.
local client={rooms={},notice='Serwer gry jest ustawiony. Zaloguj się albo utwórz konto.'}
local function ipv4(value)
 if type(value)~='string' then return false end
 local a,b,c,d=value:match('^(%d+)%.(%d+)%.(%d+)%.(%d+)$')
 if not a then return false end
 for _,part in ipairs({a,b,c,d}) do if tonumber(part)>255 then return false end end
 return true
end
client.ipv4=ipv4
-- Players see and type the project page; its API lives in the page's /api folder.
local project_page='https://www.projektocalenie.pl/projekty/polish-fighters'
function client.api_endpoint(endpoint)
 local trimmed=tostring(endpoint or ''):gsub('/+$','')
 if trimmed==project_page or trimmed==project_page:gsub('://www%.','://') then return trimmed..'/api' end
 return endpoint
end
function client.request(endpoint,operation,payload,purpose)
 if client.pending then return nil,'Poczekaj na poprzednie żądanie.' end
 if client.token and endpoint~=client.origin then return nil,'Wyloguj się przed zmianą serwera.' end
 if not engine.account then return nil,'Ten build nie obsługuje kont.' end
 local body,problem
 if not payload or next(payload)==nil then body='{}' else body,problem=engine.json_encode(payload) end
 if not body then return nil,problem end
 local ok;ok,problem=engine.account('start',client.api_endpoint(endpoint),operation,body,client.token or '')
 if not ok then return nil,problem end
 client.pending={operation=operation,endpoint=endpoint,purpose=purpose}
 client.notice='Łączenie z serwerem…'
 return true
end
function client.tick()
 if not client.pending then
  if client.cleanup_room and client.token then
   client.cleanup_room=nil;client.request(client.origin,'delete-room',{});return
  end
  if client.auto_refresh and client.token then
   client.auto_refresh=nil;client.request(client.origin,'list-rooms',{});return
  end
  if client.token and client.room and engine.network_time()>=(client.heartbeat or 0) then
   client.heartbeat=engine.network_time()+30000
   client.request(client.origin,'heartbeat-room',{room=client.room})
  end
  return
 end
 local raw,problem=engine.account('poll')
 if raw=='pending' then return end
 local pending=client.pending;client.pending=nil
 if not raw then client.notice=tostring(problem);return end
 local result;result,problem=engine.json_decode(raw)
 if type(result)~='table' then client.notice='Nieprawidłowa odpowiedź serwera.';return end
 if result.error then
  if pending.operation=='publish-room' then client.cancel_publish=nil end
  client.notice='Błąd serwera: '..tostring(result.error):sub(1,140)
  if result.error=='Session required' then client.token=nil;client.room=nil;client.rooms={} end
  return
 end
 local operation=pending.operation
 if operation=='login' or operation=='register' then
  if type(result.token)~='string' or #result.token>128 then client.notice='Brak poprawnego tokenu sesji.';return end
  client.token,client.origin,client.name=result.token,pending.endpoint,result.name
  local document,read_problem=engine.read_settings()
  if not read_problem then
   if type(document)~='table' then document={} end
   document.account_server=pending.endpoint
   engine.write_settings(document)
  end
  client.recovery=result.recovery_code
  client.notice='Zalogowano jako '..tostring(result.name)
  client.auto_refresh=true
 elseif operation=='list-rooms' then
  client.rooms={}
  client.relay_available=result.relay==true
  for _,room in ipairs(type(result.rooms)=='table' and result.rooms or {}) do
   if #client.rooms<200 and type(room.host)=='string' and type(room.port)=='number' and
      ((room.relay==true and type(room.id)=='string') or ipv4(room.host)) and
      room.port>=1024 and room.port<=65535 and room.port%1==0 and type(room.profile)=='string' then
    client.rooms[#client.rooms+1]=room
   end
  end
  client.notice='Pokojów: '..#client.rooms..(client.relay_available and '. Gra przez serwer pośredniczący.' or '. Lista nie potwierdza dostępności gospodarzy.')
 elseif operation=='publish-room' then
  client.room=result.id;client.heartbeat=engine.network_time()+30000
  if client.cancel_publish then
   client.cancel_publish=nil;client.cleanup_room=true;client.navigate=nil;client.pending_join=nil
   client.notice='Anulowano publikację. Usuwanie ogłoszenia…';return
  end
  -- Relay rooms accept players only through the relay, so the host listens on loopback.
  client.pending_join={host=true,address=client.publish_relay and '127.0.0.1' or '0.0.0.0',port=client.publish_port}
  client.hosting_relay=client.publish_relay
  client.navigate=true;client.notice='Pokój opublikowany. Uruchamianie gospodarza…'
 elseif operation=='logout' then client.notice='Wylogowano.'
 elseif operation=='delete-room' then client.room=nil;client.notice='Usunięto ogłoszenie pokoju.'
 elseif operation=='heartbeat-room' then client.notice='Ogłoszenie pokoju odświeżone.'
 elseif operation=='relay-ticket' then
  local relay=type(result.relay)=='table' and result.relay or {}
  if type(result.ticket)~='string' or not result.ticket:match('^[%w_%-]+$') or #result.ticket<16 or #result.ticket>128 or
     not ipv4(relay.host) or type(relay.port)~='number' or relay.port%1~=0 or relay.port<1 or relay.port>65535 then
   client.notice='Serwer nie podał poprawnego przekaźnika.';return
  end
  if pending.purpose=='host' then
   local ok,offer_problem=engine.network('relay_offer',relay.host..':'..result.ticket,relay.port)
   if not ok then client.notice='Przekaźnik: '..tostring(offer_problem) end
  else
   client.pending_join={host=false,address=relay.host,port=relay.port,relay={address=relay.host,port=relay.port,ticket=result.ticket}}
   client.navigate=true;client.notice='Łączenie przez serwer…'
  end
 else client.notice='Zapisano.' end
end
-- Host side of a relay room: keep exactly one relay channel waiting for the next player.
function client.maintain_relay(session)
 if not (client.hosting_relay and client.token and client.room) or client.pending then return end
 if engine.network_time()<(client.relay_check or 0) then return end
 client.relay_check=engine.network_time()+1000
 local status=engine.network('relay_status')
 local waiting,active=tostring(status or ''):match('^(%d+):(%d+):')
 waiting,active=tonumber(waiting) or 0,tonumber(active) or 0
 local capacity=session and session.capacity or 2
 if waiting==0 and active<capacity-1 then
  client.request(client.origin,'relay-ticket',{room=client.room,role='host'},'host')
 end
end
function client.logout()
 local ok,problem=client.request(client.origin,'logout',{})
 if not ok then return nil,problem end
 client.token=nil;client.name=nil;client.rooms={};client.room=nil;client.recovery=nil;client.hosting_relay=nil
 return true
end
return client
