-- Registry browsing only; presence here is not evidence of availability or compatibility.
local entries=require('polish-fighters/mod_catalog')
local locale=require('polish-fighters/menu_locale')
local navigation=require('base/ui/navigation')
local controls=require('base/ui/controls')
local screen={}
local categories={'all','classic','naruto','dragon-ball','bleach','one-piece','anime','gameplay'}
local words={
 pl={title='KATALOG MODÓW',search='SZUKAJ: ',category='KATEGORIA: ',all='Wszystkie',classic='Klasyczne LF',naruto='Naruto',['dragon-ball']='Dragon Ball',bleach='Bleach',['one-piece']='One Piece',anime='Inne anime',gameplay='Mechanika',prev='POPRZEDNIE',next='NASTĘPNE',back='WSTECZ',unknown='Niepotwierdzone',note='Rejestr nazw. Linki, dostępność i zgodność nie zostały jeszcze sprawdzone.',status='Zgodność: nieprzetestowany',empty='Brak wyników',author='Autor: ',version='Wersja: ',source='Źródło: ',actions='Gotowe, podpisane mody pobierzesz w: POLISH FIGHTERS - GITHUB.',search_hint='Szukaj po nazwie, autorze lub postaci. Enter kończy wpisywanie.',github='POLISH FIGHTERS - GITHUB',refresh='ODŚWIEŻ KATALOG',gh_title='POLISH FIGHTERS - GITHUB',gh_loading='Pobieram podpisany katalog...',gh_ready='Podpis katalogu poprawny.',gh_download='Pobieranie: ',gh_verify='Sprawdzam podpis i SHA-256...',gh_unpack='Instaluję pliki: ',gh_done='Zainstalowano: ',gh_failed='Błąd: ',gh_android='Na Androidzie mody z GitHuba instaluje ekran Mody w menu głównym.',gh_installed=' [zainstalowany]',gh_restart='Wybierz go w menu modułów.'},
 en={title='MOD CATALOGUE',search='SEARCH: ',category='CATEGORY: ',all='All',classic='Classic LF',naruto='Naruto',['dragon-ball']='Dragon Ball',bleach='Bleach',['one-piece']='One Piece',anime='Other anime',gameplay='Gameplay',prev='PREVIOUS',next='NEXT',back='BACK',unknown='Unverified',note='Name registry. Links, availability and compatibility have not been verified yet.',status='Compatibility: not tested',empty='No results',author='Author: ',version='Version: ',source='Source: ',actions='Ready, signed mods are in: POLISH FIGHTERS - GITHUB.',search_hint='Search name, author or character. Enter finishes editing.',github='POLISH FIGHTERS - GITHUB',refresh='REFRESH CATALOGUE',gh_title='POLISH FIGHTERS - GITHUB',gh_loading='Downloading the signed catalogue...',gh_ready='Catalogue signature verified.',gh_download='Downloading: ',gh_verify='Checking signature and SHA-256...',gh_unpack='Installing files: ',gh_done='Installed: ',gh_failed='Error: ',gh_android='On Android, GitHub mods are installed from the Mods screen in the main menu.',gh_installed=' [installed]',gh_restart='Select it in the module menu.'}
}
local function strings() return words[locale.id()] end
-- Polish Fighters — GitHub: signed catalogue and installer provided by the engine (engine.mods).
local profile_tags={lf_four_turbo='lf_four_turbo',dbz='dbz',one_piece='one_piece',kate='kate',reinforced='reinforced',
 ntsd='ntsd',bleach='bleach',polish_fighters='polish_fighters',all='mixed'}
