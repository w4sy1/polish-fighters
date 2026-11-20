-- SPDX-License-Identifier: MIT
-- Copyright (c) 2026 OpenLF2 contributors

local constants = require("base/game/constants")
local virtual_keys = constants.virtual_keys
-- Session-owned screen routing. Base screens and replacements share this API.
local title = require("base/ui/title")
local speed = require("base/game/speed")
local controls = require("base/ui/controls")
local music = require("base/game/music")
local recording = require("base/game/recording")
local catalog = require("base/game/catalog")
local font = require("base/ui/font")
local i18n = require("base/i18n/i18n")
local network = require("base/game/network")
local unlock = require("base/game/unlock")
local user_options = require("base/game/options")
local hybrid = require("base/ui/hybrid_input")
local hybrid_hud = require("base/ui/hybrid_hud")
local hybrid_layout = require("base/ui/hybrid_layout")
local command_menu = require("base/ui/team_command_menu")
local command_hud = require("base/ui/team_command_hud")
local quit_dialog = require("base/ui/quit_dialog")
local flow = {}
local function screen_module(name)
    if name == "characters" then return require("base/ui/character_select") end
    if name == "backgrounds" then return require("base/ui/background_preview") end
    if name == "match" then return require("base/ui/match_screen") end
    if name == "battle" then return require("base/ui/battle_setup") end
    if name == "championship" then return require("base/ui/championship") end
    if name == "ending" then return require("base/ui/ending") end
    if name == "network" then return require("base/ui/network") end
    if name == "launch" then return require("base/ui/launch") end
    return title
end
local function hybrid_mode(state)
    if state.quit_dialog then return nil end
    if state.active == "match" then
        local match = state.match.match
        if match.replay and not match.replay_ended or state.match.view and state.match.view.paused then return "pause" end
        return "match"
    end
    if state.active == "characters" or state.active == "battle" or state.active == "championship" then
        return "selection"
    end
end
local function screen_state(state)
    return state[state.active]
end
local function can_drop_replay(state)
    return not state.session and not state.quit_dialog and (state.active == "title"
        or (state.active == "launch" and state.launch.page == "menu"))
end
function flow.create(options)
    local settings = controls.load(options.default_controller, options.desktop_controls)
    -- OpenLF2's own options (base/game/options), e.g. the unlocked characters.
    user_options.start()
    local state = {active = "launch", title = title.create(options), options = options,
        launch = require("base/ui/launch").create({menu_seed = options.menu_seed, problem = settings.problem}),
        pointer_x = 0, pointer_y = 0, previous_button = false, volume_frames = 0,
        hybrid = hybrid.create(user_options.current().hybrid)}
    music.play("bgm/main.wma")
    -- A startup recording is already queued by the host; route consumes it on the first frame.
    if options.start_screen == "replay" then state.active = "title" end
    -- Developer entry points requested by the host; not part of the original flow.
    if options.start_screen == "ending" then
        state.ending = require("base/ui/ending").create(0)
        state.active = "ending"
    end
    if options.start_screen == "backgrounds" then
        state.backgrounds = require("base/ui/background_preview").create()
        state.active = "backgrounds"
    end
    if options.network_role then
        state.network = require("base/ui/network").create(options)
        state.active = "network"
        state.network_cli = options.network_trace
        require("base/ui/network").begin(state.network, options.network_role == "host", options.network_address)
    end
    return state
end
local function with_recording(state, options)
    options.network = state.session ~= nil
    local settings = controls.current()
    if settings.record == 0 then return options end
    local names = {}
    for slot = 0, 7 do names[slot + 1] = controls.name(slot) end
    options.record = {names = names, version = state.options.recording_version or 0, time = engine.local_time(),
        music = music.selected and music.selected:gsub("/", "\\") or "", author = settings.author,
        info = settings.info, email = settings.email}
    return options
