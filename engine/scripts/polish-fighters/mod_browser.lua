-- Registry browsing only; presence here is not evidence of availability or compatibility.
local entries=require('polish-fighters/mod_catalog')
local locale=require('polish-fighters/menu_locale')
local navigation=require('base/ui/navigation')
local controls=require('base/ui/controls')
local screen={}
local categories={'all','classic','naruto','dragon-ball','bleach','one-piece','anime','gameplay'}
local words={
 pl={title='KATALOG MODÓW',search='SZUKAJ: ',category='KATEGORIA: ',all='Wszystkie',classic='Klasyczne LF',naruto='Naruto',['dragon-ball']='Dragon Ball',bleach='Bleach',['one-piece']='One Piece',anime='Inne anime',gameplay='Mechanika',prev='POPRZEDNIE',next='NASTĘPNE',back='WSTECZ',unknown='Niepotwierdzone',note='Rejestr nazw. Linki, dostępność i zgodność nie zostały jeszcze sprawdzone.',status='Zgodność: nieprzetestowany',empty='Brak wyników',author='Autor: ',version='Wersja: ',source='Źródło: ',actions='Gotowe, podpisane mody pobierzesz w: POLISH FIGHTERS - GITHUB.',search_hint='Szukaj po nazwie, autorze lub postaci. Enter kończy wpisywanie.',github='POLISH FIGHTERS - GITHUB',refresh='ODŚWIEŻ KATALOG',gh_title='POLISH FIGHTERS - GITHUB',gh_loading='Pobieram podpisany katalog...',gh_ready='Podpis katalogu poprawny. Wybierz mod, aby go pobrać i zainstalować.',gh_download='Pobieranie: ',gh_verify='Sprawdzam podpis i SHA-256...',gh_unpack='Instaluję pliki: ',gh_done='Zainstalowano: ',gh_failed='Błąd: ',gh_android='Na Androidzie mody z GitHuba instaluje ekran Mody w menu głównym.',gh_installed=' [zainstalowany]',gh_restart='Wybierz go w menu modułów.'},
 en={title='MOD CATALOGUE',search='SEARCH: ',category='CATEGORY: ',all='All',classic='Classic LF',naruto='Naruto',['dragon-ball']='Dragon Ball',bleach='Bleach',['one-piece']='One Piece',anime='Other anime',gameplay='Gameplay',prev='PREVIOUS',next='NEXT',back='BACK',unknown='Unverified',note='Name registry. Links, availability and compatibility have not been verified yet.',status='Compatibility: not tested',empty='No results',author='Author: ',version='Version: ',source='Source: ',actions='Ready, signed mods are in: POLISH FIGHTERS - GITHUB.',search_hint='Search name, author or character. Enter finishes editing.',github='POLISH FIGHTERS - GITHUB',refresh='REFRESH CATALOGUE',gh_title='POLISH FIGHTERS - GITHUB',gh_loading='Downloading the signed catalogue...',gh_ready='Catalogue signature verified. Choose a mod to download and install it.',gh_download='Downloading: ',gh_verify='Checking signature and SHA-256...',gh_unpack='Installing files: ',gh_done='Installed: ',gh_failed='Error: ',gh_android='On Android, GitHub mods are installed from the Mods screen in the main menu.',gh_installed=' [installed]',gh_restart='Select it in the module menu.'}
}
local function strings() return words[locale.id()] end
-- Polish Fighters — GitHub: signed catalogue and installer provided by the engine (engine.mods).
local profile_tags={lf_four_turbo='lf_four_turbo',dbz='dbz',one_piece='one_piece',kate='kate',reinforced='reinforced',
 ntsd='ntsd',bleach='bleach',polish_fighters='polish_fighters',all='mixed'}
local function mods_api() return engine and engine.mods end
local function github_start(s)
 local w=strings();local api=mods_api();s.github={packages={},status=w.gh_loading}
 if not api then s.github.status=w.gh_android;return end
 local ok,err=api('catalogue')
 if ok==true then s.github.busy='catalogue' else s.github.status=w.gh_failed..tostring(err or '') end
 if err=='Mods handled by platform' then s.github.status=w.gh_android end
end
local function github_install(s,id)
 local api=mods_api();local g=s.github;if not api or g.busy then return end
 local ok,err=api('install',id)
 if ok==true then g.busy='install';g.target=id;g.status=strings().gh_download..'0%' else g.status=strings().gh_failed..tostring(err or '') end
