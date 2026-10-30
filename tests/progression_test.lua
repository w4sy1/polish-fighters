local document={options={unlock_characters=true},other='keep'}
local function copy(v)
    if type(v)~='table' then return v end
    local out={};for k,x in pairs(v) do out[k]=copy(x) end;return out
end
local fail=false
engine={read_settings=function() return copy(document) end,write_settings=function(value)
    if fail then return nil,'disk full' end
    document=copy(value);return true
end}
local fighters={{id=1,name='Starter',hidden=false},{id=31,name='Boss A',hidden=true},{id=32,name='Boss B',hidden=true}}
package.preload['base/game/catalog']=function() return {profile_id='test-pack',load=function() return fighters end} end
local settings={allowed_ids={},allow_hidden=false}
package.preload['polish-fighters/settings']=function() return settings end
local progress=require('polish-fighters/progression')
local journal=require('polish-fighters/chronicle')
local function finish(chapter,clear,network)
    local entry={profile='test-pack',mode=1,players={{kind='human'}},chapter=chapter,campaign_clear=clear,network=network}
    return journal.append(entry),entry
end
assert(not progress.earned('test-pack',31))
finish(0,false,false);finish(0,true,true)
assert(not progress.earned('test-pack',31),'losses and online matches must not grant rewards')
local ok,entry=finish(4,true,false)
assert(ok and entry.reward.id==31)
assert(progress.earned('test-pack',31) and not progress.earned('test-pack',32))
local _,repeated=finish(0,true,false)
assert(not repeated.reward,'replaying the same chapter must not farm rewards')
assert(not progress.earned('other-pack',31),'IDs must be scoped to their content pack')
fail=true
assert(not finish(10,true,false))
assert(not progress.earned('test-pack',32),'failed save must not grant reward')
fail=false;finish(10,true,false)
assert(progress.earned('test-pack',32))
assert(document.other=='keep' and document.options.unlock_characters)
local count,next_fighter=progress.summary('test-pack',fighters)
assert(count==2 and not next_fighter)
local catalog=dofile(arg[1]..'/engine/scripts/polish-fighters/catalog.lua')({profile_id='test-pack',
    load=function() return fighters end,selectable=function(f) return not f.hidden end,
    random_eligible=function() return false end})
assert(catalog.selectable(fighters[2]),'earned character must be selectable locally')
settings.allowed_ids={1}
assert(not catalog.selectable(fighters[2]),'explicit roster restriction must remain effective')
settings.allowed_ids={}
local network=dofile(arg[1]..'/engine/scripts/polish-fighters/progression_network.lua')({
    create=function() return {room=true} end,close=function() return true end,
    start=function() progress.suspended=false;return true end})
network.create()
network.start()
assert(not catalog.selectable(fighters[2]),'local progress must not alter shared online roster')
assert(network.close())
assert(catalog.selectable(fighters[2]))
package.loaded['base/game/catalog'].profile_id='hook-pack'
package.preload['polish-fighters/dashboard_model']=function() return {} end
local screen=dofile(arg[1]..'/engine/scripts/polish-fighters/match_history.lua')({
    create=function() return {match={stage_run={id=4},finished=true,items={},winner=1,frame_number=100}} end,
    outcome=function() return {auto_start=true} end})
local state=screen.create({mode=1,slots={[0]={kind='human',fighter=1,team=1}},fighters=fighters})
state.match.stage_run.id=10 -- engine has already advanced to the next chapter
screen.outcome(state)
assert(progress.earned('hook-pack',31),'real finish hook must grant reward for the completed chapter')
assert(document.polish_fighters_progress['hook-pack'].completed['0'])
assert(not document.polish_fighters_progress['hook-pack'].completed['1'])
print('PASS: chapter rewards, no farming, save failure, pack isolation, roster limits, network suspension')