end
-- The title's Replay entry: a recording the player chose arrives from the host; after
-- data/version checks, the game starts at once.
local function start_replay(state, block)
    local replay, problem = recording.open(block, state.options.recording_version or 0)
    if not replay then
        recording.status = {kind = constants.recording_statuses.error, text = i18n.clip(i18n.tr(problem), 96), count = 0}
        return
    end
    controls.replace_names(replay.names)
    unlock.begin_replay(replay.unlock_characters, replay.unlock_function_keys)
    if replay.mode ~= constants.modes.stage and replay.music ~= "" then
        music.selected = replay.music:gsub("\\", "/"):lower()
        music.play_selected()
    end
    local options = {mode = replay.mode, difficulty = replay.difficulty, background = replay.background,
        stage_level = replay.stage_level, fighters = catalog.load(), backgrounds = catalog.backgrounds(), slots = {},
        replay = replay, battle = replay.battle}
    state.match = require("base/ui/match_screen").create(options)
    state.active = "match"
    state.wait_release = true
end
local function leave_replay(state)
    controls.replace_names(nil)
    unlock.end_replay()
    music.play("bgm/main.wma")
    speed.fast = false
    state.active = "title"
    state.wait_release = true
end

local function route(state, input, context)
    if can_drop_replay(state) then
        local block, problem = engine.take_recording()
        if block then
            start_replay(state, block)
            return
        elseif problem then
            recording.status = {kind = constants.recording_statuses.error, text = i18n.tr("Loading error!  Recording file may be corrupted!!"), count = 0}
        end
    end
    if state.wait_release then
        if not controls.idle(input) then return end
        state.wait_release = false
    end
    local routed = {}
    for key, value in pairs(context) do routed[key] = value end
    local requested
    function routed.action(name)
        assert(not requested, "multiple screen actions in one update")
        requested = name
    end
    screen_module(state.active).update(screen_state(state), input, routed)
    -- A recording opened from a file manager or the command line owns this window.
    -- F4 and leaving its result screen finish that invocation.
    if state.options.start_screen == "replay" and state.active == "match"
       and state.match.match.replay and (requested == "title" or requested == "round_over") then
        context.action("quit")
        return
    end
    if requested=='resume_campaign' and not state.session then
        local saved,problem=require('base/game/campaign_save').options(catalog.profile_id)
        if saved then
            state.match=require('base/ui/match_screen').create(saved)
            state.active='match';state.wait_release=true
        else
            state.launch.hud.message=tostring(problem)
        end
    elseif requested=='training' and not state.session then
        state.characters=require('base/ui/character_select').create({mode='versus',previous=state.characters})
        state.training_requested=true;state.active='characters';state.wait_release=true
    elseif requested == "network" then
        state.training_requested=nil
        state.network = require("base/ui/network").create(state.options)
        state.active = "network"
    elseif requested == "network_ready" then
        unlock.reset_session()
        state.session = state.network.session
        controls.replace_names(state.session.names)
        state.title = title.create(state.options)
        if title.set_replay_disabled then title.set_replay_disabled(state.title, true) end
        state.active = "title"
        state.wait_release = true
        -- A new connection starts a new deterministic menu session on both peers.
        state.characters, state.championship, state.championship_options, state.battle_config = nil, nil, nil, nil
        require("base/game/stage").set_random_list({constants.fighter_ids.deep,
            constants.fighter_ids.john, constants.fighter_ids.henry, constants.fighter_ids.rudolf,
            constants.fighter_ids.louis, constants.fighter_ids.davis, constants.fighter_ids.dennis,
            constants.fighter_ids.woody, constants.fighter_ids.freeze, constants.fighter_ids.firen}, -1)
        require("base/ui/demo").reset()
        recording.status = nil
        music.enabled, music.selected = true, nil
        speed.fast = false
        music.play("bgm/main.wma")
    elseif requested == "launch" then
        state.active = "launch"
        state.session = nil
        controls.replace_names(nil)
    elseif requested == "versus" or requested == "stage" or requested == "battle" then
        state.training_requested=nil
        -- The previous visit's state carries the values the original keeps in globals.
        state.characters = require("base/ui/character_select").create({mode = requested,
            participants = state.session and state.session.room and state.session.peers or nil,
            previous = state.characters})
        state.active = "characters"
        state.wait_release = true
    elseif requested == "start_match" then
        local options
        if state.active == "battle" then
            options = require("base/ui/battle_setup").match_options(state.battle)
        elseif state.active == "championship" then
            options = require("base/ui/championship").match_options(state.championship)
        else
            options = require("base/ui/character_select").match_options(state.characters)
        end
        if state.training_requested and not state.session then options.training=true end
        state.match = require("base/ui/match_screen").create(with_recording(state, options))
        state.active = "match"
        state.wait_release = true
    elseif requested == "championship" or requested == "team_championship" then
        state.championship_options = state.championship_options or (state.characters and state.characters.options)
            or {background = constants.background_rows.random, random_background = true, difficulty = 0}
        state.championship = require("base/ui/championship").create(state.championship_options,
            requested == "team_championship")
        state.active = "championship"
        state.wait_release = true
    elseif requested == "battle_setup" then
        local setup = require("base/ui/battle_setup")
        state.battle_config = state.battle_config or setup.create_config()
        state.battle = setup.create(state.characters, state.battle_config)
        state.active = "battle"
        state.wait_release = true
    elseif requested == "characters_back" then
        local selection=require("base/ui/character_select")
        if state.characters then
            state.characters=selection.reset_all(state.characters)
        else
            state.characters=selection.create({mode="versus"})
        end
        -- Keep room ownership, map, module and match options on the same screen.
        for _,peer in ipairs(state.session and state.session.room and state.session.peers or {{slot=0}}) do
            state.characters.slots[peer.slot].phase=constants.character_slot_phases.choosing_fighter
        end
        state.match,state.quit_dialog=nil,nil
        state.active,state.wait_release="characters",true
        speed.fast=false
        music.play("bgm/main.wma")
    elseif requested == "characters" then
        -- Reset All / back from the Battle setup: the character menu starts over.
        state.characters = require("base/ui/character_select").reset_all(state.characters)
        state.active = "characters"
        state.wait_release = true
    elseif requested == "replay_error" then
        recording.status = {kind = constants.recording_statuses.error, text = i18n.tr("Recording file error! Replaying canceled!"), count = 0}
        leave_replay(state)
    elseif requested == "round_over" and state.match.match.replay then
        -- After a replay, the game returns to the title.
        leave_replay(state)
    elseif requested == "demo" or (requested == "round_over" and state.match.match.mode == constants.modes.demo) then
        if requested == "round_over" and not state.match.match.random_game then
            speed.fast = false
            music.play("bgm/main.wma")
            state.active = "title"
        else
            music.play_selected()
            state.match = require("base/ui/match_screen").create(require("base/ui/demo").match_options(state.characters))
            state.active = "match"
        end
        state.wait_release = true
    elseif requested == "round_over" then
        local outcome = require("base/ui/match_screen").outcome(state.match)
        local selection = require("base/ui/character_select")
        if state.match.match.mode == constants.modes.championship
           or state.match.match.mode == constants.modes.team_championship then
            require("base/ui/championship").round_over(state.championship, state.match.match)
            state.active = "championship"
        elseif state.characters.mode == constants.modes.battle then
            state.battle = require("base/ui/battle_setup").create(state.characters, state.battle_config)
            state.battle.state = constants.battle_setup_states.options
            state.active = "battle"
        elseif outcome.ending then
            state.ending = require("base/ui/ending").create(state.match.match.difficulty)
            state.active = "ending"
        elseif outcome.auto_start then
            state.characters = selection.resume_options(state.characters, outcome)
            state.match = require("base/ui/match_screen").create(with_recording(state, selection.match_options(state.characters)))
            state.active = "match"
        else
            state.characters = selection.resume_options(state.characters, outcome)
            state.active = "characters"
        end
        state.wait_release = true
    elseif requested == "game_start" then
        music.play("bgm/main.wma")
        state.active = "title"
        if title.latch_input then title.latch_input(state.title, input)
        else state.wait_release = true end
    elseif requested == "title" then
        if not state.session then controls.replace_names(nil) end
        unlock.end_replay()
        music.play("bgm/main.wma")
        state.active = "title"
        -- Do not turn the key returning to the title into a new title action.
        state.wait_release = true
    elseif requested then context.action(requested) end
