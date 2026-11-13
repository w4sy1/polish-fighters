-- First menu shared by all profiles. Only installed packages can be activated.
local hub={}
hub.profiles={
 {id="polish_fighters",profile="polish-originals",title="Polish Fighters"},
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
local L=require('polish-fighters/menu_locale').text
function hub.rows(state)
 local mode=state.hub_mode
 local function row(id,key) return {id,L(key or id)} end
 if mode=='root' or mode==nil then
  return {row('battle'),row('library','modules'),row('online'),row('settings'),row('language'),row('credits'),row('quit')}
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
  return {row('controls'),row('options','video'),row('recording'),row('extras'),{'diagnostics','DIAGNOSTYKA / DIAGNOSTICS'},row('root','back')}
 elseif mode=='language' then return {{'lang_pl','POLSKI'},{'lang_en','ENGLISH'},row('root','back')}
 elseif mode=='credits' then return {row('root','back')}
 elseif mode=='players' then return {row('controls'),row('start_mode','start'),row('library','back')}
 elseif mode=='online' then
  return {row('unavailable','quick'),row('network','host'),row('network','join'),row('account','rooms'),row('unavailable','friends'),row('root','back')}
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
 if state.hub_custom_profile then rows[#rows+1]={'profile_current',L('current_mod')..state.hub_custom_profile:sub(5,16)} end
 for _,entry in ipairs(hub.profiles) do
  if not state.hub_selected or state.hub_selected[entry.id]~=false then
   rows[#rows+1]={'profile_'..entry.id,entry.title..(state.hub_available and state.hub_available[entry.id]==false and L('missing') or '')}
  end
 end
 rows[#rows+1]=row('mods');rows[#rows+1]=row('packs');rows[#rows+1]=row('profile_mixed','mixed');rows[#rows+1]=row('status');rows[#rows+1]=row(state.hub_pending_mode and 'battle' or 'root','back')
 return rows
end
return hub
