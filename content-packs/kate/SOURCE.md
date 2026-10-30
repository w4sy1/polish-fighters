# Kate — zgodność danych, 2026-10-29

Oryginalny EXE SHA256: 14a545a6ffa43879db62f3cef9efd56e6ba34edcde36de628ed5dfc004d9d55e.
Statycznie odzyskane dane: 29 postaci, 98 obiektów, 11 aren, 719 zasobów. ID i kolejność zachowane. Nie wykonywano oryginalnych programów ani instalatorów. Nie budowano gry.

Audyt wszystkich 44 wcześniejszych alarmów: 36 ma komplet używanych komórek w granicach obrazu (pusta zadeklarowana pojemność); 8 ma klatki odwołujące się poza obraz. Nie dorysowano brakujących animacji ani nie przenumerowano klatek. To nie jest potwierdzenie ich wyglądu w oryginalnej grze. Szczegóły, prostokąty i dodatkowe numery pic spoza wszystkich arkuszy: validation/pack-compatibility-2026-10-29/kate-final.json.

Aktywne braki zasobów po imporcie: 0. Kontrole rozmiarów obrazów i ich sumy w asset-checksums.json.

Bazę brakujących plików zastąpiono danymi współdzielonymi Starterkitu LF Empire, który zawiera obok siebie LF2v1.9.exe, LF2v1.9c.exe i LFv2.0.exe. Źródło: https://www.lf-empire.de/downloads/LF2-Starterkit.zip ; opis: https://www.lf-empire.de/lf2-empire/introduction/downloads/lf2-starterkit ; SHA256 archiwum: 143b6797ce3cff6ae202a6e3a80eaa94e3425314daaa164efafc9e3607c3b358.
Dodano wyłącznie brakujące ścieżki (425), nigdy pliki autora dodatku. Lista i sumy: ../games/Kate-with-starterkit-2026-10-29/BASE-DEPENDENCIES.json. Wszystkie badane obrazy mają te same wymiary co poprzednia baza 1.9. To statyczne potwierdzenie zgodności geometrii z paczką obsługującą 1.9c; nie jest to wykonany test gry ani odczyt pełnego oryginalnego instalatora 1.9c.

Kod i dane sekcji .text, .rdata oraz .data EXE dodatku są bajtowo identyczne z LF2v1.9.exe ze Starterkitu. Różni się .rsrc. W tych sekcjach nie ma autorskiej poprawki mechaniki do przeniesienia; własne akcje pozostają w DAT. Nie potwierdzono pełnej zgodności mechaniki LF2 1.9 z naszym silnikiem 2.0a.
Źródło dodatku: https://www.lf-empire.de/downloads/versions/LF2_Kate.zip.

Kate: oryginalne kate.dat frame174/action390 i frame180/action392 wskazują nieistniejące oid99. Znaleziono wiele plików z tymi numerami klatek, więc nie da się wybrać celu jednoznacznie.

Testy natywne na historycznym własnym EXE nie doszły do meczu: Bleach przekracza limit rozmiaru zasobu, Kate/Reinforced zatrzymuje wcześniejszy match_history.lua (niedostępny setmetatable w sandboxie). Nie zmieniono historycznej paczki. Pełna grywalność, AI i kampanie pozostają niezweryfikowane. Autorstwo zasobów pozostaje przy twórcach; nie publikowano pakietu.

## Aktualna walidacja natywna — 2026-10-30

Powyższa informacja o blokadach testów jest historyczna: usunięto błąd setmetatable i ograniczenie dużych BMP przez bezstratne PNG. Własny istniejący silnik uruchomił 29/29 postaci przez 300 klatek, bez zaobserwowanych prostokątów poza obrazami. Testy headless nie potwierdzają wyglądu ani wszystkich ataków.

Klasyfikacja dawnych alarmów po korekcie odczytu: {'referenced_cells_fit': 36, 'partial_clipping_remaining': 2, 'empty_sources_suppressed': 6}. Częściowe przycięcia pozostają jawne. sprite_layout.lua koryguje tylko dokładnie upakowane osie i pomija źródła całkowicie poza obrazem; nie zmienia pikseli, klatek symulacji, hitboxów ani czasu. Raport: validation/native-fixes-2026-10-29/REPORT.md.

Jedyny nienumerowany transform otrzymał wywnioskowany numer350 na podstawie hit_ja350 i ciągu351+. To naprawa importu z oznaczoną inferencją, bez potwierdzenia oryginalnego runtime; data-repairs.json.
