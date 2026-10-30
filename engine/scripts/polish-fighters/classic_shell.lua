-- The upstream launch/title screens remain intact. Extras use the original blue/bitmap style.
return function(base)
    local font=require("base/ui/font")
    local nav=require("base/ui/navigation")
    local model=require("polish-fighters/dashboard_model")
    local options=require("base/game/options")
    local original_create,original_update,original_draw,original_describe=base.create,base.update,base.draw,base.describe
    local function items(s)
        if s.pf_message then return {{"back","POWROT"}} end
        if s.pf_panel=="unlock" then
            return {{"unlock-input",s.pf_typing and ("KOD: "..(s.pf_code or "")) or "WPISZ KOD (KLAWIATURA)"},
                {"unlock-submit","ZATWIERDZ KOD"},{"progress-info","POSTEP PRZYGODY I NAGRODY"},
                {"unlock-all","UZYJ KODU POLISHFIGHTERS"},{"back","POWROT"}}
        elseif s.pf_panel=="history" then
            local entries,problem=require("polish-fighters/chronicle").entries()
            if problem or model.history_error then
                return {{"history-error","BLAD HISTORII - SZCZEGOLY"},{"back","POWROT"}}
            end
            local pages=math.max(1,math.ceil(#entries/7))
            s.pf_history_page=math.max(1,math.min(s.pf_history_page or 1,pages))
            local list={}
            for index=#entries-(s.pf_history_page-1)*7,math.max(1,#entries-s.pf_history_page*7+1),-1 do
                local entry=entries[index]
                list[#list+1]={"history:"..index,"#"..entry.id.." "..entry.profile..(entry.network and " / SIEC" or " / LOKALNIE")}
            end
            if #entries==0 then list[#list+1]={"history-empty","BRAK ZAKONCZONYCH ROZGRYWEK"} end
            if s.pf_history_page>1 then list[#list+1]={"history-prev","< NOWSZE"} end
            if s.pf_history_page<pages then list[#list+1]={"history-next","STARSZE >"} end
            list[#list+1]={"back","POWROT"};return list
        end
        if s.pf_panel=="maps" then
            local list={}
            local maps=model.maps()
            local pages=math.max(1,math.ceil(#maps/8))
            s.pf_map_page=math.max(1,math.min(s.pf_map_page or 1,pages))
            for index=(s.pf_map_page-1)*8+1,math.min(s.pf_map_page*8,#maps) do
                local map=maps[index]
                list[#list+1]={"map:"..map.row,(model.current().map==map.row and "> " or "  ")..map.name}
            end
            if s.pf_map_page>1 then list[#list+1]={"maps-prev","< POPRZEDNIE MAPY"} end
            if s.pf_map_page<pages then list[#list+1]={"maps-next","NASTEPNE MAPY >"} end
            list[#list+1]={"play","GRAJ NA WYBRANEJ MAPIE"};list[#list+1]={"back","POWROT"}
            return list
        elseif s.pf_panel=="packs" then
            local list={}
            for index,pack in ipairs(model.packs) do list[#list+1]={"pack:"..index,pack[1]..(pack[2] and " [AKTYWNY]" or " [NIEAKTYWNY]")} end
            list[#list+1]={"back","POWROT"};return list
        elseif s.pf_panel=="account" then
            return {{"google","KONTO GOOGLE"},{"email","KONTO E-MAIL"},{"guest","GRAJ BEZ LOGOWANIA"},{"back","POWROT"}}
        elseif s.pf_panel=="pack-content" then
            return {{"fighters","PRZEGLADAJ POSTACIE"},{"maps","PRZEGLADAJ MAPY"},
                {"campaigns","PRZEGLADAJ ETAPY KAMPANII"},{"back","POWROT"}}
        elseif s.pf_panel=="fighters" or s.pf_panel=="campaigns" then
            local entries=s.pf_contents and s.pf_contents[s.pf_panel] or {}
            local list={}
            local pages=math.max(1,math.ceil(#entries/8))
            s.pf_content_page=math.max(1,math.min(s.pf_content_page or 1,pages))
            for index=(s.pf_content_page-1)*8+1,math.min(s.pf_content_page*8,#entries) do
                local entry=entries[index]
                local label=s.pf_panel=="fighters" and entry.name or (entry.name or ("ETAP "..entry.id.." / FAZY: "..entry.phases))
                list[#list+1]={"detail:"..index,label}
            end
            if s.pf_content_page>1 then list[#list+1]={"content-prev","< POPRZEDNIE"} end
            if s.pf_content_page<pages then list[#list+1]={"content-next","NASTEPNE >"} end
            list[#list+1]={"back","POWROT"};return list
        elseif s.pf_panel=="connection" then
            return {{"room","POKOJ LAN (2-8 URZADZEN)"},{"tcp","STARE POLACZENIE (2 URZADZENIA)"},{"capacity","LIMIT POKOJU: "..model.current().room_capacity..""},
                {"lan","HOTSPOT / SIEC LOKALNA"},{"bluetooth","BLUETOOTH"},{"back","POWROT"}}
        elseif s.pf_panel=="touch" then
            return {{"touch-small","MALE PRZYCISKI"},{"touch-medium","SREDNIE PRZYCISKI"},
                {"touch-large","DUZE PRZYCISKI"},{"touch-opacity","PRZEZROCZYSTOSC"},
                {"touch-left","PRZESUN PRZYCISKI W LEWO"},{"touch-right","PRZESUN PRZYCISKI W PRAWO"},
                {"touch-up","PRZESUN PRZYCISKI W GORE"},{"touch-down","PRZESUN PRZYCISKI W DOL"},
                {"touch-reset","PRZYWROC UKLAD"},{"touch-classic","UKLAD: KLASYCZNY LF"},
                {"touch-modern","UKLAD: NOWOCZESNY JOYSTICK"},{"back","POWROT"}}
        end
        return {{"play","GRAJ W LF2 CLASSIC"},{"maps","WYBIERZ MAPE"},{"packs","PAKIETY I POSTACIE"},
            {"connection","POLACZENIA: 2-8 URZADZEN"},{"account","KONTO / GOSC"},{"options","USTAWIENIA"},
            {"touch","STEROWANIE DOTYKOWE"},{"history","HISTORIA ROZGRYWEK"},
            {"unlock","ODBLOKOWANIE POSTACI"},{"close","POWROT DO LF2"}}
    end
    function base.create(value)
        local s=original_create(value);s.pf_navigation=nav.create();return s
    end
    local function activate(s,id,c)
        if s.pf_typing and id~="unlock-input" and id~="unlock-submit" then
            s.pf_typing=false;if c.text_input then c.text_input(false) end
        end
        if id=="close" then s.pf_panel=nil
        elseif id=="back" then
            if s.pf_typing then s.pf_typing=false;if c.text_input then c.text_input(false) end end
            if s.pf_message then s.pf_message=nil
            elseif s.pf_panel=="fighters" or s.pf_panel=="campaigns" then s.pf_panel="pack-content"
            elseif s.pf_panel=="pack-content" then s.pf_panel="packs"
            else s.pf_panel="extras" end
        elseif id=="guest" then s.pf_panel=nil
        elseif id=="unlock-input" then
            s.pf_code="";s.pf_typing=true
            if c.text_input then c.text_input(true) end
        elseif id=="unlock-submit" then
            if s.pf_code=="polishfighters" then activate(s,"unlock-all",c)
            else
                s.pf_typing=false;if c.text_input then c.text_input(false) end
                s.pf_message={"NIEPRAWIDLOWY KOD","Sprawdz wpisany kod i sprobuj ponownie."}
            end
        elseif id=="progress-info" then
            local catalog=require("base/game/catalog")
            local count,next_fighter=require("polish-fighters/progression").summary(catalog.profile_id,catalog.load())
            s.pf_message={"POSTEP PRZYGODY","Ukonczone rozdzialy: "..count,
                next_fighter and ("Nastepna nagroda: "..next_fighter) or "Brak kolejnych ukrytych postaci.",
                "Ukoncz nowy rozdzial lokalnej przygody.","Powtorki, porazki i siec nie przyznaja nagrod."}
        elseif id=="unlock-all" then
            s.pf_typing=false;if c.text_input then c.text_input(false) end
            local values=options.current();values.unlock_characters=true
            local ok,problem=options.save(values)
            if ok then require("base/game/unlock").flags.characters=1 end
            s.pf_message={ok and "POSTACIE ODBLOKOWANE" or "BLAD ZAPISU",
                ok and "Odblokowano ukryte postacie dostepnego rosteru." or tostring(problem),
                "Kod nie instaluje brakujacych dodatkow."}
            s.pf_code=""
        elseif id=="history-next" then s.pf_history_page=(s.pf_history_page or 1)+1
        elseif id=="history-prev" then s.pf_history_page=math.max(1,(s.pf_history_page or 1)-1)
        elseif id=="history-empty" then
            s.pf_message={"HISTORIA","Zapisywane sa zakonczone mecze, bez pokazow i powtorek."}
        elseif id=="history-error" then
            local _,problem=require("polish-fighters/chronicle").entries()
            s.pf_message={"BLAD HISTORII",tostring(problem or model.history_error):sub(1,80)}
        elseif id:sub(1,8)=="history:" then
            local entry=require("polish-fighters/chronicle").entries()[tonumber(id:sub(9))]
            if entry then
                local lines={"ROZGRYWKA #"..entry.id,"Pakiet: "..entry.profile.." / tryb: "..entry.mode,
                    "Zwycieska druzyna: "..tostring(entry.winner).." / klatki: "..tostring(entry.frames)}
                if entry.reward then lines[3]="NAGRODA: "..entry.reward.name end
                for _,player in ipairs(entry.players) do
                    lines[#lines+1]=(player.name or tostring(player.fighter)).." / pokonani: "..tostring(player.kills or 0)
                end
                s.pf_message=lines
            end
        elseif id=="maps-prev" then s.pf_map_page=math.max(1,(s.pf_map_page or 1)-1)
        elseif id=="maps-next" then s.pf_map_page=(s.pf_map_page or 1)+1
        elseif id=="content-prev" then s.pf_content_page=math.max(1,(s.pf_content_page or 1)-1)
        elseif id=="content-next" then s.pf_content_page=(s.pf_content_page or 1)+1
        elseif id=="fighters" or id=="campaigns" then s.pf_panel=id;s.pf_content_page=1
        elseif id:sub(1,7)=="detail:" then
            local entry=s.pf_contents[s.pf_panel][tonumber(id:sub(8))]
            if s.pf_panel=="campaigns" and entry.path then
                if entry.requires_custom_unlock then
                    s.pf_message={"KAMPANIA ZABLOKOWANA","Dodatek ma wlasne warunki odblokowania.","Ich obsluga wymaga jeszcze przeniesienia."}
                else model.pending_campaign=entry;s.pf_panel=nil;c.action("stage") end
            else s.pf_message={s.pf_panel=="fighters" and entry.name or "ETAP KAMPANII",
                "ID: "..entry.id,"Dane katalogowe; pelna zgodnosc niepotwierdzona."}
            end
        elseif id=="play" then
            model.pending_map=model.selected_map().row;c.action("versus")
        elseif id=="room" then require("base/game/network").next_room=true;s.pf_panel=nil;c.action("network")
        elseif id=="tcp" then s.pf_panel=nil;c.action("network")
        elseif id=="capacity" then
            local value=model.current().room_capacity%8+1
            if value<2 then value=2 end
            local ok=model.save({room_capacity=value})
            if not ok then s.pf_message={"NIE ZAPISANO USTAWIEN","Sprawdz dostep do plikow ustawien."} end
        elseif id=="options" then s.pf_panel=nil;s.page="options";s.options=options.current();s.options_focus=1
        elseif id:sub(1,6)=="touch-" then
            local values=options.current()
            local layout=values.gamepad
            local scales={["touch-small"]=0.8,["touch-medium"]=1,["touch-large"]=1.2}
            if id=="touch-classic" or id=="touch-modern" then
                values.touch_layout=id=="touch-classic" and "classic" or "modern"
                values.digipad=values.touch_layout=="classic"
            elseif id=="touch-reset" then values.gamepad=options.default_gamepad()
            elseif scales[id] then
                local defaults=options.default_gamepad()
                for name,entry in pairs(layout) do
                    if entry.radius then entry.radius=math.floor(defaults[name].radius*scales[id]+0.5) end
                end
            elseif id=="touch-opacity" then
                local value=layout.appearance.opacity
                layout.appearance.opacity=value<0.4 and 0.66 or (value<0.8 and 1 or 0.25)
            else
                for _,name in ipairs({"c","b","f","da","dj","daj"}) do
                    local entry=layout[name]
                    if id=="touch-left" then entry.right=math.min(600,entry.right+16)
                    elseif id=="touch-right" then entry.right=math.max(entry.radius,entry.right-16)
                    elseif id=="touch-up" then entry.bottom=math.min(450,entry.bottom+16)
                    elseif id=="touch-down" then entry.bottom=math.max(entry.radius,entry.bottom-16) end
                end
            end
            local ok,problem=options.save(values)
            s.pf_message={ok and "ZAPISANO STEROWANIE" or "BLAD ZAPISU",ok and "Uklad zostanie uzyty w kolejnym meczu." or tostring(problem)}
        elseif id:sub(1,4)=="map:" then
            local ok=model.save({map=tonumber(id:sub(5))})
            if not ok then s.pf_message={"NIE ZAPISANO MAPY","Sprawdz dostep do plikow ustawien."} end
        elseif id:sub(1,5)=="pack:" then
            local pack=model.packs[tonumber(id:sub(6))]
            if pack[2] then
                local content,problem=model.contents()
                if content then s.pf_contents=content;s.pf_panel="pack-content"
                else s.pf_message={"BLAD DANYCH PAKIETU",tostring(problem):sub(1,80)} end
            else s.pf_message={pack[1],"Pakiet nie jest zaladowany w tej sesji."} end
        elseif id=="google" or id=="email" then
            s.pf_message={"LOGOWANIE NIEDOSTEPNE","Usluga kont nie jest jeszcze podlaczona.","Mozesz grac offline jako gosc."}
        elseif id=="bluetooth" then s.pf_message={"BLUETOOTH NIEDOSTEPNY","Ten transport wymaga jeszcze implementacji."}
        elseif id=="lan" then s.pf_message={"GRA BEZ INTERNETU","Podlacz urzadzenia do wspolnego Wi-Fi lub hotspotu.","Otworz POKOJ LAN i wpisz adres IP gospodarza."}
        else s.pf_panel=id end
    end
    function base.update(s,input,c)
        if s.page~="menu" then return original_update(s,input,c) end
        if s.pf_panel=="unlock" and not s.pf_message then
            local text=input.text or ""
            if #text>0 then
                s.pf_code=((s.pf_code or "")..text:lower():gsub("[^a-z]","")):sub(-14)
            end
            for _,key in ipairs(#text==0 and (input.presses or {}) or {}) do
                if key>=65 and key<=90 then
                    s.pf_code=((s.pf_code or "")..string.char(key+32)):sub(-14)
                elseif key==8 then s.pf_code=(s.pf_code or ""):sub(1,-2)
                elseif key==13 then activate(s,"unlock-submit",c);return
                else s.pf_code="" end
            end
            if s.pf_code=="polishfighters" then activate(s,"unlock-all",c);return end
            if s.pf_typing and not (input.nav and input.nav.cancel) and not input.click then return end
        end
        if not s.pf_panel then
            local enter=input.click and input.pointer_x>=260 and input.pointer_x<=535 and input.pointer_y>=414 and input.pointer_y<=444
            local f10=input.keys[121] and not s.pf_f10
            s.pf_f10=input.keys[121]
            if enter or f10 then s.pf_panel="extras";return end
            return original_update(s,input,c)
        end
        local list=items(s);local targets={}
        for index in ipairs(list) do targets[#targets+1]=nav.target(210,214+(index-1)*25,635,236+(index-1)*25) end
        local mapped=nav.apply(s.pf_navigation,input,{page="classic:"..s.pf_panel..":"..tostring(s.pf_map_page or 1)..":"..tostring(s.pf_content_page or 1)..":"..tostring(s.pf_history_page or 1)..(s.pf_message and ":message" or ""),targets=targets,default=1})
        s.pf_hover=nil
        for index,box in ipairs(targets) do
            if mapped.pointer_x>=box.left and mapped.pointer_x<=box.right and mapped.pointer_y>=box.top and mapped.pointer_y<=box.bottom then
                s.pf_hover=index
                if mapped.click then activate(s,list[index][1],c);break end
            end
        end
        if mapped.nav.cancel then
            if s.pf_typing then s.pf_typing=false;if c.text_input then c.text_input(false) end end
            if s.pf_message then s.pf_message=nil elseif s.pf_panel=="extras" then s.pf_panel=nil else s.pf_panel="extras" end
        end
    end
    function base.draw(s,c)
        if not s.pf_panel or s.page~="menu" then
            original_draw(s,c)
            if s.page=="menu" then
                font.draw(c,"POLISH FIGHTERS - DODATKI [F10]",397,422,2,nil,"center")
            end
            return
        end
        c.viewport(794,550,16,32,108)
        c.image("pe/menu_back"..s.background,0,0,true)
        c.sprite("pe/menu_clip",{0,41,434,80},155,55,true)
        c.sprite("pe/menu_clip",{434,41,62,68},589,55,true)
        c.fill(186,164,470,359,16,32,80,235)
        local titles={extras="POLISH FIGHTERS",maps="MAPY",packs="PAKIETY",account="KONTO / GOSC",connection="POLACZENIA",touch="STEROWANIE DOTYKOWE",
            ["pack-content"]="ZAWARTOSC PAKIETU",fighters="POSTACIE",campaigns="KAMPANIE",history="KRONIKA ROZGRYWEK",unlock="KOD ODBLOKOWANIA"}
        font.draw(c,s.pf_message and s.pf_message[1] or titles[s.pf_panel],421,183,4,nil,"center")
        if s.pf_message then
            for i=2,#s.pf_message do font.gdi(c,s.pf_message[i],210,270+(i-2)*28,0xffffff) end
        end
        for index,entry in ipairs(items(s)) do
            if index==s.pf_hover then c.fill(200,212+(index-1)*25,442,24,32,58,115) end
            font.draw(c,entry[2],421,219+(index-1)*25,index==s.pf_hover and 4 or 1,nil,"center")
        end
        font.gdi(c,"ESC: POWROT     POLISH FIGHTERS 0.6",210,532,0x5077d0)
    end
    function base.describe(s)
        return original_describe(s).." pf_panel="..tostring(s.pf_panel or "classic").." pf_map="..model.current().map.." pf_room_capacity="..model.current().room_capacity
    end
    return base
end
