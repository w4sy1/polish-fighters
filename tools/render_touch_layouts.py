"""Preview real Lua gamepad draw commands with Pillow; no game binary or device test."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from test_lua_scripts import runtime, ROOT


def render(style):
    image = Image.new('RGB', (794, 550), (14, 25, 56))
    draw = ImageDraw.Draw(image, 'RGBA')
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
    heading = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 24)
    lua = runtime()
    def fill(x, y, width, height, r, g, b, a=255):
        if width > 0 and height > 0:
            draw.rectangle((int(x), int(y), int(x+width-1), int(y+height-1)), fill=(int(r), int(g), int(b), int(a)))
    def label(text, x, y):
        draw.text((int(x), int(y)), text, font=font, anchor='mt', fill='white')
    lua.globals().preview_label = label
    lua.execute("package.preload['base/ui/font']=function() return {draw=function(c,text,x,y) preview_label(text,x,y) end} end")
    pad = lua.eval("require('base/ui/touch_gamepad')")
    options = lua.eval("require('base/game/options')")
    state = pad.create(options.default_gamepad(), style == 'classic', style)
    pad.set_available(state, lua.table_from({'da': True, 'dj': True, 'daj': True}))
    input_state = lua.table_from({'touch_active': True, 'touches': lua.table()})
    if style == 'modern':
        button = state.buttons[1]
        input_state.touches = lua.table_from([lua.table_from({'id': 2, 'x': button.x, 'y': button.y})])
        pad.update(state, input_state)
        input_state.touches[1].x = button.x + 70
    pad.update(state, input_state)
    pad.draw(state, lua.table_from({'overlay': lambda active: None, 'fill': fill}))
    draw.text((397, 35), 'Klasyczny LF' if style == 'classic' else 'Nowoczesny joystick',
              font=heading, anchor='mt', fill='white')
    draw.text((397, 76), 'Podgląd poleceń renderera Lua — bez uruchamiania gry', font=font, anchor='mt', fill='#b7c6e8')
    destination = ROOT / 'preview' / ('touch-' + style + '.png')
    image.save(destination)
    print(destination)


if __name__ == '__main__':
    render('classic')
    render('modern')
