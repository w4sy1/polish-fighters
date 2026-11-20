-- SPDX-License-Identifier: MIT
-- Copyright (c) 2026 OpenLF2 contributors

-- OpenLF2's own settings, which the original game does not have. They
-- live in config.json's "options" member, next to the original's controls and recording values.
local unlock = require("base/game/unlock")
local i18n = require("base/i18n/i18n")
local hybrid_layout = require("base/ui/hybrid_layout")
local options = {}

options.battlefield_layouts = {"classic", "expand"}
local revision=0
function options.revision() return revision end

-- Every valid value, in the dropdown's order. "xbrz" is a shader: the host offers it only on
-- renderers that can run it (see options.available_filters), but a saved choice stays valid.
options.upscaling_filters = {"nearest", "linear", "xbrz"}
-- The values to offer: `features` is what the host reported ({xbrz = true} when it can run the shader).
function options.available_filters(features)
    local list = {}
    for _, filter in ipairs(options.upscaling_filters) do
        if filter ~= "xbrz" or (features and features.xbrz) then list[#list + 1] = filter end
    end
    return list
end
-- The values to offer: the default language always, the others when the host can draw TrueType text
-- (`features.text`, see i18n.host).
function options.available_languages(features)
    local list = {"default"}
    if features and features.text then
        for _, language in ipairs(i18n.languages) do list[#list + 1] = language end
    end
    return list
end
local defaults = {battlefield_layout = "classic", unlock_characters = false, upscaling_filter = "linear", fullscreen = false, show_fps = false,
    rumble = false, language = "polish", font_antialiasing = true,
    character_shading = false, projected_shadows = false,
    light_azimuth = -50, light_elevation = 70, shadow_blur = 2, shadow_opacity = 0.275}
local current

local function valid_filter(value)
    for _, filter in ipairs(options.upscaling_filters) do
        if value == filter then return true end
    end
    return false
end
local function angle(value, default, low, high)
    if type(value) ~= "number" or value ~= value or value == math.huge or value == -math.huge then return default end
    return math.max(low, math.min(high, value))
end
local function copy(values)
    return {battlefield_layout = values.battlefield_layout == "expand" and "expand" or defaults.battlefield_layout,
        hybrid = hybrid_layout.copy(values.hybrid), auto_advance = values.auto_advance == true,
        unlock_characters = values.unlock_characters,
        upscaling_filter = valid_filter(values.upscaling_filter) and values.upscaling_filter or defaults.upscaling_filter,
        fullscreen = values.fullscreen, show_fps = values.show_fps, rumble = values.rumble,
        font_antialiasing = values.font_antialiasing,
        character_shading = values.character_shading == true,
        projected_shadows = values.projected_shadows == true,
        light_azimuth = angle(values.light_azimuth, defaults.light_azimuth, -180, 180),
        light_elevation = angle(values.light_elevation, defaults.light_elevation, 12, 89),
        shadow_blur = math.floor(angle(values.shadow_blur, defaults.shadow_blur, 0, 8)),
        shadow_opacity = angle(values.shadow_opacity, defaults.shadow_opacity, 0, 1),
        language = i18n.is_language(values.language) and values.language or defaults.language}
end

-- The saved options, or the defaults for anything missing or invalid.
function options.load()
    local document = engine.read_settings()
    local saved = type(document) == "table" and document.options
    local values = copy(defaults)
    if type(saved)=='table' then values.auto_advance=saved.auto_advance==true end
    if type(saved) == "table" then
        if type(saved.character_shading) == "boolean" then values.character_shading = saved.character_shading end
        if type(saved.projected_shadows) == "boolean" then values.projected_shadows = saved.projected_shadows end
        values.light_azimuth = angle(saved.light_azimuth, defaults.light_azimuth, -180, 180)
        values.light_elevation = angle(saved.light_elevation, defaults.light_elevation, 12, 89)
        values.shadow_blur = math.floor(angle(saved.shadow_blur, defaults.shadow_blur, 0, 8))
        values.shadow_opacity = angle(saved.shadow_opacity, defaults.shadow_opacity, 0, 1)
    end
    if type(saved) == "table" and type(saved.unlock_characters) == "boolean" then
        values.unlock_characters = saved.unlock_characters
    end
    if type(saved) == "table" and valid_filter(saved.upscaling_filter) then
        values.upscaling_filter = saved.upscaling_filter
    end
    if type(saved) == "table" and type(saved.fullscreen) == "boolean" then
        values.fullscreen = saved.fullscreen
    end
    if type(saved) == "table" and type(saved.show_fps) == "boolean" then
        values.show_fps = saved.show_fps
    end
    if type(saved) == "table" and type(saved.rumble) == "boolean" then
        values.rumble = saved.rumble
    end
    if type(saved) == "table" and type(saved.font_antialiasing) == "boolean" then
        values.font_antialiasing = saved.font_antialiasing
    end
    if type(saved) == "table" and i18n.is_language(saved.language) then
        values.language = saved.language
    end
    if type(saved) == "table" then values.hybrid = hybrid_layout.copy(saved.hybrid) end
    if type(saved) == "table" and (saved.battlefield_layout == "classic" or saved.battlefield_layout == "expand") then
        values.battlefield_layout = saved.battlefield_layout
    end
    current = copy(values)
    revision=revision+1
    return copy(values)
end
function options.current()
    if not current then options.load() end
    return copy(current)
end

local function apply(before, after)
    i18n.use(after.language, after.font_antialiasing)
    if after.unlock_characters and not (before and before.unlock_characters) then
        unlock.flags.characters = 1
    elseif before and before.unlock_characters and not after.unlock_characters then
        unlock.flags.characters = 0
    end
end

local function same(a, b)
    if type(a) ~= "table" or type(b) ~= "table" then return a == b end
    for key, value in pairs(a) do
        if not same(value, b[key]) then return false end
    end
    for key in pairs(b) do
        if a[key] == nil then return false end
    end
    return true
end

-- At startup: load and apply the saved options, then rewrite config.json's "options" so it
-- lists every option: missing ones filled with defaults, invalid or unknown ones dropped.
function options.start()
    local loaded = options.load()
    apply(nil, loaded)
    local document, problem = engine.read_settings()
    if problem then return end
    if type(document) == "table" and document.touch_profiles == nil and same(document.options, loaded) then return end
    options.save(loaded)
end

local function persist(values)
    local stored = engine.read_settings()
    local document = {}
    if type(stored) == "table" then
        for key, value in pairs(stored) do document[key] = value end
    end
    document.version = 1
    document.options = copy(values)
    document.touch_profiles = nil
    return engine.write_settings(document)
end

-- Existing settings screens can apply immediately. The Hybrid editor keeps changes
-- private until the user successfully saves them.
function options.save(values, require_persistence)
    local before = options.current()
    local candidate = copy(values)
    if require_persistence then
        local saved, problem = persist(candidate)
        if not saved then return nil, problem end
    end
    current = candidate
    revision = revision + 1
    apply(before, current)
    if require_persistence then return true end
    return persist(current)
end
return options
