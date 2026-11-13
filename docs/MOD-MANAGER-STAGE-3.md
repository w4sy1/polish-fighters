# Mod Manager — etap 3, 2026-11-13 (nieprzetestowany)

Użytkownik zezwolił na kontynuację ze środków dodatkowych po wyczerpaniu limitu 5-godzinnego. Nadal obowiązuje polecenie „bez testów”. Nie uruchamiano testów, parserów składni, lint, buildów, GUI, importu, pobierania ani gry. Przeczytano kod oraz `git diff`, `git diff --stat`, `git diff --check` i status plików. Wyniki testów etapu 1 nie obejmują obecnego kodu.

## Zmiany

- `tools/mod_library.py`: centralna biblioteka w ignorowanym `userdata/mod-manager/`; instalacja, deduplikacja, aktualizacja z ZIP, profile, włączanie/wyłączanie, kontrola konfliktów, usunięcie z lokalną kopią i przywracanie. Zapisy JSON są atomowe, operacje biblioteki mają blokadę, przed zmianą stanu powstaje kopia poprzednich wyborów. Stan nie zawiera pełnych kopii list SHA-256 wszystkich plików — zapisuje zbiorczy digest, aby ograniczyć rozmiar kopii.
- Przy włączaniu/planowaniu uruchomienia sprawdzana jest zgodność plików z inwentarzem instalacji, nie zgodność rozgrywki. Dwie pełne konwersje nadpisujące katalog LF2/dźwięki są blokowane; kontrolowane są identyfikatory obiektów, przestrzenie nazw zasobów i limit zasobów silnika. Nie zaimplementowano scalania pełnych katalogów ani emulowania patchy EXE.
- Identyfikator nowego pakietu wynika z SHA-256 archiwum. Dwa niezależne importy identycznej paczki mogą dzięki temu używać tych samych nazw wirtualnych. Aktualizacja zachowuje ID poprzedniej instalacji. Mod nie otrzymuje wymyślonej wersji: `package_api_version=1` dotyczy manifestu, a wersja moda pozostaje nieustalona.
- `tools/mod_archive.py` / `tools/mod_manager.py`: jawny tryb `data_only` pomija niedozwolone EXE, DLL, Lua i pozostałe nieobsługiwane typy przed ekstrakcją. Limity, kontrola ścieżek, szyfrowania, symlinków i kolizji nadal obejmują całe archiwum. Domyślny starszy import CLI pozostaje rygorystyczny; `--data-only` włącza pomijanie. Biblioteka zarządzana używa trybu danych.
- `tools/mod_manager_gui.py`: zakładka Zainstalowane i profile, aktualizacja ZIP, podgląd rzeczywistej listy plików przed instalacją, lista pomijanych plików, przywracanie pakietów i wyborów profilu. Powiązanie z pozycją katalogu jest wyborem użytkownika, nie potwierdzeniem pochodzenia paczki.
- Launcher desktopowy tworzy argumenty `--scripts`, `--config-dir` i `--mod`. Uruchomienie następuje dopiero po poleceniu CLI `launch` lub przycisku „Graj wybranym profilem”. Wybór EXE ograniczono do nazw gry; manager nie potwierdza podpisu/autentyczności wybranego EXE. Plik gry musi pochodzić z zaufanej paczki. Nie wolno uruchamiać programu z katalogu danych/downloadów managera.
- Manager blokuje zmiany pakietów/profili, gdy proces gry uruchomiony przez managera nadal działa. Nie wykrywa wszystkich ręcznych uruchomień gry; przed aktualizacją/usunięciem należy również zamknąć grę uruchomioną ręcznie.
- `engine/scripts/polish-fighters/hub_flow.lua`, `hub.lua`, `hub_launch.lua`, `locales/pl.lua`, `locales/en.lua`: rozpoznanie zarządzanego `mod-*`, start od wyboru trybu dla bieżącego moda i powrót do niego z biblioteki. Bez zmian C++/Javy, AndroidManifest, signing, uprawnień i wersji aplikacji.

