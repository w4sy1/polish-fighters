# Bleach — zgodność danych, 2026-10-29

Oryginalny EXE SHA256: 3e8f030d15872a2d2c57efeb05cc4b9bc0318da6fb5111680b9a921222670414.
Statycznie odzyskane dane: 34 postaci, 100 obiektów, 12 aren, 753 zasobów. ID i kolejność zachowane. Nie wykonywano oryginalnych programów ani instalatorów. Nie budowano gry.

Audyt wszystkich 43 wcześniejszych alarmów: 18 ma komplet używanych komórek w granicach obrazu (pusta zadeklarowana pojemność); 25 ma klatki odwołujące się poza obraz. Nie dorysowano brakujących animacji ani nie przenumerowano klatek. To nie jest potwierdzenie ich wyglądu w oryginalnej grze. Szczegóły, prostokąty i dodatkowe numery pic spoza wszystkich arkuszy: validation/pack-compatibility-2026-10-29/bleach-final.json.

Aktywne braki zasobów po imporcie: 0. Kontrole rozmiarów obrazów i ich sumy w asset-checksums.json.

Sześć dawnych „braków nagrań” występuje wyłącznie jako #sound: w Kon.dat. Osiem adnotacji dotyczy sześciu unikalnych ścieżek. Natywny czytnik rozpoznaje sound:, więc #sound: jest nieaktywne. Importer zachowuje te adnotacje, lecz nie wpisuje ich do zależności; nagrań nie odzyskano i nie zastąpiono innymi.

Statyczne porównanie odtworzonego PE z przypiętym LF2 v2.0a: 157 różnych bajtów .text, identyczne .rdata/.data. Jedną rozpoznaną zmianę mechaniki przeniesiono: transformacje stanów 8000–8999 mają pic_offset=0 zamiast 140. Manifest ładuje frame_rules.lua, ustawienie jest izolowane w pakiecie. Test LuaJIT używa rzeczywistego before_advance. Pozostałe różnice dotyczą wskazań tekstów/brandingu, danych tekstowych w pustej części sekcji i sekwencji klawiszy odblokowania BLEACHX; nie są przeniesionym patchem walki. Nie jest to pełny audyt zgodności silnika.

Aktywne błędne cele pochodzą już z oryginalnych danych: zaraki_2.dat frame 9 → oid284/action83; wind.dat frame153 → oid151/action30. Brak tych ID w źródłowym katalogu. Nie przypisano im zgadywanych plików.

Źródło: https://lf-empire.de/forum/showthread.php?tid=9077 ; odzysk demoleition 0.61 z UniExtract2 RC3. Oryginalny katalog i log odzyskiwania zachowane. Ponowny import generycznym importerem wymaga zachowania osobnego rozszerzenia frame_rules.lua i jego wpisu w manifeście.

Testy natywne na historycznym własnym EXE nie doszły do meczu: Bleach przekracza limit rozmiaru zasobu, Kate/Reinforced zatrzymuje wcześniejszy match_history.lua (niedostępny setmetatable w sandboxie). Nie zmieniono historycznej paczki. Pełna grywalność, AI i kampanie pozostają niezweryfikowane. Autorstwo zasobów pozostaje przy twórcach; nie publikowano pakietu.

## Aktualna walidacja natywna — 2026-10-30

Powyższa informacja o blokadach testów jest historyczna: usunięto błąd setmetatable i ograniczenie dużych BMP przez bezstratne PNG. Własny istniejący silnik uruchomił 34/34 postaci przez 300 klatek, bez zaobserwowanych prostokątów poza obrazami. Testy headless nie potwierdzają wyglądu ani wszystkich ataków.

Klasyfikacja dawnych alarmów po korekcie odczytu: {'empty_sources_suppressed': 11, 'referenced_cells_fit': 26, 'partial_clipping_remaining': 6}. Częściowe przycięcia pozostają jawne. sprite_layout.lua koryguje tylko dokładnie upakowane osie i pomija źródła całkowicie poza obrazem; nie zmienia pikseli, klatek symulacji, hitboxów ani czasu. Raport: validation/native-fixes-2026-10-29/REPORT.md.