end
local function size_label(bytes) return string.format('%.1f MB',(tonumber(bytes) or 0)/1048576) end
local function github_poll(state)
 local s=state.hub_mods;local g=s and s.github;local api=mods_api()
 if not g or not g.busy or not api then return end
 local w=strings();local result,err=api('poll')
 if result=='pending' then
  if g.busy=='install' then
   local received,total,phase,files=api('progress')
   g.fraction=(tonumber(total) or 0)>0 and (tonumber(received) or 0)/total or 0
   if phase==2 then g.status=w.gh_verify elseif phase==3 then g.status=w.gh_unpack..tostring(files or 0)
   else g.status=w.gh_download..math.floor(g.fraction*100)..'% ('..size_label(received)..' / '..size_label(total)..')' end
  end
  return
 end
 local busy=g.busy;g.busy=nil
 if result==nil then g.status=w.gh_failed..tostring(err or '');return end
 if busy=='catalogue' then
  g.packages=type(result)=='table' and type(result.packages)=='table' and result.packages or {}
  table.sort(g.packages,function(a,b) return tostring(a.name)<tostring(b.name) end)
  g.status=w.gh_ready
 else
  g.fraction=1;g.installed=g.installed or {};g.installed[g.target]=true
  local name=g.target
  for _,entry in ipairs(g.packages) do if entry.id==g.target then name=entry.name
   local tag=profile_tags[entry.profile or '']
   if tag and state.hub_available then state.hub_available[tag]=true end
  end end
  g.status=w.gh_done..tostring(name)..'. '..w.gh_restart
 end
end
screen.github_poll=github_poll
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
 if s.github then
  local rows={}
  for i,entry in ipairs(s.github.packages) do
   if i>9 then break end
   local mark=(s.github.installed and s.github.installed[entry.id]) and w.gh_installed or ''
   rows[#rows+1]={'gh:'..entry.id,tostring(entry.name)..'  ('..size_label(entry.size_bytes)..')'..mark,30,96+(i-1)*36,734,32}
  end
  rows[#rows+1]={'gh_refresh',w.refresh,30,445,300,32};rows[#rows+1]={'back',w.back,534,445,230,32}
  return rows
 end
 local rows={{'search',w.search..s.query,30,82,470,32},{'github',w.github,514,82,250,32},{'category',w.category..w[categories[s.category]],30,125,734,32}}
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
  if s.edit then s.edit=false elseif s.detail then s.detail=nil elseif s.github then s.github=nil else state.hub_mods=nil end
 elseif id=='github' or id=='gh_refresh' then
  if not (s.github and s.github.busy) then github_start(s) end
  -- Android installs from its native Mods screen; leave the game loop to open it.
  if s.github and s.github.status==strings().gh_android and state.hub_android and context.action then
   local opened,problem=require('polish-fighters/hub').open_android_mods(context)
   if not opened then s.github.status=strings().gh_failed..tostring(problem or '') end
  end
 elseif id:sub(1,3)=='gh:' then github_install(s,id:sub(4))
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
 github_poll(state)
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
 local mapped=navigation.apply(s.nav,input,{page='mods:'..s.page..':'..s.category..':'..tostring(s.detail and s.detail.id)..(s.github and ':gh' or ''),targets=targets,default=1})
 for index,box in ipairs(targets) do
  if mapped.click and mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then screen.activate(state,rows[index][1],context);break end
 end
 if state.hub_mods and mapped.nav.cancel then screen.activate(state,'back',context) end
end
function screen.draw(state,context)
 local s=state.hub_mods;local w=strings()
 context.viewport(794,550,4,10,65);context.image('pe/menu_back1',0,0,true);context.fill(0,0,794,550,4,10,65,210)
 local function text(value,x,y,size,color,align) context.text(value,x,y,align or 'left',size,color or 0xf4f5ff,nil,nil,true) end
 text(s.github and w.gh_title or w.title,397,24,24,nil,'center')
 if s.github then
  text(s.github.status or '',397,62,13,0xffdc82,'center')
  if s.github.busy=='install' or (s.github.fraction or 0)>0 then
   context.fill(30,418,734,12,122,157,255);context.fill(32,420,math.floor(730*math.min(1,s.github.fraction or 0)),8,255,220,130)
  end
 elseif s.detail then
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
