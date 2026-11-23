-- Background check for a newer/unfetched signed mod catalogue (mods/catalog.json), so players
-- learn that new or updated content packs exist without first having to open KATALOG MODÓW /
-- POLISH FIGHTERS - GITHUB manually. Before this module existed nothing ever polled the
-- catalogue until the player opened that screen themselves (see mod_browser.lua github_start),
-- so a freshly published GitHub release (new revision, new packages) was silent: MODUŁY kept
-- showing the old [BRAK DANYCH] state for anything not already downloaded in a previous
-- session, with no hint that there was something to fetch.
--
-- engine.mods is a single-slot async request (engine/src/adapters/luajit/runtime.cpp
-- mods_operation): only one 'catalogue'/'install'/'import' can be in flight at a time, and
-- mod_browser.lua uses the same slot once the player opens KATALOG MODÓW. This module only
-- ever starts a request while that screen is closed (state.hub_mods==nil) and gives up
-- quietly - no error shown to the player - if the slot is already busy or the platform has no
-- engine.mods at all (Linux/macOS builds: see mods_operation's #if !_WIN32 && !__ANDROID__).
local watch={}
local function api() return engine and engine.mods end

-- Starts one background catalogue fetch per app run. Safe to call every frame: it is a no-op
-- once state.hub_catalog_started is set, or forever if engine.mods is unavailable.
function watch.poll(state)
 if state.hub_mods or state.hub_catalog_done then return end
 if state.hub_android then
  -- Android downloads GitHub mods through the native AndroidModsActivity (hub.lua
  -- open_android_mods / context.action('open_android_mods')), not through this engine.mods
  -- Lua binding - mod_browser.lua's own "github" row skips straight past engine.mods there
  -- too (it relaunches that Activity instead). Calling engine.mods here would exercise an
  -- untested path for Android, so this background check stays desktop-only for now; Android
  -- still has no "new catalogue" notice (tracked, not fixed here).
  state.hub_catalog_done=true;return
 end
 local mods=api()
 if not mods then state.hub_catalog_done=true;return end
 if not state.hub_catalog_started then
  local ok=mods('catalogue')
  -- ok==false on "Mod request already pending": a game-start download/import raced us.
  -- Try again next frame rather than giving up for the whole session.
  if ok==true then state.hub_catalog_started=true end
  return
 end
 local result,err=mods('poll')
 if result=='pending' then return end
 state.hub_catalog_done=true
 if type(result)~='table' or type(result.packages)~='table' then return end -- offline/invalid: stay quiet, KATALOG MODÓW reports failures explicitly when opened
 local updates={}
 for _,entry in ipairs(result.packages) do
  local id=tostring(entry.id or '')
  if id~='' then
   local receipt=mods('receipt',id)
   local current=tostring(entry.version)..' '..tostring(entry.sha256)
   if receipt==nil or receipt~=current then updates[#updates+1]=tostring(entry.name or id) end
  end
 end
 if #updates>0 then
  local pl=require('polish-fighters/menu_locale').id()=='pl'
  local label=#updates..' '..(pl and 'paczek do pobrania/aktualizacji' or 'packs to download/update')
  state.hub_catalog_notice=(pl and 'Nowy katalog modów: ' or 'New mod catalogue: ')..label..' '..
   (pl and '(KATALOG MODÓW).' or '(MOD CATALOGUE).')
 end
end
return watch
