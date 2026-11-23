-- First menu shared by all profiles. Only installed packages can be activated.
local hub={}
hub.profiles={
 {id="polish_fighters",profile="polish-originals",title="Polish Originals"},
 {id="lf_two",profile="lf2-classic",title="LF2"},
 {id="lf_four_turbo",profile="lf4-turbo",title="LF4 Turbo"},
 {id="dbz",profile="dbz",title="Dragon Ball"},
 {id="one_piece",profile="one-piece",title="One Piece"},
 {id="kate",profile="kate",title="Kate"},
 {id="reinforced",profile="reinforced",title="Reinforced"},
 {id="ntsd",profile="ntsd",title="NTSD / Naruto"},
 {id="bleach",profile="bleach",title="Bleach"},
}
hub.optional_profiles={
 {id="dragon_ball_super", profile="dragon-ball-super", title="Dragon Ball Super"},
 {id="fighter_hero", profile="fighter-hero", title="Fighter Hero"},
 {id="gf2", profile="gf2", title="GF2"},
 {id="lf2_ns", profile="lf2-ns", title="LF2 NS"},
 {id="sx2", profile="sx2", title="Sx2"},
 {id="lf2_sv", profile="lf2-sv", title="LF2 SV"},
 {id="rn_lf2", profile="rn-lf2", title="RN LF2"},
 {id="lf_seed", profile="lf-seed", title="LF Seed"},
 {id="wlf2_al", profile="wlf2-al", title="WLF2 AL"},
 {id="ce_lf2", profile="ce-lf2", title="CE LF2"},
 {id="ntsd_community", profile="ntsd-community", title="NTSD Community"},
 {id="ntsd_ce_setup", profile="ntsd-ce-setup", title="NTSD CE"},
 {id="killer_lf2", profile="killer-lf2", title="Killer LF2", campaign=false},
 -- Downloadable via the GitHub mod catalogue (tools/build_mod_release.py) but previously had
 -- no entry here nor in application.cpp's profile_definitions nor mod_browser.lua's
 -- profile_tags, so a successful download could never be selected as the active profile.
 {id="mortal_kombat", profile="mortal-kombat", title="Mortal Kombat LF2"},
 {id="lf3", profile="lf3", title="LF3BYTITASZIBIKAS 2.0b"},
 {id="oplos", profile="oplos", title="One Piece: Legends of Sea"},
}
function hub.title(profile)
 if profile=='mixed-all' then return 'Polish Fighters: wszystkie mody' end
 for _,entry in ipairs(hub.profiles) do if entry.profile==profile then return entry.title end end
 for _,entry in ipairs(hub.optional_profiles) do if entry.profile==profile then return entry.title end end
 if type(profile)=='string' and profile:match('^mod%-') then return 'MOD '..profile:sub(5,16) end
 return "Little Fighters"
end
local L=require('polish-fighters/menu_locale').text
local function open_android_screen(context,key)
 local settings,problem=engine.read_settings()
 if problem then return nil,problem end
 settings=type(settings)=='table' and settings or {}
 settings[key]=true
 local saved,problem=engine.write_settings(settings)
 if not saved then return nil,problem end
 context.action('quit')
 return true
