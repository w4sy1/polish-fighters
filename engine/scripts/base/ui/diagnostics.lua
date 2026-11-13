local font=require('base/ui/font')
local diagnostics={}
function diagnostics.create()
 local doc=engine.read_settings() or {};local lines={'DIAGNOSTYKA / DIAGNOSTICS','Raporty sa lokalne. Udostepniaj je tylko swiadomie.'}
 local function add(text)
  for line in (tostring(text)..'\n'):gmatch('(.-)\n') do
   repeat lines[#lines+1]=line:sub(1,104);line=line:sub(105) until line==''
  end
 end
 for _,key in ipairs({'polish_fighters_last_crash','polish_fighters_last_session'}) do
  local report=doc[key]
  if type(report)=='table' then
   add(key);add('Wersja: '..tostring(report.version));add('Modul: '..tostring(report.profile))
   add('Tryb: '..tostring(report.mode)..' Etap: '..tostring(report.stage)..' Faza: '..tostring(report.phase))
   add('Obiekty: '..tostring(report.object_count)..' Klatka: '..tostring(report.frame))
   add(report.traceback or 'Ostatni zapis kontekstu gry')
  end
 end
 if #lines==2 then add('Brak raportow awarii.') end
 return {lines=lines,offset=0}
end
function diagnostics.update(s,input)
 if input.nav and input.nav.cancel or input.click and input.pointer_y>505 and input.pointer_x>600 then return 'back' end
 if input.click and input.pointer_y>505 then
  s.offset=math.max(0,math.min(math.max(0,#s.lines-21),s.offset+(input.pointer_x<200 and -19 or 19)))
 end
end
function diagnostics.draw(s,context)
 context.viewport(794,550,12,20,40)
 for row=1,21 do if s.lines[s.offset+row] then font.draw(context,s.lines[s.offset+row],12,14+(row-1)*23) end end
 for _,b in ipairs({{8,'WSTECZ'},{248,'DALEJ'},{620,'ZAMKNIJ'}}) do
  context.fill(b[1],508,158,34,35,65,105,255);font.draw(context,b[2],b[1]+79,518,nil,nil,'center')
 end
end
return diagnostics