end
function flow.describe(state)
    local module = screen_module(state.active)
    local detail = module.describe and module.describe(screen_state(state)) or ""
    local status = recording.status_text()
    local unlocked = unlock.describe()
    return (state.session and "network_frames=" .. state.session.frames .. " " or "") .. "screen=" .. state.active .. (detail ~= "" and " " .. detail or "") .. (status and " status=" .. status or "")
        .. (unlocked and " unlock=" .. unlocked or "")
end
function flow.draw(state, context)
    context.replay_drop(can_drop_replay(state))
    local shown_options = user_options.current()
    context.render_filter(shown_options.upscaling_filter)
    -- Fullscreen (OpenLF2 extension): no-op without a real window; reasserted every frame
    -- like the filter above.
    context.fullscreen(shown_options.fullscreen)
    if state.active == "match" and shown_options.battlefield_layout == "expand" then
        screen_module(state.active).draw(screen_state(state), context, state.window_bounds)
    else
        screen_module(state.active).draw(screen_state(state), context)
    end
    if hybrid_mode(state) and state.hybrid.geometry then
        hybrid_hud.draw(context, state.hybrid.geometry, state.hybrid)
    end
    if hybrid_mode(state) == "match" then command_hud.draw(context, state.command_menu) end
    local status = recording.status_text()
    if status then font.gdi(context, i18n.clip(status, 128), 3, 0x213, recording.status_color())
    elseif state.volume_text then font.gdi(context, state.volume_text, 3, 0x213, 0x00ff00) end
    -- Show FPS (OpenLF2 extension): centered on the statusbar line so it never overlaps the
    -- left-aligned text. Polish Fighters fills that line with its key hint (menus, character
    -- selection), so the counter stays off it there.
    if shown_options.show_fps and state.fps and not context.pf_selection_hint and not context.pf_status_line then
        local fps_text = "FPS: " .. state.fps
        font.gdi(context, fps_text, math.floor((constants.screen.width - font.gdi_width(fps_text)) / 2), 0x213)
    end
    if state.quit_dialog then quit_dialog.draw(state.quit_dialog, context) end
