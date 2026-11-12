local doc={options={language='english'},controls={keep=true}}
local fail=false
engine={read_settings=function() return doc end,write_settings=function(value)
 if fail then return nil,'read only' end;doc=value;return true end}
local hub=require('polish-fighters/hub')
local packs=require('polish-fighters/pack_preferences')
local selected=assert(packs.read(hub.profiles))
assert(selected.bleach and selected.polish_fighters)
selected.bleach=false
assert(packs.save(hub.profiles,selected))
assert(doc.options.language=='english' and doc.controls.keep)
assert(packs.read(hub.profiles).bleach==false)
local rows=hub.rows({hub_mode='root',hub_selected=selected})
assert(#rows==7,'classic main menu must keep its seven top-level actions')
local modules=false;for _,row in ipairs(rows) do if row[1]=='library' then modules=true end end
assert(modules,'module library is missing from the main menu')
for _,row in ipairs(hub.rows({hub_mode='library',hub_selected=selected})) do assert(row[1]~='profile_bleach') end
local toggles=hub.rows({hub_mode='packs',hub_pack_edit=selected})
local excluded=false;for _,row in ipairs(toggles) do if row[1]=='toggle_bleach' then excluded=true end end
assert(excluded,'excluded modules must remain available in module settings')
assert(#toggles==14)
for _,entry in ipairs(hub.profiles) do selected[entry.id]=false end
assert(not packs.save(hub.profiles,selected),'empty launcher selection allowed')
selected.lf_two=true;fail=true
assert(not packs.save(hub.profiles,selected),'write error ignored')
print('PASS: pack visibility selection, reload, preserved controls and failed saves')
