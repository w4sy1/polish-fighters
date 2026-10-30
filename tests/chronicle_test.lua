local document={other={preserved=true}}
local function copy(value)
    if type(value)~='table' then return value end
    local result={};for k,v in pairs(value) do result[k]=copy(v) end;return result
end
local fail=false
engine={read_settings=function() return copy(document) end,write_settings=function(value)
    if fail then return nil,'disk full' end
    document=copy(value);return true
end}
local journal=require('polish-fighters/chronicle')
for index=1,55 do assert(journal.append({profile='lf4-turbo',mode=0,players={}})) end
assert(#journal.entries()==50 and journal.entries()[1].id==6)
assert(document.other.preserved)
local before=#journal.entries()
fail=true
assert(not journal.append({profile='lf4-turbo',mode=0,players={}}))
assert(#journal.entries()==before)
fail=false
package.preload['base/game/catalog']=function() return {profile_id='ntsd'} end
package.preload['polish-fighters/dashboard_model']=function() return {} end
local decorator=dofile(arg[1]..'/engine/scripts/polish-fighters/match_history.lua')
local original_setmetatable=setmetatable
setmetatable=nil -- Match the native package sandbox instead of unrestricted LuaJIT.
local base=decorator({create=function() return {match={finished=true,winner=1,frame_number=900,
    background_row=2,items={[0]={hp=200,kills=3,damage_dealt=150}}}} end,
    outcome=function() return {auto_start=false} end})
local opts={mode=0,network=true,slots={[0]={kind='human',fighter=1,team=1}},fighters={{id=52,name='Naruto'}}}
local state=base.create(opts)
base.outcome(state);base.outcome(state)
local entries=journal.entries()
assert(entries[#entries].id==56,'finish must be recorded once')
assert(entries[#entries].players[1].kills==3 and entries[#entries].network)
assert(state.match.history==nil,'local bookkeeping must stay outside simulation')
opts.replay={};base.outcome(base.create(opts))
opts.replay=nil;opts.demo=true;base.outcome(base.create(opts))
assert(journal.entries()[#journal.entries()].id==56,'replays and demos do not count')
opts.demo=false
local abandoned={}
for index=1,20 do abandoned[index]=base.create(opts) end
base.outcome(abandoned[1])
assert(journal.entries()[#journal.entries()].id==56,'abandoned cache must be bounded')
base.outcome(abandoned[20])
assert(journal.entries()[#journal.entries()].id==57,'latest match must remain recordable')
setmetatable=original_setmetatable
print('PASS: bounded history, preserved settings, failed writes, finish hook, duplicates and replay exclusion')
