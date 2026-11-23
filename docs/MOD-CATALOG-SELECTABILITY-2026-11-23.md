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
