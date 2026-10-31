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
assert(#rows==17)
for _,row in ipairs(rows) do assert(row[1]~='profile_bleach') end
assert(#hub.rows({hub_mode='packs',hub_pack_edit=selected})==12)
for _,entry in ipairs(hub.profiles) do selected[entry.id]=false end
assert(not packs.save(hub.profiles,selected),'empty launcher selection allowed')
selected.lf_two=true;fail=true
assert(not packs.save(hub.profiles,selected),'write error ignored')
print('PASS: pack visibility selection, reload, preserved controls and failed saves')
