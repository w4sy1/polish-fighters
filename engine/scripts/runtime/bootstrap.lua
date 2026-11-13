-- SPDX-License-Identifier: MIT
-- Copyright (c) 2026 OpenLF2 contributors

-- Trusted runtime implementation. The host prepends the validated declarations table.
local compile = loadstring or load
local read_resource = openlf2_read_resource
local read_object_data = openlf2_read_object_data
local read_background_data = openlf2_read_background_data
local read_stage_data = openlf2_read_stage_data
local random = openlf2_random
local crt_random = openlf2_crt_random
local read_settings = openlf2_read_settings
local write_settings = openlf2_write_settings
local random_state, set_random_state = openlf2_random_state, openlf2_set_random_state
local reset_random_sequence = openlf2_reset_random_sequence
local save_recording, take_recording = openlf2_save_recording, openlf2_take_recording
local local_time = openlf2_local_time
local build_label = openlf2_build_label
local application_version='0.15.0-mod-browser-test'
local new_table = jit and require("table.new")
local function new_array(capacity)
    if new_table then return new_table(capacity, 0) end
    return {}
end
local json_encode, json_decode, state_digest = openlf2_json_encode, openlf2_json_decode, openlf2_state_digest
local network, network_time = openlf2_network, openlf2_network_time
local account = openlf2_account
local updates = openlf2_updates
local set_environment = setfenv
local unpack_values = unpack or table.unpack
local traceback = debug.traceback
local protected_call = xpcall
local module_definitions, module_cache, loading = {}, {}, {}

local function copy_library(library)
    local copy = {}
    for key, value in pairs(library) do copy[key] = value end
    return copy
end

local load_module
local function evaluate(declaration, previous)
    local environment = {
        assert = assert, error = error, ipairs = ipairs, pairs = pairs,
        next = next, select = select, tonumber = tonumber, tostring = tostring,
        type = type, unpack = unpack_values, pcall = pcall,
        math = copy_library(math), string = copy_library(string), table = copy_library(table),
        require = load_module,
        engine = {read_resource = read_resource, read_object_data = read_object_data,
            read_background_data = read_background_data, read_stage_data = read_stage_data,
            random = random, crt_random = crt_random, new_array = new_array,
            read_settings = read_settings, write_settings = write_settings,
            random_state = random_state, set_random_state = set_random_state,
            reset_random_sequence = reset_random_sequence, save_recording = save_recording,
            take_recording = take_recording, local_time = local_time, build_label = build_label,
            json_encode = json_encode, json_decode = json_decode, state_digest = state_digest,
            network = network, network_time = network_time, account = account, updates = updates},
    }
    environment.math.random = nil
    environment.math.randomseed = nil
    environment.string.dump = nil
    local chunk, message
    if set_environment then
        chunk, message = compile(declaration[4], "@" .. declaration[3])
    else
        chunk, message = compile(declaration[4], "@" .. declaration[3], "t", environment)
    end
    assert(chunk, message)
    if set_environment then set_environment(chunk, environment) end
    local exported = chunk()
    if declaration[1] == "extend" then
        assert(type(exported) == "function", declaration[3] .. ": extension must return a decorator")
        exported = exported(previous)
    end
    assert(type(exported) == "table", declaration[3] .. ": module must export a table")
    return exported
end

