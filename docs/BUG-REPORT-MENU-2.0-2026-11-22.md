# Przebudowa menu kontaktowego i formularza zgłaszania błędów -- 2026-11-22

Realizacja zadania "Polish Fighters -- naprawa i przebudowa systemu kontaktu, Discorda i
zgłaszania błędów" (poza punktem Bluetooth na Windows, który czeka osobno). Patrz też
`docs/CRASH-REPORTER-1.1-2026-11-22.md` -- automatyczny crash reporter jest osobną,
niezmienioną funkcją.

## Co było nie tak (stan przed zmianą)

Menu "TWÓRCY" miało 4 wiersze (DISCORD / ZGŁOŚ BŁĄD E-MAIL / ZGŁOŚ BŁĄD DISCORD / WSTECZ), a
licencje/autorzy silnika wyświetlały się jako statyczny tekst pod tymi samymi wierszami, bez
osobnego podmenu. Prosty formularz zgłoszenia błędu na Discordzie był jednym polem tekstowym i
wysyłał się **prosto z klienta gry na webhook Discorda** -- co wymagało, żeby każdy build (Windows
i Android) miał wpisany realny URL webhooka (`OPENLF2_DISCORD_WEBHOOK_URL` / Gradle property). Bez
tego gracz widział `Brak konfiguracji webhooka Discord (OPENLF2_DISCORD_WEBHOOK_URL)` -- błąd #2 z
listy zgłoszeń. To też znaczyło, że webhook był (musiał być) częścią tego, co trafia do każdego
builda klienta -- sprzecznie z wymogiem "nigdy nie umieszczaj webhooka w APK/EXE/kliencie".

## Co się zmieniło

### Architektura: webhook przeniesiony na serwer

Zamiast klienta rozmawiającego z Discordem, zgłoszenie idzie teraz tą samą drogą co konta i
pokoje online:

```
Gra (Android/Windows) --HTTPS--> account_service.py / passenger_wsgi.py (operacja "bug-report")
    --walidacja, numeracja, rate-limit-- --webhook Discord-- #błędy
```

- Nowa operacja `bug-report` w `tools/account_service.py` (`Service._submit_bug_report`), używana
  przez lokalny serwer deweloperski i przez `server/passenger_wsgi.py` (hosting współdzielony) --
  to jest ten sam plik serwisowy co dla kont/pokoi, więc nic nowego nie trzeba wdrażać.
- Webhook (`OPENLF2_DISCORD_WEBHOOK_URL`) jest teraz czytany **wyłącznie z środowiska procesu
  serwera** (`send_discord_webhook` w `account_service.py`). Klient go nie zna, nie wysyła, nie ma
  go w kodzie, w APK, w EXE ani w repozytorium.
- Klient (silnik C++, `engine/src/adapters/luajit/runtime.cpp` + `account_http.cpp`) woła
  `engine.report_bug('start', endpoint, json)`, co pod spodem jest tym samym `account_post()`, co
  logowanie/pokoje -- tylko z operacją `"bug-report"` dodaną do białej listy w `account_http.cpp`.
  Usunięto `engine/include/openlf2/engine/bug_report.hpp`, `engine/src/engine/bug_report.cpp` i
  `tests/bug_report_test.cpp` (ten plik nie był zarejestrowany w żadnym skrypcie testowym --
  kompilowany ręcznie g++, jak opisano w `CRASH-REPORTER-1.1`), bo cała logika formatowania
  wiadomości i wysyłki przeniosła się na serwer (Python).

### Numeracja, idempotencja, rate-limit (sekcja 7-8-9 zadania)

- Numer zgłoszenia `PF-BUG-NNNNNN` to autoincrement SQLite (`bug_reports.id`), generowany pod tym
  samym `self.lock`, co resztę serwisu -- unikalny przy równoczesnych zgłoszeniach.
- Klient generuje losowy `client_ref` (nie z deterministycznego RNG rozgrywki -- z
  `engine.crt_random()`) raz na szkic zgłoszenia i wysyła go z każdą próbą. Powtórzona wysyłka z
  tym samym `client_ref` (np. po błędzie sieci) dostaje ten sam numer i **nie** trafia drugi raz na
  Discord (`sent` flag w tabeli `bug_reports`).
