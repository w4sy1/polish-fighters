-- SPDX-License-Identifier: MIT
-- Copyright (c) 2026 OpenLF2 contributors

local transport = require("base/game/network")
local controls = require("base/ui/controls")
local font = require("base/ui/font")
local i18n = require("base/i18n/i18n")
local sounds = require("base/game/sounds")
local navigation = require("base/ui/navigation")
local constants = require("base/game/constants")
local virtual_keys = constants.virtual_keys
local screen = {}
local frames = {[1] = {0, 41, 434, 80}, [2] = {434, 41, 62, 68}, [3] = {0, 247, 304, 126}, [4] = {0, 376, 363, 123},
    [5] = {500, 42, 291, 27}, [6] = {500, 72, 291, 27}, [10] = {460, 203, 334, 108},
    [11] = {460, 313, 334, 108}, [12] = {643, 426, 151, 26}, [13] = {489, 426, 151, 26},
    [14] = {490, 462, 304, 38}}
local function inside(input, left, top, right, bottom)
    return input.pointer_x >= left and input.pointer_x <= right and input.pointer_y >= top and input.pointer_y <= bottom
end
function screen.create(options)
    return {session = transport.create(options), page = "transport", transport_label = 'Wi-Fi / hotspot', address = "", previous_keys = {},
        allow_loopback = options.network_role ~= nil,
        nav = navigation.create(), keyboard = false,
        background = (options.menu_seed or 0) % 13 + 1, pointer_x = 0, pointer_y = 0,
        bind = options.network_bind or "0.0.0.0", started = engine.network_time()}
end
function screen.begin(state, host, address)
    state.message = nil
    if not host then
        local ip,port=address:match('^(.-):(%d+)$')
        if ip then
            port=tonumber(port)
            if port<1 or port>65535 then state.message='Port TCP: 1–65535.';return end
            state.session.port=port;address=ip
        end
        local a,b,c,d=address:match('^(%d+)%.(%d+)%.(%d+)%.(%d+)$')
        if not a or tonumber(a)>255 or tonumber(b)>255 or tonumber(c)>255 or tonumber(d)>255
            or (tonumber(a)==127 and not state.allow_loopback and not state.session.relay) or address=='0.0.0.0' then
            state.message='Wpisz IPv4 gospodarza (np. 192.168.1.82), opcjonalnie :12345.';return
        end
    end
    state.host_addresses = nil
    if host and not state.session.internet and address ~= "127.0.0.1" then
        -- A LAN host must read its own address to the others; relay hosts listen on loopback.
        local ok, list = pcall(engine.network, "addresses")
        if ok and type(list) == "string" and list:match("%d") then state.host_addresses = list:gsub(" ", ", ") end
    end
    if transport.start(state.session, host, address) then state.page = "waiting"
    else
        state.message = state.session.error
        if state.session.internet then state.page = "internet_error" end
    end
    state.started = engine.network_time()
end
-- The clickable areas for keyboard and controller navigation (base/ui/navigation); the join
-- page starts on its Connect button so Enter connects at once, as it always did.
local function navigation_spec(page, host)
    local target = navigation.target
    if page == "lobby" then
        local targets = {target(210,420,400,447), target(421,452,645,477)}
        if host then table.insert(targets,2,target(410,420,600,447)) end
        return {page = page, autofocus = true, targets = targets}
    end
    if page == "internet_error" then return {page = page, autofocus = true, targets = {target(242,361,552,386)}} end
    if page == "waiting" then return {page = page, targets = {target(0x142, 0x169, 0x1d8, 0x182)}} end
    if page == "join" then
        return {page = page, autofocus = true,
            targets = {target(0xef, 0x165, 0x185, 0x17e), target(0x19b, 0x165, 0x231, 0x17e)}}
    end
    return {page = page, targets = {target(0x104, 0x112, 0x223, 0x12c), target(0x104, 0x131, 0x223, 0x14a),
        target(0x104, 0x150, 0x223, 0x169)}}
