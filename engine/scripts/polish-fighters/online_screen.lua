local client=require('polish-fighters/online_client')
local controls=require('base/ui/controls')
local catalog=require('base/game/catalog')
local navigation=require('base/ui/navigation')
local screen={}
function screen.open(state)
 local doc=engine.read_settings() or {}
 state.hub_online={endpoint=client.origin or (type(doc.account_server)=='string' and doc.account_server or 'http://127.0.0.1:8765'),
  name='',password='',room='Pokój Polish Fighters',host='127.0.0.1',port='12345',
  page=1,nav=navigation.create(),previous={}}
end
function screen.rows(s)
 local rows={{'field:endpoint','SERWER KONT: '..s.endpoint,40,100,714,32}}
 if not client.token then
  rows[#rows+1]={'field:name','LOGIN: '..s.name,40,160,714,32}
  rows[#rows+1]={'field:password','HASŁO: '..string.rep('*',#s.password),40,205,714,32}
  rows[#rows+1]={'login','ZALOGUJ',40,260,220,34}
  rows[#rows+1]={'register','UTWÓRZ KONTO',280,260,220,34}
 else
  rows[#rows+1]={'field:room','NAZWA POKOJU: '..s.room,40,145,714,30}
  rows[#rows+1]={'field:host','ADRES GOSPODARZA (IPv4): '..s.host,40,182,500,30}
  rows[#rows+1]={'field:port','PORT: '..s.port,550,182,204,30}
  rows[#rows+1]={'publish','OPUBLIKUJ I HOSTUJ',40,230,220,34}
  rows[#rows+1]={'refresh','ODŚWIEŻ POKOJE',280,230,220,34}
  rows[#rows+1]={'logout','WYLOGUJ',520,230,234,34}
  for index=(s.page-1)*4+1,math.min(#client.rooms,s.page*4) do
   local room=client.rooms[index]
   rows[#rows+1]={'join:'..index,tostring(room.name):gsub('[%c]',''):sub(1,48)..' / '..room.profile,40,310+(index-(s.page-1)*4-1)*34,714,30}
  end
  rows[#rows+1]={'prev','POPRZEDNIE',40,455,200,30}
  rows[#rows+1]={'next','NASTĘPNE',550,455,204,30}
 end
 rows[#rows+1]={'back','POWRÓT',40,500,220,34}
 rows[#rows+1]={'lan','POKÓJ LAN / TCP',520,500,234,34}
 return rows
end
function screen.activate(state,id,context)
 local s=state.hub_online
 if id:sub(1,6)=='field:' then s.focus=id:sub(7);return end
 s.focus=nil
 if id=='back' then
  if client.pending and client.pending.operation=='publish-room' then client.cancel_publish=true end
  s.password='';state.hub_online=nil;return
 elseif id=='lan' then state.hub_online=nil;context.action('network');return
 elseif id=='prev' then s.page=math.max(1,s.page-1);return
 elseif id=='next' then s.page=math.min(math.max(1,math.ceil(#client.rooms/4)),s.page+1);return end
 if client.pending then return end
 local ok,problem
 if id=='login' or id=='register' then
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
  ok,problem=client.request(s.endpoint,'publish-room',{host=s.host,port=port,name=s.room,
    profile=catalog.profile_id,capacity=require('polish-fighters/dashboard_model').current().room_capacity})
 elseif id:sub(1,5)=='join:' then
  local room=client.rooms[tonumber(id:sub(6))]
  if room.profile~=catalog.profile_id then client.notice='Najpierw uruchom zestaw '..room.profile;return end
  if not room.host:match('^%d+%.%d+%.%d+%.%d+$') then client.notice='Ten klient wymaga adresu IPv4.';return end
  client.pending_join={host=false,address=room.host,port=room.port}
  state.hub_online=nil;context.action('network');return
 end
 if not ok and problem then client.notice=tostring(problem) end
end
function screen.update(state,input,context)
 local s=state.hub_online
 if client.navigate then client.navigate=nil;state.hub_online=nil;context.action('network');return end
 if s.focus and not client.pending then
  local addition=input.text or ''
  if addition=='' then
   for code=32,222 do
    if input.keys[code] and not s.previous[code] then addition=addition..(controls.key_character(code,input.keys[16]) or '') end
   end
  end
  local limit=s.focus=='endpoint' and 512 or (s.focus=='password' and 128 or 48)
  if input.keys[8] and not s.previous[8] then s[s.focus]=s[s.focus]:sub(1,-2) end
  s[s.focus]=(s[s.focus]..addition:gsub('[^ -~]','')):sub(1,limit)
 end
 s.previous={};for code,value in pairs(input.keys) do s.previous[code]=value end
 local rows=screen.rows(s);local targets={}
 for _,row in ipairs(rows) do targets[#targets+1]=navigation.target(row[3],row[4],row[3]+row[5],row[4]+row[6]) end
 local mapped=navigation.apply(s.nav,input,{page='online:'..tostring(client.token~=nil),targets=targets,default=1})
 for index,box in ipairs(targets) do
  if mapped.click and mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then
   screen.activate(state,rows[index][1],context);break
  end
 end
 if mapped.nav.cancel then screen.activate(state,'back',context) end
end
function screen.draw(state,context)
 context.viewport(794,550,8,13,27);context.image('pe/menu_back1',0,0,true)
 context.fill(0,0,794,550,8,13,27,185)
 context.text('POLISH FIGHTERS / KONTO I POKOJE',397,25,'center',25,0xf0f5ff,nil,nil,true)
 context.text('HTTPS dla serwera zdalnego. Hasło i sesja nie są zapisywane na dysku.',397,68,'center',13,0xadc3df,nil,nil,true)
 for _,row in ipairs(screen.rows(state.hub_online)) do
  local active=row[1]=='field:'..tostring(state.hub_online.focus)
  context.fill(row[3],row[4],row[5],row[6],active and 42 or 22,active and 80 or 42,active and 120 or 68,230)
  context.text(row[2]:sub(-95),row[3]+10,row[4]+7,'left',13,0xf0f5ff,nil,nil,true)
 end
 context.text(client.notice,397,client.token and 276 or 315,'center',12,0xffdc82,nil,nil,true)
 if client.recovery then
  context.text('Zapisz kod odzyskiwania: '..client.recovery,397,client.token and 293 or 355,'center',11,0xffdc82,nil,nil,true)
 end
end
return screen
