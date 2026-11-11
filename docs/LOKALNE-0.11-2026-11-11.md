# Polish Fighters 0.11 — lokalna wersja do sprawdzenia

Raport etapu lokalnego. Następnie użytkownik zatwierdził publikację 0.11 (2026-11-11), tag `guide-updates-test-2026-11-11`. Poniższy opis zachowuje stan i wyniki sprzed publikacji.

Stan: zmiany lokalne na `codex/local-leumas-combo-guide-2026-11-11`, bez nowego commita, push i publikacji. Publiczna wersja 0.10 pozostaje dostępna. Przed następną publikacją użytkownik chciał poznać pomysły na dalsze funkcje.

## Co zmieniono

1. **LeumasEX nie przywołuje żadnych postaci**: zarówno osobny LF4 Turbo (55), jak i wspólna pula (1001). Test natywny: zero potomków, zwykły pocisk nadal powstaje. Rudolf zachowuje ograniczenie trzech kopii bez dalszego rozmnażania. Własne klony SZ pozostają bez zmian.
2. **Poradnik kombosów w grze**: POLISH FIGHTERS → PORADNIK KOMBOSÓW / POSTACIE. Wasyl, SZ, Mega Ninja Jaś, Skibidi Sigma Tata, Remonoko i forma mecha; 42 kombinacje sprawdzone względem rzeczywistych klatek DAT. Podstawy wyjaśniają przyciski działań, kierunki, kolejność, manę i sterowanie dotykowe. Przeglądanie pełnej listy postaci nadal dostępne.
3. **Powiadomienie o nowszej wersji z GitHuba**: Windows i Android sprawdzają przy uruchomieniu listę pięciu ostatnich wydań. Okienko „Pobierz / Później” otwiera stronę pobierania. Nie instaluje plików automatycznie. Brak internetu i limity GitHuba nie zatrzymują gry.
4. Zachowano wcześniejsze poprawki: wybór pojedynczych modułów/wszystkich/własnej puli, filtr powtórek, przechodzenie kampanii i powrót do modułów, kod `polishfighters` na PC oraz ustawienie kodów z komunikatem `lamus` na Androidzie.

**Powtórki:** w próbie wspólnej puli Deep, Firen, Freeze, Dennis, Davis, John, Woody, Henry, Louis i Rudolf występują po jednym razie zamiast trzech. Łącznie 308 → 258 pozycji wyboru. Nie usunięto zasobów ani rekordów obiektów: nadal 947 obiektów i 310 wpisów postaci. Warianty w pojedynczych modułach i możliwość wyłączenia filtra zachowane.

## Aktualizacje — warunki działania

- Wersję 0.11 należy zainstalować raz ręcznie; starsza 0.10 nie zawiera jeszcze powiadomień.
- Nowsze wydanie powinno mieć numer `X.Y.Z` w nazwie lub tagu, np. `Polish Fighters 0.12.0`, oraz ukończony plik `.apk` dla Androida lub `Windows*.zip`/`.exe` dla Windows. Wersje testowe też są uwzględniane, szkice nie.
- Sam push kodu nie oznacza gotowej aktualizacji aplikacji. Numer wersji musi rosnąć. Windows: `scripts/polish-fighters/updates.lua`; Android: Gradle i parametry skryptu budowania.
- Sprawdzenie następuje przy uruchomieniu, nie jest zdalnym powiadomieniem na zamkniętym urządzeniu. Jedno okienko na sesję. Zaufany adres repozytorium jest ustalony w aplikacji.
- Zapytanie anonimowe HTTPS, bez konta i tokenów, w tle, z limitami czasu i odpowiedzi do 512 KiB. Android używa kodu Java; istniejące biblioteki ARM silnika zachowano.

## Pliki

- Logika Leumasa: `content-packs/lf4-turbo/catalog.lua`, `content-packs/mixed-all/catalog.lua`, `engine/scripts/base/game/objects.lua`.
- Poradnik: `engine/scripts/polish-fighters/combo_guide.lua`, `classic_shell.lua`, `hub.lua`, `hub_launch.lua`, `package.manifest`; instrukcja `docs/PORADNIK-KOMBOSOW-2026-11-11.md`.
- Windows: `engine/scripts/polish-fighters/updates.lua`, `updates_flow.lua`, `engine/scripts/base/ui/quit_dialog.lua`, `engine/scripts/runtime/bootstrap.lua`, `engine/include/openlf2/ports/download.hpp`, `engine/src/adapters/curl/account_http.cpp`, `engine/src/adapters/luajit/runtime.cpp`, `engine/src/app/application.cpp`.
- Android: `GitHubUpdates.java`, podłączenie w `BluetoothLobbyActivity.java` i `OpenLF2Activity.java`, `engine/android/app/build.gradle`, `tools/build_android_local.ps1`. ApplicationId, manifest, uprawnienia i podpis bez zmian.
- Próby: `tests/leumas_no_clones_test.lua`, `tests/combo_guide_test.lua`, `tests/updates_test.lua`, `GitHubUpdatesTest.java`, izolacja sieci w dwóch istniejących testach Androida, `tools/check_combo_guide.py`, `probe_combo_guide.py`, `probe_updates.py`, aktualizacja `probe_clone_families.py`.
- Dokumentacja: bieżący raport, `PROJECT-STATUS.md` i `docs/KOREKTY-2026-11-11.md`.