end
function screen.update(state, flow_input, context)
    local input = navigation.apply(state.nav, flow_input, navigation_spec(state.page,state.session.slot==0))
    state.pointer_x, state.pointer_y = input.pointer_x, input.pointer_y
    local cancel = input.nav.cancel
    if state.page == "internet_error" then
        cancel = cancel or input.click and inside(input,242,361,552,386)
    elseif state.page == "lobby" then
        cancel = cancel or input.click and inside(input,421,452,645,477)
        local ready,problem
        if not cancel then ready,problem=transport.poll(state.session) end
        if ready then context.action("network_ready")
        elseif problem then state.page,state.message=state.session.internet and "internet_error" or "choice",problem
        elseif not cancel and input.click and inside(input,210,420,400,447) then
            local own
            for _,p in ipairs(state.session.peers) do if p.slot==state.session.slot then own=p end end
            transport.room_ready(state.session,not (own and own.ready))
        elseif not cancel and input.click and inside(input,410,420,600,447) and state.session.slot==0 then
            transport.room_begin(state.session)
        end
    elseif state.page == "waiting" then
        cancel = cancel or input.click and inside(input, 0x142, 0x169, 0x1d8, 0x182)
        if not cancel then
            local ready, problem = transport.poll(state.session)
            if ready then context.action("network_ready")
            elseif problem then state.page, state.message = state.session.internet and "internet_error" or "choice", problem
            elseif state.session.room and state.session.phase=="lobby" then state.page="lobby" end
        end
    elseif state.page == "join" then
        for code = 0, 255 do
            if input.keys[code] and not state.previous_keys[code] then
                if code == virtual_keys.backspace then state.address = state.address:sub(1, -2)
                else
                    local character = controls.key_character(code, false)
                    if character and character:match("^[%d.:]$") and #state.address < 21 then state.address = state.address .. character end
                end
            end
        end
        -- Text a soft keyboard delivers without key events.
        for character in input.text:gmatch("[%d.:]") do
            if #state.address < 21 then state.address = state.address .. character end
        end
        cancel = cancel or input.click and inside(input, 0x19b, 0x165, 0x231, 0x17e)
        -- Enter connects wherever the focus is (the raw keys: navigation may have taken it).
        if not cancel and (flow_input.keys[virtual_keys.enter] and not state.previous_keys[virtual_keys.enter]
           or input.click and inside(input, 0xef, 0x165, 0x185, 0x17e)) then
            screen.begin(state, false, state.address)
        end
    else
        cancel = cancel or input.click and inside(input, 0x104, 0x150, 0x223, 0x169)
        if input.click and inside(input, 0x104, 0x112, 0x223, 0x12c) then
            sounds.direct(state, "ok")
            if state.page=='transport' then state.transport_label='Wi-Fi / hotspot';state.page='choice'
            else screen.begin(state, true, state.bind) end
        elseif input.click and inside(input, 0x104, 0x131, 0x223, 0x14a) then
            sounds.direct(state, "ok")
            if state.page=='transport' then state.transport_label='Hotspot Bluetooth / PAN';state.page='choice'
            else state.page = "join" end
        end
    end
    if cancel then
        transport.close(state.session)
        sounds.direct(state, "cancel")
        if state.session.internet or state.page == "transport" then context.action("launch")
        elseif state.page=='choice' then state.page='transport' else state.page = "choice" end
    end
    state.previous_keys = flow_input.keys
    -- The on-screen keyboard follows the address field.
    local typing = state.page == "join"
    if typing ~= state.keyboard then
        state.keyboard = typing
        context.text_input(typing)
    end
    for _, sound in ipairs(sounds.flush(state)) do context.sound(sound.resource, sound.volume, sound.pan) end
