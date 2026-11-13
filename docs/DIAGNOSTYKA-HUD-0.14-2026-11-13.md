# Polish Little Fighters 0.14.0 — wydanie testowe

Aktualizacja dodaje lokalną diagnostykę, ogranicza Szymonoko do jednego klona,
rozbudowuje sterowanie dotykowe, zapis kampanii i trening. **Nie potwierdza
usunięcia zgłaszanych awarii LF4/PolishF.** Nie udało się ich odtworzyć w
opisanych próbach Windows. Użytkownik zaakceptował dodanie logów do zebrania
przyczyny przy kolejnym wystąpieniu, prawdopodobnie na obu platformach.

## Zmiany

- Szymonoko: jeden żywy klon na właściciela, brak potomków, ponowne przywołanie
  po śmierci/usunięciu klona, usuwanie starych klonów przy zmianie odcinka.
  Poprzednia logika w `heroes.clone_allowed` celowo dopuszczała dwie generacje
  i trzy żywe jednostki w rodzinie; nowy test najpierw wykazał tę rozbieżność.
- Leumas EX: zachowano istniejący zakaz przywoływania postaci i działające
  pociski. Sprawdzono LF4 i remapowanie mixed-all; nie usunięto innych ruchów.
- Ustawienia obrazu/sterowania → EDYTOR HUD: przeciąganie, rozmiar,
  przezroczystość, czułość i martwa strefa joysticka, stały/dynamiczny środek,
  profile klasyczny/mobilny oraz trzy zapisy własnego układu.
- Przycisk CMD: COME, STAY, ATTACK, DEFEND, potwierdzenie i zamknięcie menu.
  Komendy korzystają z istniejących bitów wejścia `udlr` z odpowiednimi
  przyciskami, przed wysłaniem do sieci; te zarezerwowane kombinacje są
  konsumowane przez logikę i nie wykonują zwykłego ataku. Klasyczne komendy
  i zwykłe kombinacje zachowano. Wszyscy uczestnicy powinni używać tej wersji.
- Opcja AUTO PRAWO w edytorze HUD (domyślnie wyłączona): tylko kampania,
  po wyczyszczeniu fali, bez oczekujących przywołań i tylko przy istniejącym
  przejściu. Ręczne wejście anuluje automat do następnej fazy. Sojusznicy
  podążają za graczem w wyczyszczonej części; STAY/DEFEND mają pierwszeństwo.
- Checkpoint po zakończeniu odcinka, oddzielony według profilu i kampanii,
  suma SHA-256, poprzedni zweryfikowany checkpoint, odtworzenie postaci,
  drużyny, trudności i HP/MP. BITWA → WZNÓW KAMPANIĘ. Sieć i powtórki
  nie zapisują lokalnego postępu. Zapisy wykorzystują dotychczasowe atomowe
  zastępowanie `config.json`; nie dodano drugiego fizycznego pliku kopii.
- BITWA → TRENING: prawdziwy silnik walki, pasywny odradzany przeciwnik,
  podgląd rozpoznanych wejść, klatki animacji, HP/MP i liczby klonów.
- Diagnostyka Lua: ślad stosu, wersja aplikacji i niezmienionego silnika,
  platforma/architektura, tryb, kampania/etap/faza, postacie, moduły,
  urządzenia sterowania i pamięć Lua. Bounded ring: 16 ostatnich zdarzeń.
  Ostatni kontekst zapisuje się przy zmianie ekranu/fazy i co 300 klatek.
- Windows: rotowane logi wyjścia (dwa pliki po około 1 MiB), lokalny podgląd
  USTAWIENIA → DIAGNOSTYKA i jawny eksport samych pól diagnostycznych.
- Android: lokalne wyjątki Java, kod błędnego powrotu silnika, a od API 30
  dostępna historia błędów natywnych/ANR/braku pamięci. USTAWIENIA →
  DIAGNOSTYKA umożliwia podgląd i udostępnienie dopiero po naciśnięciu Share.
  Tokeny, hasła, Bearer i adresy URL są maskowane. Nie dodano transmisji raportów.

## Wyniki weryfikacji

