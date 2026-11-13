# Mod Manager — etap 1, 2026-11-13

Stan bazowy: `bebc5ce`, gałąź `main`. Praca przerwana po wykorzystaniu około 10 punktów procentowych limitu. To częściowe wdrożenie, bez publikacji i bez testów urządzeń.

## Dostępne funkcje

- MODUŁY → KATALOG MODÓW: 103 pozycje wymienione w specyfikacji, kategorie, wyszukiwarka, strony po 7 wpisów i karty PL/EN. Zbiorcza pozycja NTSD Community Seasons 1–7 pozostaje jednym wpisem, bez zgadywania metadanych poszczególnych sezonów.
- Kanoniczny rejestr `data/mods/catalog.json`; brak potwierdzonych danych zapisany jako null lub stan nieprzetestowany. Wygenerowana kopia Lua nie wymaga parsera JSON w silniku.
- CLI: analiza lokalnego ZIP bez instalacji oraz konwersja do nowego, odizolowanego pakietu istniejącym importerem LF2. Import nie aktywuje pakietu ani nie zmienia danych podstawowych.
- ZIP: ograniczenia rozmiarów/liczby plików/stopnia kompresji, kontrola miejsca, odrzucanie traversal, kolizji nazw Windows, symlinków, plików specjalnych, szyfrowania i kodu wykonywalnego. CRC podczas ekstrakcji, SHA-256 jako identyfikator (nie dowód zaufania), usuwanie katalogu tymczasowego po błędzie.

## Użycie z katalogu repozytorium

```powershell
.\.build-venv\Scripts\python.exe tools/mod_manager.py list --query Naruto
.\.build-venv\Scripts\python.exe tools/mod_manager.py inspect 'C:\paczki\mod.zip'
.\.build-venv\Scripts\python.exe tools/mod_manager.py import 'C:\paczki\mod.zip' 'C:\paczki\nowy-mod' --id moj-mod
.\.build-venv\Scripts\python.exe tools/generate_mod_catalog.py
```

Katalog nadrzędny celu musi istnieć; sam cel nie może istnieć. Import wymaga dokładnie jednego `data/data.txt`. Obsługiwane są wyłącznie ZIP-y z dozwolonymi plikami danych. Paczki z EXE/DLL/skryptami są w całości odrzucane, nawet jeśli zawierają też zasoby. Brak obsługi RAR/7z i patchy EXE. Wyszukiwanie w GUI przyjmuje obecnie znaki ASCII; dane o autorach i postaciach będą przeszukiwane po ich zweryfikowaniu i uzupełnieniu.

## Walidacja i ograniczenia

Nowe testy Python: 8 PASS (zagrożenia ZIP, pełny import syntetycznej paczki i wycofanie błędu). Istniejący importer: 8 PASS. Lua: składnia 139 plików PASS, test przeglądarki i preferencji pakietów PASS. Pełny przebieg Lua wymagał aktualizacji oczekiwanej liczby akcji biblioteki z 5 na 6 po dodaniu katalogu; końcowo wszystkie 44 zestawy Lua PASS.

Bez budowy EXE/APK, wizualnej kontroli uruchomionej gry, fizycznych urządzeń, pobierania prawdziwych modów, testowania mechanik i multiplayera. Syntetyczny test importu nie potwierdza kompatybilności rzeczywistych modów.

## Następny etap

1. Zweryfikować źródła i linki, dodać adaptery katalogów i downloader na żądanie.
2. Podłączyć bezpieczny import do GUI Windows/Android; CLI nie jest jeszcze funkcją importu w grze.
3. Dodać stan instalacji, profile, konflikty, aktywację/wyłączanie i przywracanie.
4. Przetestować rzeczywiste legalne paczki, zgodność mechanik i sesji sieciowej.
5. Dopiero po realizacji i walidacji kolejnych etapów przygotować nowe wydanie GitHub i sprzątnąć zbędne wyniki budowy.
