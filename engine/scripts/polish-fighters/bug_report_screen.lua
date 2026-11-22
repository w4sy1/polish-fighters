-- SPDX-License-Identifier: MIT
-- A small text box next to the credits menu's existing e-mail-based "report_bug"
-- action (hub.lua / hub_launch.lua), letting a player type a short description and
-- send it straight to the project's Discord webhook. This shares its native code
-- (redaction, message formatting, rate/length limits) with the automatic crash
-- reporter rather than duplicating it: see engine.report_bug() and
-- engine/include/openlf2/engine/bug_report.hpp.
local navigation = require('base/ui/navigation')
local controls = require('base/ui/controls')
local screen = {}
local text_limit = 900 -- the native side also trims/redacts before building the Discord message

function screen.open(state)
    state.hub_bug_report = {text = '', focus = nil, nav = navigation.create(), previous = {}, status = nil, message = nil}
end

local function display_text(s)
    if s.text == '' then return 'OPIS BŁĘDU (kliknij, aby wpisać)' end
    local flat = s.text:gsub('[\r\n]+', ' / ')
    if #flat > 90 then flat = flat:sub(1, 87) .. '...' end
    return flat
end

local function rows(s)
    return {
        {'field:text', display_text(s), 40, 140, 714, 110},
        {'send', s.status == 'sending' and 'WYSYŁANIE…' or 'WYŚLIJ NA DISCORD', 40, 280, 340, 38},
        {'back', 'WSTECZ', 414, 280, 340, 38},
    }
end

function screen.activate(state, id, context)
    local s = state.hub_bug_report
    if not s then return end
    if id == 'back' then
        if context.text_input then context.text_input(false) end
        state.hub_bug_report = nil
        return
    elseif id == 'field:text' then
        if s.status ~= 'sending' then s.focus = 'text' end
        return
    elseif id == 'send' then
        if s.status == 'sending' then return end
        local trimmed = s.text:match('^%s*(.-)%s*$')
        if trimmed == '' then s.message = 'Wpisz opis błędu przed wysłaniem.'; return end
        local started, problem = engine.report_bug('start', trimmed)
        if not started then s.status = 'error'; s.message = tostring(problem or 'Nie udało się wysłać zgłoszenia.'); return end
        s.status, s.message, s.focus = 'sending', 'Wysyłanie…', nil
        if context.text_input then context.text_input(false) end
    end
end

function screen.update(state, input, context)
    local s = state.hub_bug_report
    if not s then return end
    if s.status == 'sending' then
        local result, problem = engine.report_bug('poll')
        if result == 'pending' then
            -- still in flight; nothing to draw differently this frame
        elseif result then
            s.status, s.message, s.text = 'sent', 'Zgłoszenie wysłane. Dziękujemy!', ''
        else
            s.status, s.message = 'error', tostring(problem or 'Nie udało się wysłać zgłoszenia.')
        end
    end
    if context.text_input then context.text_input(s.focus ~= nil) end
    if s.focus and s.status ~= 'sending' then
        local addition = input.text or ''
        if addition == '' then
            for code = 32, 222 do
                if input.keys[code] and not s.previous[code] then addition = addition .. (controls.key_character(code, input.keys[16]) or '') end
            end
        end
        if input.keys[8] and not s.previous[8] then s.text = s.text:sub(1, -2) end
        s.text = (s.text .. addition:gsub('[^ -~\r\n]', '')):sub(1, text_limit)
    end
    s.previous = {}
    for code, value in pairs(input.keys) do s.previous[code] = value end
    local list = rows(s)
    local targets = {}
    for _, row in ipairs(list) do targets[#targets + 1] = navigation.target(row[3], row[4], row[3] + row[5], row[4] + row[6]) end
    local mapped = navigation.apply(s.nav, input, {page = 'bug_report', targets = targets, default = 1, remember = true, locked = s.focus ~= nil})
    for index, box in ipairs(targets) do
        if mapped.click and mapped.pointer_x >= box.left and mapped.pointer_x <= box.right and mapped.pointer_y >= box.top and mapped.pointer_y <= box.bottom then
            screen.activate(state, list[index][1], context)
            return
        end
    end
    if mapped.nav.cancel and state.hub_bug_report then
        if s.focus then
            s.focus = nil
            if context.text_input then context.text_input(false) end
        else
            screen.activate(state, 'back', context)
        end
    end
end

function screen.draw(state, context)
    context.viewport(794, 550, 8, 13, 27)
    context.image('pe/menu_back1', 0, 0, true)
    context.fill(0, 0, 794, 550, 8, 13, 27, 185)
    local s = state.hub_bug_report
    context.text('POLISH FIGHTERS / ZGŁOŚ BŁĄD NA DISCORD', 397, 25, 'center', 18, 0xf0f5ff, nil, nil, true)
    context.text('Opisz krótko, co się stało. Trafi to na kanał Discord zespołu.', 397, 60, 'center', 13, 0xadc3df, nil, nil, true)
    for index, row in ipairs(rows(s)) do
        local active = row[1] == 'field:' .. tostring(s.focus)
        context.fill(row[3], row[4], row[5], row[6], active and 42 or 22, active and 80 or 42, active and 120 or 68, 230)
        context.text(row[2]:sub(1, 400), row[3] + 10, row[4] + 7, 'left', 13, 0xf0f5ff, nil, nil, true)
    end
    if s.message then context.text(s.message, 397, 335, 'center', 13, 0xffdc82, nil, nil, true) end
end

return screen
