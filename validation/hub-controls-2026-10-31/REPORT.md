# Little Fighters — menu, sterowanie i poprawki postaci, 2026-10-31

## Zakres i zmiany

Dodano nowe pierwsze menu **Little Fighters** oraz odrębnie nazwany zestaw **Polish Fighters**. Menu pozwala wybrać dziewięć profili: bazowy LF2 i osiem pakietów. Zmiana profilu przeładowuje katalogi/skrypty i zasoby w tym samym programie; przytrzymany przycisk nie przechodzi przypadkowo do następnego ekranu. Dostępne są walka lokalna, kampania, bitwa, turniej, mapy, historia, istniejący LAN i ustawienia. „Wszystkie mody — katalog” uruchamia pojedynczy profil; nie przedstawia łączenia modów jako gotowego.

Nowy ekran sterowania obsługuje czterech lokalnych graczy, klawiaturę, klawiaturę z przyciskami myszy oraz pady 1–4. Zawiera przypisywanie, gotowe układy, anulowanie, zapis, domyślne ustawienia i jawne usuwanie kolizji klawiszy między graczami. Zapis jest wspólny dla pakietów. Dodano mapowanie LPM/PPM/środkowego/bocznych przycisków myszy na konfigurowalne akcje. To mapowanie przycisków, nie celowanie kursorem.

Zwykły atak SZ tworzy pocisk bez zużycia many. Naprawiono gubienie krótkich tapnięć ataku/skoku/bloku między dwiema próbkami wejścia. Replays nie są objęte nowym buforem, a oczekujące tapnięcia są kasowane podczas pauzy. Dodano podpowiedź aktualnych przypisań przy wyborze postaci.

Portrety miały poprzednio 55×55, mimo że bazowy LF2 używa 120×120. Rozdzielono portret wyboru 120×120 i ikonę HUD 40×45. Zwiększono skalę sylwetek, wyrównano stopy na podstawie widocznej alfy, poprawiono wycinki pocisków i przypisano właściwsze pozy skoku/bloku/umiejętności. Obrazy PNG pozostały bez zmian. Naprawiono również rzeczywisty błąd renderowania pasków HP powyżej 500, dotyczący m.in. bossa z 1500 HP; bazowy zakres LF2 zachowuje dotychczasowe proporcje.

Nowy katalog: `engine/out/LittleFighters-hub-2026-10-31`. Uruchamiany plik: **LittleFighters.exe**; stary `openlf2.exe` pozostaje zgodnym aliasem. Dane obok EXE są wykrywane bez dodatkowych argumentów. Starszych katalogów i paczek nie nadpisywano. Nie wykonano commita, pushu, publikacji release ani wdrożenia.

## Zmienione pliki

- Nowe moduły `engine/scripts/polish-fighters/`: hub.lua, hub_launch.lua, hub_flow.lua, input_settings.lua, input_buffer.lua, input_match.lua, controls_hint.lua; ich wpisy w package.manifest oraz etykieta aktywnego zestawu w classic_shell.lua.
- `engine/scripts/base/ui/controls.lua`: zapis/odczyt trybu myszy; `base/ui/match_screen.lua`: bezpieczne paski HUD z obsługą podwyższonego HP.
- `engine/src/app/application.cpp`: wybór/przeładowanie profili, wykrywanie danych przy EXE, wspólne ustawienia przenośne oraz diagnostyczny zrzut klatki. `engine/src/adapters/sdl/platform.cpp`: przyciski myszy, tytuł okna i diagnostyczny zapis obrazu; interfejs capture_frame w `engine/include/openlf2/ports/platform.hpp`.
- `content-packs/polish-originals/`: runtime.lua, render.lua, layout.lua/json, package.manifest, lokalne DAT/katalog, sumy zasobów i README. Generator: tools/build_polish_originals.py.
- Testy/narzędzia: tests/hub_input_test.lua, rozszerzony polish_originals_test.lua; tools/probe_hub_controls.py, audit_hub_delivery.py, package_hub_windows.py; nazwa EXE i wspólne ustawienia w build_windows_local.ps1.
- Dokumentacja/status: LITTLE_FIGHTERS_WINDOWS.md, PROJECT-STATUS.md, config/project.json, .gitignore i ten raport.

