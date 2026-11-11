-- Shared selection for launcher visibility and the generated mixed roster.
local preferences={}
function preferences.read(profiles)
 local doc,problem=engine.read_settings()
 if problem then return nil,problem end
 local saved=type(doc)=='table' and doc.little_fighters_packs
 local result={}
 for _,entry in ipairs(profiles) do result[entry.id]=not(type(saved)=='table' and saved[entry.id]==false) end
 return result
end
function preferences.hide_duplicates()
 local doc,problem=engine.read_settings()
 if problem then return nil,problem end
 return not(type(doc)=='table' and doc.little_fighters_hide_duplicates==false)
end
function preferences.save(profiles,selected,hide_duplicates)
 local count,clean=0,{}
 for _,entry in ipairs(profiles) do
  clean[entry.id]=selected[entry.id]~=false
  if clean[entry.id] then count=count+1 end
 end
 if count==0 then return nil,'Wybierz przynajmniej jeden pakiet.' end
 local doc,problem=engine.read_settings()
 if problem then return nil,problem end
 if type(doc)~='table' then doc={} end
 doc.little_fighters_packs=clean
 if hide_duplicates~=nil then doc.little_fighters_hide_duplicates=hide_duplicates==true end
 return engine.write_settings(doc)
end
return preferences
