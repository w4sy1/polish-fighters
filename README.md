# Polish Fighters

Własny silnik OpenLF2 z rozszerzeniami Polish Fighters: Windows, źródła Androida, klasyczne i dotykowe sterowanie, izolowane dodatki, lokalna historia i postęp oraz pokoje TCP.

## Pobranie

**Najnowszy kod jest w domyślnej gałęzi `main`.** [Pełna gra Windows i APK Android na Dysku Google](https://drive.google.com/drive/folders/1vcpOvSZaoTbZmctIKFq1myZqGjtew2jV) — [instrukcja pobierania, łączenia części i sumy kontrolne](tools/distribution/GOOGLE-DOWNLOADS.md). To paczki testowe z 11.11.2026; folder Google ma dostęp właściciela do czasu włączenia udostępniania linkiem.

**Starsze wydanie testowe 0.10.0 (2026-11-11): [APK Android i aktualizacja Windows](https://github.com/w4sy1/polish-fighters/releases/tag/fixes-test-2026-11-11).** Wybór pojedynczych modułów i własnej puli, ukrycie powtórzeń LF2, poprawione przejście kampanii, powrót do wyboru modułów oraz ograniczenie samopowielania klonów. [Instrukcja, pliki i wyniki testów](docs/POPRAWKI-0.10-2026-11-11.md). Pełna paczka Windows jest w [poprzednim wydaniu 0.9.0](https://github.com/w4sy1/polish-fighters/releases/tag/mobile-test-2026-11-11); nowy mały ZIP nakłada dziewięć plików Lua. Fizyczny telefon i radio Bluetooth nadal wymagają prób.

Poniżej starsze paczki źródeł i samego silnika:

- [Windows — silnik, DLL i skrypty](artifacts/PolishFighters-Windows-core-2026-10-30.zip). Rozpakuj całość i uruchom `Graj-Polish-Fighters.cmd`. Nie przenoś pojedynczego EXE. Przy braku danych aplikacja zaoferuje pobranie przypiętego LF2; możesz też dostarczyć swój `LF2_v2.0a.exe`.
- [Kod do Android Studio](artifacts/PolishFighters-AndroidStudio-2026-10-30.zip). Otwórz `engine/android` i wybierz Gradle JDK17. [Instrukcja](ANDROID_STUDIO.md).
- [Sumy SHA256](artifacts/checksums.json).

Historia kodu Git nie zawiera importowanych katalogów danych LF2 i modów; `content-packs/*/assets/` pozostają wyłączone przez `.gitignore`. Paczki do grania są osobnymi plikami wydania. Narzędzia importu i pochodzenie zasobów są w repozytorium.

## Co sprawdzono 2026-10-30

Nowy EXE Windows x64 został zbudowany z bieżących źródeł. Poprawiono odczyt arkuszy, przycinanie do istniejących pikseli, niewidoczne cienie na mapie Reinforced o szerokości50000, limit warstw map (do256) i limit muzyki WMA (64MiB; pozostałe zasoby nadal16MiB).

Odzyskano oryginalny obiekt Kate99 z archiwum autora, z akcjami390/392 i25 plikami zależności. Oba wadliwe opoint przeszły natywne próby utworzenia i300 klatek. W Bleach nadal nie odnaleziono obiektów284 i151 z wymaganymi akcjami.

Sprawdzono128 map z katalogów i wbudowaną Lee On Road oraz starty259 zadeklarowanych etapów przygód, po120 klatek. Testy używają stałej postaci QA Deep; przeciwnicy kampanii są z danego dodatku. **117/129 map i170/259 startów etapów przeszło**. To headless: odczyt zasobów, polecenia rysowania i starty; nie ocena obrazu ani pełne przejścia kampanii.

| Profil | Mapy | Starty etapów |
|---|---:|---:|
| LF2 z Lee On Road |13/13|25/25|
| LF4 Turbo |12/12|25/25|
| Bleach |12/12|20/20|
| Kate |11/11|33/33|
| Reinforced |14/14|44/44|
| NTSD |17/17|2/25|
| DBZ |2/14|0/62|
| One Piece |36/36|21/25|

**DBZ, NTSD i część kampanii One Piece pozostają eksperymentalne.** W DBZ brakuje przeniesienia dynamicznych ustawień scen i rozszerzonej numeracji klatek, w NTSD występują liczby poza zakresem32-bit. Nie zastępowano brakującej mechaniki domyślnymi danymi. Nie potwierdzono wyglądu wszystkich animacji, fizycznego LAN/Bluetooth ani działania na telefonie.

Android: Gradle Wrapper i przygotowanie źródeł SDL są dołączone, konfiguracja i kompilacja Java przeszły. Natywne biblioteki Androida i test urządzenia pozostają do wykonania. Lint wykazał problemy, głównie w klasach SDL; nie wyłączono kontroli globalnie. Instrukcja zawiera rzeczywisty pipeline C++ i blokadę pakowania APK bez silnika.

[Pełny raport i lista zmian](validation/maps-build-2026-10-30/REPORT.md), [status](PROJECT-STATUS.md), [budowa Windows](BUILD_WINDOWS.md), [archiwalny opis funkcji](README_PL.md). Kod silnika ma licencję opisaną w [engine/LICENSE](engine/LICENSE); biblioteki w [THIRD-PARTY-NOTICES](engine/THIRD-PARTY-NOTICES.md). Autorstwo zasobów dodatków pozostaje przy ich twórcach.
