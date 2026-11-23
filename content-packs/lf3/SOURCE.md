# LF3BYTITASZIBIKAS 2.0b — import eksperymentalny

Plik dostarczony przez użytkownika: `LF3BYTITASZIBIKAS2.0b.rar` (466MB, rozpakowane ~1.8GB —
głównie nieskompresowane BMP w `bg/`, `sprite/`, `sprite_ce/`). Rozpakowane lokalnie przez
użytkownika (za duże do bezpośredniego transferu w tej sesji), spakowane ponownie po folderach
(bg/bgm/sprite/sprite_ce osobno) i przesłane partiami. Folder `bgm` (muzyka, 198MB) pominięty —
importer nie korzysta z plików `.wma`.

Trzy naprawy zastosowane na źródłowym `data/data.txt` przed importem:
1. 4 wystąpienia twardej spacji (U+00A0 / `\xc2\xa0`, zapewne z kopiowania tekstu z edytora/strony
   web) zamiast zwykłej spacji między polami `id:`/`type:`/`file:` — zamienione na zwykłą spację.
2. Duplikat ID 295 (`sprite\clide\clide_ball.dat` vs `sprite\volt\electricity.dat`) — drugie
   wystąpienie zakomentowane.
3. Folder tła `bg\sys\M&M\` — znak `&` w nazwie ścieżki odrzucany przez walidację bezpieczeństwa
   importera (`tools/import_legacy.py`, dozwolony wzorzec `[a-z0-9_./-]+`). Folder przemianowany na
   `bg/sys/mm`, referencja w `data.txt` poprawiona analogicznie.

Postacie: 206 obiektów, 92 tła, 2128 zasobów — największy dotąd zaimportowany pakiet. 7 drobnych
braków: `data/109.wav` i 6 klatek `m/fall_*.bmp`/`m/base2.bmp`/`m/s.bmp` (najwyraźniej osobny,
niepowiązany z główną ścieżką `data/` zestaw plików animacji — nie krytyczne). 76 arkuszy sprite'ów
nierozwiązanych pod kątem dopasowania wymiarów, 1 automatyczna naprawa krawędzi sprite'a
(`sprite_edge_repairs: 1`) — wymaga audytu przed pełnym uznaniem za kompatybilne.

Zawiera też postać `Broly` (DBZ crossover) jako osobny folder najwyższego poziomu w archiwum.

Status: eksperymentalny. Nie potwierdzono działania postaci, AI, kampanii ani efektów — tylko
statyczny import danych.

Autorstwo i prawa do oryginalnych zasobów pozostają przy twórcach moda. Brak publicznej publikacji.
