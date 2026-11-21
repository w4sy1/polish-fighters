local root=arg[1]
local document={unrelated={keep=true}}
local writes=0
engine={read_settings=function() return document end,write_settings=function(value)
    document=value;writes=writes+1;return true
end}
local controls=require('base/ui/controls')
local constants=require('base/game/constants')
local keyboard=constants.input_devices.keyboard
local settings={sets={},names={}}
for index=1,4 do
    settings.sets[index]={device=keyboard,keys={index*10+1,index*10+2,index*10+3,index*10+4,index*10+5,index*10+6,index*10+7},buttons={0,1,2}}
    settings.names[index]='Player '..index
end
assert(#controls.conflicts(settings)==0)
assert(controls.save(settings))
assert(document.unrelated.keep)
local before=writes
settings.sets[1].keys[2]=settings.sets[1].keys[1]
assert(#controls.conflicts(settings)==1)
assert(not controls.save(settings))
assert(writes==before,'conflict must not overwrite configuration')
settings.sets[1].keys[1]=0;settings.sets[1].keys[2]=0
assert(#controls.conflicts(settings)==0,'unassigned keys may repeat')
settings.sets[1].device=constants.input_devices.controller_one
settings.sets[1].buttons={0,0,2}
assert(#controls.conflicts(settings)==1,'button zero is assigned')

print('PASS: keyboard and controller conflicts, save preservation')

-- Etap 1.14 / Zadanie 5.1: hybrid control mode toggle + HUD editor rows,
-- Android-only, staged until 'save' like the rest of this screen.
package.loaded['base/game/catalog']={profile_id='test',
 load=function() return {{name='Davis',path='davis.dat'}} end,
 backgrounds=function() return {{path='arena'}} end,selectable=function() return true end}
package.loaded['base/game/background']={load=function() return {} end,create_state=function() return {} end}
package.loaded['base/game/object_data']={load=function(path) return {frames={[0]={hits={}},[300]={hits={}}}} end}
local input_settings=require('polish-fighters/input_settings')
local function row_ids(rows) local ids={} for _,row in ipairs(rows) do ids[row[1]]=true end return ids end

local desktop={}
input_settings.open(desktop)
assert(not row_ids(input_settings.rows(desktop,{})).hybrid_mode,'desktop must not expose hybrid_mode')
assert(not row_ids(input_settings.rows(desktop,{})).hybrid_hud,'desktop must not expose hybrid_hud')

local android={hub_android=true}
input_settings.open(android)
local ids=row_ids(input_settings.rows(android,{}))
assert(ids.hybrid_mode and ids.hybrid_hud,'Android must expose hybrid_mode and hybrid_hud rows')

local saved_document
engine.write_settings=function(value) saved_document=value;writes=writes+1;return true end
engine.read_settings=function() return {} end
local before_mode=android.hub_hybrid_mode
input_settings.activate(android,'hybrid_mode')
assert(android.hub_hybrid_mode~=before_mode,'hybrid_mode must flip the staged value')
input_settings.activate(android,'save')
assert(saved_document and saved_document.options.hybrid.controls.stick.enabled==(android.hub_hybrid_mode=='stick'),
 'save must persist the staged hybrid mode into options.hybrid.controls')
assert(saved_document.options.hybrid.controls.left.enabled==(android.hub_hybrid_mode=='arrows'))

-- hybrid_hud opens the HUD editor on the shared state.page dispatch and releases
-- hub_edit (stashed, not dropped -- see below), so hub_launch's own update() falls
-- through to the wrapped base's 'hud' page instead of staying routed into
-- input_settings.update.
local hud_state={hub_android=true}
input_settings.open(hud_state)
input_settings.activate(hud_state,'hybrid_hud')
assert(hud_state.page=='hud' and hud_state.hud and not hud_state.hub_edit,
 'hybrid_hud must open the editor and release hub_edit')
assert(hud_state.hud.destination=='menu','HUD editor must return to the hub menu, not the options page default')
print('PASS: Android hybrid control toggle + HUD editor rows, staged until save')

-- Final review finding 1: unsaved key/pad rebinds must not be silently lost while the
-- HUD editor is open. hub_launch.lua stashes hub_edit in hub_hybrid_pending_edit and
-- restores it once the delegated base hands state.page back to 'menu', re-entering
-- STEROWANIE (hub_edit non-nil routes straight back into input_settings.update).
local hub=require('polish-fighters/hub')
local shell=dofile(root..'/engine/scripts/polish-fighters/hub_launch.lua')({
 create=function() return {page='menu'} end,
 update=function(state) if state.page=='hud' and state.hud_finish then state.page='menu' end end,
 draw=function() end,describe=function() return '' end})
local round_state=shell.create({});round_state.hub_enabled=true;round_state.hub_mode='settings'
round_state.hub_android=true
local round_context={action=function() end,sound=function() end}
input_settings.open(round_state)
round_state.hub_edit.names[1]='CustomUnsavedName'
input_settings.activate(round_state,'hybrid_hud')
assert(not round_state.hub_edit and round_state.hub_hybrid_pending_edit
 and round_state.hub_hybrid_pending_edit.names[1]=='CustomUnsavedName',
 'unsaved edit must be stashed, not dropped, while the HUD editor is open')
shell.update(round_state,{keys={},gamepad={},pointer_x=0,pointer_y=0},round_context)
assert(round_state.page=='hud' and not round_state.hub_edit,
 'edit must stay stashed while the HUD editor is still open')
round_state.hud_finish=true
shell.update(round_state,{keys={},gamepad={},pointer_x=0,pointer_y=0},round_context)
assert(round_state.page=='menu' and round_state.hub_edit
 and round_state.hub_edit.names[1]=='CustomUnsavedName' and not round_state.hub_hybrid_pending_edit,
 'closing the HUD editor must restore the stashed edit, not lose it')
print('PASS: unsaved key/pad rebinds survive a trip through the HUD editor')
