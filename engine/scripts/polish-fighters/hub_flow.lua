return function(base)
 local create=base.create
 function base.create(options)
  local state=create(options)
  state.launch.hub_enabled=not options.legacy_menu
  state.launch.hub_available=options.profiles_available
  state.launch.hub_mode=options.profile_start and "profile" or "root"
  state.launch.hub_wait_release=options.profile_start==true
  return state
 end
 return base
end
