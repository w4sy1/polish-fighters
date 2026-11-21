# Przebudowa menu głównego — etap 1.14 — plan implementacji

> **Dla wykonawcy (Codex/Claude Code):** użyj superpowers:subagent-driven-development
> (polecane) albo superpowers:executing-plans, zadanie po zadaniu. Kroki ze
> znacznikiem `- [ ]` służą do śledzenia postępu.

**Cel:** jedno drzewo menu (MODUŁY/GRAJ LOKALNIE/GRAJ ZDALNIE/USTAWIENIA),
jedna nawigacja wszędzie, Bluetooth działający na Windows i Androidzie.

**Architektura:** reorganizacja istniejącego Lua (`hub.lua`,
`online_screen.lua`, `classic_shell.lua`) pod nowe `hub_mode`; dla
Bluetootha dwa równoległe, symetryczne natywne ekrany parowania
(Android, Windows), restart-wrapped, bez zmiany protokołu TCP/relay.

**Stos:** LuaJIT (engine/scripts), C++/SDL (engine/src), Java/Gradle
(engine/android), natywny build Windows (engine/dist/build-windows.ps1).

**Specyfikacja:** `docs/MENU-PRZEBUDOWA-1.14-DESIGN-2026-11-21.md`
(ten plan wykonuje tę specyfikację — wykonawca czyta oba dokumenty).

## Ograniczenia globalne

- Jedna gałąź, commity liniowo na main, każdy commit sprawdzony pod
  regresję (zasada repo — patrz `docs/audyt-github-codex`/AGENTS.md).
- Nie zmieniać protokołu sieciowego (`room_host.cpp`, `relay_link.cpp`,
  `online_client.lua` API) — tylko ekrany, które do niego prowadzą.
- Każda zmiana w jednym adapterze platformowym (Android/Windows) ma
  swój odpowiednik w drugim, inaczej jedna platforma dostaje martwy
  wiersz menu.
- Po każdym etapie: `python tools/test_lua_scripts.py` (składnia 145+
  plików PASS) i pełny zestaw `tests/*_test.lua` PASS, zero regresji.
- Bluetooth: restart-wrapped, bez PAN/tetheringu (patrz spec §6).

## Ogniska uwagi (Review Focus)

1. **Wejście w ekran bez zainstalowanego modułu zgodnego z pokojem** —
   dziś `online_screen.lua` pokazuje "POBRAĆ BRAKUJĄCY MOD?"; nowy
   ekran GRAJ ZDALNIE musi zachować tę ścieżkę (Etap 3, Zadanie 3.2).
2. **Wejście w BLUETOOTH na platformie bez adaptera / z wyłączonym
   Bluetoothem** — ekran musi pokazać komunikat "włącz Bluetooth w
   ustawieniach systemu", nie ciche nic (Etap 4, Zadanie 4A.2 i 4B.2).
3. **"Wstecz" w trakcie wpisywania pola tekstowego** (adres IP, nick) —
   dziś zamyka klawiaturę najpierw, potem dopiero wychodzi z ekranu;
   nowy ekran WIFI/HOTSPOT musi to zachować (Etap 3, Zadanie 3.1).
4. **Profil `mixed-all` w GRAJ ZDALNIE** — dziś sieć jest zablokowana
   dla wspólnej puli modułów ("Wspólna pula: najpierw testy lokalne");
   nowy `hub_mode` `remote` musi to sprawdzać tak jak stary (Etap 3,
   Zadanie 3.1).
5. **Powrót z natywnego ekranu Bluetooth bez połączenia** (gracz klika
   wstecz w trakcie skanowania/parowania) — musi wrócić do GRAJ
   ZDALNIE w menu Lua, nie do pulpitu/ekranu głównego Androida/Windows
   i nie zostawić uchwytu adaptera otwartego (Etap 4, Zadanie 4A.2, 4B.2).

---

## Jak czytać ten plan

Pięć etapów = pięć w większości niezależnych podsystemów ze specyfikacji
(§8.1–§8.4). Etapy 1, 2, 3, 5 to czysto Lua — mogą iść w dowolnej
kolejności, każdy osobno dający grywalny, testowalny wynik. Etap 4
(Bluetooth) jest największy i najbardziej ryzykowny — osobny natywny
kod na dwóch platformach — i warto go rozbić na dwa dalsze pod-PR-y
(Android, Windows), bo nie dzielą kodu, tylko kontrakt (nazwy flag).

