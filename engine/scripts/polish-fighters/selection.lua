return function(base)
    local create,match_options = base.create,base.match_options
    function base.create(options)
        local state = create(options)
        local model = require("polish-fighters/dashboard_model")
        -- One-shot preset only when explicitly launched from the local dashboard.
        local row = model.pending_map
        model.pending_map = nil
        if options.mode == "versus" and row ~= nil then
            state.options.background, state.options.random_background = row, false
        end
        local campaign=model.pending_campaign
        model.pending_campaign=nil
        if options.mode=="stage" then
            state.pf_campaign=campaign or (options.previous and options.previous.pf_campaign)
            if campaign then state.options.stage_level=campaign.start_id end
        end
        return state
    end
    function base.match_options(state)
        local value=match_options(state)
        if state.pf_campaign then
            value.campaign_path=state.pf_campaign.path
            value.campaign_id=state.pf_campaign.id
            value.campaign_background=state.pf_campaign.background
        end
        return value
    end
    return base
end
