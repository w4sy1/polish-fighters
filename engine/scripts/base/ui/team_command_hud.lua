-- SPDX-License-Identifier: MIT
local hud = {}
local colors = {attack = {174, 31, 34}, stay = {169, 107, 14}, come = {38, 115, 41},
    defend = {29, 84, 152}}
local icons = {
    attack = {"#.......#", ".#.....#.", "..#...#..", "...#.#...", "....#....",
        "...#.#...", "#.#...#.#", ".#.....#.", "#.#...#.#"},
    stay = {"..#.#.#..", "..#.#.#.#", "..#.#.#.#", "..#######", "#.#######",
        "#########", ".########", "..######.", "...####.."},
    come = {"....#....", ".....#...", "......#..", "########.", "#########",
        "########.", "......#..", ".....#...", "....#...."},
    defend = {"....#....", "..#####..", "#########", "##.....##", "##.....##",
        ".##...##.", "..##.##..", "...###...", "....#...."},
}

function hud.draw(context, state)
    local layout = state and state.layout
    if not layout then return end
    local scale = layout.scale
    local function fill(x, y, w, h, r, g, b)
        context.fill(math.floor(x), math.floor(y), math.max(1, math.floor(w)), math.max(1, math.floor(h)), r, g, b, 255)
    end
    local function text(label, x, y, size)
        if context.text then context.text(label, math.floor(x), math.floor(y), "center", math.max(9, math.floor(size * scale)), 0xffffff, 0x171825) end
    end
    context.overlay(true)
    local trigger = layout.trigger
    local radius = trigger.w / 2
    local cx, cy = trigger.x + radius, trigger.y + radius
    for dy = -math.floor(radius), math.floor(radius) do
        local dx = math.sqrt(math.max(0, radius * radius - dy * dy))
        fill(cx - dx, cy + dy, 2 * dx, 1, 195, 205, 232)
        local inner = radius - math.max(1, scale)
        if math.abs(dy) < inner then
            local half = math.sqrt(inner * inner - dy * dy)
            fill(cx - half, cy + dy, 2 * half, 1, 26, 30, 70)
        end
    end
    fill(cx - 9 * scale, cy - 6 * scale, 18 * scale, 10 * scale, 242, 241, 246)
    fill(cx - 5 * scale, cy + 3 * scale, 4 * scale, 4 * scale, 242, 241, 246)
    for i = -1, 1 do fill(cx + (4 * i - 1) * scale, cy - 2 * scale, 2 * scale, 2 * scale, 26, 30, 70) end
    local progress = state.progress or 0
    if progress > 0 then
        for _, box in ipairs(layout) do
            local r, g, b = unpack(colors[box.command])
            local x, y, w, h = box.x, box.y, box.w, box.h
            local travel = (1 - progress)^2 * 10 * scale
            if layout.touch then x = x + travel else y = y + travel end
            fill(x, y, w, h, 229, 232, 243)
            fill(x + 2 * scale, y + 2 * scale, w - 4 * scale, h - 4 * scale, r, g, b)
            fill(x + w - 15 * scale, y + h, 9 * scale, 3 * scale, r, g, b)
            fill(x + w - 11 * scale, y + h + 3 * scale, 5 * scale, 2 * scale, r, g, b)
            local pixel = math.max(1, math.floor(2 * scale))
            for row, pattern in ipairs(icons[box.command]) do
                for col = 1, #pattern do
                    if pattern:sub(col, col) == "#" then
                        fill(x + 7 * scale + (col - 1) * pixel, y + h / 2 + (row - 5.5) * pixel,
                            pixel, pixel, 249, 246, 231)
                    end
                end
            end
            text(box.command:upper(), x + w * 0.59, y + 9 * scale, 14)
        end
    end
    context.overlay(false)
end

return hud
