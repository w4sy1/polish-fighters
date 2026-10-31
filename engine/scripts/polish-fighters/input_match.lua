return function(base)
 local step=base.step
 local buffer=require("polish-fighters/input_buffer")
 function base.step(state,held) return step(state,buffer.prepare(state,held)) end
 return base
end