- Dedykowany limit: maksymalnie 5 zgłoszeń na 10 minut z jednego adresu IP, niezależnie od ogólnego
  limitu API (30-120/min, już istniejącego w `account_service.py`/`passenger_wsgi.py`).
- `@everyone`, `@here` i `<@id>` w treści gracza są neutralizowane (zero-width space) przed
  wysłaniem -- nie da się tym zgłoszeniem zrobić mass-pingu na kanale.
- Dane wrażliwe (`token:`, `password:`, `Bearer ...`, gołe adresy URL) są redagowane z treści przed
  złożeniem wiadomości -- ten sam rodzaj redakcji co natywny crash reporter, tylko po stronie
  Pythona (`_redact_bug_report_text`).

### Menu kontaktowe (sekcja 4)

`hub.lua` / `hub_launch.lua`: menu "TWÓRCY" ma teraz **5** wierszy zgodnie ze specyfikacją:

1. **TWÓRCY I INFORMACJE O PROJEKCIE** -- nowe podmenu (`credits_info`), z silnikiem
   OpenLF2/Marti Wongiem i Starsky Wongiem, odnośnikiem do dokumentacji pakietów
   (`content-packs/`) i do listy współtwórców na GitHub -- bez przypisywania czyjegoś autorstwa
   zespołowi Polish Fighters i bez usuwania istniejących informacji licencyjnych.
2. DISCORD (link do serwera -- bez zmian).
3. ZGŁOŚ BŁĄD (E-MAIL) -- bez zmian (`mailto:prestigetechkoszalin@gmail.com`).
4. ZGŁOŚ BŁĄD (DISCORD) -- teraz pełny formularz, patrz niżej.
5. WSTECZ.

### Formularz zgłoszenia (sekcja 5-6)

`engine/scripts/polish-fighters/bug_report_screen.lua` to teraz formularz z polami: **kategoria**
(14 kategorii z zadania, przełączana kliknięciem), **nick** (auto z ustawień, edytowalny,
opcjonalny), **tytuł**, **opis błędu**, **kroki odtworzenia** (opcjonalne) -- bez wymogu konta.
Serwer zawsze dostaje też automatycznie: platformę (android/windows), wersję gry, aktywny moduł
(`catalog.profile_id`). Serwer zwraca numer zgłoszenia, wyświetlany graczowi po wysłaniu.

## Czego NIE zrobiono w tej wersji (świadomie, nie "na pewno działa")

- **Zrzut ekranu i prawdziwe logi diagnostyczne nie są dołączane.** Zadanie prosiło o opcjonalny
  zrzut ekranu i logi -- to wymagałoby nowego kodu przechwytywania/kodowania obrazu po stronie
  silnika C++/Androida i multipart-upload po stronie serwera, którego nie da się bezpiecznie
  domyślić bez większej, osobnej zmiany w już niestabilnym miejscu (ekran menu). Serwer i tak
  zawsze wysyła platformę/wersję/moduł (to są podstawowe dane, nie wymagają zgody z sekcji 6).
- **Multiplayer/discord webhook dla automatycznego crash reportera nie został przeniesiony.** To
  osobna funkcja (`docs/CRASH-REPORTER-1.1-2026-11-22.md`), nadal łącząca się z Discordem prosto z
  klienta (`OPENLF2_DISCORD_WEBHOOK_URL` na Windows, `BuildConfig.DISCORD_WEBHOOK_URL` na
  Androidzie). Zostawiono nietkniętą, żeby nie poszerzać zakresu tej zmiany -- jeśli ma to też
  przejść przez serwer, to osobne zadanie.
- **Format osadzony w Discordzie jest tekstem, nie "Embed" w sensie Discord API** -- prostszy,
  czytelny format tekstowy (patrz `_format_bug_report_message` w `account_service.py`), przycinany
  do limitu 2000 znaków Discorda bez wysyłania pliku-załącznika.

## WERYFIKACJA -- co faktycznie uruchomiono tutaj

