# Mapy, przygody i dostarczenie projektu — 2026-10-30

Zakres: 11 arkuszy Bleach/Kate/Reinforced, cztery brakujące opoint, mapy i przygody wszystkich zaimportowanych profili oraz LF2, nowy EXE, kod Android Studio i publikacja kodu na prywatnym GitHub. Nie wykonywano żadnego oryginalnego EXE/DLL. Archiwa czytano jako dane.

## Zmiany i wyniki

- sprite_layout.lua trzech pakietów przecina częściowe źródła z fizycznymi granicami obrazów. Odbicie zachowuje położenie widocznej części. Nie skalowano/dorysowywano pikseli, nie zmieniano pic, hitboxów ani czasu. 11 starych problemów ma bezpieczny odczyt, ale nie odtworzono nieistniejącej grafiki ani intencji autora. Rzeczywista funkcja Lua przeszła58768 lookupów wszystkich klatek przy offsetach0/140, bez zwróconych prostokątów poza obrazami (sprite-source-verification.json).
- Kate: odzyskano dokładny oid99 z V1.00 Ver2 autora, z25 oryginalnymi plikami, nie zgadywanego zastępcy. Stare rekordy zachowują indeksy; helper nie trafia do wyboru gracza. Diagnostyczne uruchomienie prawdziwych opoint obiektu300/frame174 i180 tworzy99/action390 i392, po czym przechodzi300 klatek. To uruchomienie źródłowych klatek w QA, nie dowód naturalnego wykonania kombinacji. Dowody: kate-oid99/summary.json, content-packs/kate/recovered-oid99.json; źródła i sumy zachowane.
- Bleach oid284/action83 i151/action30 nadal nie mają jednoznacznie odzyskanych danych. Nie mapowano ich na dowolne istniejące obiekty.
- Silnik: mapy do256 warstw (DBZ ma154), tylko WMA do64MiB zgodnie z dekoderem (inne zasoby nadal16MiB). Żadnej warstwy nie pominięto. Niewidoczne cienie na arenie Reinforced o szerokości50000 nie trafiają do ograniczonego mostka rysowania. Test tej areny teraz przechodzi.
- DBZ: rekordy hidden:4 bez portretu są wewnętrznymi aktorami, nie wybieralnymi kafelkami; nie usunięto ich ze spawnowania ani nie zmieniono numeracji. NTSD: naprawiono wyłącznie zapis x: - 250 na x: -250, z zachowaniem nagłówka i wartości.
- Nowy EXE Windows zbudowany i dołączony do osobnej paczki. Cztery próby gotowej paczki (Bleach, Kate, Reinforced, LF4) przeszły300 klatek na rzeczywistych postaciach i danych paczki; portable-smoke/summary.json.

## Wszystkie mapy i przygody

128 map z katalogów plus wbudowana Lee On Road:117/129 OK. Starty259 etapów w31 plikach przygód:170/259 OK. Inwentaryzacja obejmuje1287 faz (187 LF2 +1100 dodatków). Testy startu nie przechodzą każdej fazy i nie stanowią ukończonych kampanii.

| Profil | Mapy | Starty etapów |
|---|---:|---:|
| lf2-classic | 13/13 | 25/25 |
| lf4-turbo | 12/12 | 25/25 |
| bleach | 12/12 | 20/20 |
| kate | 11/11 | 33/33 |
| reinforced | 14/14 | 44/44 |
| ntsd | 17/17 | 2/25 |
| dbz | 2/14 | 0/62 |
| one-piece | 36/36 | 21/25 |

To testy headless: odczyt zasobów, walidacja poleceń i120 wywołań rysowania, bez oceny obrazu na ekranie. Gracz QA to bazowy Deep, dzięki czemu nie mylimy błędu mapy z błędem rozszerzonej postaci; przeciwnicy kampanii pozostają autorskimi rekordami dodatku. Dla etapów QA wybiera jawnie poprawną arenę; nie potwierdza to mapowania/odblokowań autora. all-native-results.json ma kompletny indeks; native/<profil>/<próba>/ ma log i niezależny config z potwierdzeniem stworzenia/rysowania.

Nie przeszły12 scen DBZ (brak statycznego width, autorskie quest/opoint i dynamiczny silnik),62 starty DBZ (m.in. klatki499/500 poza obsługiwanym0–399),23 NTSD (m.in. liczby poza32-bit i nieprawidłowy zasób [mu]),4 One Piece (dekoder muzyki nie obsługuje tych ścieżek). W statycznych etapach są także rozszerzone selektory DBZ8002..8008 i brakujący obiekt One Piece122. Nie podstawiano za nie domyślnych postaci. Logi źródłowe i pełne inwentarze pozostają lokalne.