end
local function disconnect(state, message)
    if message and state.session and state.session.room and engine.write_settings then
        -- Keep only the last bounded failure in private settings, preserving preferences.
        -- Hex avoids binary RNG bytes making the settings document invalid UTF-8.
        pcall(function()
            local document=engine.read_settings() or {}
            local snapshot=require('polish-fighters/sync_state').snapshot(state):sub(1,32768)
            document.last_network_error={reason=tostring(message),screen=state.active,
                frame=state.session.frames,slot=state.session.slot,
                snapshot_hex=snapshot:gsub('.',function(c) return string.format('%02x',string.byte(c)) end)}
            engine.write_settings(document)
        end)
    end
    if state.session then network.close(state.session) end
    state.session = nil
    controls.replace_names(nil)
    state.active, state.wait_release = "launch", true
    state.swallow_pointer = true
    state.title = title.create(state.options)
    state.characters, state.championship, state.championship_options, state.battle_config = nil, nil, nil, nil
    state.launch.message = message
    speed.fast = false
    music.play("bgm/main.wma")
end
-- Shared by the optional module launcher; closes a session without exiting the app.
function flow.return_to_modules(state)
    if state.network and state.network.session then network.close(state.network.session) end
    state.network = nil
    if state.match and state.match.match and state.match.match.finished then
        require("base/ui/match_screen").outcome(state.match)
    end
    disconnect(state)
    unlock.end_replay()
    state.match, state.battle, state.ending, state.quit_dialog = nil, nil, nil, nil
    state.pending_leave, state.return_modules_after_match = nil, nil
    state.launch.page, state.launch.hub_mode = "menu", "library"
    state.launch.hub_pending_mode, state.launch.hub_hover = nil, nil
    state.launch.hub_classic, state.launch.pf_panel, state.launch.hub_edit, state.launch.hub_online = nil, nil, nil, nil
    state.launch.hub_pack_edit, state.launch.pf_typing, state.launch.hub_mods = nil, nil, nil
    state.wait_release, state.swallow_pointer = true, true