- `tests/test_account_service.py` (nowa klasa `BugReportTest`, 9 przypadków): numeracja, retry
  idempotentny, odrzucenie nieznanej kategorii, odrzucenie zbyt długich pól, rate-limit per-IP,
  neutralizacja @everyone/@here/mentions, redakcja sekretów, błąd przy braku skonfigurowanego
  webhooka -- **bez żadnego realnego połączenia sieciowego** (wstrzyknięty `send_discord`). 18/18
  testów w tym pliku, łącznie ze wszystkimi wcześniej istniejącymi (kontami/pokojami), przechodzi.
- `python3 tools/test_lua_scripts.py`: 132/132, w tym `classic_menu_test.lua`, `global_menu_test.lua`,
  `hub_input_test.lua`, `content_menu_test.lua` -- menu z nowym 5-wierszowym "TWÓRCY" i nowym
  podmenu nie psuje istniejącej nawigacji/testów.
- `tests/test_classic_menu_assets.py`, `tests/test_android_bundle.py`, `tests/test_bundle_contract.py`:
  przechodzą; `classic-menu.json` zregenerowany (`tools/generate_classic_menu_assets.py`) z dwoma
  nowymi kluczami (`credits_info`, `credit_authors`) identycznymi w `pl`/`en`.

**Nie zweryfikowano tutaj** (ten sandbox nie ma ani Windows/MSVC, ani Android NDK/Gradle, ani
realnego serwera z prawdziwym webhookiem -- tak samo jak w `CRASH-REPORTER-1.1`):

- Że `engine/src/adapters/luajit/runtime.cpp` i `account_http.cpp` faktycznie się kompilują --
  zmiana w `report_bug_operation` jest wiernym odwzorowaniem już kompilującego się
  `account_operation` (ten sam wzorzec `std::async`/`account_post`), ale nie było tu
  zestawionego `DEPS/` (LuaJIT/SDL3/curl) do realnej kompilacji -- patrz `BUILD_LOCAL.md`.
  **Do zrobienia przed wydaniem**: `tools/manual_linux_build.py` albo pełny build Windows/Android.
- Rzeczywistego końcowego wysłania z gry (Android/Windows) przez realny serwer na prawdziwy kanał
  Discord.
- Testy integracyjne backendu na hostingu docelowym (`server/passenger_wsgi.py` pod Passenger).

## Konfiguracja webhooka -- WYMAGANA AKCJA ADMINISTRATORA

**To jest to miejsce, gdzie trzeba wpisać prawdziwy URL webhooka Discorda -- i tylko to miejsce.**
Webhook nie jest już nigdzie w kliencie (nie w Gradle, nie w zmiennej środowiskowej do builda
Windows) -- jest wyłącznie zmienną środowiskową procesu serwera:

- **Lokalny serwer deweloperski** (`tools/account_service.py` / `server/Start-LocalServer.ps1`):
  ustaw `OPENLF2_DISCORD_WEBHOOK_URL` w środowisku przed uruchomieniem, np.
  `$env:OPENLF2_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/.../..."` (PowerShell) albo w
  pliku `.env` obok serwera (już objęte istniejącym wzorcem `.gitignore` dla `.env`/`.env.*`).
- **Hosting docelowy pod `server/passenger_wsgi.py`** (Passenger/cPanel -- ten sam serwer, który
  już obsługuje konta/pokoje pod `projektocalenie.pl/projekty/polish-fighters/api`): zmienną
  środowiskową ustawia się w panelu hostingu (np. w cPanelu "Setup Python App" -> Environment
  Variables), **nigdy** w pliku w repozytorium. Jeśli nie wiesz, czy ten endpoint jest już
  wdrożony -- `server/README_PL.md` mówi, że publiczna usługa nie była wdrożona; jeśli to się
  zmieniło, webhook trzeba dodać tam, gdzie faktycznie stoi ten proces.

Bez tej zmiennej serwer odpowiada błędem (`Brak konfiguracji webhooka Discord
(OPENLF2_DISCORD_WEBHOOK_URL) po stronie serwera`), a gracz widzi to jako komunikat błędu serwera
-- nic nie trafia do Discorda, nic się nie wywala w grze.
