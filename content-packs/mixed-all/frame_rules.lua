return function(base)
 local before=base.before_advance
 local objects=require('base/game/objects')
 local metadata=require('mixed-all/metadata')
 function base.before_advance(state,index,value)
  local current=value.record.frame(value.frame).state
  if current>=300000 then
   local origin=metadata[value.record.id]
   local target=objects.record(state,current-300000)
   if target then
    value.record=target;value.frame=0
    value.pic_offset=origin and origin.pack=='bleach' and 0 or 140
   end
   -- A missing source target must not turn into a different pack's character.
  end
  return before(state,index,value)
 end
 return base
end
