# Lokalna budowa i walidacja Windows x64

Wydanie testowe 0.6, 2026-10-25. Bez instalacji systemowej, commitów, pushów ani publikacji.

## Uruchomienie

Folder `engine/out/PolishFighters-Windows-x64-portable`:

- `Graj-LF2.cmd` — profil klasyczny.
- `Graj-LF4-Turbo.cmd` — osobny profil LF4 Turbo.

Ustawienia są zapisywane osobno w `userdata/LF2` i `userdata/LF4-Turbo` wewnątrz paczki. Wygląd i nawigacja pozostają klasyczne. Dodatki: F10; pokój: Połączenia → Pokój LAN. Port domyślny TCP 12345. Fizycznego LAN/Wi-Fi jeszcze nie sprawdzono.

## Odtworzenie budowy

W katalogu projektu, PowerShell:

```powershell
python -m venv .build-venv
.\.build-venv\Scripts\python.exe -m pip install conan==2.32.0 cmake ninja Pillow
.\tools\build_windows_local.ps1
```

Wymagane MSVC C++ Build Tools 2022 i Windows SDK. Skrypt używa osobnego `engine/build/conan-home`; nie zmienia domyślnego profilu Conan użytkownika. Installer LF2 jest czytany z `../downloads/LF2_v2.0a.exe` i sprawdzany SHA-256. Można wskazać go parametrem `-Installer`. `-SkipDependencies` służy ponownemu buildowi po przygotowaniu zależności.

Pierwszy serwer FreeType przekierowywał do nieodpowiadającego mirrora. Pobranie z `https://distfiles.macports.org/freetype/freetype-2.13.2.tar.xz` sprawdzono oczekiwanym SHA-256 `12991c4e55c506dd7f9b765933e62fd2be2e06d421505d7950a132e4f1bb484d`. Zweryfikowany plik zapisano w lokalnym cache Conan `engine/build/source-cache/s/` pod nazwą równą sumie. Nie zmieniano wersji biblioteki ani nie wyłączano kontroli TLS/hash.

Pierwszy link ujawnił konflikt CRT (LNK4098): statyczny LuaJIT używał innego CRT niż główny program. Poprawiono własny przepis `engine/conan/luajit/conanfile.py`, aby respektował ustawienia CRT Conan. Końcowy build Release używa /MD; końcowy log linkowania nie zawiera LNK4098.

## Testy

```powershell
.\tools\test_windows_native.ps1 -TigerData '..\games\LF4-Turbo\Little Fighter 4 Turbo\tiger\tiger.dat'
python -m unittest discover -s tests -v
python tools/check_classic.py --engine engine/out/PolishFighters-Windows-x64-portable/openlf2.exe --installer ../downloads/LF2_v2.0a.exe --output-dir validation/windows-native/classic
python tools/smoke_lf4.py --engine engine/out/PolishFighters-Windows-x64-portable/openlf2.exe --installer ../downloads/LF2_v2.0a.exe --output-dir validation/windows-native/lf4
python tools/check_room_game.py --engine engine/out/PolishFighters-Windows-x64-portable/openlf2.exe --installer ../downloads/LF2_v2.0a.exe --output-dir validation/windows-native/room-game
```

Wykonano również warianty `--counts 2,8 --menu`, `--counts 2,8 --pack lf4-turbo` i `--counts 2 --probe`. Testy źródłowe zmieniają ustawienia rosteru/pokoju na czas testu i przywracają je w finally; nie uruchamiać ich równolegle z innymi testami zmieniającymi te pliki ani z grą korzystającą z katalogu źródłowego.

Wyniki w `validation/windows-native/`: 5 natywnych testów C++, 3 zestawy reguł Lua, 9 testów Python zaliczonych / 1 pominięty (Windows nie pozwolił utworzyć symlinka), TCP 2–8 klientów z przerwaniem po rozłączeniu/timeout/niedozwolonym poleceniu, 11 scenariuszy menu/walki, 32 postacie LF4 po 300 klatek, mecze 2–8 procesów po 120 klatek. Oddzielny test gotowej paczki potwierdził oba profile, używając wyłącznie jej danych i skryptów z obcego katalogu roboczego. Wszystkie 975 zasobów LF4 w paczce ma poprawne sumy.

Na potrzeby rzeczywistego importu NTSD podniesiono limit zasobów pakietów z 1024 do 2048. Osobny test akceptuje 2048 i odrzuca 2049; ograniczenia wielkości manifestu, liczby pakietów, skryptów i poprawności ścieżek pozostały zachowane. NTSD pozostało eksperymentalne: 13/42 postaci przeszło smoke test; patrz `content-packs/ntsd/SOURCE.md`.

## Granice

Testy gry wykonano bez okna. Nie potwierdzono ręcznie obrazu, sterowania, dźwięku z urządzenia, pełnych zestawów ciosów, kampanii, fizycznego LAN ani zgodności z Androidem. Bluetooth, konta i mieszanie modów nie są ukończone. R-LF2, Kate, NTSD, DBZ, One Piece i Bleach nie są dołączone jako działające profile. Szczegóły blokad: `validation/windows-native/mod-audit.json`.

Paczka z lokalnymi danymi LF2/modów nie jest publicznym wydaniem. Licencje kodu i bibliotek oraz autorstwo zasobów pozostają zachowane.