**Uwaga o wykonaniu:** ta sesja ma tylko odczyt repo (bez push) i nie
ma zainstalowanego Android SDK / toolchainu Windows — nie może
zbudować ani wypchnąć żadnej z tych zmian. Etapy 1/2/3/5 (czyste Lua,
testowalne przez `tools/test_lua_scripts.py`) może wykonać Claude Code
w sesji z pushem do repo. Etap 4 wymaga albo Codexa z dostępem do
Android Studio/Windows toolchainu, albo Claude Code w sesji z tym
środowiskiem podłączonym — biorąc pod uwagę limity Codexów, sensowna
kolejność to: Etapy 1/2/3/5 teraz (nie potrzebują Codexa), Etap 4
(Android) jak zwolni się pierwszy Codex, Etap 4 (Windows) jak zwolni
się drugi.

---

## Etap 1: MODUŁY

**Pliki:**
- Modyfikacja: `engine/scripts/polish-fighters/hub.lua` (`hub.rows`
  tryby `root`, `library`, `packs`, `optional_modules`, `status`)
- Modyfikacja: `engine/scripts/polish-fighters/hub_launch.lua`
  (`activate`, etykiety)
- Test: `tests/global_menu_test.lua`, `tests/content_menu_test.lua`,
  `tests/mod_browser_test.lua`

**Interfejsy:**
- Konsumuje: `module_inventory.lua`, `pack_preferences.lua`,
  `mod_browser.lua` — bez zmian w ich API.
- Produkuje: wiersz `library` w `hub.rows(mode='root')` z etykietą
  "MODUŁY" (dziś: "Moduły" — potwierdzić że etykieta już to mówi, bo
  `L('modules')`/locale może już być w porządku — jeśli tak, ten
  punkt to tylko test regresyjny, nie zmiana).

- [ ] **Zadanie 1.1: Test — `library`/`packs`/`mods`/`status` mają
  dokładnie jedno wstecz do `library`, nigdy do `root`**
  - [ ] Napisać w `tests/global_menu_test.lua` (albo nowym
    `tests/moduly_menu_test.lua`) asercję: z `hub_mode='packs'`,
    aktywacja wiersza `packs_cancel` ustawia `state.hub_mode=='library'`
    (nie `'root'`); analogicznie dla `status`→`back` i
    `optional_modules`→`back`.
  - [ ] Uruchomić: `python tools/test_lua_scripts.py tests/global_menu_test.lua`
    — oczekiwany FAIL (dziś może już przechodzić — jeśli przechodzi,
    zapisać to jako test regresyjny i przejść do 1.2 bez zmiany kodu).
  - [ ] Jeśli FAIL: poprawić `elseif id=="packs_cancel"` w
    `hub_launch.lua` tak, by ustawiało `state.hub_mode="library"`
    (dziś już tak robi — sprawdzić pozostałe trzy ścieżki tym samym
    wzorcem).
  - [ ] Uruchomić ponownie — PASS.
  - [ ] Commit: `fix(hub): one-level back from every MODUŁY subscreen`

- [ ] **Zadanie 1.2: Relabel wiersza głównego `library`→"MODUŁY"**
  - [ ] Sprawdzić `menu_locale.lua` klucz `modules` — jeśli już brzmi
    "MODUŁY", nic nie zmieniać w kodzie, tylko dopisać test
    `assert(require('polish-fighters/menu_locale').text('modules')=='MODUŁY')`.
  - [ ] Jeśli nie: zmienić wartość w `menu_locale.lua` (PL i EN klucz
    odpowiednio), nie zmieniać samego `id` wiersza (`'library'` zostaje
    jako identyfikator wewnętrzny — zmiana `id` złamałaby zapisane
    stany nawigacji `remember=true` w `navigation.lua`).
  - [ ] `python tools/test_lua_scripts.py` — PASS, zero regresji w
    `classic_menu_test.lua` (który odwołuje się do etykiet).
  - [ ] Commit: `chore(hub): confirm MODUŁY label / add regression test`

---

## Etap 2: GRAJ LOKALNIE

**Pliki:**
- Modyfikacja: `engine/scripts/polish-fighters/hub.lua` (etykieta
  wiersza `battle` w `hub.rows(mode='root')`)
- Test: `tests/global_menu_test.lua`

**Interfejsy:**
- Konsumuje: istniejący przepływ `battle`→`profile`/`players` bez zmian.
- Produkuje: etykieta "GRAJ LOKALNIE" na wierszu `battle`.

