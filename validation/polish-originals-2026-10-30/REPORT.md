# Cztery postacie Polish Fighters — 2026-10-31

## Zmieniono

Dodano oddzielny pakiet `content-packs/polish-originals`: Wasyl 410, Szymonoko/SZ 411, Mega Ninja Jaś 412, Skibidi Sigma Tata 413 oraz siedem obiektów umiejętności 420–426. Nowe rekordy są dopisane po wszystkich rekordach oryginalnego katalogu LF2. Oryginalne postacie, ich DAT, mapy i siedem wcześniej importowanych pakietów zachowano.

Zaimplementowano podstawowe animacje i ataki, jeden klon do pokonania, leczenie Wasyla, teleporty, salwy SZ i klona, osiem mieczy, śluz ze spowolnieniem, surfowanie, tupnięcie bossa, robaka, pomocników, deszcz kul i drugą fazę poniżej 50% HP. Klony nie mogą tworzyć klonów. Dla nowych postaci komputerowych dodano osobną obsługę ruchu i używania umiejętności. Parametry Jasia: siła 2, trudność 2,5.

Dodano polecenie rysowania skalowanego RGBA w Lua/C++/SDL. Dotychczasowe polecenia i domyślne rozmiary nie zmieniają się. Własne atlasy zachowano bajt w bajt; położenia klatek opisują metadane. Zbudowano nowy Windows EXE i osobny katalog przenośny `engine/out/PolishFighters-originals-2026-10-31`. Starszych paczek nie nadpisywano. Build Windows uwzględnia nowy pakiet.

## Pliki

- Nowy pakiet: `package.manifest`, `catalog.lua`, `runtime.lua`, `frame_rules.lua`, `ai.lua`, `match.lua`, `render.lua`, `selection.lua`, `match_screen.lua`, `layout.lua/json`, `asset-checksums.json`, `import-report.json`, `art/*.png`, lokalne `assets/*.dat` i `assets/catalog.txt`, README_PL.md, SOURCE.md, ART-PROMPTS.md.
- Silnik: `engine/include/openlf2/ports/platform.hpp`, `engine/src/adapters/luajit/runtime.cpp`, `engine/src/adapters/sdl/platform.cpp`, `engine/scripts/runtime/bootstrap.lua`; opcjonalny test SDL w `engine/CMakeLists.txt`.
- Narzędzia: `tools/build_polish_originals.py`, `check_polish_originals.py`, `probe_polish_originals.py`, `package_polish_originals.py`, rozszerzona lista pakietów w `build_windows_local.ps1`.
- Testy: `tests/polish_originals_test.lua`, `tests/scaled_sprite_probe.cpp`.
- Status: PROJECT-STATUS.md, config/project.json, .gitignore (udostępnienie tego raportu).

## Testy i wyniki

- Windows Release: nowy silnik i opcjonalny test SDL skompilowane poprawnie.
- Oryginały: SHA256 **7712/7712** plików bazowych i siedmiu pakietów zgodne z punktem przywracania. Po usunięciu dodanych rekordów katalog jest identyczny bajtowo z przypiętym LF2.
- Dane nowego pakietu: **707 klatek DAT**, **256 adresów wycinków** i **16 sum zasobów** sprawdzonych; brak pustych/wychodzących poza atlas wycinków oraz brakujących celów przejść klatek.
- Lua: **18 testów**, składnia **99 plików** poprawna. Nowe przypadki sprawdzają limit i trwałość klona przez 900 kroków, zakaz rekurencji, odnowienie po pokonaniu, dokładnie osiem mieczy, ograniczone leczenie bez wskrzeszania, śluz/obrażenia/spowolnienie/wygaśnięcie, pomocników i fazę bossa, spadające kule, granice teleportu i niezmienione parametry delegowanych oryginalnych sprite'ów.
- Python: **48 testów — 47 OK, 1 pominięty**.
- Natywne próby rzeczywistych wejść: **4/4 postacie**, każda **2 × 900 klatek**, wybrana postać potwierdzona, wyniki deterministyczne, brak obserwowanych brakujących opoint/wyjść poza atlas.
- Osobne kontrolowane próby natywne: **4/4**, wejście do wszystkich **7 umiejętności każdej postaci** i 900 kroków z parserem DAT, symulacją i dekoderem rysowania. Zapisano zdarzenia i obecność obiektów; brak nieokreślonych klatek. Te próby wymuszają stany testowe i nie są testem wykonania wszystkich kombinacji ręką gracza.
- Produkcyjny adapter SDL software: **64 rysowania** (32 wybrane pozy × dwa kierunki); zapisano i obejrzano `render.bmp`. Na jego podstawie poprawiono przycięcia dolnych rzędów Wasyla. To kontrola renderera i wybranych pozycji, nie pełna ocena animacji podczas interaktywnej gry.
- Gotowy katalog przenośny: dodatkowe **4/4 próby po 900 klatek** z jego własnymi skryptami i zasobami; cztery PNG mają identyczne bajty jak wyniki ImageGen. ZIP sprawdzono przez CRC i obecność wszystkich zasobów manifestu.
- C++: **6 testów natywnych** oraz oddzielne próby TCP **2–8 klientów**, rozłączenia i timeout — OK. To regresja istniejącego transportu, nie potwierdzenie synchronizacji nowych mechanik przez sieć.

Dowody lokalne: `preservation-before.json`, `preservation-after.json`, `native-summary.json`, `staged-summary.json`, `art-preservation.json`, `native/`, `skills/`, `render.log/bmp`, `lua-tests.log`, `python-tests.log`, `cpp-tests.log`, `build.log`, `render-build.log`. Lista SHA paczki: `delivery.json` i plik `.zip.sha256` obok dostawy.

## Granice i ryzyka

To działająca w próbach natywnych wersja eksperymentalna. Balans, płynność każdej animacji, wszystkie pojedyncze kombinacje w walce, pełne kampanie, zapis/odtworzenie nagrań z nowymi mechanikami, sieć między urządzeniami oraz Android/ARM nie zostały zweryfikowane. Nie zbudowano APK w tym etapie. Własne postacie nie korzystają jeszcze z opcjonalnego cieniowania CPU. W atlasach są powtórzenia i drobne artefakty przy efektach; nie wszystkie 256 adresów są unikalnymi rysunkami. Nowa lista losowania zachowuje dotychczasową zasadę LF2 — nową czwórkę wybiera się ręcznie.

Znane wcześniejsze braki Bleach/DBZ/pozostałych dodatków pozostają opisane w poprzednim raporcie; ten etap ich nie naprawia ani nie przedstawia jako ukończonych. Zakres odpowiada prośbie o cztery własne postacie z zachowaniem oryginalnych postaci LF. Nie wykonano commita, pushu ani publikacji release.
