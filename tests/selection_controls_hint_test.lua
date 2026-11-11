local set={device=0,keys={87,83,65,68,103,104,105}}
package.loaded['base/ui/controls']={current=function() return {sets={set}} end,
 key_label=function(key) return string.char(key) end}
local hints=require('polish-fighters/input_settings')
local lines=hints.selection_hint(false,'classic',1)
assert(lines[1]:find('GRACZ 2') and lines[1]:find('W / S / A / D'))
assert(lines[2]:find('Num 7') and lines[2]:find('Num 8') and lines[2]:find('Num 9'))
set.keys[5]=1;assert(hints.selection_hint(false,'classic',0)[2]:find('MYSZ: LEWY'))
set.device=2;set.buttons={5,6,7}
assert(hints.selection_hint(false,'classic',0)[2]:find('ATAK / OK 6'))
assert(hints.selection_hint(true,'modern',1)[1]:find('DOTYK 2'))
assert(hints.selection_hint(true,'classic',0)[1]:find('DOTYK 1'))
print('PASS selection hints: current keyboard/mouse/controller bindings, device slot, both touch layouts')