end
function hub.open_android_tools(context) return open_android_screen(context,'little_fighters_open_android_tools') end
-- Android: BLUETOOTH is restart-wrapped, same quit+relaunch pattern as android_tools above;
-- OpenLF2Activity reads little_fighters_open_bluetooth on the next launch and opens
-- BluetoothPairingActivity (Etap 1.14 / Etap 4A).
function hub.open_android_bluetooth(context) return open_android_screen(context,'little_fighters_open_bluetooth') end
-- Android: the native Mods screen downloads and installs signed mods from Polish Fighters - GitHub.
function hub.open_android_mods(context) context.action('open_android_mods') end
function hub.rows(state,active_profile)
 local mode=state.hub_mode
 local function row(id,key) return {id,(L(key or id))} end
 if mode=='root' or mode==nil then
  return {row('library','modules'),row('battle','play_main'),row('remote'),row('settings'),row('guide'),row('language'),row('credits'),row('quit')}
 elseif mode=='profile' or mode=='battle' then
  local rows={}
  local campaign=(mode=='battle' and not state.hub_preselected) or require('base/game/catalog').stage_path~=false
  for _,id in ipairs({'versus','stage','championship','team_championship','battle_setup','demo','replay'}) do
   rows[#rows+1]=(id=='stage' and not campaign) and row('campaign_unavailable') or row('mode_'..id,id)
  end
  if campaign then rows[#rows+1]={'resume_campaign','WZNOW KAMPANIE / RESUME'} end
  rows[#rows+1]={'training','TRENING / TRAINING'}
  rows[#rows+1]=row('root','back');return rows
 elseif mode=='status' then
  local rows={};local inventory=require('polish-fighters/module_inventory')
  for _,entry in ipairs(hub.profiles) do
   local data=inventory[entry.id] or {missing=1}
   rows[#rows+1]={'status_'..entry.id,entry.title..' / '..L('missing_files')..data.missing}
  end
  rows[#rows+1]={'unavailable',L('absent_turbo')};rows[#rows+1]=row('library','back');return rows
 elseif mode=='settings' then
  local rows={row('controls'),row('options','video'),row('recording'),row('extras'),{'diagnostics','DIAGNOSTYKA / DIAGNOSTICS'}}
  rows[#rows+1]={'capacity','LIMIT POKOJU / ROOM CAPACITY: '..require('polish-fighters/dashboard_model').current().room_capacity}
  rows[#rows+1]={'information','INFORMACJE'}
  if state.hub_android then rows[#rows+1]={'android_tools','ANDROID / BLUETOOTH'} end
  rows[#rows+1]=row('root','back')
  return rows
 elseif mode=='information' then
  if state.hub_android then return {{'check_android_update','AKTUALIZUJ GRĘ'},row('settings','back')} end
  return {row('settings','back')}
 elseif mode=='language' then return {{'lang_pl','POLSKI'},{'lang_en','ENGLISH'},row('root','back')}
 elseif mode=='credits' then
  return {row('credits_info'),row('discord','discord_link'),row('report_bug'),row('report_bug_discord'),row('root','back')}
 elseif mode=='credits_info' then return {row('credits','back')}
 elseif mode=='players' then return {row('controls'),row('start_mode','start'),row('library','back')}
 elseif mode=='remote' then
  -- Windows Bluetooth (Etap 4B) does not exist yet; state.hub_bluetooth_available lets a
  -- future native bridge override this per platform without touching this file again.
  local bluetooth=state.hub_bluetooth_available
  if bluetooth==nil then bluetooth=state.hub_android end
  local rows={row('remote_server')}
  if bluetooth then rows[#rows+1]=row('remote_bluetooth') end
  rows[#rows+1]=row('remote_wifi');rows[#rows+1]=row('remote_hotspot');rows[#rows+1]=row('root','back')
  return rows
 elseif mode=='packs' then
  local rows={}
  for _,entry in ipairs(hub.profiles) do
   local missing=state.hub_available and state.hub_available[entry.id]==false
   rows[#rows+1]={'toggle_'..entry.id,(state.hub_pack_edit[entry.id]~=false and L('on') or L('off'))..entry.title..(missing and L('missing') or '')}
  end
  rows[#rows+1]=row('packs_all','all')
  rows[#rows+1]=row('packs_duplicates',state.hub_hide_duplicates~=false and 'duplicates_hidden' or 'duplicates_shown')
  rows[#rows+1]=row('status');rows[#rows+1]=row('packs_save','save');rows[#rows+1]=row('packs_cancel','cancel');return rows
 end
 local rows={}
 local function profile_row(id,title,profile)
  local missing=state.hub_available and state.hub_available[id]==false
  rows[#rows+1]={'profile_'..id,title..(missing and L('missing') or ''),profile==active_profile}
 end
 local available=state.hub_available
 if mode=='optional_modules' then
  for _,entry in ipairs(hub.optional_profiles) do
   if available and available[entry.id] then profile_row(entry.id,entry.title,entry.profile) end
  end
  rows[#rows+1]=row('library','back')
  return rows
 end
 if state.hub_custom_profile then profile_row('current',hub.title(state.hub_custom_profile),state.hub_custom_profile) end
 for _,entry in ipairs(hub.profiles) do
  profile_row(entry.id,entry.title,entry.profile)
 end
 if available then
  for _,entry in ipairs(hub.optional_profiles) do
   if available[entry.id] then rows[#rows+1]=row('optional_modules');break end
  end
 end
 rows[#rows+1]=row('mods');rows[#rows+1]=row('packs');profile_row('mixed',L('mixed'),'mixed-all');rows[#rows+1]=row('status');rows[#rows+1]=row(state.hub_pending_mode and 'battle' or 'root','back')
 return rows
end
return hub