## Sprawdzenia

- Kompilacja Windows: PASS.
- Lua: 33 zestawy testów i składnia 128 plików PASS.
- Python: 51 PASS, jeden SKIP.
- Android: 21 testów jednostkowych/Robolectric PASS, w tym wyświetlenie okienka i otwarcie właściwego adresu.
- Natywny Windows: prawdziwe pobranie listy wydań GitHub, okienko aktualizacji, pobranie/później — 4 PASS; poradnik — 7 stron PASS; kampania — 7 PASS; powrót do modułów — 5 PASS; Leumas/Rudolf — 4 PASS; pule postaci — 4 PASS.
- Lint Androida nadal zgłasza **27 wcześniejszych błędów w generowanych klasach SDL**: 25 MissingPermission, jeden NewApi, jeden UnspecifiedRegisterReceiverFlag. Zero błędów lint w dodanym kodzie aktualizacji. Nie wyłączano kontroli.
- Dowody: `validation/updates-2026-11-11/` oraz próby poradnika w `validation/combo-guide-2026-11-11/`.
- Końcowy APK: build PASS; podpis v1/v2 i ten sam certyfikat PASS; wyrównanie ZIP i ARM64 16 KiB PASS; oba ABI i zależności natywne PASS; CRC PASS. Zweryfikowano SHA256 wszystkich 7798 unikalnych plików danych odpowiadających 15402 ścieżkom logicznym. Skrypty i katalogi paczki zgodne ze źródłami, klasa aktualizacji obecna w DEX.
- Poradnik uruchomiony z danych wyjętych z końcowego pakietu Androida pod silnikiem Windows: siedem stron PASS. To kontrola danych, nie uruchomienie aplikacji Android.
- Pełny ZIP Windows: 15445 plików, CRC PASS, bez zapisów i ustawień użytkownika. Kopie obu paczek w katalogu `outputs` mają zgodne SHA256.

## Gotowe pliki lokalne

- `engine/out/PolishFighters-Android-LOCAL-0.11.apk` — 542705823 bajty, versionCode 11, versionName 0.11.0-local. SHA256 `9999c6c01e0a386beed7354eab53a857673f7b43b9d1509e0b0632ded6b473b8`.
- `engine/out/PolishFighters-Windows-LOCAL-0.11.zip` — komplet gry, 1048460018 bajtów. SHA256 `9aa89d758b03c5774fb4a3a76a15c2dbacbb7022fda444c0c07e60ab21aece56`.
- Rozpakowana gra: `engine/out/PolishFighters-Guide-LOCAL-2026-11-11/LittleFighters.exe`.
- Skrót pulpitu **Polish Fighters** wskazuje nowy EXE. Zachowano ikonę i dotychczasowy katalog ustawień `engine/out/LittleFighters-Heroes-2026-11-06/userdata/common`. Kopia poprzedniego skrótu w katalogu dowodów.
- Paczki, ten raport, poradnik i `SHA256SUMS-LOCAL-0.11.txt` skopiowano do `C:/Users/01dwa/Documents/Codex/2026-11-10/referenced-chatgpt-conversation-this-is-an/outputs`.

## Granice weryfikacji i ryzyka

Brak podłączonego telefonu: nie sprawdzono instalacji nowego APK, dotykowego grania ani fizycznego Bluetooth. Próby kampanii obejmują kontrolowany koniec etapu i sześć form własnych postaci oraz bazowego Deepa; nie są pełnym przejściem wszystkich kampanii. Nowe wydanie GitHuba zasymulowano w testach; prawdziwe połączenie HTTP sprawdzono na obecnych publicznych wydaniach. Istniejące błędy SDL wymagają osobnej naprawy.

Zakres odpowiada kolejce: dokończenie Leumasa i poradnika, następnie aktualizacje. Bez dużego refaktoru, kasowania danych projektu i publikacji.

## Pomysły do wyboru przed następną publikacją

1. Trening z manekinem, paskiem obrażeń i szybkim resetem HP/MP.
2. Podświetlanie kolejnych przycisków kombosa oraz komunikat o brakującej manie.
3. Krótkie wyzwania uczące po trzech ruchach każdej własnej postaci.
4. Ulubione postacie i zapis ostatniej wybranej puli modułów jako gotowego zestawu.

Pomysły nie zostały dodane do bieżącej wersji.
