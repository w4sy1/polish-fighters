local root=arg[1]
local constants=require('base/game/constants')
local target={id=12,kind=0,frame=function() return {state=0} end}
package.loaded['base/game/objects']={record=function(_,id) if id==12 then return target end end}
package.loaded['base/game/merge']={}
package.loaded['base/game/unlock']={}
local function rules(bleach)
    local value=dofile(root..'/engine/scripts/base/game/frame_rules.lua')
    if bleach then value=dofile(root..'/content-packs/bleach/frame_rules.lua')(value) end
    return value
end
for _,bleach in ipairs({false,true}) do
    for _,frame_state in ipairs({7999,8012,8999,9000}) do
        local source={id=1,kind=0,frame=function() return {state=frame_state} end}
        local item={record=source,frame=4,pic_offset=7,wait_counter=0}
        rules(bleach).before_advance({},0,item)
        if frame_state>=8000 and frame_state<9000 then
            assert(item.frame==0)
            assert(item.pic_offset==(bleach and 0 or 140))
            if frame_state==8012 then assert(item.record==target) end
        else
            assert(item.frame==4 and item.pic_offset==7 and item.record==source)
        end
    end
end
assert(rules(false).record_transform_picture_offset==140, 'pack option leaked into classic')
print('PASS: Bleach transformation offset, record switch, range bounds and classic isolation')
