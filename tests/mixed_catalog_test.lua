engine={read_settings=function() return {little_fighters_packs={dbz=false}} end}
package.preload['mixed-all/metadata']=function() return {[1000]={pack='dbz',id=1},[1001]={pack='bleach',id=1}} end
local fighters={{id=1,name='Deep'},{id=410,name='Wasyl'},{id=1000,name='Goku'},{id=1001,name='Ichigo'}}
local original={load=function() return fighters end,selectable=function(f) return not f.hidden end}
local catalog=dofile(arg[1]..'/content-packs/mixed-all/catalog.lua')(original)
assert(catalog.object_limit==4096 and catalog.fighter_limit==2048)
local constants=dofile(arg[1]..'/content-packs/mixed-all/constants.lua')({})
assert(constants.background_rows.random>256 and constants.background_rows.lee_on_road>256,
 'mixed map 99/100 must not collide with classic special selectors')
catalog.load();catalog.load()
assert(fighters[3].name=='[dbz] Goku','pack labels duplicated after cache reload')
assert(not catalog.selectable(fighters[3]) and catalog.selectable(fighters[4]))
assert(catalog.selectable(fighters[1]) and catalog.selectable(fighters[2]))
local called=false
local target={id=1001,frame=function() return {state=0} end}
package.preload['base/game/objects']=function() return {record=function(s,id) assert(id==1001);return target end} end
local rules=dofile(arg[1]..'/content-packs/mixed-all/frame_rules.lua')({before_advance=function() called=true end})
local value={record={id=1001,frame=function() return {state=301001} end},frame=5}
rules.before_advance({},0,value)
assert(called and value.record==target and value.frame==0 and value.pic_offset==0)
print('PASS: mixed catalog filters packs, stable labels, limits and scoped Bleach transformation')
