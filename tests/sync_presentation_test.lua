local captured
engine={random_state=function() return string.rep('r',3000),0 end,
 state_digest=function(bytes) captured=bytes;return bytes end}
package.loaded['base/game/stage']={random_list=function() return {1,2},-1 end}
package.loaded['base/game/unlock']={flags={characters=0}}
local sync=require('polish-fighters/sync_state')
local function flow(window)
 return {active='match',match={match={frame_number=1,held={[0]='c',filters={window=window,text=true,xbrz=true}},
  items={[0]={hp=500,x=100}}}}}
end
local pc,phone=flow(true),flow(false)
assert(sync.digest(pc)==sync.digest(phone),'renderer capabilities must not abort a cross-platform match')
assert(not captured:find('filters',1,true))
phone.match.match.items[0].hp=499
assert(sync.digest(pc)~=sync.digest(phone),'real simulation divergence must still be detected')
phone=flow(false);phone.match.match.held[0]='b'
assert(sync.digest(pc)~=sync.digest(phone),'player inputs must remain checked')
print('PASS sync: Windows/Android capabilities excluded, health and input divergence retained')
