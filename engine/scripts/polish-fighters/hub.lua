-- First menu shared by all profiles. Only installed packages can be activated.
local hub={}
hub.profiles={
 {id="polish_fighters",profile="polish-originals",title="Polish Fighters"},
 {id="lf_two",profile="lf2-classic",title="LF2"},
 {id="lf_four_turbo",profile="lf4-turbo",title="LF4 Turbo"},
 {id="dbz",profile="dbz",title="Dragon Ball"},
 {id="one_piece",profile="one-piece",title="One Piece"},
 {id="kate",profile="kate",title="Kate"},
 {id="reinforced",profile="reinforced",title="Reinforced"},
 {id="ntsd",profile="ntsd",title="NTSD / Naruto"},
 {id="bleach",profile="bleach",title="Bleach"},
}
function hub.title(profile)
 if profile=='mixed-all' then return 'Polish Fighters: wszystkie mody' end
 for _,entry in ipairs(hub.profiles) do if entry.profile==profile then return entry.title end end
 return "Little Fighters"
end
function hub.rows(state)
 if state.hub_mode=="packs" then
  local rows={}
  for _,entry in ipairs(hub.profiles) do
   rows[#rows+1]={"toggle_"..entry.id,(state.hub_pack_edit[entry.id]~=false and "[WŁ.] " or "[WYŁ.] ")..entry.title}
  end
  rows[#rows+1]={"packs_all","ZAZNACZ WSZYSTKIE"}
  rows[#rows+1]={"packs_duplicates",state.hub_hide_duplicates~=false and "POWTÓRZENIA LF2: UKRYTE" or "POWTÓRZENIA LF2: WIDOCZNE"}
  rows[#rows+1]={"packs_save","ZAPISZ WYBÓR"}
  rows[#rows+1]={"packs_cancel","ANULUJ"}
  return rows
 end
 if state.hub_mode=="profile" then
  return {{"versus","WALKA LOKALNA"},{"stage","KAMPANIA / PRZYGODA"},{"battle_setup","BITWA DRUŻYN"},
    {"championship","TURNIEJ"},{"maps","WYBIERZ MAPĘ"},{"fighters","PORADNIK KOMBOSÓW / POSTACIE"},
    {"network","KONTA / POKOJE / LAN"},{"controls","USTAWIENIA STEROWANIA"},{"root","MODUŁY / MENU GŁÓWNE"}}
 end
 local rows={}
 if state.hub_mode~="library" then rows[#rows+1]={"library","WSZYSTKIE MODY / WSPÓLNA PULA"} end
 for _,entry in ipairs(hub.profiles) do
  if state.hub_mode~="library" or not state.hub_selected or state.hub_selected[entry.id]~=false then
  local available=state.hub_available and state.hub_available[entry.id]
  rows[#rows+1]={"profile_"..entry.id,entry.title:upper()..(available==false and " [BRAK PAKIETU]" or "")}
  end
 end
 if state.hub_mode=="library" then
  rows[#rows+1]={"packs","DOBIERZ AKTYWNE PAKIETY"}
  rows[#rows+1]={"profile_mixed","WSZYSTKIE RAZEM — TRYB TESTOWY"}
  rows[#rows+1]={"root","POWRÓT"};return rows
 end
 rows[#rows+1]={"controls","USTAWIENIA STEROWANIA"}
 rows[#rows+1]={"options","USTAWIENIA"}
 rows[#rows+1]={"versus","GRA LOKALNA"}
 rows[#rows+1]={"network","KONTA / POKOJE / LAN"}
 rows[#rows+1]={"extras","HISTORIA / ODBLOKOWANIA"}
 rows[#rows+1]={"recording","USTAWIENIA NAGRAŃ"}
 rows[#rows+1]={"replay","ODTWÓRZ NAGRANIE"}
 rows[#rows+1]={"quit","WYJŚCIE"}
 return rows
end
return hub
