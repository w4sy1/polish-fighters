local training={}
function training.prepare(options)
 if not options.training or options.network or options.replay or options.mode~=0 then return end
 local chosen=options.slots[0]
 if not chosen or chosen.kind~='human' then return end
 options.slots[1]={kind='computer',fighter=chosen.fighter,team=chosen.team==1 and 2 or 1}
end
function training.reset(state)
 if not state.training then return end
 state.round_counter=0;state.finished=false;state.winner=-1
 for index,v in pairs(state.items) do
  if not v.human and index<20 and v.record.kind==0 and v.hp<=0 then
   v.hp,v.dark_hp=v.max_hp,v.max_hp;v.frame=0;v.wait_counter=0;v.hit_lag=0
   v.x_int,v.x=500,500;v.y_int,v.y=0,0;v.z_int,v.z=300,300
   v.vx,v.vy,v.vz=0,0,0
  end
 end
end
function training.lines(state)
 local v=state.items[0];if not v then return {} end
 local keys={}
 for _,name in ipairs({'up','down','left','right','attack','jump','defend'}) do if v.keys[name] then keys[#keys+1]=name end end
 local clones=0
 for _,t in pairs(state.items) do if (t.pf_clone or t.spawn_clone_generation) and t.hp>0 then clones=clones+1 end end
 return {'TRENING / TRAINING | F4 - POSTACIE','INPUT: '..table.concat(keys,' + '),
  string.format('FRAME: %d | HP: %d | MP: %d | KLONY: %d',v.frame,v.hp,v.mp,clones)}
end
return training