| Sprawdzenie | Wynik i granice |
|---|---|
| LuaJIT | 49 zestawów PASS; składnia 143 plików PASS |
| Python | 61 testów: 60 PASS, 1 SKIP (uprawnienie symlink Windows) |
| Android JVM/Robolectric | 58 testów: 57 PASS, 1 SKIP; w tym prywatność, limit raportu i świadome udostępnianie |
| Android Gradle | testDebugUnitTest, lintDebug i assembleDebug PASS; lint: 0 błędów, 55 ostrzeżeń |
| APK | versionCode 16, versionName 0.14.0-diagnostics-test; podpis v1/v2 i zipalign 16 KiB PASS |
| Kampanie | Po 25 odcinków opowieści LF4 (Leumas EX) i PolishF (Szymonoko), wspomagane usuwaniem spawnów i przesuwaniem gracza: PASS. To test zasobów/przejść, nie naturalne ukończenie walk |
| Walka LF4 | Leumas EX, pięć rozdziałów po 3000 klatek, gracz sztucznie chroniony przed śmiercią: bez awarii; nie ukończono wszystkich walk |
| Auto przejścia | Natywny pusty etap z prawdziwym ruchem i AI, bez teleportacji: automat ON/OFF oraz ręczne anulowanie PASS; stary klon znika po przejściu |
| Klony i sieć | 2 i 8 osobnych procesów TCP na jednym laptopie, prawdziwe klony i komendy, identyczne końcowe skróty stanu: PASS |
| HUD/trening/zapis | Natywne próby z rzeczywistymi zasobami i zrzutami; limit klonów, odrodzenie przeciwnika, wznowienie i awaryjny poprzedni checkpoint: PASS |
| Brakujący zasób | Celowo brakujący zasób przy starcie: czytelny błąd i lokalny raport PASS |
| Raport błędu | Celowy wyjątek Lua: zapis kontekstu/stosu i maskowanie tokenu PASS; pierwotny błąd nie jest ukrywany |
| Eksport Windows | Windows PowerShell 5.1: poprawny JSON z samymi polami diagnostycznymi PASS |

Kod C++/Objective-C++ i biblioteki silnika nie były zmieniane. Brak lokalnego
MSVC i niedostępny dysk WSL uniemożliwiały ich ponowną kompilację. Użyto
binarnych bibliotek 0.13.0 pobranych zakresami z GitHuba (7,2 MB Windows,
11,5 MB Android). Osadzony SHA-256 kodu natywnego odpowiada obecnym źródłom
na obu ABI Androida. Nowy Java/Lua i pełne APK zostały zbudowane lokalnie.

## Status całego zamówienia

| Zakres | Status |
|---|---|
| Rozbieżność limitu Szymonoko i rekurencja | NAPRAWIONE I PRZETESTOWANE |
| Leumas EX i zachowanie pocisków | NAPRAWIONE I PRZETESTOWANE (istniejąca poprawka zweryfikowana) |
| HUD, multitouch, joystick, komendy, trening | ZAIMPLEMENTOWANE, WYMAGA TESTU NA URZĄDZENIU |
| Auto przejścia, sojusznicy i checkpointy | ZAIMPLEMENTOWANE, WYMAGA TESTU NA URZĄDZENIU |
| Raporty i kontekst Lua/Windows | NAPRAWIONE I PRZETESTOWANE |
| Diagnostyka Java/natywna Androida | ZAIMPLEMENTOWANE, WYMAGA TESTU NA URZĄDZENIU |
| Przyczyna zgłaszanych zamknięć LF4/PolishF | ZABLOKOWANE — nieodtworzone; oczekuje na raport z urządzenia |
| Pełne naturalne przejście każdą postacią, Survival i wszystkie ruchy | NIE ROZPOCZĘTE |
| Nowa konfiguracja natywnej martwej strefy gamepada | NIE ROZPOCZĘTE — zachowano dotychczasowy próg SDL i mapowanie |
| Fizyczne USB/Bluetooth, Wi-Fi i 2–8 urządzeń | ZABLOKOWANE — nie podłączono telefonu ani kontrolera |
| Pełna przebudowa modów i pobierania | NIE ROZPOCZĘTE w tym wydaniu; istniejące funkcje i walidację zachowano |
| Całościowy audyt balansu, hitboxów i wszystkich zdolności | NIE ROZPOCZĘTE; podstawowe testy istniejącej mechaniki PASS |

Zakres aktualizacji odpowiada priorytetom zamówienia i późniejszej decyzji
użytkownika o dodaniu logów. **Cały rozbudowany zakres nie jest zakończony.**
Nie dołączono nieopublikowanego Mod Managera z równoległego czatu.

## Jak zgłosić kolejną awarię

