return function(base)
 local create=base.create
 function base.create(options)
  local state=create(options)
  local catalog=require("base/game/catalog")
  local fighters=catalog.load()
  local index
  for i,f in ipairs(fighters) do if f.id==55 then index=i end end
  assert(index,"LeumasEX is missing")
  state.match=require("base/ui/match_screen").create({mode=0,difficulty=0,background=0,
   fighters=fighters,backgrounds=catalog.backgrounds(),slots={
    [0]={kind="human",fighter=index,team=1},[1]={kind="computer",fighter=index,team=2}}})
  state.active="match";state.wait_release=nil
  return state
 end
 return base
end
