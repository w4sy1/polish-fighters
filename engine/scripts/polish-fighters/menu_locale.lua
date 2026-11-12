local options=require('base/game/options')
local locale={}
function locale.id() return options.current().language=='english' and 'en' or 'pl' end
function locale.text(key)
 local strings=require('polish-fighters/locales/'..locale.id())
 return assert(strings[key], 'Missing menu translation: '..key)
end
function locale.select(id)
 assert(id=='pl' or id=='en')
 local values=options.current()
 values.language=id=='en' and 'english' or 'polish'
 values.font_antialiasing=false
 return options.save(values)
end
local replacements
function locale.translate(value)
 if locale.id()~='en' or type(value)~='string' then return value end
 local strings=require('polish-fighters/locales/ui_en')
 if strings[value] then return strings[value] end
 if not replacements then
  replacements={};for key in pairs(strings) do replacements[#replacements+1]=key end
  table.sort(replacements,function(a,b) return #a>#b end)
 end
 -- Literal matching; input bindings and punctuation must never become Lua patterns.
 for _,key in ipairs(replacements) do
  local start=1
  while true do
   local a,b=value:find(key,start,true);if not a then break end
   value=value:sub(1,a-1)..strings[key]..value:sub(b+1);start=a+#strings[key]
  end
 end
 return value
end
return locale
