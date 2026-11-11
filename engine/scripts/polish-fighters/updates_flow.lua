return function(base)
 local create,draw,overlay=base.create,base.draw,base.overlay_update
 local updates=require('polish-fighters/updates')
 local dialog=require('base/ui/quit_dialog')
 function base.create(options)
  local state=create(options)
  if not options.headless and engine.updates then
   state.update_pending=engine.updates('start')==true
  end
  return state
 end
 function base.overlay_update(state,input,context)
  if state.update_pending then
   local raw=engine.updates('poll')
   if raw~='pending' then
    state.update_pending=false
    if type(raw)=='table' then state.available_update=updates.select(raw) end
   end
  end
  if state.available_update and state.active=='launch' and not state.quit_dialog then
   state.update_notice=dialog.create('update');state.available_update=nil
  end
  if state.update_notice then
   local result=dialog.update(state.update_notice,input,context)
   if result then
    state.update_notice=nil
    if result=='exit' then context.action('open_update_release') end
   end
   return true
  end
  return overlay and overlay(state,input,context) or false
 end
 function base.draw(state,context)
  draw(state,context)
  if state.update_notice then dialog.draw(state.update_notice,context) end
 end
 return base
end
