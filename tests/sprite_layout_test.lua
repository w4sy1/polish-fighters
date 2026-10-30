local root=arg[1]
local original=require('base/game/object_data')
local base={picture=original.picture}
local patched=assert(loadfile(root..'/content-packs/bleach/sprite_layout.lua'))()(base)
local function data(resource,w,h,cols,rows,picture)
 return {frames={[0]={picture=picture}},sheets={{resource=resource,cell_width=w,cell_height=h,columns=cols,rows=rows,first_picture=0}}}
end
local d=data('mods/bleach/a/000188.bmp',42,150,15,1,14)
local resource,rect=patched.picture(d,0)
assert(resource and rect[1]==588 and rect[3]==42)
assert(d.frames[0].picture==14)
d.frames[0].picture=13
_,rect=patched.picture(d,0,1)
assert(rect[1]==588)
_,rect=patched.picture(data('mods/bleach/a/000240.bmp',80,90,4,1,3),0)
assert(rect[1]==240)
assert(patched.picture(data('mods/bleach/a/000573.bmp',79,99,10,21,200),0)==nil)
_,rect=patched.picture(data('mods/bleach/a/000573.bmp',79,99,10,21,19),0)
assert(rect[1]==720 and rect[2]==100)
-- Physical intersection preserves existing pixels, with no stretch/replacement image.
_,rect=patched.picture(data('mods/bleach/a/000573.bmp',80,99,10,21,9),0)
assert(rect[1]==729 and rect[3]==70 and rect[4]==99)
-- Right-facing anchor is unchanged. Left-facing anchor shifts by the trimmed right edge.
local anchor,center=400,40
assert(anchor+center-rect[3]==anchor+center-80+10)
_,rect=patched.picture(data('mods/bleach/a/000210.bmp',53,155,1,1,0),0)
assert(rect[3]==53 and rect[4]==71)
assert(patched.picture(d,999)==nil)
_,rect=original.picture(data('mods/bleach/a/000188.bmp',42,150,15,1,14),0)
assert(rect[1]==602)
print('PASS: packed strides, offsets, empty and partial clipping, profile isolation')
