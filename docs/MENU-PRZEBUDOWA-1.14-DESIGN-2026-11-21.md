# Przebudowa menu głównego — etap 1.14 (projekt, przed implementacją)

Status: PROJEKT DO ZATWIERDZENIA. Nic z tego dokumentu nie zostało jeszcze
zaimplementowane. To specyfikacja dla budowniczego (Codex/Claude Code), nie
raport ze zmian.

## 1. Intencja i dlaczego

Gracz otwiera menu i trafia na trzy nałożone na siebie systemy nawigacji,
które wyrosły w różnym czasie i nigdy nie zostały scalone:

1. `hub.lua` / `hub_launch.lua` — główny hub (MODUŁY/BITWA/SIECI/USTAWIENIA/...).
2. `classic_shell.lua` — osobny system paneli "classic" (`pf_panel`:
   extras/connection/maps/packs/fighters/campaigns/touch/options/...),
   wejście przez `extras`/`maps`/`fighters`/`guide` w hubie. Ma własny,
   **duplikujący** panel "POLACZENIA" (POKOJ LAN / STARE POLACZENIE /
   HOTSPOT / BLUETOOTH), niezależny od SIECI w hubie.
3. Natywny ekran Androida `BluetoothLobbyActivity` (+ `LanWifiMode`) —
   całkiem osobna nawigacja z własnymi `AlertDialog`, poza silnikiem Lua,
   z własnym "wstecz" kończącym grę do systemu Android, nie do menu.

Efekt: trzy różne miejsca, w których gracz może zacząć sieciową rozgrywkę,
z trzema różnymi wzorcami "wstecz", różnym stylem przycisków i częściowo
powtórzoną logiką (adres IP gospodarza, port, wybór LAN vs Internet).
Bluetooth istnieje tylko na Androidzie (`BluetoothSession.java`); na
Windows to pusty komunikat "BLUETOOTH: ANDROID".

Cel etapu 1.14: jeden system nawigacji, jedno wejście = jedno wejście,
jedno wstecz = jeden poziom w tył, zawsze i wszędzie. Bluetooth ma
zacząć działać też na Windows (realny natywny stos, nie placeholder).

## 2. Cele (goals)

- Jedno drzewo menu głównego: MODUŁY / GRAJ LOKALNIE / GRAJ ZDALNIE /
  USTAWIENIA, każde z jedną, przewidywalną ścieżką w głąb i w tył.
- GRAJ ZDALNIE ma 4 równoległe kategorie: SERWER, BLUETOOTH, WIFI,
  HOTSPOT — każda od razu pokazuje tylko to, co potrzebne (Utwórz
  pokój / Dołącz, ewentualnie wykryj/paruj dla Bluetootha), bez
  dodatkowych przystanków.
- Bluetooth działa na Windows i na Androidzie, przez ten sam wzorzec
  wejścia z menu głównego co dziś "Android Tools" (restart-wrapped,
  patrz §6) — gracz zawsze wraca do GRAJ ZDALNIE, nigdy do
  pulpitu/systemu.
- `classic_shell.lua` traci panel "POLACZENIA" — ta ścieżka do sieci
  przestaje istnieć, zostaje jedna: nowe GRAJ ZDALNIE.
- `BluetoothLobbyActivity` jako dzisiejszy natywny ekran z
  zagnieżdżonymi dialogami przestaje istnieć — zastępuje go jeden,
  prostszy natywny ekran parowania, wywoływany tylko z nowego
  GRAJ ZDALNIE→BLUETOOTH.
- Kolorystyka ekranu głównego zostaje w stylu LF2 (to już jest
  zrobione w 0.16.0 — zostaje, nie dotykamy bez potrzeby).
- Mod manager (zaznaczanie/odznaczanie paczek) zostaje na bazie
  istniejącego `hub` mode `packs` + `mod_browser.lua`, przeniesiony pod
  nowy wpis MODUŁY, bez przepisywania logiki pobierania/instalacji.

