-- A checkpoint is a clean section start, not a dump of live engine objects.
local saves={}
local function digest(payload)
 local text,problem=engine.json_encode(payload)
 if not text then return nil,problem end
 return engine.state_digest(text)
end
local function integer(n,lo,hi) return type(n)=='number' and n%1==0 and n>=lo and n<=hi end
local function valid(envelope,profile)
 if type(envelope)~='table' or type(envelope.payload)~='table' then return nil end
 local p=envelope.payload
 if p.version~=1 or p.profile~=profile or not integer(p.level,0,59) or
    not integer(p.difficulty,-1,2) or not integer(p.background,0,1000) or type(p.source)~='string' or type(p.fighters)~='table' or
    type(envelope.digest)~='string' or digest(p)~=envelope.digest then return nil end
 if #p.fighters<1 or #p.fighters>8 then return nil end
 local seen={}
 for _,v in ipairs(p.fighters) do
  if not integer(v.slot,0,7) or not integer(v.id,0,2147483647) or
     (v.kind~='human' and v.kind~='computer') or not integer(v.team,0,1000) or
     not integer(v.hp,0,100000) or not integer(v.max_hp,1,100000) or
     not integer(v.dark_hp,0,100000) or not integer(v.mp,0,100000) or seen[v.slot] then return nil end
  seen[v.slot]=true
 end
 return p
end
function saves.capture(state,completed)
 local run=state.stage_run
 if not run or state.replay or state.random_game or (state.held and state.held.network) then return end
 local catalog=require('base/game/catalog')
 local p={version=1,profile=catalog.profile_id,source=run.source_path or catalog.stage_path,
  level=run.id,difficulty=state.difficulty,background=state.background_row,fighters={},completed=completed==true}
 local human=false
 for index=0,19 do
  local v=state.items[index]
  if v and v.record.kind==0 and not v.pf_clone and (index<8 or index>=10 and index<18) then
   human=human or v.human==true
   p.fighters[#p.fighters+1]={slot=index<8 and index or index-10,id=v.record.id,
    kind=v.human and 'human' or 'computer',team=v.team,hp=math.floor(v.hp),dark_hp=math.floor(v.dark_hp),
    max_hp=math.floor(v.max_hp),mp=math.floor(v.mp)}
  end
 end
 if not human then return end
 local sum,problem=digest(p)
 if not sum then saves.last_error=problem;return nil,problem end
 local doc=engine.read_settings() or {}
 doc.campaign_checkpoints=type(doc.campaign_checkpoints)=='table' and doc.campaign_checkpoints or {}
 doc.campaign_last=type(doc.campaign_last)=='table' and doc.campaign_last or {}
 local key=p.profile..'|'..p.source
 local prior=doc.campaign_checkpoints[key]
 local previous=type(prior)=='table' and (valid(prior.current,p.profile) and prior.current or prior.previous) or nil
 doc.campaign_checkpoints[key]={current={payload=p,digest=sum},previous=previous}
 doc.campaign_last[p.profile]=key
 local ok,why=engine.write_settings(doc);saves.last_error=not ok and tostring(why) or nil
 return ok,why
end
function saves.load(profile)
 local doc=engine.read_settings() or {}
 local key=type(doc.campaign_last)=='table' and doc.campaign_last[profile]
 local entry=type(doc.campaign_checkpoints)=='table' and doc.campaign_checkpoints[key]
 if type(entry)~='table' then return nil,'Brak zapisu dla tego modulu' end
 local p=valid(entry.current,profile) or valid(entry.previous,profile)
 if not p then return nil,'Uszkodzony zapis kampanii' end
 if p.completed then return nil,'Ta kampania jest juz ukonczona' end
 return p
end
function saves.options(profile)
 local p,problem=saves.load(profile)
 if not p then return nil,problem end
 local catalog=require('base/game/catalog');local permitted=p.source==catalog.stage_path
 for _,campaign in ipairs(catalog.campaigns or {}) do if campaign.path==p.source then permitted=true end end
 if not permitted then return nil,'Zapis wymaga innej lub brakujacej kampanii' end
 local fighters=catalog.load();local rows={}
 for row,fighter in ipairs(fighters) do rows[fighter.id]=row end
 local slots,vitals={},{}
 for _,v in ipairs(p.fighters) do
  if not rows[v.id] then return nil,'Zapis wymaga brakujacej postaci: '..v.id end
  slots[v.slot]={kind=v.kind,fighter=rows[v.id],team=v.team}
  vitals[v.kind=='human' and v.slot or v.slot+10]=v
 end
 return {mode=1,difficulty=p.difficulty,background=p.background,stage_level=p.level,
  campaign_path=p.source,campaign_background=p.background,fighters=fighters,backgrounds=catalog.backgrounds(),
  slots=slots,checkpoint_vitals=vitals}
end
return saves