## Testy i wyniki

- Windows Release: kompilacja C++/LuaJIT/SDL zakończona poprawnie.
- Lua: **19 testów**, składnia **106 plików** — OK. Nowe przypadki obejmują zapisy i ponowne wczytanie, mysz, przypisywanie pada, ignorowanie przycisku otwierającego, Escape, konflikty graczy, błąd zapisu, krótki tap, pauzę i wyłączenie bufora podczas replay.
- Python: **48 testów — 47 OK, 1 pominięty**.
- C++: **6 testów** oraz procesowe TCP **2–8 klientów**, rozłączenie i timeout — OK. To regresja transportu, nie fizyczny multiplayer nowej czwórki.
- Natywne menu: **9/9 profili**, rzeczywiste kliknięcia we współrzędne menu, właściwy profil po przeładowaniu; test przytrzymanego kliknięcia. Ustawienia zapisano przez faktyczny ekran, ponownie otwarto, zmieniono klawisz i sprawdzono JSON. Przycisk pada przypisano przez syntetyczne wejście kontrolera.
- Zwykły strzał SZ: pojedynczy tap przypisanego LPM → **1 strzał, 22 obrażenia, 0 zużycia MP**. Przeciwnik Deep i jego położenie zostały ustawione kontrolowanie w izolowanym pakiecie QA; wejście ataku przeszło przez rzeczywiste mapowanie sterowania i symulację.
- Cztery postacie: każda **2 × 900 klatek** rzeczywistych sekwencji wejść, deterministycznie, poprawna postać potwierdzona. Dodatkowo po siedem umiejętności w kontrolowanych próbach natywnych.
- SDL software: zapisano i obejrzano rzeczywiste klatki pierwszego menu, konfiguracji, wyboru portretów, strzału oraz pięciu postaci obok siebie — z oryginalnym Deepem i bossem. To ujawniło i pozwoliło naprawić błąd paska HP; obraz strzału potwierdza widoczny pocisk i ikonę HUD.
- Zachowanie źródeł: **7710 plików** z poprzedniego punktu kontrolnego bez zmian; dwa jawnie zmienione pliki bazowe to UI controls.lua i match_screen.lua. Oryginalne dane postaci LF i siedmiu poprzednich dodatków zachowane. W ośmiu pakietach sprawdzono **7603 odwołania zasobów** — żadnych braków ani różnic względem źródeł. Cztery PNG identyczne bajtowo z wcześniejszymi wynikami generacji.
- `git diff --check`, przegląd diff/stat i składnia PowerShell — wykonane przy finalizacji. Wynik CRC, rozmiar i SHA256 dostawy są w delivery.json.

Dowody lokalne: summary.json, preservation.json, build.log, lua-tests.log, python-tests.log, cpp-tests.log, profile-*/run.log, held-switch/, input/, remap/, pad/, basic-shot/, shot-visual/, portraits/, lineup/, fighters/ i skill-regression/.

## Pozostałe prace i ograniczenia

Nie ukończono wspólnej puli wszystkich modów, dobierania mieszanego zestawu ani pobierania/aktualizacji pakietów z GitHuba. Grafika pozostaje eksperymentalna: przypisania i skala są poprawione, lecz nie powstał pełny nowy zestaw spójnych klatek animacji ani finalny balans. Pełnych kampanii i brakujących mechanik wcześniejszych dodatków nie naprawiano w tym etapie.

Nie przetestowano fizycznego pada, Androida/APK/ARM, nowego sterowania na telefonie ani synchronizacji nowej czwórki na urządzeniach. Fizyczny mysz/klawiatura nadal wymaga próby użytkownika; automatyczne wejścia sprawdzają tę samą ścieżkę mapowania, a zrzuty powstają w SDL software. Podgląd pięciu postaci i test pojedynczego strzału używają jawnych danych QA. Nie stanowią pełnego ręcznego przejścia gry.

Zakres odpowiada pierwszemu etapowi zaakceptowanego planu: dostępne menu pakietów i sterowania oraz naprawa podstawowych problemów postaci. Cały opisany przez użytkownika produkt nie jest jeszcze ukończony.
