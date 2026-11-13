# Polish Little Fighters 0.14.0 — wydanie testowe

## Wznowienie prac — 2026-11-13

Audyt źródeł po zgłoszeniu problemów wykazał, że ekran `launch` wyłączał
gamepad dotykowy, mimo że zawiera menu BITWA/STAGE/KAMPANIA. Na ekranie wyboru
postaci dotyk był kierowany do nawigacji myszy zamiast do akcji gracza. Naprawiono
routing: w menu ATAK mapuje się na Enter, a w wyborze postaci na oryginalne `c`;
strzałki joysticka trafiają do odpowiedniego odbiornika ekranu. W walce nadal
używany jest oryginalny zestaw przycisków i kombinacji LF2.

Joystick rysuje się i przyjmuje dotyk jako koło także dla profili zapisanych
w 0.14 z `digipad=true`; strefa rozpoczęcia ruchu jest kołowa, a po puszczeniu
palca wejście znika. Hit-test przycisków akcji obejmuje dokładnie cały promień
widocznego koła (nie dodaje marginesu poza kołem). Zachowano zapisany wariant
trzech/sześciu przycisków akcji; historyczne pole `digipad` jest normalizowane
do `false` przy zapisie ustawień.

Weryfikacja lokalna: 48 zestawów Lua PASS (w tym profile/migracja, dotyk,
krótkie wejścia, komendy i istniejące wejście hubu), składnia 145 plików PASS.
Pełny zestaw Pythona: 68 PASS, 1 SKIP. Zaktualizowano wygenerowany Android
`classic-menu.json`, aby zawierał teksty z lokalnego Mod Managera. Nie ma
podłączonego telefonu (`adb devices` puste); nie potwierdzono fizycznego dotyku.
Nie zbudowano jeszcze kompletnych paczek Windows/APK.

Uzupełnienie wznowienia: dodano ekran Androida „Szukaj i importuj mody”. Scraper
działa tylko po wyborze źródła, sprawdza `robots.txt`, ogranicza przekierowania
do skonfigurowanej domeny HTTPS i pokazuje wyłącznie strony projektów. Nie
oznacza linków jako pobrań zweryfikowanych. Rzeczywiste sprawdzenie desktopowego
scrapera: ModDB zwrócił kandydatów i elementy nawigacji (te ostatnie odfiltrowano
w wersji Android); LF Empire/forum wymagały dłuższego odstępu; strona Ultimate
Fighters zawierała w opisie zewnętrzny krótki link, którego scraper nie uznał za
bezpieczne pobranie. Android umożliwia wybór ZIP z systemowego selektora i
instalację paczki konwertera `mod-<24 hex>` z limitem plików/rozmiaru, kontrolą
ścieżek oraz odrzuceniem EXE/DLL i obcych skryptów. Desktopowy Mod Manager ma
przycisk „Eksportuj na Androida” dla zainstalowanych paczek. Surowe archiwa modów
trzeba przekonwertować wcześniej na komputerze; automatycznego pobierania
zweryfikowanych archiwów ani surowej konwersji na Androidzie nie ma.

Wersja Androida podniesiona do code 17 / `0.15.0-mod-browser-test`. Workflow
Android został rozszerzony o `testDebugUnitTest` i `lintDebug` przed buildem.
Lokalnie: Lua 48 zestawów PASS / 145 plików składni PASS; Python 69 PASS / 1
SKIP. Próba lokalnego Gradle nie ruszyła z powodu JDK 25 (projekt wymaga JDK 17);
testów Android Java nie potwierdzono lokalnie. Telefon nadal niedostępny.

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
| HUD/trening/zapis | Natywne próby z rzeczywistymi zasobami i zrzutami; testy Lua sterowania PASS. Fizyczny dotyk wciąż niezweryfikowany. |
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
| Sterowanie dotykowe i wybór postaci | Poprawiono routing, okrągły joystick i hit-test ataku w źródłach; testy Lua PASS, wymaga testu telefonu |
| Komendy drużyny | Zachowano dymki, AI i bit wejścia sieciowego; testy Lua PASS, renderowanie/touch w kampanii wymaga testu telefonu |
| Android scraper/importer | GUI źródeł i importu ograniczonej paczki konwertera dodane lokalnie; testy/build Android i użycie urządzenia niepotwierdzone; brak pobierania zweryfikowanych archiwów i konwersji surowych ZIP na telefonie |
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

## Pliki zmienione w wydaniu 0.14

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
## Uzupełnienie — menu gry i importer Androida (2026-11-13)

W osobnej lokalnej poprawce główne menu hub używa teraz tła, dwóch fragmentów
logo i bitmapowej czcionki z oryginalnego UI LF2, zamiast przyciemnionego tła,
nowego nagłówka i prostokątnych kart. Zachowano identyfikatory wierszy,
nawigację, wybór języka i przepływy gry. Pozycje menu są wyśrodkowane w szerokiej
kolumnie, a test pilnuje użycia oryginalnej grafiki i braku nowych wypełnionych
kart. Ekran `AndroidModsActivity` otrzymał tę samą granatowo-niebieską paletę
i przyciski `ClassicButton`; zachowuje bezpieczne sprawdzanie źródeł, systemowy
selektor ZIP, walidację/import, status, błędy i wybór modułu. Scraper nadal
otwiera strony projektów. Nie dodano pobierania ZIP ani automatycznej instalacji.

Weryfikacja tej poprawki: testy Lua `classic_menu_test.lua`, `hub_input_test.lua`,
`mod_browser_test.lua`, `global_menu_test.lua` PASS; składnia Lua 145 plików PASS;
pełny zestaw Python 70 PASS, 1 SKIP (uprawnienia symlink w Windows). GitHub Actions
na commit `258e273` zbudował Windows installer i APK ARM64; workflow zweryfikował
APK. Lokalnie potwierdzono `versionCode=18`, nazwę `0.16.0-classic-menu-test`,
podpis APK i sumę. Brak testu na telefonie: rzeczywisty wygląd, dotyk, instalacja
aktualizacji i rozgrywka nie są potwierdzone. Nie twierdzimy, że pierwotne błędy
sterowania zostały naprawione na sprzęcie. Scraper nadal otwiera stronę, ZIP trzeba
pobrać ręcznie i wskazać w importerze; importer obsługuje transferowe paczki z
konwertera, a zgodność dowolnych modów nie jest potwierdzona.

Publiczne wydanie testowe: [0.16.0](https://github.com/w4sy1/polish-fighters/releases/tag/classic-menu-0.16.0-2026-11-13).
APK SHA-256 `f2bab9f724a8ba979d6c3b4def2dd61302c2209604f089f9efcf079eda6733e7`;
Windows installer SHA-256 `e040f7234349df26f98ba60ede5c085ecc96582abd9114377d6283af42c03cbe`.