## 3. Nie-cele (non-goals)

- Nie zmieniamy formatu zapisów ustawień (`engine.read_settings` /
  `write_settings`), poza dodaniem kluczy potrzebnych nowym ekranom.
- Nie zmieniamy protokołu sieciowego pokoi (`room_host.cpp`,
  `relay_link.cpp`) — SERWER/WIFI/HOTSPOT nadal to ten sam TCP/relay,
  zmienia się tylko menu, które do niego prowadzi.
- Nie przepisujemy `online_client.lua` (logowanie, konta, relay) — jego
  API zostaje, zmienia się ekran, który je woła (patrz §5.1).
- Nie dodajemy nowych trybów rozgrywki, kampanii, postaci — to czysto
  menu/nawigacja/łączność.
- Nie ruszamy silnika kombosów, AI, fizyki — zero ryzyka regresji w
  warstwie walki.

## 4. Anty-cele (co by oznaczało porażkę)

- Gracz nadal trafia na dwa różne ekrany sieciowe w zależności od tego,
  czy wejdzie przez SIECI, USTAWIENIA czy EXTRAS.
- "Wstecz" na którymkolwiek nowym ekranie wychodzi z gry do systemu
  Android albo przeskakuje więcej niż jeden poziom.
- Bluetooth na Windows zrobiony jako kolejny oddzielny, nie-Lua ekran
  (powielenie dzisiejszego problemu, tylko na nowej platformie).
- Regresja w czymkolwiek, co dziś działa: zapisany profil startowy,
  logowanie kontem, pokoje LAN z wpisanym IP, wznawianie pokoju po
  restarcie, klasyczne menu paczek zawartości (fighters/maps/campaigns
  poza panelem "connection" — te zostają w classic_shell, nie są
  częścią tej przebudowy).

## 5. Ograniczenia (constraints)

- Jedna stabilna gałąź, commit liniowo na main (zgodnie z ustalonymi
  zasadami repo), każda zmiana sprawdzana pod kątem regresji.
- Projekt silnika to C++ (SDL/LuaJIT) + Android (Java/Gradle) + Windows
  (natywny build, instalator). Bluetooth jest restart-wrapped (§6), więc
  nowy ekran parowania trzeba zbudować **po obu stronach niezależnie**
  (natywny Android, natywny Windows) — to nie jeden wspólny kod w C++
  wołany z Lua, tylko dwa równoległe, symetryczne ekrany natywne;
  inaczej jedna platforma dostaje martwy wiersz menu.
- Bluetooth na Windows to zupełnie nowy kod naywny (Win32/WinRT
  Bluetooth Classic, RFCOMM) — dziś nie istnieje żaden wiersz kodu
  Bluetootha poza Androidem. To jest realna, nietrywialna robota
  natywna, nie "podłączenie czegoś co już jest".
- Android: `BLUETOOTH_SCAN`/`BLUETOOTH_CONNECT`/`BLUETOOTH_ADVERTISE`
  wymagają uprawnień w runtime (już obsłużone w `BluetoothSession`/
  `OpenLF2Activity.requestBluetoothPermissions`) — logika uprawnień
  przechodzi do nowego mostka, nie jest pisana od zera.
- Windows: Classic Bluetooth RFCOMM wymaga włączonego stosu Bluetooth
  w systemie i sparowanych urządzeń (podobnie jak Android) — UI musi to
  komunikować tak samo jak dziś robi to Android (ekran z komunikatem
  "włącz Bluetooth w ustawieniach systemu", nie cichy fail).

## 6. Rozważane podejścia i decyzja

**A — bezpieczne, Bluetooth zostaje natywnym ekranem Androida.**
Niskie ryzyko, ale nie realizuje celu "jedno menu wszędzie" i nie dawało
Bluetootha na Windows.