end
function screen.draw(state, context)
    local function sprite(frame, x, y) context.sprite("pe/menu_clip", frames[frame], x, y, true) end
    context.viewport(constants.screen.width, constants.screen.height, 16, 32, 108)
    context.image("pe/menu_back" .. state.background, 0, 0, true)
    -- The logo without the version in its bottom-right corner.
    sprite(1, 0x9b, 0x69)
    sprite(2, 0x9b + 434, 0x69)
    local internet = state.session.internet
    if not internet then
        sprite(3, 0xfd, 0xde)
        sprite(14, 0xfd, 0x14f)
    end
    -- The original writes " Your IP Address: <address>" here on an opaque box, which also hides
    -- the art's own label; OpenLF2 has no address to show, so it shows its TCP port instead.
    if not internet then font.gdi(context, " " .. i18n.tr("Your TCP port: %s", state.session.port), 0x121, 0xfb, 0xffffff, 0x001e50) end
    if state.page == "lobby" then
        context.fill(186,210,470,295,16,32,80)
        font.draw(context,(internet and "POKOJ INTERNETOWY 2-" or "POKOJ LAN 2-")..state.session.capacity,421,220,4,nil,"center")
        for index,peer in ipairs(state.session.peers) do
            font.gdi(context,(peer.slot+1)..". "..peer.name..(peer.ready and " [GOTOWY]" or " [CZEKA]")..(peer.slot==state.session.slot and " < TY" or ""),210,251+(index-1)*19,0xffffff)
        end
        font.draw(context,"GOTOWOSC",300,427,4,nil,"center")
        if state.session.slot==0 then font.draw(context,"START",500,427,4,nil,"center") end
        font.gdi(context,state.session.notice or "Gospodarz uruchamia gre po zebraniu graczy.",210,487,0xffffff)
        context.fill(421,452,224,25,21,46,84)
        font.draw(context,"ROZLACZ",533,458,4,nil,"center")
        if state.host_addresses and state.session.slot==0 then
            font.gdi(context,"Twoje IP: "..state.host_addresses.."  port "..state.session.port,210,405,0xffdc82)
        end
    elseif state.page == "waiting" then
        if internet then
            context.fill(236,290,334,108,16,32,80)
            local label=state.session.host and "Otwieranie pokoju internetowego..." or "Laczenie z pokojem internetowym..."
            font.gdi(context,label,252,310,0xffffff)
        else sprite(state.session.host and 10 or 11, 0xec, 0x122) end
        sprite(12, 0x142, 0x169)
        local count = math.floor((engine.network_time() - state.started) / 150) % 14
        for index = 0, count - 1 do context.fill(0x119 + index * 20, 0x156, 5, 12, 87, 127, 215) end
    elseif state.page == "internet_error" then
        context.fill(106,240,582,166,16,32,80)
        font.draw(context,"PROBLEM Z POLACZENIEM",397,258,4,nil,"center")
        font.gdi(context,i18n.clip(state.message or "",94),122,303,0xffdc82)
        context.fill(242,361,310,25,21,46,84)
        font.draw(context,"WROC DO LISTY POKOI",397,367,4,nil,"center")
    elseif state.page == "join" then
        sprite(4, 0xdb, 0x10c)
        sprite(13, 0xef, 0x165)
        sprite(12, 0x19b, 0x165)
        font.gdi(context, state.address .. "_", 0x153, 0x147, 0xffffff, 0x001e50)
    else
        local input = {pointer_x = state.pointer_x, pointer_y = state.pointer_y}
        if inside(input, 0x104, 0x112, 0x223, 0x12c) then sprite(5, 0x103, 0x112) end
        if inside(input, 0x104, 0x131, 0x223, 0x14a) then sprite(6, 0x103, 0x130) end
        if inside(input, 0x104, 0x150, 0x223, 0x169) then sprite(12, 0x149, 0x150) end
        context.fill(260,274,291,27,16,32,80)
        context.fill(260,305,291,27,16,32,80)
        font.gdi(context,state.page=='transport' and 'WI-FI / HOTSPOT' or 'UTWÓRZ POKÓJ',278,280,0xffffff)
        font.gdi(context,state.page=='transport' and 'HOTSPOT BLUETOOTH / PAN' or 'DOŁĄCZ DO POKOJU',278,311,0xffffff)
    end
    if not internet then
        font.gdi(context,state.transport_label..': jeden gospodarz, pozostali dołączają.',30,180,0xffffff)
        if state.page~='lobby' then
            if state.page=='waiting' and state.host_addresses then
                font.gdi(context,'Twoje IP: '..state.host_addresses..'  (podaj je graczom, którzy dołączają)',20,450,0xffdc82)
            else
                font.gdi(context,'IP gospodarza: Windows: ipconfig / IPv4; Android: ekran Utwórz pokój.',20,450,0xffffff)
            end
            font.gdi(context,'Ten sam moduł i wersja gry. Domyślny TCP 12345. Dołącz: IP lub IP:port.',20,470,0xffffff)
            if state.transport_label=='Hotspot Bluetooth / PAN' then
                font.gdi(context,'Najpierw połącz urządzenia przez udostępnianie sieci Bluetooth w systemie.',20,430,0xffdc82)
            end
        end
        if state.message then
            font.gdi(context, i18n.clip(state.message, 94), 10, 500)
            font.gdi(context,'Sprawdź IP/port, wspólną sieć, izolację Wi-Fi oraz zaporę gospodarza.',10,520,0xffdc82)
        end
    end
    context.image("pe/lf2_cursor", math.min(state.pointer_x, 0x307), math.min(state.pointer_y + 2, 0x217), true)
end
function screen.describe(state)
    return "network_page=" .. state.page .. " phase=" .. state.session.phase .. (state.message and " error=" .. state.message or "")
end
return screen