Windows: uruchamiaj `GRAJ.cmd`. Po problemie uruchom `RAPORT-BLEDU.cmd`.
Plik znajduje się w `userdata/common/diagnostics/raport-diagnostyczny.json`.
W tym katalogu są też `session-latest.log` i `session-previous.log`.
Można przeglądać kontekst przez USTAWIENIA → DIAGNOSTYKA.

Android: po ponownym otwarciu aplikacji wybierz USTAWIENIA → DIAGNOSTYKA.
Przejrzyj raport i opcjonalnie użyj UDOSTĘPNIJ. Napisz również postać i etap,
o ile je pamiętasz. Starszy Android może nie udostępnić natywnego stosu.

W USTAWIENIA → OBRAZ → EDYTOR HUD wybierz układ, przesuń kontrolki i użyj
ZASTOSUJ. WŁĄCZ AUTO PRAWO jest opcjonalne. Trening i wznowienie są w BITWA.
`CZYSTA-GRA.cmd` uruchamia profil LF2 w klasycznym menu do diagnostyki.

Znane granice: raport Lua nie obejmie błędu przed uruchomieniem runtime ani
twardego błędu pamięci C++; ostatni kontekst i log Windows mogą wtedy pomóc,
ale nie zastępują minidumpu. Checkpointy są w jednym pliku ustawień: całkowite
uszkodzenie tego pliku wymaga niezależnej kopii użytkownika. GUI i fizyczny
dotyk, kontrolery, dźwięk oraz długie kampanie nadal wymagają próby sprzętu.

## Pliki zmienione

Pełna lista plików źródłowych i testów jest w końcowym commicie wydania.
Główne miejsca: `engine/scripts/base/game/{team_commands,campaign_advance,
campaign_save,training}.lua`, `base/ui/{hud_editor,diagnostics}.lua`, runtime
`bootstrap.lua`, `content-packs/polish-originals/heroes.lua`, Android
`GameDiagnostics.java`, punkty integracji i testy. Zmian signing, applicationId,
uprawnień, Firebase, postaci/zasobów innych modów nie wprowadzono.

Pelna lista (49 plikow):

- content-packs/polish-originals/heroes.lua
- docs/DIAGNOSTYKA-HUD-0.14-2026-11-13.md
- engine/android/app/build.gradle
- engine/android/app/src/main/java/io/github/openlf2/openlf2/BluetoothLobbyActivity.java
- engine/android/app/src/main/java/io/github/openlf2/openlf2/GameBootstrapActivity.java
- engine/android/app/src/main/java/io/github/openlf2/openlf2/GameDiagnostics.java
- engine/android/app/src/main/java/io/github/openlf2/openlf2/OpenLF2Activity.java
- engine/android/app/src/test/java/io/github/openlf2/openlf2/GameDiagnosticsTest.java
- engine/scripts/base/game/campaign_advance.lua
- engine/scripts/base/game/campaign_save.lua
- engine/scripts/base/game/match.lua
- engine/scripts/base/game/options.lua
- engine/scripts/base/game/stage.lua
- engine/scripts/base/game/team_commands.lua
- engine/scripts/base/game/training.lua
- engine/scripts/base/package.manifest
- engine/scripts/base/ui/diagnostics.lua
- engine/scripts/base/ui/flow.lua
- engine/scripts/base/ui/hud_editor.lua
- engine/scripts/base/ui/launch.lua
- engine/scripts/base/ui/match_screen.lua
- engine/scripts/base/ui/touch_gamepad.lua
- engine/scripts/polish-fighters/hub_launch.lua
- engine/scripts/polish-fighters/hub.lua
- engine/scripts/polish-fighters/input_buffer.lua
- engine/scripts/polish-fighters/room_network.lua
- engine/scripts/polish-fighters/updates.lua
- engine/scripts/runtime/bootstrap.lua
- PROJECT-STATUS.md
- tests/campaign_advance_test.lua
- tests/campaign_save_test.lua
- tests/classic_menu_test.lua
- tests/heroes_test.lua
- tests/hud_editor_test.lua
- tests/input_buffer_test.lua
- tests/room_input_buffer_test.lua
- tests/szymonoko_clone_limit_test.lua
- tests/team_commands_test.lua
- tests/training_test.lua
- tests/updates_test.lua
- tools/check_room_game.py
- tools/Export-Diagnostics.ps1
- tools/prepare_android_game.py
- tools/probe_auto_campaign.py
- tools/probe_campaign_stability.py
- tools/probe_crash_diagnostics.py
- tools/probe_gameplay_update.py
- tools/room-check/flow.lua
- tools/Start-Game.ps1
