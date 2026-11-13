local updates=require('polish-fighters/updates')
local function release(v,asset)
 return {name='Polish Fighters '..v,html_url='https://github.com/w4sy1/polish-fighters/releases/tag/test',
 assets={{name=asset or 'PolishFighters-Windows.zip',state='uploaded'}}}
end
assert(not updates.select({release('0.10.0'),release('0.11.0'),release('0.12.0')}))
assert(not updates.select({release('0.15.0')}),'installed version must not advertise itself as an update')
local newer=release('0.16.0');assert(updates.select({newer})==newer)
assert(not updates.select({release('0.16.0','Android.apk')}))
newer.draft=true;assert(not updates.select({newer}));newer.draft=false
newer.html_url='https://evil.invalid';assert(not updates.select({newer}))
assert(not updates.select(false))
local calls={}
engine={updates=function(op) calls[#calls+1]=op;return op=='start' and true or '[]' end,json_decode=function() return {} end}
package.loaded['base/ui/quit_dialog']={create=function() return {} end,update=function() return 'exit' end,draw=function() end}
local flow=dofile(arg[1]..'/engine/scripts/polish-fighters/updates_flow.lua')({create=function() return {active='launch'} end,
 draw=function() end,overlay_update=function() return false end})
flow.create({headless=true});assert(#calls==0,'headless tests must not access network')
local state=flow.create({});assert(calls[1]=='start')
flow.overlay_update(state,{},{});assert(calls[2]=='poll' and not state.update_pending)
state.available_update=release('0.13.0');local action
assert(flow.overlay_update(state,{},{action=function(a) action=a end}))
assert(action=='open_update_release' and not state.update_notice)
print('PASS update versions, assets, drafts, trusted links, headless, nonblocking polling and download action')
