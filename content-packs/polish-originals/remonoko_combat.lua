return function(base)
 local apply=base.apply
 local rn=require('polish-originals/remonoko')
 local heroes=require('polish-originals/heroes')
 function base.apply(state,index)
  local attacker=state.items[index]
  local restored={}
  local original_list,original_itr,original_count
  if attacker and attacker.pf_family~=nil and attacker.hit_list_count>0 then
   original_list,original_itr,original_count=attacker.hit_list,attacker.hit_list_itr,attacker.hit_list_count
   local list,itrs={},{}
   for n=1,original_count do
    local victim=state.items[original_list[n]]
    if not victim or not heroes.family(attacker,victim) then
     list[#list+1]=original_list[n];itrs[#itrs+1]=original_itr[n]
    end
   end
   attacker.hit_list,attacker.hit_list_itr,attacker.hit_list_count=list,itrs,#list
  end
  if attacker then
   local frame=attacker.record.frame(attacker.frame_at_pass)
   for n=1,attacker.hit_list_count do
    local victim=state.items[attacker.hit_list[n]]
    local itr=frame.interactions[attacker.hit_list_itr[n]]
    if victim and rn.owns(victim) and itr then
     if restored[victim]==nil then restored[victim]=victim.armor end
     local contact={y=itr.y,h=itr.height,centery=frame.center_y or frame.centery}
     victim.armor=rn.armor(victim,attacker,contact)
    end
   end
  end
  local ok,result=pcall(apply,state,index)
  for victim,armor in pairs(restored) do victim.armor=armor end
  if original_list then attacker.hit_list,attacker.hit_list_itr,attacker.hit_list_count=original_list,original_itr,original_count end
  if not ok then error(result) end
  return result
 end
 return base
end
