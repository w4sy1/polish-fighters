-- SPDX-License-Identifier: MIT
-- Structured bug-report form reached from the contact menu's "ZGŁOŚ BŁĄD (DISCORD)" row
-- (hub.lua / hub_launch.lua). The player fills in a category, an optional nick, a title, a
-- description and (optional) reproduction steps, with no account required. The native side
-- (engine.report_bug, engine/src/adapters/luajit/runtime.cpp) sends this as JSON to the account
-- server's 'bug-report' operation over the same HTTPS channel used for online play -- the
-- server alone holds the Discord webhook secret and relays the report to the team's channel,
-- returning a report number (PF-BUG-NNNNNN). See docs/BUG-REPORT-MENU-2.0-2026-11-22.md for the
-- full design and docs/CRASH-REPORTER-1.1-2026-11-22.md for the unrelated, still-direct-to-Discord
-- automatic crash reporter.
--
-- Not implemented in this version (documented rather than faked): an optional screenshot
-- attachment and uploading real diagnostic log excerpts -- see the "Not implemented" note in
-- that doc. The server still always receives platform/version/module, which need no consent.
local navigation = require('base/ui/navigation')
local controls = require('base/ui/controls')
local catalog = require('base/game/catalog')
local screen = {}

-- Keep this list and its order identical to BUG_REPORT_CATEGORIES in tools/account_service.py --
-- there is no shared source file between Lua and Python in this repo.
local CATEGORIES = {
 'Awaria gry / crash', 'Błąd graficzny', 'Sterowanie', 'Postacie i umiejętności', 'Kombosy',
 'Rozgrywka', 'Kampania', 'Multiplayer i połączenia sieciowe', 'Moduły gry', 'Dźwięk i muzyka',
 'Interfejs użytkownika', 'Wydajność', 'Profile i zapisy gry', 'Inne',
}
screen.default_server = 'https://www.projektocalenie.pl/projekty/polish-fighters/api'

local function api_endpoint(endpoint)
 local project_page = 'https://www.projektocalenie.pl/projekty/polish-fighters'
 local trimmed = tostring(endpoint or ''):gsub('/+$', '')
 if trimmed == project_page or trimmed == project_page:gsub('://www%.', '://') then return trimmed .. '/api' end
 return endpoint
end

-- Non-deterministic (engine.crt_random, not the replay-synced gameplay RNG): identifies one
-- report draft so a retried send after a network error reuses the same number instead of the
-- server creating (and posting to Discord) a second one. See account_service.py's client_ref.
local function new_client_ref()
 local a = math.floor(tonumber(engine.crt_random()) or 0)
 local b = math.floor(tonumber(engine.crt_random()) or 0)
 local c = math.floor(tonumber(engine.crt_random()) or 0)
 return ('cref-%d-%d-%d'):format(a, b, c)
end

function screen.open(state)
 local doc = engine.read_settings()
 doc = type(doc) == 'table' and doc or {}
 local endpoint = type(doc.account_server) == 'string' and doc.account_server:match('%S') and doc.account_server or screen.default_server
 state.hub_bug_report = {
  category = 1, nick = type(doc.online_nick) == 'string' and doc.online_nick:sub(1, 24) or '',
  title = '', description = '', steps = '', focus = nil, nav = navigation.create(), previous = {},
  status = nil, message = nil, report = nil, client_ref = new_client_ref(), endpoint = endpoint,
 }
end

local function flatten(text, limit)
 if text == '' then return nil end
 local flat = text:gsub('[\r\n]+', ' / ')
 if #flat > limit then flat = flat:sub(1, limit - 3) .. '...' end
 return flat
end

local function rows(s)
 return {
  {'category', 'KATEGORIA: ' .. CATEGORIES[s.category] .. '  (kliknij, aby zmienić)', 40, 90, 714, 34},
  {'field:nick', 'NICK (OPCJONALNIE): ' .. (flatten(s.nick, 60) or '(kliknij, aby wpisać)'), 40, 132, 714, 34},
  {'field:title', 'TYTUŁ ZGŁOSZENIA: ' .. (flatten(s.title, 55) or '(kliknij, aby wpisać)'), 40, 174, 714, 34},
  {'field:description', 'OPIS BŁĘDU: ' .. (flatten(s.description, 70) or '(kliknij, aby wpisać)'), 40, 216, 714, 56},
  {'field:steps', 'KROKI ODTWORZENIA (OPCJONALNIE): ' .. (flatten(s.steps, 55) or '(kliknij, aby wpisać)'), 40, 280, 714, 34},
  {'send', s.status == 'sending' and 'WYSYŁANIE…' or 'WYŚLIJ ZGŁOSZENIE', 40, 334, 340, 40},
  {'back', 'WSTECZ', 414, 334, 340, 40},
 }