end
-- Whether Escape (and Android's back button, which the platform reports as Escape) is free to ask about leaving
-- the game: not in a network game, where it disconnects, and not on the launch screen's pages that use it.
local function escape_free(state)
    if state.session then return false end
    if state.active == "launch" then
        if state.launch.hub_enabled and (state.launch.hub_mode~='root' or state.launch.hub_edit or state.launch.hub_online) then return false end
        return state.launch.page == "menu" and not state.launch.pf_panel
    end
    return true
end
-- raw: the host's input; screens get it per player slot, with the last known pointer position
-- and `click`, a fresh press of the left button.
function flow.update(state, raw, context)
    local bindings = controls.current()
    local input = controls.read(bindings, raw)
    -- Local navigation must work even while a network frame is waiting for its peer.
    input.click = input.button and not state.previous_button
    input.pointer_x = input.pointer_x or state.pointer_x
    input.pointer_y = input.pointer_y or state.pointer_y
    if flow.global_navigation_update and flow.global_navigation_update(state, input, context) then
        state.previous_button = input.button
        return
    end
    i18n.host(input.filters and input.filters.text)
    -- Alt+Enter, from any screen: the fullscreen option flips (and is saved like the options page does).
    if input.toggle_fullscreen and input.filters and input.filters.window then
        local values = user_options.current()
        values.fullscreen = not values.fullscreen
        user_options.save(values)
        input.fullscreen_set = values.fullscreen
    end
    local shown_options = user_options.current()
    -- Local presentation data stays outside network and replay inputs.
    if shown_options.battlefield_layout == "expand" then
        state.window_bounds = input.screen or state.window_bounds
    else
        state.window_bounds = nil
    end
    local mode = hybrid_mode(state)
    if state.hybrid_revision ~= user_options.revision() then
        state.hybrid = hybrid.create(shown_options.hybrid)
        state.hybrid_revision = user_options.revision()
    end
    local current_match = state.active == "match" and state.match.match or nil
    local player = current_match and current_match.items[state.session and state.session.slot or 0]
    local key = player and (catalog.profile_id .. ":" .. (player.record.path or tostring(player.record.id)))
    local touch = input
    if state.options.touch_device or state.options.mouse_touch then
        touch = {touch_active = true, screen = input.screen, contacts = input.contacts, touches = input.touches}
        if state.options.mouse_touch and not input.touch_active then
            touch.contacts = false
            touch.touches = input.button and input.pointer_x and input.pointer_y and {{id = 0, x = input.pointer_x, y = input.pointer_y}} or {}
        end
    end
    local touch_menu = state.options.touch_device or input.touch_active or state.options.mouse_touch
    local menu_state = state.command_menu or {owned = {}}
    state.command_menu = menu_state
    if menu_state.match ~= current_match then
        menu_state.match, menu_state.open, menu_state.pending = current_match, false, nil
        menu_state.progress = 0
    end
    local enabled = mode == "match" and player and player.hp > 0 and player.team > 0
    local geometry = touch_menu and hybrid_layout.geometry(state.hybrid.settings, input.screen or hybrid_layout.screen)
    local layout = enabled and command_menu.layout(input.screen, touch_menu, geometry)
    local v_down = input.keys[86]
    local v, escape = v_down and not menu_state.v_down, false
    for _, code in ipairs(input.presses or {}) do
        if code == 86 and not menu_state.v_down then v = true end
        if code == virtual_keys.escape then escape = true end
    end
    menu_state.v_down = v_down
    local escape_down = input.keys[virtual_keys.escape]
    escape = escape or escape_down and not menu_state.escape_down
    if v then
        for _, set in ipairs(bindings.sets) do
            if set.device == constants.input_devices.keyboard then
                for _, code in ipairs(set.keys) do if code == 86 then v = false end end
            end
        end
    end
    if command_menu.update(menu_state, input, enabled, layout, v and not touch_menu, escape,
        touch_menu and touch) then menu_state.eat_escape = true end
    if menu_state.eat_escape then
        input.keys[virtual_keys.escape] = nil
        for i = #(input.presses or {}), 1, -1 do
            if input.presses[i] == virtual_keys.escape then table.remove(input.presses, i) end
        end
        if not escape_down then menu_state.eat_escape = nil end
    end
    menu_state.escape_down = escape_down
    state.hybrid.text = input.filters and input.filters.text
    local waiting = state.session and (state.session.pending or state.session.waiting)
    local delay = state.session and state.session.delay or 0
    local sample = not current_match or (current_match.input_phase + delay) % 2 == 1
    local touched, pause = hybrid.update(state.hybrid, touch, mode, player, key, sample and not waiting)
    if pause then
        input.function_presses = (input.function_presses or "") .. "1"
        if not input.functions:find("1", 1, true) then input.functions = input.functions .. "1" end
    end
    if input[0]:find("[lr]") then touched = touched:gsub("[lr]", "") end
    if input[0]:find("[ud]") then touched = touched:gsub("[ud]", "") end
    if not sample then touched = "" end
    for letter in touched:gmatch(".") do
        if not input[0]:find(letter, 1, true) then input[0] = input[0] .. letter end
    end
    local local_keys = input.keys
    if state.active=='match' and state.match then
        if state.auto_advance_match~=state.match then
            state.auto_advance_match=state.match;state.auto_advance_driver={}
        end
        input[0]=require('base/game/campaign_advance').input(state.auto_advance_driver,
            state.match.match,input[0],shown_options.auto_advance)
    end
    if raw:sub(1, 1) == "k" then
        for slot = 0, 7 do
            local keys = input[slot]
            if keys:find("u", 1, true) and keys:find("d", 1, true)
                and keys:find("l", 1, true) and keys:find("r", 1, true) then
                input[slot] = keys:gsub("[udlr]", "")
            end
        end
    end
    if (sample or state.session and state.session.room) and menu_state.pending and (not waiting or state.session.room) then
        input[0], menu_state.pending = menu_state.pending, nil
    end
    if state.session then
        unlock.observe(input)
        if not state.session.pending then input.unlock_bits = unlock.take_pending() end
        if input.keys[virtual_keys.escape] then
            disconnect(state, i18n.tr("Network game disconnected"))
        else
            local hp = state.active == "match" and recording.hp_sum(state.match.match) or 0
            local digest
            if state.session.room and state.session.frames > 0 and state.session.sent_checksum ~= state.session.frames - 1 then
                digest = require("polish-fighters/sync_state").digest(state)
            end
            local combined, problem = network.exchange(state.session, input, hp, digest)
            if problem then
                disconnect(state, problem)
            elseif not combined then return false
            else input = combined end
        end
    end
    local joining_cli = state.network_cli and state.active == "network"
    if input.pointer_x and input.pointer_x >= 0 and input.pointer_y >= 0 then
        state.pointer_x, state.pointer_y = input.pointer_x, input.pointer_y
    end
    input.pointer_x, input.pointer_y = state.pointer_x, state.pointer_y
    -- Renderer capability flags are kept for frames that don't repeat them.
    if input.filters then state.filters = input.filters end
    input.filters = state.filters or {}
    input.click = input.button and not state.previous_button
    state.previous_button = input.button
    -- Unlock words: typed marks are taken before the screen runs, except during a replay
    -- (recorded bits act instead); a recording match stores the frame's bits.
    if not state.session then unlock.observe(input) end
    local current = state.active == "match" and state.match and state.match.match
    if not (current and current.replay and not current.replay_ended) then
        local bits, played
        if input.network then
            bits = input.unlock_bits or 0
            played = unlock.apply_recorded(bits)
        else bits, played = unlock.take_marks() end
        for _, sound in ipairs(played) do context.sound(sound.resource, sound.volume, sound.pan) end
        if current then current.unlock_bits = bits end
    end
    local escape_pressed = false
    for _, code in ipairs(input.presses or {}) do
        if code == virtual_keys.escape then escape_pressed = true end
    end
    if input.keys[virtual_keys.escape] and not state.escape_held then escape_pressed = true end
    state.escape_held = input.keys[virtual_keys.escape] == true
    local closed_now = false
    if not state.quit_dialog and flow.overlay_update and flow.overlay_update(state, input, context) then return end
    if state.quit_dialog then
        -- While the question is open the screen below is frozen.
        local answer = quit_dialog.update(state.quit_dialog, input, context)
        if answer == "exit" and state.quit_dialog.kind == "modules" and state.session then
            flow.return_to_modules(state)
            closed_now = true
        elseif answer == "exit" and (state.quit_dialog.kind == "leave" or
                (state.quit_dialog.kind == "modules" and state.active == "match")) then
            -- Leaving the fight is F4, held for two frames after this one so that the match sees it on a frame that
            -- reads the keys (no wait for released keys here: a held F4 would never count as idle).
            state.pending_leave = 3
            if state.quit_dialog.kind == "modules" then state.return_modules_after_match = true end
            state.quit_dialog, state.swallow_pointer, closed_now = nil, true, true
        elseif answer == "exit" and state.quit_dialog.kind == "modules" then
            flow.return_to_modules(state)
            closed_now = true
        elseif answer == "exit" then
            context.action("quit")
        elseif answer == "close" then
            -- The press that closed it must not reach the screen below: it skips this frame and then ignores the
            -- pointer button until it is released.
            state.quit_dialog, state.wait_release, state.swallow_pointer, closed_now = nil, true, true, true
        end
    elseif escape_pressed and escape_free(state) then
        state.quit_dialog = quit_dialog.create(state.active == "match" and "leave" or "exit")
    end
    if state.pending_leave and not state.quit_dialog then
        if state.active == "match" and not input.functions:find("4", 1, true) then input.functions = input.functions .. "4" end
        state.pending_leave = state.pending_leave > 1 and state.pending_leave - 1 or nil
    end
    if state.swallow_pointer and not state.quit_dialog then
        if input.button then input.button, input.click = false, false else state.swallow_pointer = nil end
    end
    if not state.quit_dialog and not closed_now then route(state, input, context) end
    if state.return_modules_after_match and state.active ~= "match" then flow.return_to_modules(state) end
    if joining_cli then
        if state.network.session.error then error(state.network.session.error) end
        -- CLI traces start at the title; the handshake consumes no trace frames.
        return false
    end
    local step = 0
    if local_keys[virtual_keys.f11] then step = -1 end
    if local_keys[virtual_keys.f12] then step = 1 end
    if step ~= 0 then
        music.change_volume(step)
        state.volume_frames = 100
    end
    state.volume_text = nil
    if state.volume_frames > 0 then
        state.volume_text = i18n.tr("Volume: %d", music.master)
        state.volume_frames = state.volume_frames - 1
    end
    music.flush(context)
    recording.tick_status(state.active == "match" and state.match.match.paused)
    context.speed(speed.fast)
    -- Show FPS (OpenLF2 extension): measured FPS, nil for a trace unless given; drawn in flow.draw.
    state.fps = input.fps
end
return flow
