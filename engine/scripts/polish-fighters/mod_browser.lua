-- Registry browsing only; presence here is not evidence of availability or compatibility.
local entries=require('polish-fighters/mod_catalog')
local locale=require('polish-fighters/menu_locale')
local navigation=require('base/ui/navigation')
local controls=require('base/ui/controls')
local screen={}
local categories={'all','classic','naruto','dragon-ball','bleach','one-piece','anime','gameplay'}
local words={
 pl={title='KATALOG MODÓW',search='SZUKAJ: ',category='KATEGORIA: ',all='Wszystkie',classic='Klasyczne LF',naruto='Naruto',['dragon-ball']='Dragon Ball',bleach='Bleach',['one-piece']='One Piece',anime='Inne anime',gameplay='Mechanika',prev='POPRZEDNIE',next='NASTĘPNE',back='WSTECZ',unknown='Niepotwierdzone',note='Rejestr nazw. Linki, dostępność i zgodność nie zostały jeszcze sprawdzone.',status='Zgodność: nieprzetestowany',empty='Brak wyników',author='Autor: ',version='Wersja: ',source='Źródło: ',actions='Pobieranie i instalacja w grze: kolejny etap.',search_hint='Szukaj po nazwie, autorze lub postaci. Enter kończy wpisywanie.'},
 en={title='MOD CATALOGUE',search='SEARCH: ',category='CATEGORY: ',all='All',classic='Classic LF',naruto='Naruto',['dragon-ball']='Dragon Ball',bleach='Bleach',['one-piece']='One Piece',anime='Other anime',gameplay='Gameplay',prev='PREVIOUS',next='NEXT',back='BACK',unknown='Unverified',note='Name registry. Links, availability and compatibility have not been verified yet.',status='Compatibility: not tested',empty='No results',author='Author: ',version='Version: ',source='Source: ',actions='In-game downloading and installation: next stage.',search_hint='Search name, author or character. Enter finishes editing.'}
}
local function strings() return words[locale.id()] end
function screen.open(state)
 state.hub_mods={query='',category=1,page=1,nav=navigation.create(),previous={}}
end
function screen.filtered(s)
 local out={};local query=s.query:lower();local category=categories[s.category]
 for _,entry in ipairs(entries) do
  local haystack=(entry.name..' '..(entry.author or '')..' '..(entry.characters or '')):lower()
  if (category=='all' or entry.category==category) and haystack:find(query,1,true) then out[#out+1]=entry end
 end
 return out
end
function screen.rows(s)
 local w=strings()
 if s.detail then return {{'back',w.back,30,480,220,32}} end
 local rows={{'search',w.search..s.query,30,82,734,32},{'category',w.category..w[categories[s.category]],30,125,734,32}}
 local filtered=screen.filtered(s);s.page=math.max(1,math.min(s.page,math.max(1,math.ceil(#filtered/7))))
 for i=(s.page-1)*7+1,math.min(#filtered,s.page*7) do
  rows[#rows+1]={'mod:'..filtered[i].id,filtered[i].name,30,170+(i-(s.page-1)*7-1)*37,734,32}
 end
 rows[#rows+1]={'prev',w.prev,30,445,230,32};rows[#rows+1]={'next',w.next,280,445,230,32}
 rows[#rows+1]={'back',w.back,534,445,230,32}
 return rows
end
function screen.activate(state,id,context)
 local s=state.hub_mods
 if id=='back' then
  if s.edit then s.edit=false elseif s.detail then s.detail=nil else state.hub_mods=nil end
 elseif id=='search' then s.edit=not s.edit
 elseif id=='category' then s.category=s.category%#categories+1;s.page=1
 elseif id=='prev' then s.page=math.max(1,s.page-1)
 elseif id=='next' then s.page=math.min(math.max(1,math.ceil(#screen.filtered(s)/7)),s.page+1)
 elseif id:sub(1,4)=='mod:' then
  for _,entry in ipairs(entries) do if entry.id==id:sub(5) then s.detail=entry;s.edit=false;break end end
 end
 if context.text_input then context.text_input(state.hub_mods~=nil and s.edit==true) end
end
function screen.update(state,input,context)
 local s=state.hub_mods;local keys=input.keys or {}
 if s.edit then
  local addition=input.text or ''
  if addition=='' then
   for code=32,222 do if keys[code] and not s.previous[code] then addition=addition..(controls.key_character(code,keys[16]) or '') end end
  end
  if keys[8] and not s.previous[8] then s.query=s.query:sub(1,-2) end
  s.query=(s.query..addition:gsub('[^ -~]','')):sub(1,80);s.page=1
  if (keys[13] and not s.previous[13]) or (keys[27] and not s.previous[27]) then
   s.edit=false;if context.text_input then context.text_input(false) end
  end
  s.previous={};for k,v in pairs(keys) do s.previous[k]=v end
  return
 end
 s.previous={};for k,v in pairs(keys) do s.previous[k]=v end
 local rows=screen.rows(s);local targets={}
 for _,row in ipairs(rows) do targets[#targets+1]=navigation.target(row[3],row[4],row[3]+row[5],row[4]+row[6]) end
 local mapped=navigation.apply(s.nav,input,{page='mods:'..s.page..':'..s.category..':'..tostring(s.detail and s.detail.id),targets=targets,default=1})
 for index,box in ipairs(targets) do
  if mapped.click and mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then screen.activate(state,rows[index][1],context);break end
 end
 if state.hub_mods and mapped.nav.cancel then screen.activate(state,'back',context) end
end
function screen.draw(state,context)
 local s=state.hub_mods;local w=strings()
 context.viewport(794,550,4,10,65);context.image('pe/menu_back1',0,0,true);context.fill(0,0,794,550,4,10,65,210)
 local function text(value,x,y,size,color,align) context.text(value,x,y,align or 'left',size,color or 0xf4f5ff,nil,nil,true) end
 text(w.title,397,24,24,nil,'center')
 if s.detail then
  local e=s.detail;text(e.name,30,100,20)
  text(w.author..(e.author or w.unknown),30,155,15);text(w.version..(e.version or w.unknown),30,190,15)
  text(w.source..(e.source or w.unknown),30,225,15);text(w.status,30,260,15,0xffdc82)
  text(w.actions,30,330,14)
 else
  local note=locale.id()=='pl' and 'Dane źródłowe częściowo potwierdzone. Dostępność plików i zgodność: nieprzetestowane.' or 'Some source metadata is verified. File availability and compatibility: not tested.'
  text(note,397,58,12,0xffdc82,'center')
  local filtered=screen.filtered(s)
  text(#filtered..' / '..#entries..'   |   '..s.page..' / '..math.max(1,math.ceil(#filtered/7)),397,488,13,nil,'center')
  if #filtered==0 then text(w.empty,397,220,16,nil,'center') end
 end
 for _,row in ipairs(screen.rows(s)) do
  context.fill(row[3],row[4],row[5],row[6],122,157,255)
  context.fill(row[3]+2,row[4]+2,row[5]-4,row[6]-4,16,33,100)
  text(row[2],row[3]+10,row[4]+7,14)
 end
 if s.edit then text(w.search_hint,30,521,12,0xffdc82) end
end
return screen
