# Content Pack: audyt migracji (Punkt 3) i wielokrotny wybór pobierania (Punkt 4) — 2026-11-22

Stan bazowy: `v0.18.21` na `main`. Zakres zgodny z pierwotnym zleceniem: Punkt 3 (migracja
`mods/` → Content Pack), Punkt 4 (ekran z wielokrotnym wyborem Content Packów). Punkt 5
(restyle) nie wymagał osobnych zmian — patrz niżej.

## Punkt 3 — audyt migracji (bez zmian kodu)

`mods/catalog.json` + `mods/catalog.sig` to nie osobne źródło modów, a **wygenerowany,
podpisany indeks** budowany przez `tools/build_mod_release.py` wprost z `content-packs/<id>/`.
Każdy z 9 modów (`polish-originals, lf4-turbo, dbz, one-piece, kate, reinforced, ntsd, bleach,
mixed-all`) już jest pełnoprawnym Content Packiem (`package.manifest` z `id/version/requires/
asset=/extend=`). `engine/src/adapters/curl/github_mods.cpp` instaluje pobraną paczkę jako
`content-packs/<id>/package.manifest` — identycznie jak paczka dodana ręcznie. ID/wersje/URL-e
są zachowane (deterministyczne, nigdy nie nadpisywane wstecznie), already-installed jest już
wykrywane bez ponownego pobierania (`.github-install` receipt, `github_mod_receipt()`).

**Wniosek: migracja była już zrobiona wcześniej. To jest raport z weryfikacji, nie nowy kod.**

Co nie działa (nie dotknięte, bo to osobny zakres — zob. AGENTS.md o zmianie ID):
13 "optional" ID (`dragon-ball-super, fighter-hero, gf2, lf2-ns, sx2, lf2-sv, rn-lf2, lf-seed,
wlf2-al, ce-lf2, ntsd-community, ntsd-ce-setup, killer-lf2`) są zaszyte w `application.cpp`,
`GamePackSettings.java` i `build_mod_release.py::PACKS`, ale nie mają katalogu
`content-packs/<id>/` ani wpisu w `mods/catalog.json`. To przygotowany szkielet pod przyszły
katalog 103 modów (`mod_browser.lua`/`mod_catalog.lua`), nie usunięty — próba ich pobrania kończy
się kontrolowanym błędem, nie crashem.

Nie zweryfikowano bitowo payloadów `content-packs/*/assets/` — gitignorowane, pobierane poza
repo (`tools/distribution/GOOGLE-DOWNLOADS.md`), niedostępne w tej sesji.

## Punkt 4 — wielokrotny wybór do pobrania (nie do grania)

Ustalone z użytkownikiem: te mody to pełne, wzajemnie wykluczające się konwersje — jedna aktywna
na raz (`catalog.profile_id`). "Wielokrotny wybór" dotyczy więc **pobierania na zapas**, nie
jednoczesnego grania kilkoma naraz. Aktywację pojedynczego moda obsługuje istniejący, niezmieniony
mechanizm (`mod_browser.lua`/`AndroidModsActivity.showPackages`).

### Windows / wspólny kod (`engine/scripts/polish-fighters/mod_browser.lua`)

Nowy tryb "ZAZNACZ WIELE" w ekranie GitHub: kliknięcie paczki z akcją POBIERZ/AKTUALIZUJ
zaznacza ją w kolejce (`[X]`/`[ ]`) zamiast pobierać od razu. "POBIERZ ZAZNACZONE (N)" uruchamia
kolejkę — jedna paczka na raz, z dotychczasowym per-item progresem (`github_poll`), automatycznym
przejściem do następnej po zakończeniu poprzedniej. Kolejka jest trwała (`engine.read_settings`/
`write_settings`, klucz `little_fighters_prefetch`) — przerwanie sieci lub restart gry w trakcie
serii pomija już zainstalowane pozycje przy ponownym uruchomieniu kolejki (odporność na zerwanie
sieci bez dodatkowego stanu resume — po prostu porównuje receipt). Domyślne zachowanie (klik =
od razu pobierz) jest niezmienione, gdy tryb multi jest wyłączony — zero regresji.

### Android (`AndroidModsActivity.java`, `GamePackSettings.java`)

Ekran pierwszego uruchomienia (`FIRST_SETUP`) ma nową sekcję "POBIERZ NA ZAPAS" — checkboxy nad
pełnym katalogiem, niezależne od istniejącej logiki bazowego profilu/wspólnej puli (zero zmian w
`missingSetupPacks`/`usesMixedPool`/`saveSetup`). "POBIERZ ZAZNACZONE PACZKI (N)" pobiera
sekwencyjnie z etykietą "Pozycja i z N", korzystając z istniejącego resumable download
(`AndroidModSources.download`, Range). Wybór zapisywany natychmiast (`GamePackSettings.
savePrefetchQueue`) przed startem pobierania — zabicie procesu w trakcie serii i powrót na ten
ekran naturalnie pomija już zainstalowane pozycje. Nowy przycisk "POMIŃ POBIERANIE" na ekranie
pierwszego uruchomienia startuje grę od razu na LF2 Classic.

### Punkt 5 — restyle

Nie wymagał osobnych zmian: nowe elementy korzystają z już istniejącego systemu wizualnego
jeden-do-jednego — Lua renderuje przez generyczną pętlę `screen.draw`/`screen.rows` (ten sam font
bitmapowy, te samo hover-highlight co każdy inny wiersz tego ekranu), Android przez istniejące
`ClassicButton`/`action()`/`label()` (ten sam font pikselowy, te same kolory NAVY/BLUE/TEXT).

## Testy

- `python3 tools/test_lua_scripts.py` — **151/151 plików składnia PASS**, **91/91 testów PASS**
  (żadnej regresji w istniejących testach, w tym `mod_browser_test.lua`).
- Dodano do `tests/mod_browser_test.lua`: test nowej kolejki multi-select — toggle, trwałość
  (`engine.write_settings`), checkbox w etykiecie, automatyczne przejście do następnej pozycji po
  zakończeniu poprzedniej, zatrzymanie po wyczerpaniu kolejki. **PASS.**
- **Nie zbudowano i nie odpalono na Windows/Android.** Brak w tej sesji dostępu do Android SDK/
  realnego urządzenia (sesja bez podłączonego folderu/urządzenia). Zmiana w `AndroidModsActivity.
  java`/`GamePackSettings.java` jest niezweryfikowana kompilacją ani uruchomieniem — tylko
  przeglądem kodu i równowagą nawiasów. Przerwana sieć w trakcie serii pobierania (realny
  scenariusz z Punktu 4) nie została przetestowana na żywym urządzeniu — zweryfikowana tylko
  logicznie (receipt-based skip) i przez symulację w teście Lua powyżej.
- Weryfikacja wizualna LF2-stylu (dotyk, widoczność fokusu klawiaturą na Androidzie i Windows) —
  **niezweryfikowana**, wymaga realnego urządzenia.

## Pozostało do zweryfikowania na realnym sprzęcie

1. Build Windows + APK Android z tymi zmianami.
2. Faktyczne kliknięcie przez multi-select na obu platformach, w tym rzeczywiste przerwanie sieci
   w trakcie serii pobierania i wznowienie.
3. Kontrola dotykiem i fokusem klawiatury (Punkt 5).
4. `git diff`, `git status`, sekrety — sprawdzone w tej sesji, czyste.
