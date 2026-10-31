-- Original DBZ routine 0x402000 treats [MU] as stop/unload, not an audio path.
-- Static proof: music-sentinel-proof.json; original executable never run.
return function(base)
    local play = base.play
    function base.play(path)
        if path:lower() == "[mu]" then return base.stop() end
        return play(path)
    end
    return base
end