**B — Bluetooth w pełni w Lua, przez nowy mostek silnika, też na
Windows.** Wyższe ryzyko (nowy kod C++ na dwóch platformach), ale to
jedyne podejście, które realizuje "jedno menu, jedna nawigacja,
wszędzie" i spełnia wymóg działania na Windows.

**Decyzja gracza: B.** Reszta (SERWER/WIFI/HOTSPOT) jako reorganizacja
istniejącego kodu Lua (`online_screen.lua`, `online_client.lua`) pod
jeden wspólny wzorzec ekranu, bez zmiany protokołu sieciowego.

**Doprecyzowanie po weryfikacji budowniczego (builder check):**

- Bluetooth idzie jako **restart-wrapped**, nie jako w pełni bezproces-
  owy "live" bridge. Wejście BLUETOOTH w GRAJ ZDALNIE wywołuje ten sam
  wzorzec co dziś `hub.open_android_tools` (zapis flagi w ustawieniach,
  `context.action('quit')`, restart procesu do natywnego ekranu
  parowania/łączenia, potem powrót do silnika) — tylko ten natywny
  ekran ma teraz jedno, konsekwentne "wstecz" do GRAJ ZDALNIE, zamiast
  dzisiejszych zagnieżdżonych `AlertDialog`. To dotyczy obu platform:
  Windows też dostaje swój natywny ekran parowania (nowy kod), nie
  mostek działający w tle silnika. Mniej nowego kodu C++/JNI, mniejsze
  ryzyko regresji — zgodnie z priorytetem "nic nie rozjebać".
- **Bluetooth PAN / tethering jako nośnik IP** (dzisiejsza trzecia
  opcja "Hotspot Bluetooth / PAN", odrębna od Wi-Fi-hotspotu i od
  parowania RFCOMM) — **wyrzucamy**. Zostają tylko: Wi-Fi/hotspot (IP,
  pod WIFI i HOTSPOT) i klasyczne parowanie Bluetooth RFCOMM (pod
  BLUETOOTH). Mniejszy zakres, prostszy ekran BLUETOOTH.

## 7. Nowe drzewo menu

```
MENU GŁÓWNE
├── MODUŁY                         (dawne "biblioteka" + packs + mod_browser)
│   ├── [lista: zainstalowane + dostępne, checkbox]
│   ├── POBIERZ WIĘCEJ (GitHub mod_browser)
│   └── ZAPISZ / WSTECZ
├── GRAJ LOKALNIE                  (dawne "battle", bez pytania o moduły)
│   ├── WYBÓR MAPY → WYBÓR POSTACI (bez przystanków pomiędzy)
│   └── POJEDYNEK / KAMPANIA / TURNIEJ / TRENING / POWTÓRKA / WSTECZ
├── GRAJ ZDALNIE                   (NOWE, zamiast SIECI + ustawienia:lan +
│   │                               classic_shell:connection + natywny Android)
│   ├── SERWER
│   │   └── UTWÓRZ POKÓJ | DOŁĄCZ            (online_screen, tryb "simple")
│   ├── BLUETOOTH                             (NOWE: Windows + Android)
│   │   └── WYKRYJ/PARUJ → UTWÓRZ POKÓJ | DOŁĄCZ
│   ├── WIFI
│   │   └── UTWÓRZ POKÓJ | DOŁĄCZ            (dawny "LAN": wpisany adres IP)
│   └── HOTSPOT
│       └── UTWÓRZ HOTSPOT | DOŁĄCZ          (ta sama ścieżka IP co WIFI,
│                                              inny nagłówek/instrukcja)
└── USTAWIENIA
    ├── STEROWANIE
    │   ├── (Windows: bez zmian — bindowanie klawiszy/pada, presety)
    │   └── (Android: + przełącznik JOYSTICK/STRZAŁKI, edytor HUD
    │         Hybrid Control — przeniesiony tutaj z classic_shell "touch")
    ├── OBRAZ / DŹWIĘK             (bez zmian)
    └── NAGRANIA                   (bez zmian)
```

