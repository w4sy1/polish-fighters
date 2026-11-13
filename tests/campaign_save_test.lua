local function copy(v)
 if type(v)~='table' then return v end
 local out={};for k,x in pairs(v) do out[k]=copy(x) end;return out
end
local function encode(v)
 if type(v)~='table' then return tostring(v) end
 local keys={};for k in pairs(v) do keys[#keys+1]=k end
 table.sort(keys,function(a,b) return tostring(a)<tostring(b) end)
 local parts={};for _,k in ipairs(keys) do parts[#parts+1]=tostring(k)..'='..encode(v[k]) end
 return '{'..table.concat(parts,';')..'}'
end
local document={preserved=true};local fail=false
engine={read_settings=function() return copy(document) end,write_settings=function(doc)
 if fail then return nil,'simulated interruption' end
 document=copy(doc);return true
end,json_encode=encode,state_digest=function(text) return 'test:'..text end}
local catalog={profile_id='lf4-turbo',stage_path='mods/lf4-turbo/stage.dat',
 load=function() return {{id=55}} end,backgrounds=function() return {} end}
package.loaded['base/game/catalog']=catalog
local saves=require('base/game/campaign_save')
local actor={record={id=55,kind=0},human=true,hp=400,dark_hp=420,max_hp=500,mp=200,team=1}
local s={stage_run={id=1},difficulty=0,background_row=1,items={[0]=actor}}
assert(saves.capture(s));assert(saves.load('lf4-turbo').level==1)
s.stage_run.id=2;assert(saves.capture(s))
fail=true;s.stage_run.id=3
assert(not saves.capture(s));assert(saves.load('lf4-turbo').level==2,'failed write destroyed good checkpoint')
fail=false
local key=document.campaign_last['lf4-turbo']
document.campaign_checkpoints[key].current.payload.level=9
assert(saves.load('lf4-turbo').level==1,'corrupt current checkpoint did not fall back to verified previous')
assert(not saves.load('polish-originals'),'campaign leaked across profiles')
local resumed=saves.options('lf4-turbo')
assert(resumed.stage_level==1 and resumed.slots[0].fighter==1 and resumed.checkpoint_vitals[0].hp==400)
s.held={network=true};s.stage_run.id=4;saves.capture(s)
assert(saves.load('lf4-turbo').level==1,'network simulation wrote local campaign progress')
assert(document.preserved)
s.held=nil;s.difficulty=-1;assert(saves.capture(s));assert(saves.load('lf4-turbo').difficulty==-1,'Crazy difficulty was rejected')
print('PASS checkpoints: isolated campaigns, checksum/fallback, interrupted save, restore roster/vitals, network exclusion and preserved settings')
