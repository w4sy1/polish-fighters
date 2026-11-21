local client=require('polish-fighters/online_client')
local controls=require('base/ui/controls')
local catalog=require('base/game/catalog')
local navigation=require('base/ui/navigation')
local screen={}
-- The project's own account and relay server; any other server can still be typed in.
screen.default_server='https://www.projektocalenie.pl/projekty/polish-fighters/api'
function screen.open(state,simple,lan)
 local doc=engine.read_settings() or {}
 state.hub_online={endpoint=client.origin or (type(doc.account_server)=='string' and doc.account_server:match('%S') and doc.account_server or screen.default_server),
  name='',password='',room='Pokój Polish Fighters',nick=type(doc.online_nick)=='string' and doc.online_nick:sub(1,24) or '',host='127.0.0.1',port='12345',
  page=1,nav=navigation.create(),previous={},simple=simple,lan=lan==true,address=''}
 if simple then client.notice='' end
end

function screen.resume(state, room)
 if type(room)~='table' or type(room.id)~='string' or room.profile~=catalog.profile_id then return end
 screen.open(state,true)
 client.listed_origin=nil
 state.hub_online.resume=room
 state.hub_online.joining=true
 state.hub_online.intent='list'
end
local function simple_rows(s)
 if s.missing_mod then
  if s.mod_job then return {{'mod_no','ANULUJ',287,406,220,38}} end
  return {{'mod_yes','TAK',182,406,181,38},{'mod_no','NIE',431,406,181,38}}
 end
 local rows={
  {'publish','UTWÓRZ POKÓJ',40,153,340,45},
  {'find','DOŁĄCZ',414,153,340,45},
 }
 if s.lan then
  rows[#rows+1]={'field:address','ADRES GOSPODARZA: '..s.address,40,270,714,38}
 elseif s.joining then
  local count=#client.rooms
  local pages=math.max(1,math.ceil(count/7))
  s.page=math.min(s.page,pages)
  local first=(s.page-1)*7+1
  for index=first,math.min(count,first+6) do
   local room=client.rooms[index]
   local label=client.room_title(room)
   if room.profile==catalog.profile_id then label='DOŁĄCZ  '..label
   else label='INNY MODUŁ  '..label end
   rows[#rows+1]={'join:'..index,label,40,250+(index-first)*32,714,30}
  end
  if s.page>1 then rows[#rows+1]={'prev','< POPRZEDNIE',280,500,210,34} end
  if s.page<pages then rows[#rows+1]={'next','NASTĘPNE >',520,500,234,34} end
 end
 rows[#rows+1]={'back','< WSTECZ',40,500,220,34}
 return rows
end
function screen.rows(s)
 if s.simple then return simple_rows(s) end
 local rows={{'field:endpoint','SERWER KONT: '..s.endpoint,40,100,714,32}}
 if not client.token and not s.accounts then
  -- Default: just a nickname, no password.
  rows[#rows+1]={'field:nick','TWÓJ NICK: '..s.nick,40,160,714,36}
  rows[#rows+1]={'play','GRAJ',40,215,340,40}
  rows[#rows+1]={'accounts','KONTO Z HASŁEM',414,215,340,40}
 elseif not client.token then
  rows[#rows+1]={'field:name','LOGIN: '..s.name,40,160,714,32}
  rows[#rows+1]={'field:password','HASŁO: '..string.rep('*',#s.password),40,205,714,32}
  rows[#rows+1]={'login','ZALOGUJ',40,260,220,34}
  rows[#rows+1]={'register','UTWÓRZ KONTO',280,260,220,34}
  rows[#rows+1]={'nickmode','GRAJ NICKIEM',520,260,234,34}
 else
  rows[#rows+1]={'field:room','NAZWA POKOJU: '..s.room,40,145,714,30}
  if client.relay_available then
   rows[#rows+1]={'info','GRA PRZEZ SERWER: bez adresu IP i przekierowania portów',40,182,714,30}
  else
   rows[#rows+1]={'field:host','ADRES GOSPODARZA (IPv4): '..s.host,40,182,500,30}
   rows[#rows+1]={'field:port','PORT: '..s.port,550,182,204,30}
  end
  rows[#rows+1]={'publish','OPUBLIKUJ I HOSTUJ',40,230,220,34}
  rows[#rows+1]={'refresh','ODŚWIEŻ POKOJE',280,230,220,34}
  rows[#rows+1]={'logout','WYLOGUJ',520,230,234,34}
  for index=(s.page-1)*4+1,math.min(#client.rooms,s.page*4) do
   local room=client.rooms[index]
   rows[#rows+1]={'join:'..index,client.room_title(room),40,310+(index-(s.page-1)*4-1)*34,714,30}
  end
  rows[#rows+1]={'prev','POPRZEDNIE',40,455,200,30}
  rows[#rows+1]={'next','NASTĘPNE',550,455,204,30}
 end
 rows[#rows+1]={'back','POWRÓT',40,500,220,34}
 rows[#rows+1]={'lan','POKÓJ LAN / TCP',520,500,234,34}
 return rows
end
local function network_action(state,context,join)
 if context.text_input then context.text_input(false) end
 if join then client.pending_join=join end
 state.hub_online=nil
 context.action('network')
end

local function switch_for_room(state,s,context,room,entry)
 local doc,problem=engine.read_settings()
 if problem then s.mod_message=tostring(problem);client.notice=s.mod_message;return end
 doc=type(doc)=='table' and doc or {}
 doc.little_fighters_room_resume={id=room.id,profile=room.profile}
 if state.hub_android then doc.little_fighters_start_profile=entry.id end
 local saved; saved,problem=engine.write_settings(doc)
 if not saved then s.mod_message=tostring(problem);client.notice=s.mod_message;return end
 state.hub_online=nil
 context.action('profile_'..entry.id)
end

local function poll_mod(state,s,context)
 local target=s.missing_mod
 if not s.mod_job then return end
 local result,problem=engine.mods('poll')
 if result=='pending' then
  if s.mod_job=='install' then
   local received,total,phase,files=engine.mods('progress')
   if phase==3 then s.mod_message='Instaluję pliki: '..tostring(files or 0)
   elseif phase==2 then s.mod_message='Sprawdzam podpis i SHA-256…'
   elseif total and total>0 then s.mod_message='Pobieranie: '..math.floor(100*(received or 0)/total)..'%' end
  end
  return
 end
 local job=s.mod_job;s.mod_job=nil
 if s.mod_cancelled then
  s.missing_mod,s.mod_cancelled,s.mod_message=nil,nil,nil
  client.notice='Anulowano dołączanie.';s.refresh_at=0
  return
 end
 if not result then s.mod_message='Błąd: '..client.utf8_prefix(problem or 'Instalacja przerwana.',76);return end
 if job=='catalogue' then
  for _,entry in ipairs(type(result.packages)=='table' and result.packages or {}) do
   if entry.id==target.room.profile then
    local ok;ok,problem=engine.mods('install',entry.id)
    if ok then s.mod_job='install';s.mod_message='Pobieram '..entry.name..'…'
    else s.mod_message='Błąd: '..client.utf8_prefix(problem,76) end
    return
   end
  end
  s.mod_message='Brak zgodnej paczki w podpisanym katalogu.'
 else
  switch_for_room(state,s,context,target.room,target.entry)
 end
end

local function cancel_simple(s)
 local pending=client.pending
 if pending and pending.purpose=='quick-join' then pending.cancelled=true end
 if pending and pending.operation=='publish-room' then client.cancel_publish=true end
 s.focus,s.intent,s.login_requested,s.joining,s.refresh_requested,s.publish_listed=nil,nil,nil,nil,nil,nil
end

local function tick_simple(state,s,context)
 if s.missing_mod then poll_mod(state,s,context);return end
 if s.lan or client.pending then return end
 if s.resume and client.listed_origin==s.endpoint then
  local target=s.resume;s.resume=nil;s.intent=nil
  for _,room in ipairs(client.rooms) do
   if room.id==target.id and room.profile==target.profile then s.intent=room;break end
  end
  if not s.intent then client.notice='Pokój został zamknięty lub jest pełny.';s.refresh_at=(engine.network_time() or 0)+5000;return end
 end
 if s.login_requested then
  s.login_requested=nil
  if not client.token then
   local conflict=client.last_login_error=='Nick in use' or client.last_login_error=='Nick taken by an account'
   if not conflict or s.guest_retry then s.intent=nil;return end
   s.guest_retry=true;s.nick=''
  elseif s.intent=='list' then
   -- Logging in already queues a room list in online_client.
   s.intent=nil
   s.refresh_at=(engine.network_time and engine.network_time() or 0)+5000
  end
 end
 if s.refresh_requested then
  s.refresh_requested=nil
  if client.listed_origin~=s.endpoint then s.intent=nil;return end
 end
 if not s.intent and not s.joining then return end
 if not client.token then
  if not s.intent then return end
  local nick=s.nick
  if not nick:match('^[A-Za-z0-9_]+$') or #nick<3 or #nick>24 then
   local stamp=engine.network_time and engine.network_time() or 0
   local tail=engine.random and engine.random(10000) or 0
   nick=string.format('Gosc_%06d%04d',math.floor(stamp)%1000000,tail)
  end
  local ok,problem=client.request(s.endpoint,'login',{nick=true,name=nick,nick_key=client.nick_key(s.endpoint)},'quick-login')
  if ok then s.login_requested=true else s.intent=nil;client.notice=tostring(problem) end
  return
 end
 local room=s.intent
 -- Publishing waits for a room list requested for this click, so the relay flag is current.
 if s.intent=='publish' and s.publish_listed and client.listed_origin==s.endpoint then
  s.publish_listed=nil
  s.intent=nil
  if not client.relay_available then client.notice='Przekaźnik niedostępny. Możesz utworzyć pokój w LAN.';return end
  client.publish_port=12345
  client.publish_relay=true
  local ok,problem=client.request(s.endpoint,'publish-room',{
   port=12345,name=client.listing_name(client.name,s.room),profile=catalog.profile_id,relay=true,
   capacity=require('polish-fighters/dashboard_model').current().room_capacity
  })
  if not ok then client.notice=tostring(problem) end
  return
 elseif type(room)=='table' then
  s.intent=nil
  if room.relay then
   local ok,problem=client.request(s.endpoint,'relay-ticket',{room=room.id,role='join'},'quick-join')
   if not ok then client.notice=tostring(problem) end
  else network_action(state,context,{host=false,address=room.host,port=room.port}) end
  return
 end
 local now=engine.network_time and engine.network_time() or 0
 if s.intent=='list' or s.intent=='publish' or s.joining and now>=(s.refresh_at or 0) then
  if s.intent=='list' then s.intent=nil end
  s.refresh_at=now+5000
  local ok,problem=client.request(s.endpoint,'list-rooms',{})
  if ok and s.intent=='publish' then s.refresh_requested=true;s.publish_listed=true
  elseif not ok then s.intent=nil;client.notice=tostring(problem) end
 end
end

local function activate_simple(state,s,id,context)
 if id=='back' then
  if context.text_input then context.text_input(false) end
  cancel_simple(s);state.hub_online=nil
 elseif id=='mod_yes' then
  if not s.mod_job and s.missing_mod then
   local ok,problem=engine.mods('catalogue')
   if ok then s.mod_job='catalogue';s.mod_message='Pobieram podpisany katalog…'
   elseif problem=='Mods handled by platform' then s.mod_message='Pobierz tę paczkę w Mod Managerze i wróć na listę.'
   else s.mod_message='Błąd: '..client.utf8_prefix(problem,76) end
  end
 elseif id=='mod_no' then
  if s.mod_job then
   s.mod_cancelled=true;s.mod_message='Anulowanie…'
   if s.mod_job=='install' then engine.mods('cancel') end
  else s.missing_mod,s.mod_message=nil,nil;s.refresh_at=0 end
 elseif id=='prev' or id=='next' then
  s.page=math.max(1,s.page+(id=='next' and 1 or -1))
 elseif id=='field:address' then s.focus='address'
 elseif id=='find' and s.lan then
  local address=(s.address or ''):match('^%s*(.-)%s*$')
  if address=='' then s.focus='address';return end
  local ip,port=address:match('^([%d.]+):(%d+)$')
  ip,port=ip or address,tonumber(port or '12345')
  if not client.ipv4(ip) or ip=='0.0.0.0' or ip:match('^127%.') or port<1 or port>65535 then
   client.notice='Wpisz IPv4 gospodarza, np. 192.168.1.82.';return
  end
  network_action(state,context,{host=false,address=ip,port=port,internet=false})
 elseif id=='publish' and s.lan then
  network_action(state,context,{host=true,address='0.0.0.0',port=12345,internet=false})
 elseif id=='find' or id=='publish' then
  if client.pending and client.pending.operation~='list-rooms' then return end
  s.focus=nil;s.joining=id=='find';s.intent=s.joining and 'list' or 'publish';s.guest_retry=nil;s.publish_listed=nil
  tick_simple(state,s,context)
 elseif id:sub(1,5)=='join:' then
  local room=client.rooms[tonumber(id:sub(6))]
  if not room or client.pending and client.pending.operation~='list-rooms' then return end
  if room.profile~=catalog.profile_id then
   for _,entry in ipairs(require('polish-fighters/hub').profiles) do
    if entry.profile==room.profile then
     if state.hub_available and state.hub_available[entry.id]==true then
      switch_for_room(state,s,context,room,entry)
     else s.missing_mod={room=room,entry=entry};s.mod_message=nil end
     return
    end
   end
   client.notice='Brak zgodnego modułu: '..client.utf8_prefix(room.profile,45);return
  end
  s.intent=room
  tick_simple(state,s,context)
 end
end
function screen.activate(state,id,context)
 local s=state.hub_online
 if not s then return end
 if s.simple then return activate_simple(state,s,id,context) end
 if id:sub(1,6)=='field:' then s.focus=id:sub(7);return end
 s.focus=nil
 if id=='accounts' then s.accounts=true;return elseif id=='nickmode' then s.accounts=nil;s.password='';return end
 if id=='back' then
  if context.text_input then context.text_input(false) end
  if client.pending and client.pending.operation=='publish-room' then client.cancel_publish=true end
  s.password='';state.hub_online=nil;return
 elseif id=='lan' then if context.text_input then context.text_input(false) end;state.hub_online=nil;context.action('network');return
 elseif id=='prev' then s.page=math.max(1,s.page-1);return
 elseif id=='next' then s.page=math.min(math.max(1,math.ceil(#client.rooms/4)),s.page+1);return end
 if client.pending then return end
 local ok,problem
 if id=='play' then
  if not s.nick:match('^[A-Za-z0-9_]+$') or #s.nick<3 or #s.nick>24 then
   client.notice='Nick: 3–24 znaki: litery bez polskich znaków, cyfry lub _.';return
  end
  ok,problem=client.request(s.endpoint,'login',{nick=true,name=s.nick,nick_key=client.nick_key(s.endpoint)})
 elseif id=='login' or id=='register' then
  if not s.name:match('^[A-Za-z0-9_]+$') or #s.name<3 or #s.name>24 or #s.password<12 then
   client.notice='Login: 3–24 litery/cyfry/_; hasło: 12–128 znaków.';return
  end
  ok,problem=client.request(s.endpoint,id,{name=s.name,password=s.password});s.password=''
 elseif id=='refresh' then ok,problem=client.request(s.endpoint,'list-rooms',{})
 elseif id=='logout' then ok,problem=client.logout()
 elseif id=='publish' then
  local port=tonumber(s.port)
  if not port or port%1~=0 or port<1024 or port>65535 then client.notice='Port: 1024–65535.';return end
  client.publish_port=port
  client.publish_relay=client.relay_available==true
  local payload={port=port,name=client.listing_name(client.name,s.room),profile=catalog.profile_id,
    capacity=require('polish-fighters/dashboard_model').current().room_capacity}
  if client.publish_relay then payload.relay=true else payload.host=s.host end
  ok,problem=client.request(s.endpoint,'publish-room',payload)
 elseif id:sub(1,5)=='join:' then
  local room=client.rooms[tonumber(id:sub(6))]
  if room.profile~=catalog.profile_id then client.notice='Najpierw uruchom zestaw '..room.profile;return end
  if room.relay then
   -- The ticket answer arrives asynchronously; online_client then opens the match screen.
   ok,problem=client.request(s.endpoint,'relay-ticket',{room=room.id,role='join'},'join')
   if not ok and problem then client.notice=tostring(problem) end
   return
  end
  if not client.ipv4(room.host) then client.notice='Ten klient wymaga adresu IPv4.';return end
  client.pending_join={host=false,address=room.host,port=room.port}
  state.hub_online=nil;context.action('network');return
 end
 if not ok and problem then client.notice=tostring(problem) end
end
function screen.update(state,input,context)
 local s=state.hub_online
 if client.navigate then client.navigate=nil;network_action(state,context);return end
 if s.simple then
  tick_simple(state,s,context)
  if not state.hub_online then return end
 end
 -- Shows the phone's on-screen keyboard while a field is selected.
 if context.text_input then context.text_input(s.focus~=nil and not client.pending) end
 if s.focus and not client.pending then
  local addition=input.text or ''
  if addition=='' then
   for code=32,222 do
    if input.keys[code] and not s.previous[code] then addition=addition..(controls.key_character(code,input.keys[16]) or '') end
   end
  end
  local limit=s.focus=='endpoint' and 512 or (s.focus=='password' and 128 or (s.focus=='nick' and 24 or 48))
  if s.focus=='nick' then
   -- Enter (also the soft keyboard's) plays straight away.
   if (input.keys[13] and not s.previous[13]) or addition:find('[\r\n]') then
    s.previous={};for code,value in pairs(input.keys) do s.previous[code]=value end
    screen.activate(state,'play',context);return
   end
   addition=addition:gsub('[^A-Za-z0-9_]','')
  elseif s.focus=='address' then
   if (input.keys[13] and not s.previous[13]) or addition:find('[\r\n]') then
    s.previous[13]=input.keys[13]
    screen.activate(state,'find',context);return
   end
   addition=addition:gsub('[^%d.:]','')
  end
  if input.keys[8] and not s.previous[8] then s[s.focus]=s[s.focus]:sub(1,-2) end
  s[s.focus]=(s[s.focus]..addition:gsub('[^ -~]','')):sub(1,limit)
 end
 s.previous={};for code,value in pairs(input.keys) do s.previous[code]=value end
 local rows=screen.rows(s);local targets={}
 for _,row in ipairs(rows) do targets[#targets+1]=navigation.target(row[3],row[4],row[3]+row[5],row[4]+row[6]) end
 local mapped=navigation.apply(s.nav,input,{page=s.missing_mod and 'online:mod' or 'online:list',
  targets=targets,default=1,autofocus=s.missing_mod~=nil,remember=true,locked=s.focus~=nil})
 s.focused=mapped.focused
 for index,box in ipairs(targets) do
  if mapped.click and mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then
   -- POWRÓT and LAN close the screen; a cancel in the same frame must not act on it again.
   screen.activate(state,rows[index][1],context);return
  end
 end
 if mapped.nav.cancel and state.hub_online then
  if s.focus then
   s.focus=nil
   if context.text_input then context.text_input(false) end
  else screen.activate(state,s.missing_mod and 'mod_no' or 'back',context) end
 end
end
function screen.draw(state,context)
 context.viewport(794,550,8,13,27);context.image('pe/menu_back1',0,0,true)
 context.fill(0,0,794,550,8,13,27,185)
 local s=state.hub_online
 context.text(s.simple and (s.lan and 'GRA W SIECI LOKALNEJ' or 'GRAJ PRZEZ INTERNET') or 'POLISH FIGHTERS / KONTO I POKOJE',397,25,'center',25,0xf0f5ff,nil,nil,true)
 if not s.simple then
 context.text((client.token or state.hub_online.accounts) and 'HTTPS dla serwera zdalnego. Hasło i sesja nie są zapisywane na dysku.'
  or 'Wpisz nick i kliknij GRAJ. Bez hasła i bez zakładania konta.',397,68,'center',13,0xadc3df,nil,nil,true)
 end
 if s.missing_mod then
  context.fill(133,251,528,209,98,181,239,255)
  context.fill(135,253,524,205,17,25,69,255)
  context.text('POBRAĆ BRAKUJĄCY MOD?',397,278,'center',23,0xf0f5ff,nil,nil,true)
  context.text(s.missing_mod.entry.title,397,320,'center',17,0xffdc82,nil,nil,true)
  context.text(s.mod_message or 'Po instalacji gra spróbuje dołączyć do pokoju.',397,359,'center',14,0xf0f5ff,nil,nil,true)
 end
 for index,row in ipairs(screen.rows(s)) do
  local active=row[1]=='field:'..tostring(s.focus) or index==s.focused
  context.fill(row[3],row[4],row[5],row[6],active and 42 or 22,active and 80 or 42,active and 120 or 68,230)
  context.text(s.simple and client.utf8_prefix(row[2],95) or row[2]:sub(-95),row[3]+10,row[4]+7,'left',13,0xf0f5ff,nil,nil,true)
 end
 if s.missing_mod then return end
 context.text(client.notice,397,s.simple and 214 or (client.token and 276 or 315),'center',12,0xffdc82,nil,nil,true)
 if s.simple and s.joining and not s.lan and #client.rooms==0 and client.listed_origin==s.endpoint then
  context.text('Brak otwartych pokoi. Lista aktualizuje się automatycznie.',397,260,'center',14,0xadc3df,nil,nil,true)
 end
 if client.recovery and not s.simple then
  context.text('Zapisz kod odzyskiwania: '..client.recovery,397,client.token and 293 or 355,'center',11,0xffdc82,nil,nil,true)
 end
end
return screen
