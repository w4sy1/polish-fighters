return function(base)
 local draw=base.draw
 local settings=require("polish-fighters/input_settings")
 local catalog=require('base/game/catalog')
 function base.draw(state,context,...)
  -- Keep the original LF2 character grid, portraits and team colours for every module.
  local wrapped=context
  -- The key hint below owns the statusbar line; the base flow keeps its FPS counter off it.
  if context.text then context.pf_status_line=true end
  draw(state,wrapped,...)
  if context.text and not context.pf_selection_hint then context.text(settings.hint(),397,529,"center",13,0xd4e4ff,nil,nil,true) end
 end
 return base
end
