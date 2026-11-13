local updates={version='0.15.0',build=17}
local function version(text)
 local a,b,c=tostring(text or ''):match('(%d+)%.(%d+)%.(%d+)')
 if not a then return 0 end
 return tonumber(a)*1000000+tonumber(b)*1000+tonumber(c)
end
function updates.select(releases)
 if type(releases)~='table' then return nil end
 local best,score=nil,version(updates.version)
 for _,release in ipairs(releases) do
  if type(release)=='table' and not release.draft and type(release.html_url)=='string' and
   release.html_url:match('^https://github%.com/w4sy1/polish%-fighters/releases/tag/') then
   local available=false
   for _,asset in ipairs(type(release.assets)=='table' and release.assets or {}) do
    local name=tostring(asset.name or ''):lower()
    if name:find('windows',1,true) and (name:match('%.zip$') or name:match('%.exe$')) and asset.state=='uploaded' then available=true end
   end
   local candidate=version(release.name)
   if candidate==0 then candidate=version(release.tag_name) end
   if available and candidate>score then best,score=release,candidate end
  end
 end
 return best
end
return updates
