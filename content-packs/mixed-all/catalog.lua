return function(base)
 local metadata=require('mixed-all/metadata')
 local selected=assert(require('polish-fighters/pack_preferences').read(require('polish-fighters/hub').profiles))
 local hide_duplicates,problem=require('polish-fighters/pack_preferences').hide_duplicates()
 assert(not problem,problem)
 local groups={}
 local function name_key(name) return name:lower():gsub('_',' '):gsub('%s+','') end
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
   fighter.pf_source_name=fighter.pf_source_name or fighter.name
   local origin=metadata[fighter.id]
   if origin and not fighter.pack then
    fighter.pack,fighter.legacy_id=origin.pack,origin.id
    fighter.name='['..origin.pack..'] '..fighter.name
    local family=math.floor(origin.id/10)
    fighter.hidden=family==3 or family==5
   end
  end
  -- Hide selection tiles only. Keep every object/record for scripts, spawns and replays.
  local classic={}
  for _,fighter in ipairs(fighters) do
   if not metadata[fighter.id] and fighter.id<410 then classic[name_key(fighter.pf_source_name)]=true end
  end
  groups={}
  for _,fighter in ipairs(fighters) do
   local key=name_key(fighter.pf_source_name)
   if classic[key] then
    groups[key]=groups[key] or {};groups[key][#groups[key]+1]=fighter
   end
  end
  return fighters
 end
 local function permitted(fighter)
  local origin=metadata[fighter.id]
  local tag=origin and tags[origin.pack] or (fighter.id>=410 and fighter.id<=415 and 'polish_fighters' or 'lf_two')
  if selected[tag]==false then return false end
  if origin then local family=math.floor(origin.id/10);fighter.hidden=family==3 or family==5 end
  return selectable(fighter)
 end
 function base.selectable(fighter)
  if not permitted(fighter) then return false end
  if hide_duplicates then
   local group=groups[name_key(fighter.pf_source_name or fighter.name)]
   if group then
    for _,candidate in ipairs(group) do
     if permitted(candidate) then return candidate==fighter end
    end
   end
  end
  return true
 end
 function base.random_eligible(fighter) return base.selectable(fighter) end
 return base
end