## Kopie i dane

Usunięcie z biblioteki przenosi pakiet do `userdata/mod-manager/versions/`, a nie usuwa go fizycznie. Umożliwia przywrócenie, ale nie zwalnia miejsca po paczce. Aktualizacje również zachowują poprzednią wersję. Kopie nie są automatycznie kasowane ani publikowane. Odtwarzanie plików pakietu i odtwarzanie wyborów profili to dwie osobne operacje, aby nie oznaczać brakujących plików jako istniejących.

Stan `library.json` ma limit 2 MiB; zbyt duży stan powinien przerwać zapis i wycofać instalację. Staging może chwilowo wymagać miejsca na rozpakowane i przekonwertowane zasoby jednocześnie. Dane i kopie są ignorowane przez Git.

## Polecenia do późniejszego użycia — nie wykonano

Z katalogu repozytorium:

```powershell
.\.build-venv\Scripts\python.exe tools/mod_manager_gui.py
.\.build-venv\Scripts\python.exe tools/mod_manager.py library list
.\.build-venv\Scripts\python.exe tools/mod_manager.py library install --archive 'C:\paczki\mod.zip' --name 'Mój mod'
.\.build-venv\Scripts\python.exe tools/mod_manager.py library profile --profile rodzinny --name 'Rodzina' --mods
.\.build-venv\Scripts\python.exe tools/mod_manager.py library enable --profile rodzinny --id IDENTYFIKATOR-PAKIETU
.\.build-venv\Scripts\python.exe tools/mod_manager.py library disable --profile rodzinny --id IDENTYFIKATOR-PAKIETU
.\.build-venv\Scripts\python.exe tools/mod_manager.py library update --archive 'C:\paczki\nowa-wersja.zip' --id IDENTYFIKATOR-PAKIETU
.\.build-venv\Scripts\python.exe tools/mod_manager.py library remove --id IDENTYFIKATOR-PAKIETU
.\.build-venv\Scripts\python.exe tools/mod_manager.py library restore --id IDENTYFIKATOR-KOPII
.\.build-venv\Scripts\python.exe tools/mod_manager.py library history
.\.build-venv\Scripts\python.exe tools/mod_manager.py library restore-profile --id IDENTYFIKATOR-MIGAWKI
.\.build-venv\Scripts\python.exe tools/mod_manager.py library plan --profile rodzinny --exe 'C:\gra\LittleFighters.exe'
.\.build-venv\Scripts\python.exe tools/mod_manager.py library launch --profile rodzinny --exe 'C:\gra\LittleFighters.exe'
```

Ścieżki i identyfikatory w przykładach są symbolami zastępczymi. `plan` nie uruchamia procesu. Plan/funkcja launch weryfikuje inwentarz plików i konflikty; nie jest testem rozgrywki. Własny fingerprint profilu jest diagnostyczny — autorytatywna tożsamość sieciowa nadal powstaje w silniku z kodu, skryptów i zasobów.

## Pozostało

Cały projekt nie jest ukończony. Nadal brak zarządzania plikami i pobieraniem w docelowym GUI gry/Androida, kompletnej weryfikacji źródeł wszystkich wpisów i pobrania rzeczywistych paczek, importu RAR/7z, bezpiecznego scalania zasobów różnych pełnych konwersji oraz potwierdzenia mechanik i multiplayera. Kontrole strukturalne nie zastępują testów zgodności; wszystkie nowe pakiety pozostają nieprzetestowane. Nie zbudowano EXE/APK i nie wykonano commit/push/release.

Przy kolejnym etapie: najpierw Git, bieżące środki i ewentualne nakładające się prace. Następnie docelowa integracja z grą/Androidem. Nie przywracać testów bez cofnięcia zakazu użytkownika. Punkt przywracania plików narzędzi sprzed etapu 3 znajduje się w katalogu roboczym bieżącego chatu `work/checkpoint-stage3/`; stan bazowy repozytorium: `bebc5ce` na `main`.