## Testy kodu i Android

- Python46:45 OK,1 pominięty (symlinki Windows), python-tests.log.
- LuaJIT14 zestawów OK; składnia83 plików OK, lua-tests.log.
- C++6 zestawów OK, w tym154/256 warstw przy zachowaniu limitu257,4096/4097 zasobów; oddzielnieTCP2–8 klientów, synchronizacja i zerwanie/timeout, native-cpp-tests.log.
- Android: zweryfikowany Gradle Wrapper8.13, rzeczywiste12 klas Java SDL3.4.14 z przypiętym SHA, własne Lua i ikony. Gradle tasks oraz compileDebugJavaWithJavac przeszły na lokalnym JDK17.0.18. JDK25 z aktualnego Studio jest za nowy dla Gradle8.13.
- Lint:27 błędów i9 ostrzeżeń, błędy w źródłach SDL (MissingPermission, NewApi, UnspecifiedRegisterReceiverFlag); nie wyłączono lint globalnie i nie oznaczono jako OK. Poprawiono lokalny zapis SDK. Raport Androida pozostaje lokalny.
- Nie zbudowano .so/APK Androida, nie uruchamiano urządzenia. verifyNativeGame blokuje fałszywie kompletne APK bez silnika. ANDROID_STUDIO.md opisuje rzeczywisty Linux/CI cross-build; workflow eksportuje również biblioteki do lokalnego Studio.

## Pliki i bezpieczeństwo dostarczenia

Kod: engine/include/openlf2/engine/packages.hpp, src/app/application.cpp, include/openlf2/resources/background_data.hpp, src/resources/background_data.cpp, scripts/base/game/catalog.lua, scripts/base/ui/match_screen.lua. Pakiety: katalogi Kate/DBZ, sprite_layout.lua i metadane3 pakietów, nowy zasób99 i zależności, pojedynczy DAT NTSD. Android: wrapper, app/build.gradle (kontrola bibliotek); applicationId/signing/namespace/Manifest nie zmieniano. Narzędzia: build_windows_local.ps1, build_sprite_layouts.py, probe_native_packs.py i nowe audit_maps_adventures.py, verify_sprite_sources.py, recover_kate_oid99.py, probe_recovered_kate.py, prepare_android_studio.py, package_delivery.py, finalize_maps_delivery.py. Testy: sprite_layout_test.lua, internal_actor_test.lua, background_layers_test.cpp, package_assets_test.cpp, test_kate_recovery.py. Dokumentacja i konfiguracja statusu uaktualnione.

Lokalna pełna paczka Windows zawiera posiadane dane i7 dodatków, także jawnie eksperymentalne. GitHub zawiera kod, ZIP własnego silnika Windows z bibliotekami oraz ZIP projektu Android Studio. Cudze instalatory, grafiki i dźwięki dodatków, userdata, bazy, prywatne klucze, local.properties i cache buildów są wyłączone. Zachowano publiczny debug.keystore upstream; nie jest kluczem produkcyjnym.

Kopia przed zmianami: ../baseline-maps-build-2026-10-30/. Utworzono repo Git na branchu codex/maps-build-2026-10-30, ponieważ projekt wcześniej nie miał.git. Bez zmiany istniejącej historii, force-push i wydania produkcyjnego. Git diff względem kopii i staged stat oraz skan sekretów są częścią lokalnego sprawdzenia przed wysłaniem.

Zakres jest częściowo wykonany: EXE i źródła dostarczone, wszystkie zadeklarowane mapy/starty sprawdzone, Kate99 odzyskany. Bleach2 cele, nieobsługiwane mechaniki kampanii i Android runtime pozostają otwarte. Bez deklaracji pełnej grywalności.

Źródło Kate: https://hcyang1227.blogspot.com/2019/11/lf2-kate.html; archiwum autora SHA256 e71fdc5332eb88b2eb9dd5414909cb84c8809c84957e59c076ff4af2d88ab7b8. Wyłącznie ekstrakcja danych, bez wykonania instalatora. Źródło informacji o BBR2.0a: https://ntsd.forumotion.com/t26040-bleach-bankai-revolution; nie dostarczyło brakujących2 celów.

SHA256 nowego EXE: 6ab63aa8990d1d201ab14c506aa96369274c76bbdd1583fcd9d1bcfee56a3e0a
