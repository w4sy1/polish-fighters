return function(base)
 local draw=base.draw
 local settings=require("polish-fighters/input_settings")
 function base.draw(state,context,...)
  draw(state,context,...)
  if context.text then context.text(settings.hint(),397,529,"center",13,0xd4e4ff,nil,nil,true) end
 end
 return base
end
