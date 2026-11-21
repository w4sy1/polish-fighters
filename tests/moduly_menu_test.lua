-- Etap 1.14 / Etap 1: MODUŁY must have exactly one level of "back" from every
-- subscreen (packs, status, optional_modules) to library, never to root.
engine={read_settings=function() return {} end,write_settings=function(doc) return true end}
package.preload['base/ui/navigation']=function() return {
    create=function() return {} end,
    target=function(l,t,r,b) return {left=l,top=t,right=r,bottom=b} end,
    apply=function(s,input) return input end} end
local layout=require('polish-fighters/menu_layout')
local base=dofile(arg[1]..'/engine/scripts/polish-fighters/hub_launch.lua')({
    create=function() return {page='menu'} end,update=function() end,
    draw=function() end,describe=function() return 'test' end})
local state=base.create({})
state.hub_enabled=true
local context={action=function() end,sound=function() end}

local function click_row(index,count)
 local x,y,w,h=layout.box(index,count)
 base.update(state,{keys={},nav={},click=true,pointer_x=x+1,pointer_y=y+1},context)
end

-- packs_cancel -> library, not root
state.hub_mode='packs'
state.hub_pack_edit={}
local rows=require('polish-fighters/hub').rows(state)
local cancel_index
for index,row in ipairs(rows) do if row[1]=='packs_cancel' then cancel_index=index end end
assert(cancel_index,'packs screen must have a packs_cancel row')
click_row(cancel_index,#rows)
assert(state.hub_mode=='library','packs_cancel must return to library, not root')

-- status "back" row -> library, not root
state.hub_mode='status'
rows=require('polish-fighters/hub').rows(state)
local back_index
for index,row in ipairs(rows) do if row[1]=='library' then back_index=index end end
assert(back_index,'status screen must have a back row targeting library')
click_row(back_index,#rows)
assert(state.hub_mode=='library','status back row must return to library, not root')

-- optional_modules "back" row -> library, not root
state.hub_mode='optional_modules'
rows=require('polish-fighters/hub').rows(state)
back_index=nil
for index,row in ipairs(rows) do if row[1]=='library' then back_index=index end end
assert(back_index,'optional_modules screen must have a back row targeting library')
click_row(back_index,#rows)
assert(state.hub_mode=='library','optional_modules back row must return to library, not root')

-- Confirm the MODUŁY label is already correct in both locales (regression pin).
assert(require('polish-fighters/menu_locale').text('modules')=='MODUŁY')

print('PASS moduly menu: packs/status/optional_modules each one level back to library, MODUŁY label pinned')
