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
function hub.title(profile)
 if profile=='mixed-all' then return 'Polish Fighters: wszystkie mody' end
 for _,entry in ipairs(hub.profiles) do if entry.profile==profile then return entry.title end end
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
-- Android: the native Mods screen downloads and installs signed mods from Polish Fighters - GitHub.
function hub.open_android_mods(context) return open_android_screen(context,'little_fighters_open_android_mods') end
function hub.rows(state,active_profile)
 local mode=state.hub_mode
 local function row(id,key) return {id,(L(key or id))} end
 if mode=='root' or mode==nil then
  return {row('library','modules'),row('battle','play_main'),row('online'),row('settings'),row('guide'),row('language'),row('credits'),row('quit')}
 elseif mode=='profile' or mode=='battle' then
  local rows={}
  for _,id in ipairs({'versus','stage','championship','team_championship','battle_setup','demo','replay'}) do rows[#rows+1]=row('mode_'..id,id) end
  rows[#rows+1]={'resume_campaign','WZNOW KAMPANIE / RESUME'}
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
  rows[#rows+1]={'lan','GRA W SIECI LOKALNEJ'}
  rows[#rows+1]={'information','INFORMACJE'}
  if state.hub_android then rows[#rows+1]={'android_tools','ANDROID / BLUETOOTH'} end
  rows[#rows+1]=row('root','back')
  return rows
 elseif mode=='information' then return {row('settings','back')}
 elseif mode=='language' then return {{'lang_pl','POLSKI'},{'lang_en','ENGLISH'},row('root','back')}
 elseif mode=='credits' then return {row('root','back')}
 elseif mode=='players' then return {row('controls'),row('start_mode','start'),row('library','back')}
 elseif mode=='online' then
  return {row('account','quick'),row('network','host'),row('network','join'),row('account','rooms'),row('unavailable','friends'),row('root','back')}
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
 if state.hub_custom_profile then profile_row('current',hub.title(state.hub_custom_profile),state.hub_custom_profile) end
 for _,entry in ipairs(hub.profiles) do
  profile_row(entry.id,entry.title,entry.profile)
 end
 rows[#rows+1]=row('mods');rows[#rows+1]=row('packs');profile_row('mixed',L('mixed'),'mixed-all');rows[#rows+1]=row('status');rows[#rows+1]=row(state.hub_pending_mode and 'battle' or 'root','back')
 return rows
end
return hub