- [ ] **Zadanie 2.1: Test — GRAJ LOKALNIE nie prowadzi do żadnego
  `hub_mode` sieciowego**
  - [ ] Dopisać w `tests/global_menu_test.lua`: z `hub_mode='battle'`,
    żaden wiersz z `hub.rows(state,'battle')` nie ma `id` zaczynającego
    się od `'network'`/`'account'`/`'lan'`/`'remote'` (grep po liście
    wierszy).
  - [ ] `python tools/test_lua_scripts.py tests/global_menu_test.lua` —
    oczekiwane PASS już dziś (to test regresyjny pinujący obecne,
    prawidłowe zachowanie przed zmianą etykiety).
  - [ ] Zmienić etykietę `row('battle','play_main')` w
    `menu_locale.lua` (klucz `play_main`) na "GRAJ LOKALNIE", jeśli
    dziś brzmi inaczej.
  - [ ] `python tools/test_lua_scripts.py` — PASS.
  - [ ] Commit: `feat(hub): rename BITWA to GRAJ LOKALNIE, pin no-network invariant`

---

## Etap 3: GRAJ ZDALNIE — SERWER / WIFI / HOTSPOT

**Pliki:**
- Modyfikacja: `engine/scripts/polish-fighters/hub.lua` (nowy
  `hub_mode` `remote` zamiast `online`; usunięcie wiersza `lan` z
  `mode='settings'`)
- Modyfikacja: `engine/scripts/polish-fighters/hub_launch.lua`
  (`activate` dla `id=='remote'`, routing do SERWER/WIFI/HOTSPOT)
- Modyfikacja: `engine/scripts/polish-fighters/online_screen.lua`
  (`screen.open` — trzeci parametr `kind` zamiast tylko `lan:boolean`;
  dodanie wyświetlania własnego IPv4 na ekranie hostowania WIFI/HOTSPOT;
  nagłówek zależny od `kind`)
- Modyfikacja: `engine/scripts/polish-fighters/classic_shell.lua`
  (usunięcie panelu `connection` i jego aktywacji `room`/`tcp`/
  `capacity`/`lan`/`bluetooth`)
- Android: `engine/android/.../OpenLF2Activity.java` — włączenie
  `LanWifiMode.resume(...)` przy starcie sesji WIFI/HOTSPOT (nie tylko
  przy starcie z `lan_host` extra z usuwanej Activity — patrz Zadanie
  3.3)
- Test: `tests/online_simple_test.lua`, `tests/lan_menu_test.lua`,
  `tests/global_menu_test.lua`, `tests/content_menu_test.lua`

**Interfejsy:**
- Konsumuje: `online_client.lua` (`client.request`, `client.rooms`,
  `client.relay_available`) — bez zmian w API.
- Konsumuje: `engine.network('addresses')` (już istnieje — używane w
  gospodarzu LAN od 2026-11-20).
- Produkuje: `online_screen.open(state, simple:boolean, lan:boolean,
  kind:string|nil)` gdzie `kind` ∈ `nil`/`'wifi'`/`'hotspot'`, steruje
  tylko nagłówkiem i instrukcją na ekranie (zero nowej logiki
  sieciowej). Nowy `hub_mode` `'remote'` z wierszami
  `remote_server`/`remote_bluetooth`/`remote_wifi`/`remote_hotspot`/
  `back` w `hub.rows`.

- [ ] **Zadanie 3.1: Test — nowy `hub_mode` `remote` zastępuje `online`,
  blokuje sieć dla `mixed-all`**
  - [ ] W `tests/global_menu_test.lua`: `hub.rows(state,'root')` ma
    wiersz `remote` (nie `online`) z etykietą GRAJ ZDALNIE;
    `hub.rows(state,'remote')` zwraca 5 wierszy (SERWER/BLUETOOTH/
    WIFI/HOTSPOT/WSTECZ) gdy `state.hub_android` jest prawdziwe, 4
    (bez BLUETOOTH) gdy nieprawdziwe i Bluetooth niedostępny na danej
    platformie (na razie: flaga `state.hub_bluetooth_available`,
    ustawiana przez `hub_launch.create` — patrz Etap 4).
  - [ ] Test aktywacji: `activate(state,'remote_server',context)` z
    `catalog.profile_id=='mixed-all'` ustawia `state.hub_note` z tym
    samym komunikatem co dziś `id=='online'` w tym przypadku, **nie**
    otwiera `online.open`.
  - [ ] `python tools/test_lua_scripts.py tests/global_menu_test.lua` —
    FAIL (oczekiwane, `remote` nie istnieje jeszcze).
  - [ ] Zaimplementować `hub_mode='remote'` w `hub.rows` (sekcja
    `elseif mode=='remote' then return {...}`), usunąć `elseif
    mode=='online' then ...` i wiersz `lan` z `mode=='settings'`.
    Przy sukcesie `publish` (SERWER/WIFI/HOTSPOT) ustawić
    `state.hub_online.hosting=true` — to pole czyta Zadanie 3.3 do
    decyzji, czy pokazać własny adres IPv4 na ekranie.
  - [ ] Zaimplementować w `hub_launch.lua` `activate`:
    `id=='remote'→state.hub_mode='remote'`;
    `id=='remote_server'→` ta sama blokada `mixed-all` co dziś `online`,
    inaczej `online.open(state,true)`;
    `id=='remote_wifi'→online.open(state,true,true,'wifi')`;
    `id=='remote_hotspot'→online.open(state,true,true,'hotspot')`;
    `id=='remote_bluetooth'→` zob. Etap 4.
  - [ ] `python tools/test_lua_scripts.py` — PASS, plus pełny
    `tests/*_test.lua` bez regresji.
  - [ ] Commit: `feat(hub): add GRAJ ZDALNIE menu, replace SIECI+lan`

