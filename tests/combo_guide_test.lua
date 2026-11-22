local document={}
engine={read_settings=function() return document end,write_settings=function(value) document=value;return true end}
package.loaded['base/game/catalog']={profile_id='polish-originals',load=function() return {{id=410,name='Wasyl'}} end,
 backgrounds=function() return {} end,selectable=function() return true end}
package.loaded['polish-fighters/dashboard_model']={current=function() return {map=0,room_capacity=8} end,
 contents=function() return {fighters={{id=410,name='Wasyl'}},campaigns={}} end}
package.loaded['base/ui/navigation']={create=function() return {} end,
 target=function(l,t,r,b) return {left=l,top=t,right=r,bottom=b} end,apply=function(s,input) return input end}
local guide=require('polish-fighters/combo_guide')
assert(#guide.order==6 and #guide.basics==12)
for _,id in ipairs(guide.order) do
 local moves=guide.moves(id);assert(#moves==7)
 for index,move in ipairs(moves) do assert(move[3]==290+index*10,'guide uses the wrong actual move frame') end
 assert(#guide.message(id)==10,'guide overflows its nine-line body')
end
local screen=dofile(arg[1]..'/engine/scripts/polish-fighters/classic_shell.lua')({
 create=function() return {page='menu',background=1} end,update=function() end,draw=function() end,describe=function() return '' end})
local s=screen.create({});s.pf_panel='combo-guide';s.pf_root_panel='combo-guide'
local context={action=function() end}
local function click(index)
 screen.update(s,{keys={},nav={},click=true,pointer_x=420,pointer_y=219+(index-1)*25},context)
end
for row=1,6 do
 click(row);assert(s.pf_message[1]==guide.message(guide.order[row])[1] and s.pf_guide_message,'move list entry must open that hero\'s moves')
 click(1);assert(not s.pf_message)
end
click(7);assert(not s.pf_panel,'back must close the move list, no combo-guide filler screens left')
print('PASS: six heroes and mech, real frame mappings, plain move list with no combo-guide tutorial/roster filler')