Reguła nawigacji obowiązująca na każdym poziomie: jedno naciśnięcie =
jedno wejście głębiej; "wstecz"/Esc/F4/Android-wstecz = jeden poziom w
górę, nigdy wyjście z gry (poza samym korzeniem MENU GŁÓWNE → WYJŚCIE,
które zostaje jak jest).

## 8. Co się dzieje z istniejącym kodem

### 8.1 MODUŁY
- Punkt wyjścia: `hub.lua` mode `library` (lista profili) + mode `packs`
  (zaznaczanie/odznaczanie, już istnieje) + `mod_browser.lua`
  (pobieranie z GitHub, już istnieje).
- Robota: scalić te trzy w jeden ekran z jednym poziomem zagnieżdżenia
  (dziś `packs`/`mods`/`optional_modules`/`status` to cztery osobne
  `hub_mode`, każdy z własnym "wstecz" do `library` — zachować to jako
  podstrony, ale ujednolicić etykiety i upewnić się, że każde wejście
  w podstronę ma dokładnie jedno wstecz do MODUŁY, nie do `root`).
- Nie przepisywać `module_inventory.lua`, `pack_preferences.lua`,
  `mod_browser.lua`, `mod_manager.py` — logika zostaje.

### 8.2 GRAJ LOKALNIE
- Punkt wyjścia: `hub.lua` mode `battle`/`profile`/`players` — już nie
  pyta o moduł (`active_profile` ustawiony w MODUŁY) i już prowadzi
  mapa→postać bez przystanków.
- Robota: tylko zmiana etykiety wejścia z głównego menu (`battle` →
  "GRAJ LOKALNIE") i upewnienie się, że z tego wejścia nie da się
  wywołać żadnej ścieżki sieciowej (dziś się nie da — potwierdzić
  testem `classic_menu_test.lua` / `global_menu_test.lua` po zmianie).

### 8.3 GRAJ ZDALNIE — rdzeń przebudowy
- **Usunąć** z `hub.lua`: mode `online` (SIECI) w obecnej formie i
  wiersz `lan` z mode `settings`. Zamiast tego jeden nowy `hub_mode`
  (np. `remote`) z czterema wierszami: SERWER/BLUETOOTH/WIFI/HOTSPOT.
- **Usunąć** z `classic_shell.lua`: panel `connection` (wiersze
  `room`/`tcp`/`capacity`/`lan`/`bluetooth`) i jego aktywację. Ekran
  `extras` traci wejście "POLACZENIA" — gracz i tak ma teraz GRAJ
  ZDALNIE w menu głównym. `capacity` (limit pokoju 2–8) albo zostaje w
  `dashboard_model.lua`-sterowanych ustawieniach pokoju (np. jako pole
  na ekranie SERWER przy publikowaniu), albo trafia do USTAWIENIA — do
  decyzji budowniczego, to szczegół bez wpływu na architekturę.
- **SERWER**: reużyć `online_screen.lua` w trybie `simple` (dziś
  otwierany jako `online.open(state,true)`) — to już jest ekran
  "UTWÓRZ POKÓJ / DOŁĄCZ" z kontem gościa. Tylko podpięcie pod nowy
  wiersz menu, bez zmiany logiki.