local function mods_api() return engine and engine.mods end
local function github_receipt(entry) return tostring(entry.version)..' '..tostring(entry.sha256) end
local function local_profiles(g)
 local installed={}
 for _,entry in ipairs(g.packages) do
  if not entry.local_only then installed[entry.id]=true end
 end
 local packages={}
 for _,entry in ipairs(g.packages) do
  if not entry.local_only then packages[#packages+1]=entry end
 end
 for _,profile in ipairs(require('polish-fighters/hub').profiles) do
  if profile.profile~='lf2-classic' and not installed[profile.profile] then
   local receipt=mods_api()('receipt',profile.profile)
   if receipt~=nil then
    packages[#packages+1]={id=profile.profile,name=profile.title,profile=profile.id,
     receipt=receipt,local_only=true}
   end
  end
 end
 table.sort(packages,function(a,b) return tostring(a.name)<tostring(b.name) end)
 g.packages=packages
end
local function github_action(entry)
 local pl=locale.id()=='pl'
 if entry.id==require('base/game/catalog').profile_id and (entry.local_only or entry.receipt==github_receipt(entry)) then
  return pl and 'AKTYWNY' or 'ACTIVE'
 end
 if entry.local_only then return pl and 'WYBIERZ' or 'SELECT' end
 if entry.receipt==nil then return pl and 'POBIERZ' or 'DOWNLOAD' end
 if entry.receipt~=github_receipt(entry) then return pl and 'AKTUALIZUJ' or 'UPDATE' end
 if profile_tags[entry.profile] then return pl and 'WYBIERZ' or 'SELECT' end
 return pl and 'ZAINSTALOWANO' or 'INSTALLED'
end
local function github_start(s)
 local w=strings();local api=mods_api();s.github=s.github or {packages={},page=1};s.github.status=w.gh_loading
 if not api then s.github.status=w.gh_android;return end
 local ok,err=api('catalogue')
 if ok==true then s.github.busy='catalogue' else s.github.status=w.gh_failed..tostring(err or '') end
 if err=='Mods handled by platform' then s.github.status=w.gh_android end
end
local function github_install(s,id)
 local api=mods_api();local g=s.github;if not api or g.busy then return end
 local ok,err=api('install',id)
 if ok==true then g.fraction=0;g.busy='install';g.target=id;g.status=strings().gh_download..'0%' else g.status=strings().gh_failed..tostring(err or '') end
end
local function size_label(bytes) return string.format('%.1f MB',(tonumber(bytes) or 0)/1048576) end
local function github_poll(state)
 local s=state.hub_mods;local g=s and s.github;local api=mods_api()
 if not g or not api then return end
 if not g.busy then
  if api('import')==true then
   g.busy='install';g.target=nil;g.fraction=0;g.status=strings().gh_verify
  end
  return
 end
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
 if result==nil then
  if busy=='catalogue' then local_profiles(g) end
  g.status=w.gh_failed..tostring(err or '');return
 end
 if busy=='catalogue' then
  g.packages=type(result)=='table' and type(result.packages)=='table' and result.packages or {}
  for _,entry in ipairs(g.packages) do entry.receipt=api('receipt',entry.id) end
  local_profiles(g)
  g.status=w.gh_ready
 else
  g.fraction=1
  g.target=g.target or result
  local name=g.target
  local_profiles(g)
  for _,entry in ipairs(g.packages) do if entry.id==g.target then name=entry.name;entry.receipt=api('receipt',entry.id)
   local tag=profile_tags[entry.profile or '']
   if tag and state.hub_available then state.hub_available[tag]=true end
  end end
  g.status=w.gh_done..tostring(name)..'. '..w.gh_restart
 end
end
screen.github_poll=github_poll
function screen.open(state,context)
 state.hub_mods={query='',category=1,page=1,nav=navigation.create(),previous={}}
 if context then
  state.hub_mods.direct=true
  screen.activate(state,'github',context)
 end
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
  local g=s.github
  local pl=locale.id()=='pl'
  local rows={}
  local pages=math.max(1,math.ceil(#g.packages/5))
  g.page=math.max(1,math.min(g.page or 1,pages))
  local first=(g.page-1)*5+1
  if not g.busy then
   local current=require('base/game/catalog').profile_id
   rows[#rows+1]={'gh_classic','LF2 CLASSIC  ·  '..(current=='lf2-classic' and (pl and 'AKTYWNY' or 'ACTIVE') or (pl and 'WYBIERZ' or 'SELECT')),302,242,446,30}
   for i=first,math.min(first+4,#g.packages) do
    local entry=g.packages[i]
    rows[#rows+1]={'gh:'..entry.id,entry.name..'  ·  '..github_action(entry),302,275+(i-first)*31,446,30}
   end
   rows[#rows+1]={'gh_import',pl and 'IMPORTUJ ZIP' or 'IMPORT ZIP',302,430,446,28}
   rows[#rows+1]={'gh_refresh',w.refresh,302,458,220,28}
   rows[#rows+1]={'back',w.back,528,458,220,28}
   if g.page>1 then rows[#rows+1]={'gh_prev',w.prev,302,491,220,28} end
   if g.page<pages then rows[#rows+1]={'gh_next',w.next,528,491,220,28} end
  elseif g.busy=='install' then
   rows[#rows+1]={'gh_cancel',pl and 'ANULUJ' or 'CANCEL',302,458,446,30}
  end
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
  if s.edit then s.edit=false elseif s.detail then s.detail=nil
  elseif s.github and s.github.busy then
   if s.github.busy=='install' then mods_api()('cancel') end
   return
  elseif s.github and not s.direct then s.github=nil else state.hub_mods=nil end
 elseif id=='github' or id=='gh_refresh' then
  if state.hub_android and context.action then
   require('polish-fighters/hub').open_android_mods(context)
   s.github=nil
   if s.direct then state.hub_mods=nil end
  elseif not (s.github and s.github.busy) then github_start(s) end
 elseif id=='gh_import' and context.action then
  context.action('import_local_mod')
 elseif id=='gh_classic' and context.action then
  if require('base/game/catalog').profile_id~='lf2-classic' then context.action('profile_lf_two') end
 elseif id:sub(1,3)=='gh:' and not s.github.busy then
  for _,entry in ipairs(s.github.packages) do
   if entry.id==id:sub(4) then
    local tag=profile_tags[entry.profile]
    if not entry.local_only and entry.receipt~=github_receipt(entry) then github_install(s,entry.id)
    elseif tag and context.action and entry.id~=require('base/game/catalog').profile_id then context.action('profile_'..tag) end
    break
   end
  end
 elseif id=='gh_cancel' then mods_api()('cancel')
 elseif id=='gh_prev' then s.github.page=s.github.page-1
 elseif id=='gh_next' then s.github.page=s.github.page+1
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
 local mapped=navigation.apply(s.nav,input,{page='mods:'..s.page..':'..s.category..':'..tostring(s.detail and s.detail.id)..(s.github and ':gh:'..s.github.page..':'..tostring(s.github.busy) or ''),targets=targets,default=1,remember=true,autofocus=true})
 s.hover=nil
 for index,box in ipairs(targets) do
  if mapped.pointer_x and mapped.pointer_y and mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then
   s.hover=rows[index][1]
   if mapped.click then screen.activate(state,s.hover,context);return end
   break
  end
 end
 if state.hub_mods and mapped.nav.cancel then screen.activate(state,'back',context) end
end
function screen.draw(state,context)
 local s=state.hub_mods;local w=strings()
 context.viewport(794,550,16,32,108)
 context.image('pe/menu_back'..(state.background or 0),0,0,true)
 local function text(value,x,y,size,color,align) context.text(value,x,y,align or 'left',size,color or 0xf4f5ff,nil,nil,true) end
 if s.github then
  context.sprite('pe/menu_clip',{0,41,434,80},195,94,true)
  context.sprite('pe/menu_clip',{434,41,62,68},629,94,true)
  text('MOD MANAGER',397,197,24,nil,'center')
 else text(w.title,397,24,24,nil,'center') end
 if s.github then
  local current=require('base/game/catalog').profile_id
  local title=require('polish-fighters/hub').title(current)
  text((locale.id()=='pl' and 'Aktywny: ' or 'Active: ')..title,525,226,14,0x62b5ef,'center')
  text(s.github.status or '',397,532,13,0xffdc82,'center')
  if s.github.busy=='install' then
   context.fill(302,424,446,12,122,157,255)
   context.fill(304,426,math.floor(442*math.min(1,s.github.fraction or 0)),8,255,220,130)
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
  local selected=row[1]==s.hover
  if selected then context.fill(row[3],row[4],row[5],row[6],20,42,82,220) end
  text(row[2],s.github and row[3]+row[5]/2 or row[3]+10,row[4]+7,14,selected and 0xf4f5ff or 0x62b5ef,s.github and 'center' or nil)
 end
 if s.edit then text(w.search_hint,30,521,12,0xffdc82) end
end
return screen
