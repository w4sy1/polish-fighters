-- Local launcher selection. Packages remain isolated until their IDs are remapped.
local preferences={}
function preferences.read(profiles)
 local doc,problem=engine.read_settings()
 if problem then return nil,problem end
 local saved=type(doc)=='table' and doc.little_fighters_packs
 local result={}
 for _,entry in ipairs(profiles) do result[entry.id]=not(type(saved)=='table' and saved[entry.id]==false) end
 return result
end
function preferences.save(profiles,selected)
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
 return engine.write_settings(doc)
end
return preferences
