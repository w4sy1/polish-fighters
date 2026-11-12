return function(base)
 local create,describe=base.create,base.describe
 function base.create(options)
  local s=create(options)
  local catalog=require('base/game/catalog')
  local fighters=catalog.load()
  s.characters=require('base/ui/character_select').create({mode='versus'})
  s.characters.slots[0].phase=3
  s.characters.slots[0].ready=true
  s.characters.options.background=0
  s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,
   fighters=fighters,backgrounds=catalog.backgrounds(),slots={
    [0]={kind='human',fighter=1,team=1},[1]={kind='computer',fighter=2,team=2}}})
  s.active='match';s.wait_release=nil
  return s
 end
 function base.describe(s)
  return describe(s)..' ready0='..tostring(s.characters.slots[0].ready)
 end
 return base
end
