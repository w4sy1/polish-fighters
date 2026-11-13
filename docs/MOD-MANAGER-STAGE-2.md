# Mod Manager — etap 2, 2026-11-13 (bez testów)

Kontynuacja lokalnych zmian na `main`, baza `bebc5ce`. Użytkownik polecił nie wykonywać testów i przerwać przy 30% pozostałego limitu. Nie wykonano commitu, push ani publikacji wydania. Nie uruchamiano GUI, downloadera, testów, buildów, lint ani smoke testów. Kontrola zmian polegała na przeczytaniu kodu i `git diff`.

## Wprowadzone funkcje (niezweryfikowane wykonaniem)

- `tools/mod_http.py`: HTTPS, ograniczone odpowiedzi HTML, kontrola przekierowań, blokada lokalnych/prywatnych adresów, respektowanie robots.txt i opóźnień; brak obchodzenia CAPTCHA.
- `tools/mod_sources.py` i `data/mods/sources.json`: adaptery indeksów LF Empire, ModDB, LF Empire Forum i Ultimate Fighters. Na żądanie maksymalnie dwie strony wybranego źródła. Osobne projekty, strony pobrania, odnośniki do dyskusji i kandydaci plików. Bez rekurencyjnego crawlowania, rozwijania skrótów URL i automatycznego łączenia różnych wersji. Autor/wersja/opis tylko tam, gdzie parser znajduje odpowiednie metadane; brak metadanych oznacza null. Nie jest to kompletny scraper każdego układu strony.
- `tools/mod_downloads.py`: kolejka SQLite, jeden worker, historia i błędy, postęp, pauza/wznowienie/anulowanie, trzy próby błędów transportu, kontrola miejsca i limit 1 GiB na paczkę. Wznowienie przez Range/If-Range; restart od początku, gdy brak walidatora lub serwer zwraca 200. Nazwy plików wyznaczane lokalnie; rozpoznawanie ZIP/RAR/7z po nagłówku. SHA-256 wyliczany lokalnie, porównywany z referencją wyłącznie po jawnym przekazaniu `--sha256`. Identyczna zawartość może korzystać z istniejącego pobranego pliku.
- `tools/mod_manager_gui.py`: osobne okno desktopowe, zakładki katalog/źródła/pobieranie, wybór plików przez okno systemowe i izolowany import ZIP istniejącym konwerterem. Bez uruchamiania pobranego kodu. Dane użytkownika pozostają pod ignorowanym `userdata/mod-manager/`.
- `tools/mod_manager.py`: polecenia `sources`, `discover`, `downloads add/list/run/pause/resume/cancel` oprócz istniejącego importu.

## Metadane źródeł

Sprawdzono treść stron internetowych (nie pliki modów) i uzupełniono pięć istniejących wpisów: Reinforced, Naruto LF2 v2.0, Great Fighters 2 oraz DragonBall Super Edition 1.0 i 1.1. Nie wpisano niepotwierdzonych bezpośrednich linków, licencji ani zgodności. Daty `last_verified` dotyczą wyłącznie metadanych strony. Wygenerowano ponownie `mod_catalog.lua`.

Źródła:

- https://www.lf-empire.de/lfe-fileplanet/versions/634-reinforced-little-fighter-2
- https://www.lf-empire.de/lfe-fileplanet/versions/638-naruto-lf2-v20
- https://www.lf-empire.de/lfe-fileplanet/mods/846-great-fighters-2
- https://www.moddb.com/mods/dragonball-super-edition/downloads/super-dragon-ball-version-10
- https://www.moddb.com/mods/dragonball-super-edition/downloads/super-dragon-ball-version-11-full-version

Lista form z artykułu projektu DragonBall Super Edition opisuje inną zapowiadaną wersję, więc nie przypisano jej automatycznie paczkom 1.0/1.1. Suma MD5 podana przez ModDB nie została potraktowana jako SHA-256.

## Użycie (instrukcje; nie wykonano tych poleceń)

Z katalogu repozytorium:

```powershell
.\.build-venv\Scripts\python.exe tools/mod_manager_gui.py
.\.build-venv\Scripts\python.exe tools/mod_manager.py sources
.\.build-venv\Scripts\python.exe tools/mod_manager.py discover lfe --output userdata/mod-manager/source-lfe.json
.\.build-venv\Scripts\python.exe tools/mod_manager.py discover moddb --page 'https://www.moddb.com/mods/dragonball-super-edition'
.\.build-venv\Scripts\python.exe tools/mod_manager.py downloads add --url 'https://ADRES-SERWERA/PLIK.zip'
.\.build-venv\Scripts\python.exe tools/mod_manager.py downloads run
.\.build-venv\Scripts\python.exe tools/mod_manager.py downloads list
.\.build-venv\Scripts\python.exe tools/mod_manager.py downloads pause --id IDENTYFIKATOR-Z-KOLEJKI
.\.build-venv\Scripts\python.exe tools/mod_manager.py downloads resume --id IDENTYFIKATOR-Z-KOLEJKI
.\.build-venv\Scripts\python.exe tools/mod_manager.py downloads cancel --id IDENTYFIKATOR-Z-KOLEJKI
```

Adres w przykładzie jest symbolem zastępczym, nie rzeczywistym linkiem. GUI wymaga Pythona z Tkinter. Wznowienie ustawia zadanie z powrotem w kolejce; należy uruchomić „Pobierz kolejkę”. Kolejka przetwarza migawkę z chwili startu — nowo dodane zadania mogą wymagać ponownego uruchomienia. Po zamknięciu GUI pobieranie zostaje wstrzymane; pracujący wątek może kończyć oczekiwanie sieciowe do upływu timeoutu. Polityka robots może zablokować źródło — wtedy potrzebne jest ręczne otwarcie strony.

## Ograniczenia i wznowienie

To implementacja częściowa i nieprzetestowana. Nie pobrano żadnej paczki, więc nie uznajemy downloadera za potwierdzony. Rozpoznanie nagłówka archiwum nie potwierdza integralności ani bezpieczeństwa całej paczki. SHA-256 bez zaufanej referencji służy tylko identyfikacji. Importer nadal przyjmuje tylko ZIP z dozwolonymi danymi, odrzuca całą paczkę zawierającą EXE/DLL/skrypty; pobrane RAR/7z nie są importowane.

Osobne GUI desktopowe nie jest downloaderem wbudowanym w silnik gry ani aplikację Android. W grze pozostaje przeglądarka katalogu z etapu 1. Integracja GUI gry/Androida, instalacja i aktywacja nowych pakietów, profile, konflikty, aktualizacje/usuwanie i przywracanie, konwersje mechanik i kontrola modów w multiplayerze pozostają do wykonania. Nie przenosić wyników testów etapu 1 na obecne zmiany.

Przy wznowieniu: najpierw aktualny limit i Git, potem przegląd nieprzetestowanego downloadera oraz podłączenie do docelowego GUI. Testy dopiero po cofnięciu przez użytkownika bieżącego zakazu. Bez publikacji niezweryfikowanych zmian.
