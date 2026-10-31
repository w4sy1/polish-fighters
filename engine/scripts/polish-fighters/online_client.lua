-- Account credentials and tokens live only in this Lua runtime, never in settings or replays.
local client={rooms={},notice='Podaj adres własnego serwera kont. Lokalny serwer: port 8765.'}
function client.request(endpoint,operation,payload)
 if client.pending then return nil,'Poczekaj na poprzednie żądanie.' end
 if client.token and endpoint~=client.origin then return nil,'Wyloguj się przed zmianą serwera.' end
 if not engine.account then return nil,'Ten build nie obsługuje kont.' end
 local body,problem
 if not payload or next(payload)==nil then body='{}' else body,problem=engine.json_encode(payload) end
 if not body then return nil,problem end
 local ok;ok,problem=engine.account('start',endpoint,operation,body,client.token or '')
 if not ok then return nil,problem end
 client.pending={operation=operation,endpoint=endpoint}
 client.notice='Łączenie z serwerem…'
 return true
end
function client.tick()
 if not client.pending then
  if client.cleanup_room and client.token then
   client.cleanup_room=nil;client.request(client.origin,'delete-room',{});return
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
 elseif operation=='list-rooms' then
  client.rooms={}
  for _,room in ipairs(type(result.rooms)=='table' and result.rooms or {}) do
   if #client.rooms<200 and type(room.host)=='string' and type(room.port)=='number' and
      room.port>=1024 and room.port<=65535 and room.port%1==0 and type(room.profile)=='string' then
    client.rooms[#client.rooms+1]=room
   end
  end
  client.notice='Pokojów: '..#client.rooms..'. Lista nie potwierdza dostępności gospodarzy.'
 elseif operation=='publish-room' then
  client.room=result.id;client.heartbeat=engine.network_time()+30000
  if client.cancel_publish then
   client.cancel_publish=nil;client.cleanup_room=true;client.navigate=nil;client.pending_join=nil
   client.notice='Anulowano publikację. Usuwanie ogłoszenia…';return
  end
  client.pending_join={host=true,address='0.0.0.0',port=client.publish_port}
  client.navigate=true;client.notice='Pokój opublikowany. Uruchamianie gospodarza…'
 elseif operation=='logout' then client.notice='Wylogowano.'
 elseif operation=='delete-room' then client.room=nil;client.notice='Usunięto ogłoszenie pokoju.'
 elseif operation=='heartbeat-room' then client.notice='Ogłoszenie pokoju odświeżone.'
 else client.notice='Zapisano.' end
end
function client.logout()
 local ok,problem=client.request(client.origin,'logout',{})
 if not ok then return nil,problem end
 client.token=nil;client.name=nil;client.rooms={};client.room=nil;client.recovery=nil
 return true
end
return client
