return function(base)
 local create=base.create
 local background=require('base/game/background')
 local scenes=require('mixed-all/dbz_scenes')
 local runtime=require('mixed-all/dbz_runtime')
 local objects=require('base/game/objects')
 function base.create(options)
  background.reset_scene_modes()
  local entry=options.backgrounds[options.background+1]
  if entry and scenes[entry.path] then background.select_mode(entry.path,options.scene_mode or 0) end
  local state=create(options)
  runtime.spawn(state,objects)
  return state
 end
 return base
end
