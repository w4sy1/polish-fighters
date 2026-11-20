local client=require('polish-fighters/online_client')
local controls=require('base/ui/controls')
local catalog=require('base/game/catalog')
local navigation=require('base/ui/navigation')
local screen={}
-- The project's own account and relay server; any other server can still be typed in.
screen.default_server='https://www.projektocalenie.pl/projekty/polish-fighters/api'
function screen.open(state,simple)
 local doc=engine.read_settings() or {}
 state.hub_online={endpoint=client.origin or (type(doc.account_server)=='string' and doc.account_server:match('%S') and doc.account_server or screen.default_server),
  name='',password='',room='Pokój Polish Fighters',nick=type(doc.online_nick)=='string' and doc.online_nick:sub(1,24) or '',host='127.0.0.1',port='12345',
  page=1,nav=navigation.create(),previous={},simple=simple,lan=false}
 if simple then client.notice='' end
end
local function simple_rows(s)
 local rows={
  {'internet','INTERNET'..(s.lan and '' or ' [X]'),40,100,340,34},
  {'local','LAN / HOTSPOT'..(s.lan and ' [X]' or ''),414,100,340,34},
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

local function cancel_simple(s)
 local pending=client.pending
 if pending and pending.purpose=='quick-join' then pending.cancelled=true end
 if pending and pending.operation=='publish-room' then client.cancel_publish=true end
 s.focus,s.intent,s.login_requested,s.joining,s.refresh_requested=nil,nil,nil,nil,nil
end

local function tick_simple(state,s,context)
 if s.lan or client.pending then return end
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
 if s.intent=='publish' and client.listed_origin==s.endpoint then
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
  if ok and s.intent=='publish' then s.refresh_requested=true
  elseif not ok then s.intent=nil;client.notice=tostring(problem) end
 end
end

local function activate_simple(state,s,id,context)
 if id=='back' then
  if context.text_input then context.text_input(false) end
  cancel_simple(s);state.hub_online=nil
 elseif id=='local' or id=='internet' then
  if s.lan~=(id=='local') then
   cancel_simple(s)
   s.lan=id=='local';s.address=s.address or '';s.page=1;client.notice=''
  end
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
  s.focus=nil;s.joining=id=='find';s.intent=s.joining and 'list' or 'publish';s.guest_retry=nil
  tick_simple(state,s,context)
 elseif id:sub(1,5)=='join:' then
  local room=client.rooms[tonumber(id:sub(6))]
  if not room then return end
  if room.profile~=catalog.profile_id then client.notice='Najpierw wybierz moduł '..room.profile..'.';return end
  if client.pending and client.pending.operation~='list-rooms' then return end
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
 local mapped=navigation.apply(s.nav,input,{page='online:'..tostring(client.token~=nil),targets=targets,default=1})
 for index,box in ipairs(targets) do
  if mapped.click and mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then
   -- POWRÓT and LAN close the screen; a cancel in the same frame must not act on it again.
   screen.activate(state,rows[index][1],context);return
  end
 end
 if mapped.nav.cancel and state.hub_online then screen.activate(state,'back',context) end
end
function screen.draw(state,context)
 context.viewport(794,550,8,13,27);context.image('pe/menu_back1',0,0,true)
 context.fill(0,0,794,550,8,13,27,185)
 local s=state.hub_online
 context.text(s.simple and 'GRAJ PRZEZ INTERNET' or 'POLISH FIGHTERS / KONTO I POKOJE',397,25,'center',25,0xf0f5ff,nil,nil,true)
 if not s.simple then
 context.text((client.token or state.hub_online.accounts) and 'HTTPS dla serwera zdalnego. Hasło i sesja nie są zapisywane na dysku.'
  or 'Wpisz nick i kliknij GRAJ. Bez hasła i bez zakładania konta.',397,68,'center',13,0xadc3df,nil,nil,true)
 end
 for _,row in ipairs(screen.rows(state.hub_online)) do
  local active=row[1]=='field:'..tostring(state.hub_online.focus)
  context.fill(row[3],row[4],row[5],row[6],active and 42 or 22,active and 80 or 42,active and 120 or 68,230)
  context.text(s.simple and client.utf8_prefix(row[2],95) or row[2]:sub(-95),row[3]+10,row[4]+7,'left',13,0xf0f5ff,nil,nil,true)
 end
 context.text(client.notice,397,s.simple and 214 or (client.token and 276 or 315),'center',12,0xffdc82,nil,nil,true)
 if s.simple and s.joining and not s.lan and #client.rooms==0 and client.listed_origin==s.endpoint then
  context.text('Brak otwartych pokoi. Lista aktualizuje się automatycznie.',397,260,'center',14,0xadc3df,nil,nil,true)
 end
 if client.recovery and not s.simple then
  context.text('Zapisz kod odzyskiwania: '..client.recovery,397,client.token and 293 or 355,'center',11,0xffdc82,nil,nil,true)
 end
end
return screen
