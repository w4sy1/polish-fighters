# Reinforced — zgodność danych, 2026-10-29

Oryginalny EXE SHA256: 9b71fc264d214976eb77f4622ba46cb5b7760176c112f7ea3fa0b57da5241f27.
Statycznie odzyskane dane: 28 postaci, 100 obiektów, 14 aren, 687 zasobów. ID i kolejność zachowane. Nie wykonywano oryginalnych programów ani instalatorów. Nie budowano gry.

Audyt wszystkich 43 wcześniejszych alarmów: 37 ma komplet używanych komórek w granicach obrazu (pusta zadeklarowana pojemność); 6 ma klatki odwołujące się poza obraz. Nie dorysowano brakujących animacji ani nie przenumerowano klatek. To nie jest potwierdzenie ich wyglądu w oryginalnej grze. Szczegóły, prostokąty i dodatkowe numery pic spoza wszystkich arkuszy: validation/pack-compatibility-2026-10-29/reinforced-final.json.

Aktywne braki zasobów po imporcie: 0. Kontrole rozmiarów obrazów i ich sumy w asset-checksums.json.

Bazę brakujących plików zastąpiono danymi współdzielonymi Starterkitu LF Empire, który zawiera obok siebie LF2v1.9.exe, LF2v1.9c.exe i LFv2.0.exe. Źródło: https://www.lf-empire.de/downloads/LF2-Starterkit.zip ; opis: https://www.lf-empire.de/lf2-empire/introduction/downloads/lf2-starterkit ; SHA256 archiwum: 143b6797ce3cff6ae202a6e3a80eaa94e3425314daaa164efafc9e3607c3b358.
Dodano wyłącznie brakujące ścieżki (421), nigdy pliki autora dodatku. Lista i sumy: ../games/Reinforced-with-starterkit-2026-10-29/BASE-DEPENDENCIES.json. Wszystkie badane obrazy mają te same wymiary co poprzednia baza 1.9. To statyczne potwierdzenie zgodności geometrii z paczką obsługującą 1.9c; nie jest to wykonany test gry ani odczyt pełnego oryginalnego instalatora 1.9c.

Kod i dane sekcji .text, .rdata oraz .data EXE dodatku są bajtowo identyczne z LF2v1.9.exe ze Starterkitu. Różni się .rsrc. W tych sekcjach nie ma autorskiej poprawki mechaniki do przeniesienia; własne akcje pozostają w DAT. Nie potwierdzono pełnej zgodności mechaniki LF2 1.9 z naszym silnikiem 2.0a.
Źródło dodatku: https://www.lf-empire.de/downloads/versions/LF2_Reinforced.zip.

Reinforced: oid0 jest nieaktywnym spawnem; istniejący objects.spawn_from_frame odrzuca go przed tworzeniem obiektu. Bez dopisywania fikcyjnego obiektu ID0.

Testy natywne na historycznym własnym EXE nie doszły do meczu: Bleach przekracza limit rozmiaru zasobu, Kate/Reinforced zatrzymuje wcześniejszy match_history.lua (niedostępny setmetatable w sandboxie). Nie zmieniono historycznej paczki. Pełna grywalność, AI i kampanie pozostają niezweryfikowane. Autorstwo zasobów pozostaje przy twórcach; nie publikowano pakietu.

## Aktualna walidacja natywna — 2026-10-30

Powyższa informacja o blokadach testów jest historyczna: usunięto błąd setmetatable i ograniczenie dużych BMP przez bezstratne PNG. Własny istniejący silnik uruchomił 28/28 postaci przez 300 klatek, bez zaobserwowanych prostokątów poza obrazami. Testy headless nie potwierdzają wyglądu ani wszystkich ataków.

Klasyfikacja dawnych alarmów po korekcie odczytu: {'partial_clipping_remaining': 3, 'referenced_cells_fit': 37, 'empty_sources_suppressed': 3}. Częściowe przycięcia pozostają jawne. sprite_layout.lua koryguje tylko dokładnie upakowane osie i pomija źródła całkowicie poza obrazem; nie zmienia pikseli, klatek symulacji, hitboxów ani czasu. Raport: validation/native-fixes-2026-10-29/REPORT.md.