for _, declaration in ipairs(declarations) do
    local target = declaration[2]
    local chain = module_definitions[target] or {}
    if declaration[1] == "replace" then
        -- Replacement substitutes the base; explicit extensions still decorate the result.
        chain[1] = declaration
    elseif declaration[1] == "module" then
        assert(#chain == 0, "duplicate module: " .. target)
        chain[1] = declaration
    else
        chain[#chain + 1] = declaration
    end
    module_definitions[target] = chain
end

load_module = function(name)
    assert(type(name) == "string", "require expects a module name")
    if module_cache[name] then return module_cache[name] end
    assert(not loading[name], "cyclic module import: " .. name)
    local chain = assert(module_definitions[name], "module not declared: " .. name)
    loading[name] = true
    local exported
    for _, declaration in ipairs(chain) do exported = evaluate(declaration, exported) end
    loading[name] = nil
    module_cache[name] = exported
    return exported
end

local screen, i18n, state
-- Runtime-owned and bounded: never part of synchronized gameplay snapshots.
local recent_events, last_event = {}, nil
local function diagnostic_context()
    local match = state and state.match and state.match.match
    local run = match and match.stage_run
    local catalog = module_cache["base/game/catalog"] or {}
    local fighters, objects = {}, 0
    for slot, value in pairs(match and match.items or {}) do
        objects = objects + 1
        if type(slot)=="number" and slot>=0 and slot<8 then
            fighters[#fighters+1]={slot=slot,id=value.record and value.record.id}
        end
    end
    table.sort(fighters,function(a,b) return a.slot<b.slot end)
    return {screen=state and state.active or "startup",profile=catalog.profile_id,
        mode=match and match.mode,campaign=run and (run.source_path or catalog.stage_path),
        stage=run and run.id,phase=run and run.phase,frame=match and match.frame_number,
        fighters=fighters,object_count=objects}
end
local function note_event()
    local match=state and state.match and state.match.match
    local run=match and match.stage_run
    local key=table.concat({state and state.active or 'startup',tostring(run and run.id),tostring(run and run.phase)},':')
    local changed=key~=last_event
    local heartbeat=match and match.frame_number and match.frame_number%300==0
    if changed or heartbeat then
        local context=diagnostic_context()
        last_event=key;recent_events[#recent_events+1]=context
        if #recent_events>16 then table.remove(recent_events,1) end
        pcall(function()
            local doc=read_settings() or {}
            local report={};for field,value in pairs(context) do if field~='events' then report[field]=value end end
            report.events={};for index,event in ipairs(recent_events) do
                local entry={};for field,value in pairs(event) do if field~='events' then entry[field]=value end end
                report.events[index]=entry
            end
            report.version=application_version;report.native_version=build_label;report.time=local_time and local_time() or 'unknown'
            doc.polish_fighters_last_session=report;write_settings(doc)
        end)
    end
end
local function report_failure(problem)
    -- A broken/read-only configuration must never hide the original failure.
    pcall(function()
        local context=diagnostic_context()
        local message=tostring(problem):sub(1,12000):gsub("https?://%S+","[URL]")
        for _,key in ipairs({"token","password","secret","authorization"}) do
            local pattern=key:gsub('%a',function(c) return '['..c..c:upper()..']' end)
            message=message:gsub("("..pattern.."%s*[:=]%s*)%S+","%1[REDACTED]")
        end
        message=message:gsub('[Bb]earer%s+%S+','Bearer [REDACTED]')
        local modules,seen={},{}
        for _,declaration in ipairs(declarations) do
            local id=declaration[3]:match("^([^/]+)/")
            if id and not seen[id] then modules[#modules+1]=id;seen[id]=true end
        end
        table.sort(modules)
        local document=read_settings()
        if type(document)~="table" then document={} end
        context.version=application_version;context.native_version=build_label or 'unknown'
        context.platform=jit and jit.os or "unknown"
        context.architecture=jit and jit.arch or "unknown"
        context.system_version='not exposed by runtime'
        context.controllers={}
        local controls=module_cache['base/ui/controls']
        if controls and controls.current then
            local settings=controls.current()
            for index,value in ipairs(type(settings)=='table' and settings.sets or {}) do
                context.controllers[#context.controllers+1]={slot=index-1,device=value.device}
            end
        end
        context.lua_memory_kib=collectgarbage("count")
        context.time=local_time and local_time() or "unknown"
        context.traceback=message;context.modules=modules;context.events=recent_events
        document.polish_fighters_last_crash=context
        write_settings(document)
    end)
end
local started,problem=protected_call(function()
    screen=load_module("base/ui/flow")
    i18n=load_module("base/i18n/i18n")
    recent_events[#recent_events+1]=diagnostic_context()
    state=screen.create(runtime_settings or {menu_seed=0})
end,traceback)
if not started then report_failure(problem);error(problem) end
-- Private frame protocol: fixed-size numeric opcodes, matching FrameOpcode in
-- the Lua adapter. Reuse one flat buffer; the host validates each field once.
local FrameOpcode = {
    viewport = 1, sprite = 2, fill = 3, overlay = 4, render_area = 5,
    clip = 6, sound = 7, rumble = 8, music = 9, speed = 10,
    render_filter = 11, text_input = 12, replay_drop = 13, fullscreen = 14, action = 15, text = 16, file_dialog = 17, world_sprite = 18, scaled_sprite = 19,
}
local RumbleTarget = {gamepad = 0, phone = 1}
local MusicKind = {play = 0, stop = 1, resume = 2, volume = 3}
local RenderFilter = {nearest = 0, linear = 1, xbrz = 2}
local TextAlign = {left = 0, center = 1, right = 2}
local INVALID_ENUM = -1
local MAX_FRAME_COMMANDS = 4096
local frame_batch, previous_size = {}, 0
local function render(input)
    local size, count = 0, 0
    local function command(opcode, ...)
        assert(count < MAX_FRAME_COMMANDS, "frame command limit exceeded")
        local fields = select("#", ...)
        frame_batch[size + 1] = opcode
        for index = 1, fields do frame_batch[size + index + 1] = select(index, ...) end
        size, count = size + fields + 1, count + 1
    end
    local context = {}
    function context.scaled_sprite(resource, source, x, y, width, height, mirrored, tint)
        command(FrameOpcode.scaled_sprite, resource, source[1], source[2], source[3], source[4],
            x, y, width, height, not not mirrored, tint or 0xffffff)
    end
    -- What the frame has drawn that translated text must be able to restore (see i18n.paint_baked).
    local scene = {}
    function context.viewport(w, h, r, g, b)
        command(FrameOpcode.viewport, w, h, r, g, b)
        scene.red, scene.green, scene.blue = r, g, b
    end
    function context.sprite(resource, source, x, y, keyed, mirrored, flipped, tint, scale_x, translate_x)
        -- A translated language replaces the text baked into the sheet (only for unmirrored, unscaled sprites).
        local translated = i18n.active() and not (mirrored or flipped or (translate_x and translate_x ~= 0)
            or (scale_x and scale_x ~= 1))
        local solo = translated and i18n.solo(resource, source)
        if solo then
            local keep = solo.keep
            if keep then
                command(FrameOpcode.sprite, resource, keep[1], keep[2], keep[3], keep[4], x + keep[1] - source[1],
                    y + keep[2] - source[2], not not keyed, false, false, tint or 0xffffff, 1, 0)
            end
        else
            command(FrameOpcode.sprite, resource, source[1], source[2], source[3], source[4], x, y,
                not not keyed, not not mirrored, not not flipped, tint or 0xffffff, scale_x or 1, translate_x or 0)
        end
        if translated then i18n.paint_baked(context, scene, resource, source, x, y, keyed) end
    end
    function context.world_sprite(resource, source, x, y, mirrored, ground_y, azimuth, elevation, character, casts_shadow, shadow_blur, shadow_opacity)
        command(FrameOpcode.world_sprite, resource, source[1], source[2], source[3], source[4], x, y,
            true, not not mirrored, false, 0xffffff, 1, 0,
            ground_y, azimuth, elevation, not not character, not not casts_shadow, shadow_blur or 2, shadow_opacity or 0.275)
    end
    function context.fill(x, y, w, h, r, g, b, alpha) command(FrameOpcode.fill, x, y, w, h, r, g, b, alpha or 255) end
    function context.overlay(active) command(FrameOpcode.overlay, active) end
    function context.render_area(x, y, w, h) command(FrameOpcode.render_area, x, y, w, h) end
    function context.clip(x, y, w, h) command(FrameOpcode.clip, x ~= nil, x or 0, y or 0, w or 0, h or 0) end
    function context.sound(resource, volume, pan) command(FrameOpcode.sound, resource, volume, pan) end
    function context.rumble(kind, index, strength)
        command(FrameOpcode.rumble, RumbleTarget[kind] or INVALID_ENUM, index, strength)
    end
    function context.music(kind, value)
        command(FrameOpcode.music, MusicKind[kind] or INVALID_ENUM, value or false)
    end
    function context.speed(fast) command(FrameOpcode.speed, fast) end
    function context.render_filter(filter)
        command(FrameOpcode.render_filter, RenderFilter[filter] or INVALID_ENUM)
    end
    function context.text_input(active) command(FrameOpcode.text_input, active) end
    function context.replay_drop(active) command(FrameOpcode.replay_drop, active) end
    function context.fullscreen(active) command(FrameOpcode.fullscreen, active) end
    function context.action(name)
        -- The system's file dialog shows these texts in a translated language; empty ones leave its defaults.
        if name == "replay" then
            local translated = i18n.active()
            command(FrameOpcode.file_dialog, translated and i18n.tr("Open a recording") or "",
                translated and i18n.tr("LF2 recording files (*.lfr)") or "", translated and i18n.tr("Open") or "")
        end
        command(FrameOpcode.action, name)
    end
    -- TrueType text (see i18n): `outline` and `background` are 0xRRGGBB or nil for none.
    function context.text(text, x, y, align, size, color, outline, background, antialias)
        command(FrameOpcode.text, text, x, y, TextAlign[align] or INVALID_ENUM, size, color, outline or -1,
            background or -1, not not antialias)
    end
    function context.image(resource, x, y, keyed)
        local translated = i18n.active()
        if not (translated and i18n.solo(resource, nil)) then
            command(FrameOpcode.sprite, resource, 0, 0, 0, 0, x, y, not not keyed, false, false, 0xffffff, 1, 0)
        end
        if translated then
            if resource:find("^pe/menu_back") then scene.backdrop, scene.backdrop_x, scene.backdrop_y = resource, x, y end
            i18n.paint_baked(context, scene, resource, nil, x, y, keyed)
        end
    end
    if screen.update(state, input, context) == false then return false end
    screen.draw(state, context)
    for index = size + 1, previous_size do frame_batch[index] = nil end
    previous_size = size
    return frame_batch, size
end

function openlf2_describe()
    local success, output = protected_call(function()
        return screen.describe and screen.describe(state) or "no description"
    end, traceback)
    if not success then error(output) end
    return output
end

function openlf2_frame(input)
    note_event()
    local success, output, size = protected_call(function() return render(input) end, traceback)
    if not success then report_failure(output);error(output) end
    return output, size
end
return "ready"
