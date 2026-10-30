local root=arg[1]
local catalog_text='<object>\nid: 1 type: 0 file: first.txt\nid: 2 type: 0 file: internal.txt\nid: 3 type: 0 file: last.txt\n<object_end>'
local files={['data/data.txt']=catalog_text,['first.txt']='<bmp_begin> name: First head: first.bmp <bmp_end>',
 ['internal.txt']='<bmp_begin> hidden: 4\n<bmp_end>', ['last.txt']='<bmp_begin> name: Last head: last.bmp <bmp_end>'}
engine={read_resource=function(path) return assert(files[path]) end}
local strict=dofile(root..'/engine/scripts/base/game/catalog.lua')
assert(not pcall(strict.load))
local allowed=dofile(root..'/engine/scripts/base/game/catalog.lua');allowed.hidden_helpers=true
local fighters=allowed.load()
assert(#fighters==2 and fighters[1].id==1 and fighters[2].id==3)
assert(fighters[2].record==2,'internal record must retain its original index')
assert(allowed.objects().by_id[2].path=='internal.txt','internal actor must remain spawnable')
files['internal.txt']='<bmp_begin> name: Background_NPC\nhidden: 4\n<bmp_end>'
local named=dofile(root..'/engine/scripts/base/game/catalog.lua');named.hidden_helpers=true
assert(#named.load()==2,'named internal NPC without portrait must also be excluded')
print('PASS: opt-in internal actors, strict default and original record indices')
