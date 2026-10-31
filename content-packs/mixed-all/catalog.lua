return function(base)
 local metadata=require('mixed-all/metadata')
 local selected=assert(require('polish-fighters/pack_preferences').read(require('polish-fighters/hub').profiles))
 local tags={['lf4-turbo']='lf_four_turbo',dbz='dbz',['one-piece']='one_piece',kate='kate',
   reinforced='reinforced',ntsd='ntsd',bleach='bleach'}
 base.source_path='mods/mixed-all/catalog.txt'
 base.profile_id='mixed-all'
 base.mixed_pool=true
 base.hidden_helpers=true
 base.object_limit=4096;base.fighter_limit=2048;base.background_limit=256
 -- Cross-mod versus uses standard LF2 campaigns until authored scene semantics are integrated.
 base.stage_path='data/stage.dat';base.campaigns=nil
 local load,selectable=base.load,base.selectable
 function base.load()
  local fighters=load()
  for _,fighter in ipairs(fighters) do
   local origin=metadata[fighter.id]
   if origin and not fighter.pack then
    fighter.pack,fighter.legacy_id=origin.pack,origin.id
    fighter.name='['..origin.pack..'] '..fighter.name
    local family=math.floor(origin.id/10)
    fighter.hidden=family==3 or family==5
   end
  end
  return fighters
 end
 function base.selectable(fighter)
  local origin=metadata[fighter.id]
  local tag=origin and tags[origin.pack] or (fighter.id>=410 and fighter.id<=413 and 'polish_fighters' or 'lf_two')
  if selected[tag]==false then return false end
  if origin then local family=math.floor(origin.id/10);fighter.hidden=family==3 or family==5 end
  return selectable(fighter)
 end
 function base.random_eligible(fighter) return base.selectable(fighter) end
 return base
end
