# Polish Fighters 0.12 — sterowanie i powrót, 2026-11-12

## Zmiany

- Oba układy dotykowe naciskają ATAK od razu, bez oczekiwania na puszczenie palca.
  Przywrócono zachowanie zwykłego przycisku LF2 w układzie joysticka.
  Palec sterujący ruchem nie przejmuje przycisków; palec naciskający przycisk
  nie jest jednocześnie przejmowany przez strefę ruchu. Ruch i atak działają razem.
- F4 i przycisk POSTACIE podczas walki wracają do wyboru postaci, z zachowaniem
  modułu i opcji meczu. Powrót przechodzi przez wejście symulacji. W pokoju
  sieciowym polecenia funkcyjne nadal wysyła gospodarz; pozostali mogą się rozłączyć.
- Ponowny wybór czyści również stare znaczniki gotowości graczy.
- Android uruchamiany po wyborze pojedynczego modułu otwiera menu tej gry,
  bez ponownego pokazywania listy wszystkich modułów. Pełna lista pozostaje dostępna
  przez jawny powrót do modułów. Wspólna pula nadal jest oddzielnym wyborem.
- Android: versionCode 12, versionName 0.12.0-controls. ApplicationId, signing,
  manifest, uprawnienia i zasoby postaci nie były zmieniane.

- Bufor przechowuje krótkie kierunki ruchu i F4 do następnego odczytu klawiszy.
  Nowy kierunek ma pierwszeństwo przed poprzednim; puszczenie nie blokuje ruchu.
  Krótkie F4 jest także zachowane podczas oczekiwania na sieć.

## Weryfikacja

- 42 zestawy Lua i składnia 128 plików: PASS.
- Python: 53 testy, 52 PASS / 1 SKIP (uprawnienia Windows do symlinków).
- Natywny silnik: F4 i kliknięcie POSTACIE kończą na screen=characters,
  a nie na wyborze modułów; poprzednie ready=false: PASS. Obie fazy odczytu klawiszy PASS.
- Natywne próby ruchu i podstawowego ataku: wszystkie 32 postacie LF4 PASS;
  dodatkowo Wasyl, SZ, Mega Ninja Jaś, Skibidi Sigma Tata, Remonoko i Kamienny Mech PASS.
  Przywoływana nieruchoma toaleta 433 jest raportowana osobno; nie jest graczem.
  Obserwacje AI zapisano w logach; nie stanowią pełnego testu wszystkich ataków.
- Sieć: 2 i 8 rzeczywistych procesów Windows po 120 klatek, zgodne skróty stanu: PASS.
- Android: assembleDebug i testDebugUnitTest PASS. Biblioteki ARM64/ARMv7
  odzyskano z wcześniejszego APK i zweryfikowano ich odciski względem źródeł C++.
  Zmiany Lua i wersji APK nie wymagają ponownej kompilacji niezmienionego C++.
- Lint: 27 błędów / 39 ostrzeżeń w generowanych źródłach SDL, jak przed zmianami.
  Kontrola nie została wyłączona. Nie przedstawiamy lint jako zaliczonego.

Powtarzalny test natywny:

```powershell
.\.build-venv\Scripts\python.exe tools/check_controls_back.py --engine engine/out/PolishFighters-LAN-test-2026-11-11/LittleFighters.exe --installer ../downloads/LF2_v2.0a.exe --output validation/controls-back-0.12
```

- Dwa rzeczywiste procesy pokoju: krótkie F4 gospodarza wraca po obu stronach
  do wyboru postaci, ze zgodnym skrótem stanu: PASS.
- Android: 27 testów PASS; CRC i zawartość APK, podpis, wyrównanie 16 KiB i numer wersji PASS.
- Pełny ZIP Windows: CRC PASS; samodzielny start z obcego katalogu bez cache builda PASS.

## Granice i pozostałe zgłoszenie

Użytkownik zgłosił zatrzymywanie postaci również offline. Próby wejść natywnych
nie odtworzyły tego objawu w LF4. Zmieniono potwierdzone problemy sterowania i
powrotu, lecz nie stwierdzono, że wszystkie zacięcia offline zostały naprawione.
Brak podłączonego telefonu: ADB nie wykazało urządzeń. Nie zweryfikowano fizycznego
dotyku, wydajności Androida, pełnych kampanii ani Wi-Fi/Bluetooth między urządzeniami.
Wydanie jest testowe; cały zakres zgłoszenia pozostaje częściowo niezweryfikowany.

## Pliki

Źródła: base/ui/{touch_gamepad,match_screen,flow,character_select}.lua,
polish-fighters/{hub_flow,input_settings,input_buffer,room_network,updates}.lua oraz engine/android/app/build.gradle.
Regresje: tests/{global_menu,touch_layout}_test.lua i tools/check_controls_back.py
wraz z tools/{movement-probe,control-navigation-probe}.

Punkt przywracania źródeł zapisano w baseline-source.zip w katalogu rozmowy.
Zastanych dwóch archiwów w artifacts nie dodawano do commita.

## Publikacja i usunięcie lokalnych wersji

Wydanie: https://github.com/w4sy1/polish-fighters/releases/tag/controls-back-0.12.0-2026-11-12
Kod źródeł wydania: `3826ab22fc4e99fee71bb28665ba3c274b3b7ac1`.
Obie paczki mają zgodne rozmiary i SHA256 w metadanych GitHuba;
pobieranie bez zalogowania sprawdzono żądaniem zakresowym (bez powtórnego
pobierania całych 1,59 GB). Pełne lokalne archiwa wcześniej zweryfikowano.

- `PolishFighters-Android-0.12-2026-11-12.apk`: 542615045 bajtów, SHA256 `1dad757ac698873c2e57713817230090954523f7230dd1b5ffcf122da6729b61`.
- `PolishFighters-Windows-FULL-0.12-2026-11-12.zip`: 1046617302 bajtów, SHA256 `71f402c3a26306f8c026ed4215bd63bdf9c500aeaa10702687bddc7466460fb3`.

Po publikacji do Kosza trafiło 9.33 GiB lokalnych wersji i danych generowanych
oraz dwa nieaktualne skróty. Kosza nie opróżniono. Źródła, zasoby modów i prywatne
ustawienia pozostały; ustawienia wersji przenośnej skopiowano i sprawdzono hashami
w `userdata/build-cleanup-20261112-0.12`. Zastane dwa ZIP-y w `artifacts` pozostały.
Do powtórzenia prób natywnych po sprzątaniu należy pobrać ZIP wydania
i podać ścieżkę rozpakowanego EXE jako `--engine`; lokalne `engine/out` jest puste.
