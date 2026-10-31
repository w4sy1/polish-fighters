local root=arg[1]
local calls={}
local base={play=function(path)calls[#calls+1]={'play',path} end,stop=function()calls[#calls+1]={'stop'} end}
assert(loadfile(root..'/content-packs/dbz/music.lua'))()(base)
base.play('[MU]');base.play('[mu]');base.play('bgm/stage1.wma')
assert(#calls==3 and calls[1][1]=='stop' and calls[2][1]=='stop')
assert(calls[3][1]=='play' and calls[3][2]=='bgm/stage1.wma')
