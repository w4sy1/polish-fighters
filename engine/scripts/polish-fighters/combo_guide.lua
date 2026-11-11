-- Player-facing action names. D/A/J are actions, never hard-coded keyboard keys.
local guide={}
guide.order={410,411,412,413,414,415}
guide.names={[410]='Wasyl',[411]='Szymonoko / SZ',[412]='Mega Ninja Jaś',
 [413]='Skibidi Sigma Tata',[414]='Remonoko / Remek',[415]='Remonoko - Kamienny Mech'}
guide.basics={
 'JAK ROBIĆ KOMBOSY',
 'D = blok, A = atak, J = skok.',
 'To nazwy akcji, nie litery klawiatury.',
 'Wciskaj kolejno, nie wszystkie naraz.',
 '> = kierunek patrzenia; w lewo użyj <.',
 '^ = góra, v = dół. Ustaw się w linii wroga.',
 'D > A: blok, kierunek, dopiero potem atak.',
 'Telefon: te same akcje na ekranowych przyciskach.',
 'Nie działa? Sprawdź MP i poczekaj na koniec ciosu.',
 'Klawisze sprawdzisz w USTAWIENIACH STEROWANIA.'}
local moves={
 [410]={
  {'D > A','Seria trzech pocisków',300}, {'D ^ A','Jeden słabszy klon',310},
  {'D v A','Teleport w pobliże przeciwnika',320}, {'D > J','Uderzenie obszarowe',330},
  {'D ^ J','Seria pięciu pocisków',340}, {'D v J','Seria pięciu pocisków',350},
  {'D J A','Seria pięciu pocisków',360}},
 [411]={
  {'D > A','Trzy pociski',300}, {'D ^ A','Pełny klon z własnymi umiejętnościami',310},
  {'D v A','Teleport i trzy pociski',320}, {'D > J','Trzy pociski',330},
  {'D ^ J','Osiem pocisków i wsparcie klona',340}, {'D v J','Teleport i osiem pocisków',350},
  {'D J A','Osiem pocisków',360}},
 [412]={
  {'D > A','Wachlarz ośmiu pocisków',300}, {'D ^ A','Spowalniający obszar',310},
  {'D v A','Teleport w pobliże przeciwnika',320}, {'D > J','Doskok / surf i pocisk',330},
  {'D ^ J','Wachlarz ośmiu pocisków',340}, {'D v J','Spowalniający obszar',350},
  {'D J A','Wachlarz ośmiu pocisków',360}},
 [413]={
  {'D > A','Trzy kule zaćmienia',300}, {'D ^ A','Obszarowa fala uderzeniowa',310},
  {'D v A','Trzy kule zaćmienia',320}, {'D > J','Wachlarz ognistych pocisków',330},
  {'D ^ J','Przywołanie do trzech ognistych toalet',340}, {'D v J','Deszcz ciemnych kul',350},
  {'D J A','Ładowany wybuch i osiem kul',360}},
 [414]={
  {'D > A','Metalowe BUM / doskok',300}, {'D ^ A','Mega Strzał',310},
  {'D v A','Metalowy Kop',320}, {'D > J','Seria ognia',330},
  {'D ^ J','Teleport',340}, {'D v J','Pułapka',350},
  {'D J A','Przemiana w Kamiennego Mecha',360}},
 [415]={
  {'D > A','Doskok; potem A, potem A',300}, {'D ^ A','Dwie fale ognia',310},
  {'D v A','Uderzenie obszarowe i pierścień',320}, {'D > J','Wachlarz płomieni',330},
  {'D ^ J','Ognisty krąg',340}, {'D v J','Pułapka',350},
  {'D J A','Powrót do zwykłej formy, bez MP',360}}
}
local notes={
 [410]={'Regeneracja HP działa automatycznie.', 'Klon Wasyla nie tworzy kolejnych klonów.'},
 [411]={'A: zwykły strzał nie zużywa MP.', 'Rodzina SZ: oryginał i najwyżej dwa klony.'},
 [412]={'Co trzecie trafienie: unik lub kontra.', 'Pasywnej kontry nie wciskasz kombinacją.'},
 [413]={'Finisher można przerwać trafieniem lub chwytem.', 'Toalety zostają do zniszczenia; mają 180 HP.'},
 [414]={'Przemiana kosztuje 200 MP; mech nie ma limitu czasu.', 'W powietrzu: J, potem jeszcze J - dodatkowe skoki.'},
 [415]={'Kombo doskok + A + A: łącznie 150 MP.', 'Mech to forma Remonoko, nie osobna postać.'}}
function guide.moves(id) return moves[id] end
function guide.message(id)
 if not moves[id] then return nil end
 local result={guide.names[id]..' - KOMBOSY'}
 for _,move in ipairs(moves[id]) do result[#result+1]=move[1]..' - '..move[2] end
 for _,line in ipairs(notes[id]) do result[#result+1]=line end
 return result
end
return guide