end

local FIELD_LIMIT = {nick = 24, title = 120, description = 1800, steps = 1200}

function screen.activate(state, id, context)
 local s = state.hub_bug_report
 if not s then return end
 if id == 'back' then
  -- Blocked while sending: state.hub_bug_report (and so the in-flight future's only poller)
  -- would otherwise be dropped before engine.report_bug('poll') ever resolves it, leaving the
  -- native side's report_bug_future permanently "valid" and every later send stuck on "Bug
  -- report already pending" until the next full restart.
  if s.status == 'sending' then return end
  if context.text_input then context.text_input(false) end
  state.hub_bug_report = nil
  return
 elseif id == 'category' then
  if s.status == 'sending' then return end
  s.category = s.category % #CATEGORIES + 1
  return
 elseif id:sub(1, 6) == 'field:' then
  if s.status ~= 'sending' then s.focus = id:sub(7) end
  return
 elseif id == 'send' then
  if s.status == 'sending' then return end
  local title = s.title:match('^%s*(.-)%s*$')
  local description = s.description:match('^%s*(.-)%s*$')
  if title == '' then s.message = 'Wpisz tytuł zgłoszenia przed wysłaniem.'; return end
  if description == '' then s.message = 'Opisz krótko błąd przed wysłaniem.'; return end
  local payload, problem = engine.json_encode({
   category = CATEGORIES[s.category], title = title, description = description,
   steps = s.steps:match('^%s*(.-)%s*$'), player = s.nick:match('^%s*(.-)%s*$'),
   platform = state.hub_android and 'android' or 'windows',
   version = require('polish-fighters/updates').version, module = tostring(catalog.profile_id or ''),
   client_ref = s.client_ref,
  })
  if not payload then s.status = 'error'; s.message = tostring(problem or 'Nie udało się zakodować zgłoszenia.'); return end
  local started, issue = engine.report_bug('start', api_endpoint(s.endpoint), payload)
  if not started then s.status = 'error'; s.message = tostring(issue or 'Nie udało się wysłać zgłoszenia.'); return end
  s.status, s.message, s.focus = 'sending', 'Wysyłanie…', nil
  if context.text_input then context.text_input(false) end
 end
end

function screen.update(state, input, context)
 local s = state.hub_bug_report
 if not s then return end
 if s.status == 'sending' then
  local raw, issue = engine.report_bug('poll')
  if raw == 'pending' then
   -- still in flight; nothing to draw differently this frame
  elseif not raw then
   s.status, s.message = 'error', tostring(issue or 'Nie udało się wysłać zgłoszenia.')
  else
   local result = engine.json_decode(raw)
   if type(result) ~= 'table' then
    s.status, s.message = 'error', 'Nieprawidłowa odpowiedź serwera.'
   elseif result.error then
    s.status, s.message = 'error', ('Błąd serwera: ' .. tostring(result.error)):sub(1, 160)
   else
    s.status, s.report = 'sent', tostring(result.report or '')
    s.message = (result.duplicate and 'To zgłoszenie zostało już wysłane wcześniej: ' or 'Zgłoszenie wysłane. Dziękujemy! Numer: ') .. s.report
    s.title, s.description, s.steps = '', '', ''
    s.client_ref = new_client_ref()
   end
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
  local limit = FIELD_LIMIT[s.focus] or 48
  if input.keys[8] and not s.previous[8] then s[s.focus] = s[s.focus]:sub(1, -2) end
  s[s.focus] = (s[s.focus] .. addition:gsub('[^ -~\r\n]', '')):sub(1, limit)
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
 context.text('Wypełnij formularz. Zgłoszenie trafia przez serwer gry na kanał Discord zespołu. Konto nie jest wymagane.',
  397, 55, 'center', 12, 0xadc3df, nil, nil, true)
 for index, row in ipairs(rows(s)) do
  local active = row[1] == 'field:' .. tostring(s.focus)
  context.fill(row[3], row[4], row[5], row[6], active and 42 or 22, active and 80 or 42, active and 120 or 68, 230)
  context.text(row[2]:sub(1, 400), row[3] + 10, row[4] + 7, 'left', 13, 0xf0f5ff, nil, nil, true)
 end
 if s.message then context.text(s.message:sub(1, 120), 397, 390, 'center', 13, 0xffdc82, nil, nil, true) end
end

return screen
