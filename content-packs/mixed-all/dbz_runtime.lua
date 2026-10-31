-- Global scene opoints are distinct from character-relative frame opoints.
local runtime = {}
function runtime.spawn(state, objects)
    local scene, mode = state.stage.dbz_scene, state.stage.dbz_mode
    if not scene then return end
    local enabled = {}
    for _, value in ipairs(mode.arest or {0}) do enabled[value] = true end
    state.dbz_scene_objects = {}
    for _, point in ipairs(scene.opoints) do
        local selector = point.arest and point.arest[1] or 0
        if enabled[selector] then
            assert(point.kind == 1, "unsupported DBZ global opoint kind")
            local slot = objects.free_slot(state)
            assert(slot >= 0, "no free slot for DBZ scene object")
            local record = assert(objects.record(state, point.oid), "missing DBZ scene object " .. point.oid)
            assert(record.frames[point.action] and not record.frames[point.action].undefined,
                "missing DBZ scene action " .. point.oid .. "/" .. point.action)
            local value = assert(objects.place(state, slot, point.oid))
            value.frame, value.owner, value.team = point.action, slot, 0
            value.x, value.y, value.z = point.x or 0, point.y or 0, point.z or 0
            value.x_int, value.y_int, value.z_int = value.x, value.y, value.z
            value.vx, value.vy, value.vz = point.dvx or 0, point.dvy or 0, point.dvz or 0
            value.facing = point.facing or 0
            if point.hp then value.hp, value.max_hp, value.dark_hp = point.hp, point.hp, point.hp end
            state.dbz_scene_objects[#state.dbz_scene_objects + 1] = {slot=slot,oid=point.oid,action=point.action}
        end
    end
end
function runtime.transition(state,selected,backgrounds,background,objects)
    local entry=assert(backgrounds[selected.row+1],'missing DBZ transition background')
    for _,owned in ipairs(state.dbz_scene_objects or {}) do
        local value=state.items[owned.slot]
        if value and value.record.id==owned.oid then objects.remove(state,owned.slot) end
    end
    background.select_mode(entry.path,selected.mode or 0)
    state.stage=background.load(entry.path)
    state.view=background.create_state(state.stage)
    state.background_row=selected.row
    state.camera,state.camera_step,state.camera_limit,state.stage_bound=0,0,0,0
    local near,far=state.stage.zboundary[1],state.stage.zboundary[2]
    for _,value in pairs(state.items) do
        value.z=math.max(near,math.min(far,value.z));value.z_int=math.floor(value.z)
        value.x=math.max(0,math.min(state.stage.width,value.x));value.x_int=math.floor(value.x)
    end
    runtime.spawn(state,objects)
    state.dbz_scene_transitions=(state.dbz_scene_transitions or 0)+1
end
return runtime
