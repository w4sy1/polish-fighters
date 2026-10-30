return function(base)
    local journal=require("polish-fighters/chronicle")
    -- The native package sandbox deliberately exposes no setmetatable.
    -- Keep a bounded local cache outside synchronized match/flow tables.
    local matches,order={},{}
    local function forget(state)
        matches[state]=nil
        for index,key in ipairs(order) do
            if key==state then table.remove(order,index);break end
        end
    end
    local create,outcome=base.create,base.outcome
    function base.create(options)
        local state=create(options)
        if not options.replay and not options.demo then
            forget(state)
            if #order>=16 then forget(order[1]) end
            order[#order+1]=state
            matches[state]={profile=require("base/game/catalog").profile_id,
                mode=options.mode,network=not not options.network,
                chapter=state.match.stage_run and state.match.stage_run.id or nil,campaign=options.campaign_id or options.campaign_path,players={}}
            for slot=0,7 do
                local selected=options.slots and options.slots[slot]
                local fighter=selected and options.fighters and options.fighters[selected.fighter]
                if selected and selected.kind and fighter then
                    matches[state].players[#matches[state].players+1]={slot=slot,kind=selected.kind,
                        fighter=fighter.id,name=fighter.name,team=selected.team}
                end
            end
        end
        return state
    end
    function base.outcome(state)
        local result=outcome(state)
        local entry=matches[state]
        local current=state.match
        if entry and current.finished then
            entry.winner=current.winner
            entry.frames=current.frame_number
            entry.background=current.background_row
            entry.stage=current.stage_run and current.stage_run.id or nil
            entry.campaign_clear=entry.mode==1 and not entry.network and (result.auto_start==true or result.ending==true)
            for _,player in ipairs(entry.players) do
                local value=current.items[player.kind=="human" and player.slot or player.slot+10]
                if value then
                    player.kills=value.kills;player.damage=value.damage_dealt;player.hp=value.hp
                end
            end
            local ok,problem=journal.append(entry)
            if ok then forget(state);require("polish-fighters/dashboard_model").history_error=nil
            else require("polish-fighters/dashboard_model").history_error=tostring(problem) end
        end
        return result
    end
    return base
end
