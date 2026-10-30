return function(base)
 base.source_path="mods/kate/a/000718.txt"
 base.stage_path="mods/kate/a/000609.dat"
 base.profile_id="kate"
 -- Recovered dependency used by Treature effects; not a player selection.
 local selectable=base.selectable
 function base.selectable(fighter)
  return fighter.id~=99 and selectable(fighter)
 end
 return base
end
