local root=arg[1]
local scenes=assert(loadfile(root..'/content-packs/dbz/scene-modes.lua'))()
package.loaded['dbz/scene-modes']=scenes
local path, scene=next(scenes)
local layers={}
for index=1,#scene.layer_respond do layers[index]={resource='test', marker=index} end
local original={layers=layers,width=42,zboundary={1,2},groups_ready=true}
local base={load=function()return original end}
assert(loadfile(root..'/content-packs/dbz/background.lua'))()(base)
local count, modes=0,0
for key, definition in pairs(scenes) do
 count=count+1
 for index,mode in ipairs(definition.modes) do
  modes=modes+1
  base.select_mode(key,index-1)
  local got=base.load(key)
  assert(got.width==mode.width and got.zboundary[1]==mode.zboundary[1])
  assert(got~=original and got.layers~=original.layers and got.groups_ready==nil)
  local enabled={};for _,r in ipairs(mode.respond or {0}) do enabled[r]=true end
  for _,layer in ipairs(got.layers) do assert(enabled[definition.layer_respond[layer.marker] or 0]) end
 end
end
assert(count==14 and modes==50)
assert(original.width==42 and original.groups_ready)
local constants=assert(loadfile(root..'/content-packs/dbz/constants.lua'))()({frame_limit=400})
assert(constants.frame_limit==999)
assert(require('base/game/constants').frame_limit==400)
