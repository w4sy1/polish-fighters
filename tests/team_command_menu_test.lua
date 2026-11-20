local m = require("base/ui/team_command_menu")
local h = require("base/ui/team_command_hud")
local l = require("base/ui/hybrid_layout")
local commands = require("base/game/team_commands")
local function center(box) return box.x + box.w / 2, box.y + box.h / 2 end
local function click(state, layout, box, touch)
    local x, y = center(box)
    if touch then
        local input = {contacts = {{id=7, phase="d", x=x, y=y}, {id=8, phase="d", x=4, y=480}}}
        m.update(state, {}, true, layout, false, false, input)
        assert(#input.contacts==1 and input.contacts[1].id==8)
        local release = {contacts = {{id=7, phase="u", x=x, y=y}}}
        m.update(state, {}, true, layout, false, false, release)
        assert(#release.contacts==0)
    else
        m.update(state, {click=true, pointer_x=x, pointer_y=y}, true, layout, false, false)
    end
end

for _, screen in ipairs({l.screen, {left=-155,right=949,top=0,bottom=550}}) do
    for _, touch in ipairs({false,true}) do
        local controls = touch and l.geometry(l.copy(), screen)
        local layout = assert(m.layout(screen,touch,controls))
        local state = {owned={}}
        for _, box in ipairs(layout) do
            click(state, layout, layout.trigger, touch)
            assert(state.open and not state.pending)
            click(state, layout, box, touch)
            assert(not state.open and state.pending==commands.signals[box.command])
            state.pending=nil
        end
        if touch then assert(layout.trigger.y < controls.s1.y - controls.s1.ry) end
        click(state, layout, layout.trigger, touch)
        local labels = {}
        h.draw({overlay=function() end, fill=function() end, text=function(s) labels[#labels+1]=s end}, state)
        assert(table.concat(labels,",")=="ATTACK,STAY,COME,DEFEND")
        assert(m.update(state, {}, true, layout, false, true))
        assert(not state.open)
        m.update(state, {}, true, layout, true, false)
        assert(state.open)
        m.update(state, {}, false, layout, false, false)
        assert(not state.open and not state.layout)
    end
end

for order in pairs(commands.signals) do
    local label, tail
    h.draw_order({
        fill=function(x,y) if y==221 then tail=x end end,
        text=function(text,x,y,align)
            assert(x==38 and y==202 and align=="center")
            label=text
        end,
    }, order, 7, 200, 0, 794)
    assert(label==order:upper() and tail==5, "bubble must stay visible and point to the fighter")
end
