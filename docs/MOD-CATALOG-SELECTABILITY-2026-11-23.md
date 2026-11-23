# Katalog modów GitHub: brakujące powiązania profili i brak powiadomienia o nowej wersji (2026-11-23)

## Zgłoszony problem

1. Ekran MODUŁY pokazuje wszystkie paczki poza Polish Originals jako `[BRAK DANYCH]` /
   "Brak lokalnego pakietu", mimo że release `mods` na GitHubie ma 14 podpisanych paczek
   z poprawnym `mods/catalog.sig`.
2. Po zbudowaniu i wypchnięciu nowego katalogu (`mods/catalog.json`, revision 1, 14 paczek)
   gra nie pokazuje żadnego komunikatu o nowej wersji katalogu modów.

## Co faktycznie znaleziono

Cały mechanizm pobierania/weryfikacji/instalacji podpisanego katalogu i paczek
(`engine/src/adapters/curl/github_mods.cpp`, `engine/src/adapters/luajit/runtime.cpp`
`mods_operation`, `engine/android/.../AndroidModSources.java`) jest zaimplementowany poprawnie
i zgodny z formatem generowanym przez `tools/build_mod_release.py` - podpis, SHA-256, rozmiar
koperty i manifestu są sprawdzane krok po kroku. To nie jest zepsute.

Rzeczywisty problem: **po pobraniu paczki trzy z czternastu (`mortal-kombat`, `lf3`, `oplos`)
nigdy nie mogły zostać wybrane jako aktywny moduł gry** - nie były wpisane ani w
`engine/src/app/application.cpp` (`profile_definitions`, które decydują czy
`content-packs/<id>/package.manifest` jest sprawdzany przy starcie gry), ani w
`engine/scripts/polish-fighters/hub.lua` (`hub.optional_profiles`, ekran DODATKOWE MODUŁY),
ani w `engine/scripts/polish-fighters/mod_browser.lua` (`profile_tags`, który łączy wpis
katalogu z akcją `profile_<tag>`). Plik pobierał się i weryfikował poprawnie, trafiał na dysk,
ale gra nie miała żadnej ścieżki UI, która pozwoliłaby go uruchomić - wyglądało to jak
"paczka nigdy nie została zainstalowana".

`dragon-ball-super` i `ntsd-community` miały dwa z trzech wpisów (profile_definitions +
hub.optional_profiles), więc po restarcie gry stawały się wybieralne przez DODATKOWE MODUŁY,
ale `profile_tags` w mod_browser.lua ich nie znał, więc bezpośredni klik "WYBIERZ" w ekranie
KATALOG MODÓW tuż po pobraniu nic nie robił (trzeba było wyjść do menu i wejść ponownie).

Dla pozostałych siedmiu paczek bazowych (bleach, dbz, kate, reinforced, ntsd, lf4-turbo,
one-piece) cała ścieżka jest od dawna poprawnie okablowana - `[BRAK DANYCH]` na tym etapie
oznacza, że paczka po prostu nie została jeszcze pobrana w danej instalacji gry (trzeba otworzyć
KATALOG MODÓW i kliknąć POBIERZ, albo zaznaczyć kilka przez ZAZNACZ WIELE), nie błąd.

Komunikat "nowa wersja katalogu dostępna" nigdy nie istniał w kodzie - `engine.mods('catalogue')`
był wywoływany wyłącznie wtedy, gdy gracz sam otworzył KATALOG MODÓW. Nic nie sprawdzało
katalogu automatycznie przy starcie gry.

## Co naprawiono

- `engine/src/app/application.cpp`: dodano `profile_mortal_kombat`/`profile_lf3`/`profile_oplos`
  do `profile_definitions`.
- `engine/scripts/polish-fighters/hub.lua`: dodano `mortal_kombat`/`lf3`/`oplos` do
  `hub.optional_profiles`.
- `engine/scripts/polish-fighters/mod_browser.lua`: dodano `mortal_kombat`/`lf3`/`oplos` oraz
  `dragon_ball_super`/`ntsd_community` do `profile_tags`, żeby świeżo pobrana paczka była
  wybieralna od razu z ekranu KATALOG MODÓW, bez restartu gry.
- Nowy moduł `engine/scripts/polish-fighters/catalog_watch.lua`: w tle (bez blokowania menu)
  odpytuje podpisany katalog raz na start gry i, jeśli są paczki do pobrania/aktualizacji,
  wyświetla komunikat na ekranie głównym MODUŁY. Działa tylko na desktopie (Windows) - na
  Androidzie paczki GitHub są instalowane przez natywny `AndroidModsActivity`, nie przez
  `engine.mods`, więc tam wymagałoby to osobnej zmiany po stronie Javy (nieobjęte tą poprawką).

## Czego NIE naprawiono (bo nie było czym zreprodukować)

Nie da się w tym środowisku zbudować i odpalić gry (brak SDL3/LuaJIT/FFmpeg/libcurl/OpenSSL -
zob. `engine/CMakeLists.txt`), więc jeśli bazowe siedem paczek pokazuje `[BRAK DANYCH]` na
faktycznie uruchomionej grze NAWET po otwarciu KATALOG MODÓW i kliknięciu POBIERZ (a nie tylko
przed pobraniem), to jest to inny, jeszcze nieodtworzony problem - proszę o zrzut ekranu z tego
konkretnego ekranu (KATALOG MODÓW, status po POBIERZ) albo logi konsoli gry przy starcie, żeby
to zweryfikować.

## Runda 2 (po zrzutach ekranu z Androida)

Zrzuty ekranu pokazały dwie rzeczy, których runda 1 nie objęła:

1. **"Nie zapisano wyboru: Nieznany moduł" na Androidzie dla `lf3`/`mortal-kombat`.**
   `AndroidModsActivity.selectProfile()` zapisuje wybór przez
   `engine/android/.../GamePackSettings.java`, który ma SWOJĄ, czwartą, całkowicie
   niezależną od C++/Lua listę dozwolonych profili (`IDS`/`TITLES`/`PACKS` + switch
   `optionalTitle()`). Runda 1 naprawiła `profile_definitions` (C++, desktop), `hub.lua` i
   `mod_browser.lua` (Lua, desktop/ekran KATALOG MODÓW na desktopie) - ale nie dotknęła tego
   pliku. `GamePackSettings.save()` odrzucał `mortal_kombat`/`lf3`/`oplos` wyjątkiem
   `IllegalArgumentException("Nieznany moduł")`, bo nie były ani w `IDS`, ani rozpoznawane
   przez `optionalTitle()`. Paczka pobierała się i instalowała poprawnie (widać "WYBIERZ" w
   KATALOG MODÓW), ale zapis wyboru zawsze się wywalał.
   Naprawiono: dodano `dragon_ball_super`, `ntsd_community`, `mortal_kombat`, `lf3`, `oplos`
   do `IDS`/`TITLES`/`PACKS` w `GamePackSettings.java` (commit `6091356`).

2. **Wymóg: żadnego podmenu "DODATKOWE MODUŁY" dla wydanych paczek.** Runda 1 wpisała
   `mortal_kombat`/`lf3`/`oplos` do `hub.optional_profiles`, czyli do osobnego ekranu
   (`mode=='optional_modules'`, wiersz "DODATKOWE MODUŁY" na głównej liście), zamiast na
   główną listę - to nie spełniało wymagania "wszystkie mają być na liście". Przeniesiono
   `dragon_ball_super`/`ntsd_community`/`mortal_kombat`/`lf3`/`oplos` z
   `hub.optional_profiles` do `hub.profiles` (Lua, desktop) i do głównej tablicy `IDS`
   (Android) - teraz wszystkich 14 wydanych paczek z `mods/catalog.json` jest widocznych
   bezpośrednio na głównej liście MODUŁY, z `[BRAK DANYCH]` tam gdzie paczka nie jest jeszcze
   pobrana lokalnie, tak jak oryginalnych 9. `hub.optional_profiles` zostaje tylko dla paczek,
   których `tools/build_mod_release.py` PACKS jeszcze nie ma zbudowanych/wydanych
   (fighter-hero, gf2, lf2-ns, sx2, lf2-sv, rn-lf2, lf-seed, wlf2-al, ce-lf2, ntsd-ce-setup,
   killer-lf2) - gdy zostaną wydane, trzeba je analogicznie przenieść.

3. **`module_inventory.lua`** (ekran STAN/ZGODNOŚĆ MODUŁÓW) nie miał wpisów dla tych 5 paczek,
   bo jest generowany z realnych assetów przez `tools/generate_module_registry.py`, których ten
   checkout nie ma. Dopisano wpisy ręcznie na podstawie opisów z `mod_catalog.lua` i liczby
   `fighters` z `content-packs/<id>/import-report.json` (obie te dane już były w repo i
   pochodzą z wcześniejszego importu tych paczek na docelowej maszynie) - **do potwierdzenia
   ponownym odpaleniem generatora na maszynie z pełnym repo**. To nie blokuje wybierania ani
   grania paczką (o tym decyduje `state.hub_available`, realna obecność plików), tylko licznik
   "Brakujące pliki" na jednym ekranie diagnostycznym.

### Co zweryfikowano w rundzie 2, a co nie

- `luac5.4 -p` na `hub.lua` i `module_inventory.lua` - OK.
- `python3 -m pytest tests/test_github_mods.py` - 6/6 OK (bez zmian w tej logice, uruchomione
  jako regresja).
- Próba uruchomienia testów jednostkowych Androida (`./gradlew testDebugUnitTest`) - w tym
  środowisku NIE DA SIĘ: brak Android SDK (`ANDROID_HOME`/`local.properties`). Zmiana w
  `GamePackSettings.java` była więc zweryfikowana tylko manualnie: zgodność nawiasów/długości
  tablic sprawdzona skryptem, logika `IDS`/`PACKS`/`TITLES` sprawdzona pod kątem wszystkich
  miejsc, które z nich czytają (`GameLaunchArguments.build`, `BluetoothLobbyActivity`,
  `AndroidModsActivity`) - wszystkie liczą długość dynamicznie (`GamePackSettings.IDS.length`),
  żadne nie zakłada "9", więc rozszerzenie do 14 nie powinno nic złamać, ale **to nie jest
  potwierdzone realnym uruchomieniem testów Robolectric na tej maszynie**. Testy
  `GamePackSettingsTest`/`GamePackDialogTest`/`everySingleModuleLaunchesExactlyThatModule` już
  istnieją i obejmują ten kod - proszę je przepuścić lokalnie (`./gradlew testDebugUnitTest`)
  przed wydaniem.
- Nie sprawdzono, czy jest jeszcze jakiś OSOBNY ekran "MODUŁY" na Androidzie (poza KATALOG
  MODÓW i BluetoothLobbyActivity) z własną, krótszą listą - przeszukano wszystkie miejsca
  odwołujące się do `GamePackSettings.IDS`/`TITLES`/`PACKS` i wszystkie trzy znalezione pliki
  (`AndroidModsActivity.java`, `BluetoothLobbyActivity.java`, `GameLaunchArguments.java`)
  czytają je dynamicznie, więc osobnej "piątej" listy nie znaleziono - ale proszę dać znać,
  jeśli po aktualizacji na telefonie nadal gdzieś widać tylko 9 pozycji.
