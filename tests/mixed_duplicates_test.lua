local doc={little_fighters_packs={}}
engine={read_settings=function() return doc end}
package.preload['mixed-all/metadata']=function() return {
 [1000]={pack='lf4-turbo',id=0},[1001]={pack='kate',id=0},
 [1002]={pack='dbz',id=0},[1003]={pack='lf4-turbo',id=30}} end
local function fixture()
 package.loaded['mixed-all/metadata']=nil
 local fighters={{id=0,name='Deep',record=0},{id=30,name='Julian',record=1,hidden=true},
  {id=410,name='Wasyl',record=2},{id=1000,name='Deep',record=3},
  {id=1001,name='DEEP',record=4},{id=1002,name='Goku',record=5},
  {id=1003,name='Julian',record=6,hidden=true}}
 local unlocked=false
 local catalog=dofile(arg[1]..'/content-packs/mixed-all/catalog.lua')({
  load=function() return fighters end,
  selectable=function(f) return not f.hidden or unlocked end})
 catalog.load();catalog.load()
 return catalog,fighters,function() unlocked=true end
end
local catalog,fighters,unlock=fixture()
assert(#fighters==7 and fighters[4].record==3 and fighters[5].id==1001,'records changed')
assert(catalog.selectable(fighters[1]) and not catalog.selectable(fighters[4]) and not catalog.selectable(fighters[5]))
assert(catalog.selectable(fighters[3]) and catalog.selectable(fighters[6]),'unique heroes hidden')
assert(not catalog.random_eligible(fighters[4]),'random selection exposed hidden duplicate')
assert(fighters[4].name=='[lf4-turbo] Deep','labels repeated')
assert(not catalog.selectable(fighters[2]));unlock()
assert(catalog.selectable(fighters[2]) and not catalog.selectable(fighters[7]),'hidden character unlock bypasses dedup')
doc.little_fighters_packs={lf_two=false,lf_four_turbo=false}
catalog,fighters=fixture()
assert(not catalog.selectable(fighters[1]) and not catalog.selectable(fighters[4]))
assert(catalog.selectable(fighters[5]),'one selected mod must retain its Deep without LF2')
doc.little_fighters_hide_duplicates=false;doc.little_fighters_packs={}
catalog,fighters=fixture()
assert(catalog.selectable(fighters[1]) and catalog.selectable(fighters[4]) and catalog.selectable(fighters[5]))
print('PASS: basic LF2 duplicates hidden in mixed selection and random; selected-pack fallback, opt-out, unlocks, unique heroes and records preserved')
