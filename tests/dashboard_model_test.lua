local root=arg[1] or '.'
local doc={options={language='polish'},polish_fighters_dashboard={map=-2,nickname=''}}
local fail=false
engine={read_settings=function() return doc end,write_settings=function(value)
    if fail then return nil,'read only' end
    doc=value;return true
end}
package.preload['base/game/catalog']=function() return {profile_id="lf2-classic",backgrounds=function()
    return {{path='arena'},{path='placeholder'},{path='forest'}}
end} end
package.preload['base/game/background']=function() return {load=function(path)
    return {name=path=='placeholder' and 'Template1' or path}
end} end
local model=dofile(root..'/engine/scripts/polish-fighters/dashboard_model.lua')
assert(model.current().map==0 and model.current().nickname=='Gracz')
assert(model.save({map=2,nickname='Remek'}))
assert(doc.options.language=='polish' and model.current().map==2)
fail=true
assert(not model.save({map=3}))
assert(model.current().map==2)
assert(#model.maps()==2 and model.maps()[2].row==2)
assert(model.selected_map().name=='forest')
assert(model.save~=nil and model.packs[1][2]==true and model.packs[2][2]==false)
local state={options={}}
package.preload['polish-fighters/dashboard_model']=function() return model end
model.pending_map=4
local selection=dofile(root..'/engine/scripts/polish-fighters/selection.lua')({create=function() return state end})
selection.create({mode='versus'})
assert(state.options.background==4 and state.options.random_background==false)
assert(model.pending_map==nil)
state.options.background=1
selection.create({mode='versus'})
assert(state.options.background==1)
print('PASS: dashboard defaults, save preservation, failure, pack availability, one-shot map preset')
