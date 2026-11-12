return function(base)
 local draw=base.draw
 local settings=require("polish-fighters/input_settings")
 local catalog=require('base/game/catalog')
 function base.draw(state,context,...)
  -- Keep the original LF2 character grid, portraits and team colours for every module.
  local wrapped=context
  draw(state,wrapped,...)
  if context.text and not context.pf_selection_hint then context.text(settings.hint(),397,529,"center",13,0xd4e4ff,nil,nil,true) end
 end
 return base
end
