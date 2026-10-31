return function(flow)
 local create,update,describe=flow.create,flow.update,flow.describe
 function flow.create(options)
  require("base/game/network").next_room=true
  require("polish-fighters/dashboard_model").current().room_capacity=require("room-check/config").players
  return create(options)
 end
 function flow.update(s,input,context)
  local result=update(s,input,context)
  if s.session and s.session.room and not s.test_match and not require("room-check/config").menu then
   s.test_match=true
   local catalog=require("base/game/catalog");local fighters=catalog.load();local slots={}
   for _,peer in ipairs(s.session.peers) do
    local selected=peer.slot%#fighters+1
    if require("room-check/config").own then
     selected=nil
     for row,fighter in ipairs(fighters) do if fighter.id==410+peer.slot%4 then selected=row;break end end
     assert(selected,"own fighter missing in network fixture")
    end
    slots[peer.slot]={kind="human",fighter=selected,team=peer.slot+1}
   end
   s.match=require("base/ui/match_screen").create({mode=0,difficulty=0,background=0,
    fighters=fighters,backgrounds=catalog.backgrounds(),slots=slots,network=true})
   s.active="match";s.wait_release=nil
  end
  if s.session and s.test_match and require("room-check/config").damage_probe and s.session.slot==1 and s.match.match.frame_number==5 then
   s.match.match.items[1].hp=s.match.match.items[1].hp-1
  end
  return result
 end
 function flow.describe(s)
  local detail=describe(s)
  if s.test_match or s.session then
   detail=detail.." room_slot="..s.network.session.slot.." room_digest="..require("polish-fighters/sync_state").digest(s)
   local m=s.match and s.match.match or {items={}}
   for i=0,7 do if m.items[i] then detail=detail.." player"..i.."="..m.items[i].x_int..":"..m.items[i].hp end end
  end
  return detail
 end
 return flow
end