- [ ] **Zadanie 3.2: Test — `online_screen` z `kind='hotspot'` pokazuje
  inny nagłówek, tę samą logikę co `kind='wifi'`**
  - [ ] W `tests/online_simple_test.lua`: `screen.open(state,true,true,'hotspot')`
    ustawia `state.hub_online.kind=='hotspot'`;
    `screen.draw` (albo funkcja nagłówka, jeśli wydzielona) zwraca
    tekst zawierający "HOTSPOT" dla `kind='hotspot'` i "WIFI" dla
    `kind='wifi'`; `simple_rows(s)` jest identyczne dla obu `kind`
    (ten sam zestaw przycisków UTWÓRZ POKÓJ/DOŁĄCZ/pole adresu).
  - [ ] Test ścieżki "brakujący mod" (Ognisko uwagi #1): z
    `s.missing_mod` ustawionym, `simple_rows` wraca TAK/NIE niezależnie
    od `kind`.
  - [ ] `python tools/test_lua_scripts.py tests/online_simple_test.lua` —
    FAIL.
  - [ ] Dodać parametr `kind` do `screen.open`, zapisać w
    `state.hub_online.kind`, użyć w `screen.draw` do wyboru nagłówka
    (`kind=='hotspot'` → "GRA PRZEZ HOTSPOT", `kind=='wifi'` albo `nil`
    z `lan=true` → "GRA W SIECI LOKALNEJ", bez zmian dla `simple=true,
    lan=false` → "GRAJ PRZEZ INTERNET").
  - [ ] `python tools/test_lua_scripts.py` — PASS.
  - [ ] Commit: `feat(online_screen): add kind param for WIFI/HOTSPOT headers`

- [ ] **Zadanie 3.3: Host WIFI/HOTSPOT pokazuje własny adres IPv4 na
  tym samym ekranie; `LanWifiMode` włącza się w nowym miejscu**
  - [ ] W `tests/online_simple_test.lua`: po `screen.activate(state,'publish',context)`
    z `s.lan==true`, kolejne `screen.draw` zawiera jeden z adresów z
    `engine.network('addresses')` (zamockować tę funkcję w teście jak
    już robią inne testy LAN, np. `lan_menu_test.lua`).
  - [ ] `python tools/test_lua_scripts.py tests/online_simple_test.lua` —
    FAIL (dziś ta informacja jest tylko na ekranie `base/ui/network.lua`,
    nie na `online_screen`).
  - [ ] W `screen.draw` (albo `simple_rows`), gdy `s.lan and
    s.hosting` (nowe pole ustawiane po `publish`), dopisać wiersz/tekst
    z adresami z `engine.network('addresses')`.
  - [ ] `python tools/test_lua_scripts.py` — PASS.
  - [ ] Android: w `OpenLF2Activity.java`, przenieść wywołanie
    `lanWifi.resume(...)` tak, by odpalało się też gdy silnik wchodzi w
    sesję LAN przez `context.action('network')` zainicjowaną z nowego
    ekranu WIFI/HOTSPOT (dziś warunek to tylko
    `getIntent().hasExtra("lan_host")`, co po usunięciu
    `BluetoothLobbyActivity.lanAddress()` w Etapie 4 nigdy się nie
    zdarzy) — dodać drugi warunek odczytujący stan sesji z silnika
    (np. nowa metoda `engine.network('is_lan_session')` albo
    przekazanie przez istniejący kanał ustawień, do decyzji wykonawcy;
    ważne tylko, żeby `WifiLock` się włączał dla **każdej** sesji LAN
    zainicjowanej z nowego ekranu, nie tylko ze starej Activity).
  - [ ] Zaktualizować `LanWifiModeTest.java` pod nowy warunek.
  - [ ] Test Gradle: `./gradlew testDebugUnitTest` — PASS.
  - [ ] Commit: `feat(wifi): show host IPv4 inline, keep low-latency Wi-Fi lock alive`

- [ ] **Zadanie 3.4: Usunąć panel `connection` z `classic_shell.lua`**
  - [ ] Test w `tests/classic_menu_test.lua`: `pf_panel=='extras'`
    rows nie zawiera wiersza `connection`; aktywacja `id=='connection'`
    (jeśli ktoś je wywoła ze starego zapisanego stanu) nie crashuje,
    tylko jest ignorowana (fallback `else s.pf_panel=id end` — sprawdzić
    że `id='connection'` nie tworzy już nieistniejącego panelu, bo
    `rows()` dla `pf_panel=='connection'` zostanie usunięte).
  - [ ] `python tools/test_lua_scripts.py tests/classic_menu_test.lua` —
    FAIL.
  - [ ] Usunąć z `classic_shell.lua`: wiersz `{"connection", ...}` z
    listy `extras`, blok `elseif s.pf_panel=="connection" then return {...}`,
    oraz `elseif id=="room"/"tcp"/"capacity"/"lan"/"bluetooth" then ...`
    z `activate`. Przenieść `capacity` (limit pokoju) jako pole na
    ekran SERWER w `online_screen.lua` (przy `publish`) — zgodnie ze
    spec §8.3 to decyzja wykonawcy, zapisać wybór w commicie.
  - [ ] Dopisać test pinujący wybraną lokalizację `capacity`: jeśli
    trafiła na ekran SERWER, asercja że `screen.rows(s)` (z
    `s.simple=false`, po zalogowaniu) zawiera wiersz `capacity` z
    aktualną wartością `dashboard_model.current().room_capacity`;
    jeśli trafiła do USTAWIENIA, analogiczna asercja w
    `tests/control_options_test.lua`. Jedno miejsce, jeden test —
    żeby decyzja nie została tylko opisem w commicie.
  - [ ] `python tools/test_lua_scripts.py` — PASS, pełny zestaw testów
    bez regresji.
  - [ ] Commit: `refactor(classic_shell): remove duplicate connection panel`

---

## Etap 4: GRAJ ZDALNIE — BLUETOOTH (restart-wrapped)

Dwa niezależne pod-etapy (Android, Windows) łączy tylko wspólny
kontrakt: flaga w zapisanych ustawieniach i argument startowy
przekazujący rolę (`host`/`join`) i port do silnika po restarcie —
nazwane tak samo po obu stronach, żeby Lua (`hub_launch.lua`) nie
musiała znać platformy.

### 4A — Android

**Pliki:**
- Usunięcie: `engine/android/app/src/main/java/.../BluetoothLobbyActivity.java`
  (zastąpiona nowym, prostszym ekranem — patrz niżej)
- Create: `engine/android/app/src/main/java/.../BluetoothPairingActivity.java`
- Modyfikacja: `engine/android/app/src/main/java/.../OpenLF2Activity.java`
  (wywołanie nowej Activity miejsce dzisiejszego `BluetoothLobbyActivity`)
- Modyfikacja: `engine/scripts/polish-fighters/hub.lua`/`hub_launch.lua`
  (`id=='remote_bluetooth'`)
- Test: przepisany `StartScreenTest.java` pod `BluetoothPairingActivity`

**Interfejsy:**
- Konsumuje: `BluetoothSession.java` (parowanie/RFCOMM) bez zmian w
  jego logice.
- Produkuje: `BluetoothPairingActivity` z dokładnie czterema akcjami:
  "SZUKAJ URZĄDZEŃ" (paruj), "UTWÓRZ POKÓJ" (host), "DOŁĄCZ" (join do
  sparowanego), "WSTECZ" (zawsze wraca do `OpenLF2Activity` z flagą
  `little_fighters_start_menu='remote'`, tak by Lua otworzyło się
  bezpośrednio na GRAJ ZDALNIE, nie na korzeniu menu).

- [ ] **Zadanie 4A.1: Test — `hub_launch.lua` otwiera Bluetooth przez
  ten sam wzorzec co `android_tools`**
  - [ ] W `tests/global_menu_test.lua`: `activate(state,'remote_bluetooth',context)`
    na Androidzie (`state.hub_android=true`) wywołuje
    `engine.write_settings` z nowym kluczem (np.
    `little_fighters_open_bluetooth=true`) i `context.action('quit')`
    — analogicznie do istniejącego testu dla `android_tools` w
    `hub.open_android_tools`.
  - [ ] `python tools/test_lua_scripts.py tests/global_menu_test.lua` —
    FAIL.
  - [ ] Zaimplementować `hub.open_android_bluetooth(context)` w
    `hub.lua` (kopia `open_android_screen` z innym kluczem), wywołać z
    `hub_launch.activate` dla `id=='remote_bluetooth'` na Androidzie;
    na platformach bez Bluetootha (`not state.hub_bluetooth_available`)
    wiersz się nie pojawia (patrz Zadanie 3.1), więc ta ścieżka
    aktywacji nie jest wywoływana.
  - [ ] `python tools/test_lua_scripts.py` — PASS.
  - [ ] Commit: `feat(hub): route BLUETOOTH through existing quit+relaunch pattern`

- [ ] **Zadanie 4A.2: Nowa `BluetoothPairingActivity` — test
  Robolectric na starcie, wstecz, i stanie braku adaptera**
  - [ ] Napisać `BluetoothPairingActivityTest.java` (styl
    `StartScreenTest.java`): aktywność się tworzy
    (`ActivityController.setup()`), cztery przyciski widoczne;
    `pf_quit` → `startedActivity` jest `OpenLF2Activity` z extra
    `little_fighters_start_menu='remote'`; gdy
    `BluetoothAdapter.getDefaultAdapter()==null` (Robolectric shadow),
    status pokazuje komunikat "Ten telefon nie udostępnia Bluetooth."
    (Ognisko uwagi #2).
  - [ ] `./gradlew testDebugUnitTest --tests BluetoothPairingActivityTest`
    — FAIL (klasa nie istnieje).
  - [ ] Zaimplementować `BluetoothPairingActivity` przenosząc
    `connect()`, `start()`, `showConnections()`-odpowiednik (bez
    gałęzi Wi-Fi/PAN — usuniętych w spec §6) i obsługę uprawnień z
    `BluetoothLobbyActivity` — logika `BluetoothSession` wołana bez
    zmian, zmienia się tylko układ ekranu (4 przyciski zamiast
    zagnieżdżonych `AlertDialog`) i miejsce powrotu (`pf_quit` zawsze
    do `OpenLF2Activity` z flagą menu, nigdy z pustym intentem jak dziś
    `launch(null,0)` bez flagi).
  - [ ] `./gradlew testDebugUnitTest` — PASS, `lint` 0 błędów.
  - [ ] Commit: `feat(android): add BluetoothPairingActivity, remove BluetoothLobbyActivity`

- [ ] **Zadanie 4A.3: `OpenLF2Activity` czyta flagę `little_fighters_open_bluetooth`
  i uruchamia `BluetoothPairingActivity`**
  - [ ] Test: istniejący wzorzec dla `little_fighters_open_android_tools`
    w `OpenLF2Activity` (sprawdzić, czy jest test — jeśli nie, dopisać
    jeden analogiczny) — dla nowej flagi, `onCreate`/`onResume`
    uruchamia `BluetoothPairingActivity` i czyści flagę.
  - [ ] Zaimplementować analogicznie do istniejącej obsługi
    `little_fighters_open_android_tools` (jeśli taka gałąź już
    istnieje w `OpenLF2Activity` — zweryfikować przy pisaniu, spec nie
    wyklucza że dziś jest to zrobione inaczej, np. przez
    `hub_mods`/`AndroidModsActivity`; wykonawca ma to sprawdzić w
    kodzie przed implementacją, nie zgadywać).
  - [ ] `./gradlew testDebugUnitTest` — PASS.
  - [ ] Commit: `feat(android): wire bluetooth-open flag into OpenLF2Activity`

### 4B — Windows

**Pliki:**
- Create: `engine/src/adapters/bluetooth/windows_bluetooth.cpp` (+ `.h`)
- Create: `engine/src/adapters/bluetooth/bluetooth_stub.cpp` (inne
  platformy desktop: Linux/macOS/web — `available()` zwraca `false`)
- Modyfikacja: `engine/CMakeLists.txt` (dodanie nowego adaptera,
  warunkowo `WIN32`)
- Create: ekran natywny parowania — **do decyzji wykonawcy** czy jako
  osobne okno Win32 (symetryczne z Android Activity) czy jako nowy
  ekran wewnątrz tego samego binarnego uruchomienia z innym argumentem
  startowym (`--bluetooth-pairing`), analogicznie do tego, jak
  `GameLaunchArguments` już przekazuje rolę/port na Androidzie. To
  jedyne naprawdę otwarte pytanie architektoniczne tego zadania —
  spec §9 zostawia je wykonawcy, ale **zanim wykonawca zacznie pisać
  kod, ma zdecydować i zapisać wybór w treści swojego pierwszego
  commitu tego pod-etapu**, żeby kolejne zadania 4B.2+ nie zgadywały.
- Test: `tests/windows_preset_test.lua` (jeśli dotyczy ustawień
  startowych) + nowy natywny test C++ w `tests/` (wzorując się na
  istniejących `tests/*.cpp`, np. `room_test.cpp`)

**Interfejsy:**
- Konsumuje: nic nowego z istniejącego kodu (to pierwszy Bluetooth na
  tej platformie).
- Produkuje: funkcję wywoływaną z natywnego ekranu parowania,
  odpowiadającą za: wykrycie dostępności adaptera, listę sparowanych
  urządzeń, host/join, przekazanie wyniku (rola+port) do uruchomienia
  silnika z tymi samymi argumentami startowymi co dziś dostaje Android
  (patrz `GameLaunchArguments.build` jako wzór kontraktu, nie kod do
  skopiowania 1:1 — Windows ma swój łańcuch argumentów wiersza poleceń).

- [ ] **Zadanie 4B.1: Test — `bluetooth_stub` na platformach bez
  Bluetootha zwraca `available()==false`, bez wpływu na build Linuxa/weba**
  - [ ] Dodać minimalny test C++ (wzór: istniejący `tests/package_smoke.cpp`)
    kompilujący i wołający `bluetooth::available()` na stubie —
    oczekiwane `false`.
  - [ ] Skompilować: brak takiej funkcji jeszcze — FAIL (błąd linkera/
    kompilacji).
  - [ ] Zaimplementować `bluetooth_stub.cpp` z `available()` zwracającym
    `false` i pustymi/no-op implementacjami pozostałych funkcji
    interfejsu (sygnatura do ustalenia przez wykonawcę razem z
    Zadaniem 4B.2, bo musi być identyczna na Windows i stubie).
  - [ ] Build + test — PASS, build innych platform (`build-appimage.sh`
    itp.) niezmieniony (stub, nie nowa zależność).
  - [ ] Commit: `feat(engine): add bluetooth adapter interface + non-Windows stub`

- [ ] **Zadanie 4B.2: Windows — wykrywanie dostępności i sparowanych
  urządzeń (Win32 Bluetooth Classic)**
  - [ ] Test natywny (uruchamiany tylko na Windows w CI, analogicznie
    do `tests/windows_preset_test.lua`/istniejących testów oznaczonych
    jako Windows-only w `CMakeLists.txt`): `bluetooth::available()` na
    maszynie z wyłączonym radiem Bluetooth zwraca `false` z
    komunikatem do pokazania w UI (Ognisko uwagi #2); z włączonym —
    `true` i niepustą(ewentualnie puste, jeśli brak par) listę z
    `paired()`.
  - [ ] Build na Windows — FAIL (funkcje jeszcze nie istnieją po
    stronie Windows, tylko w interfejsie ze stuba).
  - [ ] Zaimplementować `windows_bluetooth.cpp` z `BluetoothFindFirstRadio`/
    `BluetoothFindFirstDevice` (albo WinRT, wedle decyzji z nagłówka
    sekcji 4B) do wykrycia radia i listy sparowanych urządzeń.
  - [ ] Build + test na Windows — PASS.
  - [ ] Commit: `feat(windows): detect bluetooth radio and paired devices`

- [ ] **Zadanie 4B.3: Windows — host/join RFCOMM i uruchomienie
  silnika z rolą+portem**
  - [ ] Test natywny: dwa procesy testowe (host/join) na localhost-
    emulowanym RFCOMM (albo, jeśli SDK nie pozwala emulować bez
    fizycznego radia, test ograniczony do sprawdzenia, że `host()`
    zwraca błąd zrozumiały dla UI gdy brak drugiego urządzenia w
    rozsądnym czasie — bez prawdziwego parowania, to idzie do
    weryfikacji ręcznej, patrz spec §10) — do ustalenia przez
    wykonawcę zależnie od tego, co faktycznie dają testy jednostkowe
    bez dwóch fizycznych maszyn.
  - [ ] Zaimplementować `host()`/`join(device)` w `windows_bluetooth.cpp`
    (RFCOMM accept/connect), zwracające rolę+port do przekazania do
    ekranu parowania, który startuje silnik tak jak dziś robi to
    Android po `BluetoothSession.Listener.ready(role,port)`.
  - [ ] Zaimplementować natywny ekran parowania zgodnie z decyzją z
    nagłówka sekcji 4B (okno Win32 albo argument startowy binarki).
  - [ ] Weryfikacja ręczna na dwóch maszynach/maszyna+telefon z
    włączonym Bluetooth (spec §10 — oznaczyć w raporcie jako wymagającą
    realnego sprzętu).
  - [ ] Commit: `feat(windows): bluetooth host/join + pairing screen`

---

## Etap 5: USTAWIENIA — Sterowanie (Android)

**Pliki:**
- Modyfikacja: `engine/scripts/polish-fighters/input_settings.lua`
  (`screen.rows` — nowy wiersz przełącznika i wiersz "EDYTOR HUD" na
  Androidzie)
- Modyfikacja: `engine/scripts/polish-fighters/classic_shell.lua`
  (decyzja: alias albo usunięcie wejścia `touch`)
- Test: `tests/control_options_test.lua`, `tests/hybrid_editor_test.lua`

**Interfejsy:**
- Konsumuje: `base/ui/hybrid_layout.lua` (pole trybu joystick/strzałki
  — nazwa pola do sprawdzenia w kodzie przy implementacji, nie
  zgadywana tutaj), `base/ui/hybrid_editor.lua` (`create(options,'menu')`).
- Produkuje: nowe wiersze w `input_settings.rows(state,input)` na
  Androidzie: `hybrid_mode` (przełącza i zapisuje wartość pola trybu),
  `hybrid_hud` (otwiera edytor).

- [ ] **Zadanie 5.1: Test — wiersze JOYSTICK/STRZAŁKI i EDYTOR HUD
  widoczne tylko na Androidzie, przełącznik zapisuje ustawienie**
  - [ ] W `tests/control_options_test.lua`: `screen.rows(state,input)`
    z `state.hub_android=true` zawiera wiersz `hybrid_mode` i
    `hybrid_hud`; z `state.hub_android=false` (Windows) — nie zawiera
    żadnego z nich; aktywacja `hybrid_mode` przełącza wartość i po
    `screen.activate(state,'save')` zapisany plik ustawień ma nową
    wartość (sprawdzić przez `engine.write_settings` mock, wzorem
    innych testów w tym pliku).
  - [ ] `python tools/test_lua_scripts.py tests/control_options_test.lua`
    — FAIL.
  - [ ] Dodać wiersze w `input_settings.rows` warunkowo na
    `state.hub_android`, obsłużyć `id=='hybrid_mode'` (przełącza pole
    trybu w strukturze zwracanej przez `hybrid_layout`) i
    `id=='hybrid_hud'` (ustawia `state.hud=require('base/ui/hybrid_editor').create(...)`,
    `state.page='hud'`, analogicznie do dzisiejszego `classic_shell`
    `id=="touch"`).
  - [ ] `python tools/test_lua_scripts.py` — PASS.
  - [ ] Zdecydować los wejścia `touch` w `classic_shell.lua` (alias do
    tej samej funkcji albo usunięcie wiersza) i zaimplementować wybór.
  - [ ] Pełny zestaw testów Lua — bez regresji.
  - [ ] Commit: `feat(settings): move hybrid control toggle + HUD editor into STEROWANIE`

---

## Weryfikacja końcowa (po wszystkich etapach)

- [ ] `python tools/test_lua_scripts.py` — wszystkie pliki + wszystkie
  `tests/*_test.lua` PASS, zero skipów ponad to, co już jest znane
  (np. ograniczenia Windows-only testów na platformie bez Windows).
- [ ] Android: `./gradlew testDebugUnitTest lintDebug` — 0 błędów.
- [ ] Windows: build natywny + `tests/windows_preset_test.lua` + próba
  ręczna Bluetooth na realnym sprzęcie (spec §10).
- [ ] Przejście całego drzewa menu ręcznie na obu platformach: każde
  wejście dokładnie jeden poziom w głąb, każde wstecz dokładnie jeden
  poziom w górę, zero przypadków wychodzenia do pulpitu/systemu poza
  MENU GŁÓWNE→WYJŚCIE.
