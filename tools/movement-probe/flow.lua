return function(base)
 local create=base.create
 function base.create(options)
  local state=create(options)
  local catalog=require('base/game/catalog')
  local match=require('base/game/match')
  local fighters=catalog.load()
  local results={}
  for row,fighter in ipairs(fighters) do
   if not fighter.internal then
    local m=match.create({mode=0,difficulty=0,background=0,fighters=fighters,backgrounds=catalog.backgrounds(),slots={
     [0]={kind='human',fighter=row,team=1},[1]={kind='human',fighter=row,team=2}}})
    local a,b=m.items[0],m.items[1]
    a.x_int,a.x,b.x_int,b.x=200,200,500,500
    a.blink,b.blink=0,0
    local start=a.x_int
    for tick=1,40 do match.step(m,{[0]='r',functions='',keys={}}) end
    local moved=math.abs(a.x_int-start)>5
    a.x_int,a.x,b.x_int,b.x=200,200,245,245
    b.z_int,b.z=a.z_int,a.z
    local attacking=false
    for tick=1,100 do
     match.step(m,{[0]=tick%8<4 and 'c' or '',functions='',keys={}})
     local frame=a.record.frame(a.frame)
     if frame.state==3 or frame.state==4 or (a.frame>=60 and a.frame<100) then attacking=true end
    end
    local ai_match=match.create({mode=0,difficulty=0,background=0,fighters=fighters,backgrounds=catalog.backgrounds(),slots={
     [0]={kind='human',fighter=row,team=1},[1]={kind='computer',fighter=row,team=2}}})
    local human,computer=ai_match.items[0],ai_match.items[11]
    human.x_int,human.x,computer.x_int,computer.x=200,200,400,400
    computer.z_int,computer.z=human.z_int,human.z
    human.blink,computer.blink=0,0
    local ai_moved,ai_attack,ai_action=false,false,false
    local initial_hp=human.hp
    for tick=1,300 do
     match.step(ai_match,{functions='',keys={}})
     if math.abs(computer.x_int-400)>5 then ai_moved=true end
     if computer.keys.attack then ai_attack=true end
     if computer.record.frame(computer.frame).state==3 then ai_action=true end
    end
    results[#results+1]=tostring(fighter.id)..':'..tostring(fighter.name)..':move='..tostring(moved)..':attack='..tostring(attacking)..':ai_move='..tostring(ai_moved)..':ai_attack='..tostring(ai_attack)..':ai_action='..tostring(ai_action)..':ai_damage='..tostring(human.hp<initial_hp)
   end
  end
  state.probe_results=table.concat(results,'\n')
  return state
 end
 function base.update() end
 function base.draw(s,c) c.viewport(794,550,0,0,0) end
 function base.describe(s) return s.probe_results end
 return base
end