- **WIFI**: reużyć `online_screen.lua` w trybie `simple+lan` (dziś
  `online.open(state,true,true)`, czyli dzisiejsze "GRA W SIECI
  LOKALNEJ") — już ma pole adresu gospodarza przy dołączaniu. Przy
  hostowaniu ekran ma też **od razu pokazywać własny adres IPv4** —
  dziś ta informacja jest na osobnym ekranie `base/ui/network.lua`
  otwieranym przez `context.action('network'); ta część ma się przenieść
  na sam ekran WIFI/HOTSPOT (odczyt przez `engine.network('addresses')`,
  który już istnieje), żeby hostowanie nie miało dodatkowego przystanku.
  Do tego: przenieść włączanie `LanWifiMode` (tryb niskich opóźnień
  Wi-Fi na Androidzie) tak, by uruchamiało się przy wejściu w sesję
  WIFI/HOTSPOT w nowym miejscu, a nie tylko przy starcie przez usuwaną
  `BluetoothLobbyActivity` — to jest dziś realna optymalizacja
  wydajności meczu i ma przetrwać przeniesienie (patrz §4, zero
  regresji).
- **HOTSPOT**: ten sam ekran i kod co WIFI (to wciąż TCP po adresie
  IPv4 — hotspot to z punktu widzenia silnika taka sama sieć lokalna).
  Różnica to tylko nagłówek/instrukcja na ekranie (np. "Włącz hotspot
  w telefonie / udostępnianie internetu w Windows, połącz drugie
  urządzenie, potem UTWÓRZ POKÓJ / DOŁĄCZ") — jeden parametr
  `online_screen.open(state,true,true,'hotspot')` zamiast nowego
  ekranu. Zero nowej logiki sieciowej. Dzisiejsza trzecia natywna
  opcja "Hotspot Bluetooth / PAN" (udostępnianie internetu przez
  Bluetooth jako nośnik IP, odrębne od klasycznego parowania RFCOMM)
  **wypada całkiem** — nie jest przenoszona pod HOTSPOT ani pod
  BLUETOOTH, mniejszy zakres.
- **BLUETOOTH** — restart-wrapped, nie "live" bridge bez restartu
  (decyzja po builder-checku: mniej nowego kodu, mniejsze ryzyko na
  obu platformach):
  - Wejście BLUETOOTH w nowym `hub_mode` `remote` działa jak dzisiejszy
    `hub.open_android_tools`: zapisuje flagę w ustawieniach,
    `context.action('quit')`, restart procesu do natywnego ekranu
    parowania. Po połączeniu albo po "wstecz" na tym ekranie, powrót
    jest zawsze do GRAJ ZDALNIE w menu głównym — jeden poziom, nie do
    pulpitu/systemu.
  - Android: nowy, uproszczony natywny ekran (bez dzisiejszych
    zagnieżdżonych `AlertDialog` z pf_connections) zastępujący
    `BluetoothLobbyActivity`'s `showConnections()`/`connect()` —
    tylko klasyczne parowanie RFCOMM (dziś: `BluetoothSession.java`,
    logika parowania/uprawnień **zostaje, nie jest przepisywana**,
    zmienia się tylko, skąd jest wywoływana i jak wygląda ekran).
  - Windows: **nowy natywny ekran + nowy kod Bluetootha** — dziś nie
    istnieje nic. Ten ekran, analogicznie do `BluetoothLobbyActivity`,
    uruchamia się przy wejściu w BLUETOOTH (restart procesu z
    odpowiednią flagą/argumentem startowym, symetrycznie do
    `GameLaunchArguments.build(...)` na Androidzie), robi
    wykrywanie/parowanie klasycznego Bluetooth (Win32 Bluetooth
    Classic RFCOMM — `BluetoothFindFirstDevice`/`BluetoothFindFirstRadio`,
    albo WinRT `Windows.Devices.Bluetooth.Rfcomm`, wybór zostaje
    budowniczemu), po połączeniu startuje silnik z tymi samymi
    argumentami roli/portu co dziś dostaje Android. To jedyny naprawdę
    nowy kod natywny w całym etapie.
  - Platformy bez Bluetootha (web, konsole w `engine/dist/*`): wiersz
    BLUETOOTH w GRAJ ZDALNIE się nie pokazuje (tak jak dziś
    `android_tools` w `hub.rows` pokazuje się tylko gdy
    `state.hub_android`) — sprawdzane prostym zapytaniem o dostępność
    przed zbudowaniem listy wierszy, bez nowego mostka działającego
    w trakcie gry.
- **Usunąć całkowicie**: `BluetoothLobbyActivity.java` i jego
  `showConnections`/`showLan`/`connect`/`lanAddress` (wejście sieciowe
  tych metod), zastąpione nowym, prostszym natywnym ekranem (patrz
  wyżej). `LanWifiMode.java` **nie jest usuwana** — jej wywołanie
  przenosi się do nowego miejsca startu sesji WIFI/HOTSPOT (patrz
  punkt WIFI wyżej), żeby nie zgubić optymalizacji Wi-Fi. Testy
  (`StartScreenTest.java`, `LanWifiModeTest.java`) do przepisania pod
  nowe ekrany, nie do wyrzucenia — sprawdzają realne zachowanie, które
  ma zostać, tylko w nowym miejscu.

### 8.4 USTAWIENIA
- STEROWANIE: `input_settings.lua` (Windows: bindowanie, presety) +
  `hybrid_editor.lua`/`hybrid_layout.lua` (Android: HUD, joystick vs
  strzałki — już obsługuje mieszanie obu per log 0.18.14/Hybrid
  Control). Robota: dodać w `input_settings.rows` na Androidzie
  wiersz-przełącznik JOYSTICK/STRZAŁKI (czyta/zapisuje istniejące pole
  trybu w `hybrid_layout`) i wiersz "EDYTOR HUD" wywołujący
  `hybrid_editor.create`, tak by nie trzeba było wchodzić przez
  `classic_shell` "touch" — ten wpis w `classic_shell` można zostawić
  jako alias (nie jest częścią problemu sieci) albo usunąć, do decyzji
  budowniczego.
- OBRAZ/DŹWIĘK, NAGRANIA: bez zmian.

## 9. Co zostaje do budowniczego (decyzje bez wpływu na architekturę)

- Dokładne piksele/layout nowych ekranów (pozycje przycisków itd.) —
  trzymać się palety i czcionki LF2 już używanej w `hub_launch.lua`.
- Czy `capacity` (limit pokoju) trafia na ekran SERWER czy do USTAWIENIA.
- Dokładna nazwa flagi w ustawieniach i argumentu startowego używanego
  do przekazania roli/portu Bluetooth do silnika po restarcie (ma być
  symetryczny na Androidzie i Windows, ale konkretne nazwy pól to
  szczegół implementacji).
- Czy Windows RFCOMM idzie przez Win32 czy WinRT — zależy od tego, co
  da się domknąć w obecnym CMake/Conan toolchainie bez nowych,
  problematycznych zależności.
- Los wejścia "touch"/HUD w `classic_shell` (alias czy usunięcie).

## 10. Testy / weryfikacja regresji (obowiązkowe przed main)

- Lua: `tests/global_menu_test.lua`, `tests/classic_menu_test.lua`,
  `tests/lan_menu_test.lua`, `tests/online_*_test.lua`,
  `tests/bluetooth_room_test.lua`, `tests/content_menu_test.lua` —
  wszystkie do przejrzenia i rozszerzenia pod nowe `hub_mode`.
- Android: `StartScreenTest.java` (do przepisania pod nowy ekran, nie
  pod `BluetoothLobbyActivity`, który ma zniknąć), `LanWifiModeTest.java`
  (do przeniesienia pod nowy mostek), Gradle unit tests + lint.
- Windows: natywna próba Bluetootha wymaga dwóch fizycznych maszyn
  (lub jednej maszyny + telefonu) z włączonym Bluetooth — oznaczyć w
  raporcie jako wymagające realnego sprzętu, nie deklarować "działa"
  bez takiej próby.
- Zero regresji w: zapamiętanym profilu startowym, logowaniu kontem,
  wznawianiu pokoju (`little_fighters_room_resume`), wspólnym ekranie
  tytułowym w grze sieciowej (`network_title_touch_test.lua`).
