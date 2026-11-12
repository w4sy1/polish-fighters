# Polish Fighters — aktualna wersja

Najnowszy kod jest w domyślnej gałęzi `main`. [Pełna gra Windows i APK Android](https://drive.google.com/drive/folders/1vcpOvSZaoTbZmctIKFq1myZqGjtew2jV) są na Dysku Google. [Instrukcja i sumy kontrolne](tools/distribution/GOOGLE-DOWNLOADS.md). Folder Google ma dostęp właściciela, dopóki właściciel nie włączy udostępniania linkiem.

Poniżej zachowana historia wcześniejszych wydań.

---
# Polish Fighters — wydanie testowe 0.10.0, 2026-11-11

[Pobierz nowe APK i aktualizację Windows](https://github.com/w4sy1/polish-fighters/releases/tag/fixes-test-2026-11-11).
Pięć poprawek: wybór modułów, filtr powtórzeń, ruch NPC do wyjścia kampanii,
powrót do modułów bez zamykania aplikacji i zablokowanie rekurencji klonów.
Na telefonie: **USTAWIENIA → Włącz kody → Zapisz**; po włączeniu pojawia się „lamus”.
Na PC nadal działa kod `polishfighters`. Bluetooth wymaga dwóch sparowanych telefonów
z tym samym APK. [Instrukcja i wyniki](docs/POPRAWKI-0.10-2026-11-11.md).
Build i testy lokalne przeszły; radio Bluetooth, instalacja i dotyk na urządzeniach
pozostają do sprawdzenia. Lint zgłasza 27 wcześniejszych błędów w klasach SDL.

Poniżej zachowana historia wcześniejszych etapów.

# Polish Fighters 0.6: oryginalne menu i LF4 Turbo

Wspólna baza OpenLF2 dla Androida i Windows. Zbudowano pełny silnik Linux x86_64 oraz lokalne wydanie testowe Windows x64. APK Android pozostaje niezbudowane. Nowy pokój LAN jest połączony z menu, wyborem postaci i symulacją meczu. Testy wykonano na osobnych procesach Linux i Windows, jeszcze bez fizycznych telefonów.

## Lokalne wydanie testowe Windows — 2026-10-25

W folderze `engine/out/PolishFighters-Windows-x64-portable` uruchom `Graj-LF2.cmd` albo `Graj-LF4-Turbo.cmd`. Paczka zawiera własny silnik, biblioteki DLL, skrypty, dane LF2 i izolowany pakiet LF4. Nie wymaga Pythona do grania. Są to lokalne pliki testowe, bez publikacji i bez instalatora systemowego.

Przeszło 11 scenariuszy menu/walki, 32/32 postacie LF4 po 300 klatek oraz mecze 2–8 osobnych procesów Windows. Sprawdzono też lobby i wybór postaci dla 2/8 procesów, LF4 dla 2/8 i przerwanie po desynchronizacji. Oba profile uruchomiono z danych gotowej paczki, z innego katalogu roboczego. Są to testy automatyczne bez okna: wygląd, dźwięk z głośników, sterowanie i fizyczne urządzenia wymagają sprawdzenia.

Wyniki: `validation/windows-native/`. Odtwarzanie budowy: `BUILD_WINDOWS.md`. Stan całego projektu: `PROJECT-STATUS.md`.

## Podgląd

Otwórz `preview/Polish_Fighters_klasyczne_menu.html` w przeglądarce. Zawiera rzeczywiste zrzuty oryginalnego menu, klasycznych dodatków oraz LeumasEX podczas walki. Klikalne obszary służą przeglądaniu interfejsu; HTML nie uruchamia silnika ani uwierzytelniania.

Przywrócono oryginalne tło, logo, pionowe menu, czcionki i podświetlenia LF2. Dodatki otwiera się przez napis pod menu lub F10. Escape zamyka dodatkowe panele. Odrzucony dashboard z kafelkami usunięto z aktywnego projektu. Domyślny język `default` zachowuje oryginalną grafikę napisów; tłumaczenia można wybrać w opcjach.

## Stan funkcji

| Funkcja | Stan |
|---|---|
| Klasyczne menu LF2 | Działa; zrzut z renderera silnika |
| Klasyczne dodatki: mapy, pakiety, konto, połączenia | Działają panele i nawigacja |
| Zapis areny i ustawienia limitu 2–8 | Działa lokalnie |
| LF4 Turbo | Dołączony przekształcony pakiet danych, uruchamiany jako osobny profil |
| LeumasEX | Potwierdzony ID 55, 300 klatek symulacji i renderowana walka |
| 32 z 32 postaci LF4 | Przeszły po 300 klatek na własnym silniku Linux; nie jest to test wszystkich ciosów |
| Tiger | Działa na własnym silniku: 300 klatek symulacji i renderowana walka po 85 klatkach |
| Pokój 2–8 | Lobby, gotowość, wybór postaci i mecz; testy 2–8 osobnych procesów gry |
| Sieć gry | Nowy pokój LAN, po jednym graczu na urządzenie; zachowano stare połączenie dwóch urządzeń |
| Bluetooth, lista pokoi, zaproszenia | Niezrealizowane |
| Google / e-mail / synchronizacja | Usługa kont niepodłączona; menu nie pobiera danych logowania |
| Mieszanie modów | Niezrealizowane; importer zachowuje oryginalne ID w osobnym profilu |
| R-LF2, Kate, Naruto, DBZ, One Piece, Bleach | Jeszcze niedodane |
| Postacie dzieci | Czekają na materiały |

## Uruchomienie ze źródeł

Potrzebny Python 3.10+, gotowy zgodny OpenLF2 i własny instalator LF2 v2.0a. Dane klasycznej gry są odczytywane przez silnik z instalatora; nie dołączono tego instalatora ani oryginalnego pliku wykonywalnego LF4.

```powershell
python tools/pf.py launch --engine "C:\gra\openlf2.exe" --installer "C:\gra\LF2_v2.0a.exe"
python tools/pf.py launch --engine "C:\gra\openlf2.exe" --installer "C:\gra\LF2_v2.0a.exe" --pack lf4-turbo
```

Druga komenda dołącza `content-packs/lf4-turbo`. Interfejs pakietów informuje, który profil jest aktywny; przełączanie profilu w uruchomionym procesie i wybór profilu na Androidzie wymagają dalszej integracji. Wszystkie postacie są w pakiecie, ale ukryte wymagają odblokowania zgodnie z zasadami silnika. `settings.lua` umożliwia plikową listę dopuszczonych postaci; domyślnie nie ogranicza katalogu.

Bazowy gotowy OpenLF2 v1.1.1 posłużył do testów. Tiger wymaga własnego silnika z dołączoną poprawką C++; wykonano już taką kompilację Linux i test walki. Wszystkie mechaniki zależne od zmodyfikowanego LF4T.exe wymagają osobnego audytu zgodności. Nie potwierdzono wszystkich przemian, sekretów, etapów ani kombinacji.

## LF4 Turbo: dane i poprawki

Źródło pobrania: https://naszthearcher.itch.io/little-fighter-4-turbo

Importer (`tools/import_legacy.py`) tworzy izolowaną przestrzeń zasobów, zachowując identyfikatory obiektów. Pakiet zawiera 32 postacie, 100 obiektów, 12 wpisów aren oraz 975 zasobów. Nie uruchamia i nie kopiuje EXE/DLL. Wymaga Pillow do kontroli arkuszy BMP.

```sh
python tools/import_legacy.py /sciezka/do/rozpakowanego/moda /nowy/folder --id moj-pakiet
```

Zmiany zgodności:

- Opisowe nazwy klatek dłuższe niż 19 znaków skrócono, zachowując numery klatek, ciosy i ich parametry.
- Trzem arkuszom brakowało 1–2 pikseli do deklarowanej siatki. Dodano czarne krawędzie, bez usuwania istniejących pikseli. Pozwoliło to wyrenderować walkę LeumasEX poza początkowym miganiem postaci.
- 64 większe rozbieżności zapisano w `content-packs/lf4-turbo/sprite-edge-repairs.json`; nie naprawiano ich automatycznie. Mogą dotyczyć niewykorzystywanych komórek, ale wymagają testów wszystkich efektów i animacji.
- Czytnik Tigera obsługuje do 16 obszarów trafienia/brył na klatkę zamiast pięciu. Test przyjmuje 16 i odrzuca 17. Nie wyrzucano dodatkowych ciosów.

Licencja MIT kodu OpenLF2 nie obejmuje zasobów LF2 i modów. Autorstwo i źródło zawarto w `content-packs/lf4-turbo/SOURCE.md`. Jest to eksperymentalny pakiet zgodności danych, a nie oficjalne wydanie LF4 Turbo.

## Sieć: minimum 2, maksimum 8 urządzeń

`engine/include/openlf2/engine/room.hpp` i `engine/src/engine/room.cpp` definiują wspólne reguły pokoju:

- Limit 2–8, odmowa startu dla jednego uczestnika i odmowa przekroczenia pojemności.
- Zgodność profilu danych, gotowość wszystkich graczy i start przez gospodarza.
- Osobny slot dla każdego uczestnika i bariera wejść przed zatwierdzeniem klatki.
- Kontrola numeracji, duplikatów, sum kontrolnych oraz przerwanie przy rozłączeniu lub rozbieżności stanu.

Test C++ uruchamia po 60 klatek dla każdej liczby logicznych uczestników od 2 do 8. NIE jest to test połączenia ośmiu telefonów. Dodano adapter wielu gniazd oraz obsługę rozłączeń i timeoutów. Wersja 0.6 podłącza menu i wejścia meczu. Pozostają optymalizacja opóźnień oraz testy fizycznych urządzeń. Bluetooth również wymaga adaptera.

W źródle aplikacji rozszerzono odcisk profilu o skróty plików zasobów. Zmiana została skompilowana i sprawdzona w rzeczywistych handshake dwóch procesów gry: zgodne procesy łączą się, starszy silnik i różniący się zasób są odrzucane. Profil obejmuje też natywny kod C++ i jest generowany zgodnie przez CMake oraz lokalny przepis.

## Weryfikacja

- `validation/classic/results.json`: 11 scenariuszy menu, powrotów, ustawień, limitu i klasycznej walki.
- `validation/lf4/all-fighters.json`: 31/32 postaci, po 300 klatek. Błąd Tigera z gotowego silnika zachowano w logu; poprawiony natywny parser sprawdzono osobno.
- `preview/classic-*.png`: rzeczywiste widoki z renderera Linux/software.
- `preview/leumas-lf4.png`: rzeczywista renderowana walka po 85 klatkach.
- Testy narzędzi Python, reguł Lua, natywnego loadera pakietów, pokoju i parsera obszarów trafienia.

```sh
python -m unittest discover -s tests -v
texlua tests/roster_test.lua .
texlua tests/random_test.lua .
texlua tests/dashboard_model_test.lua .
python tools/check_classic.py --engine /sciezka/do/AppRun --installer /sciezka/do/LF2_v2.0a.exe

g++ -std=c++23 -Wall -Wextra -Werror -I engine/include tests/room_test.cpp engine/src/engine/room.cpp -o room-test
./room-test
```

Nie wykonano testów na Androidzie ani fizycznych padach. Wykonano pełne lokalne kompilacje zmodyfikowanego silnika Linux i Windows. Szczegóły i ograniczenia metody są w BUILD_LOCAL.md i BUILD_WINDOWS.md.

## Budowanie i dalsza praca

`.github/workflows/build.yml` zawiera przepis budowania Android ARM64 i Windows x64. Nie został uruchomiony. Ograniczenia SDK/NDK, Gradle i MSVC opisane pierwotnie w Work dotyczyły tamtego środowiska. Lokalny pełny build Windows CMake/Conan wykonano na MSVC 2022; patrz BUILD_WINDOWS.md. Skrypty bazowe są w `engine/dist/`.

Najbliższe kroki: testy okna gry Windows, kompilacja Androida, pełne testy ciosów i animacji LF4, wybór profilu w aplikacji/Androidzie, optymalizacja opóźnienia pokoju, konta i synchronizacja, import kolejnych pakietów, bezpieczne remapowanie ID do mieszania pakietów, rozbudowa sterowania i języków.


## Nowe dowody w wersji 0.5

`validation/native-build/lf4/all-fighters.json` zawiera aktualne wyniki 32/32 postaci na naszym silniku. Starszy katalog `validation/lf4/` zachowuje historię pierwszych testów na gotowym OpenLF2, w których Tiger nie przechodził. `preview/tiger-native.png` pochodzi z renderowania własnego silnika.

`validation/network/tcp-results.json` dotyczy prawdziwych gniazd systemowych, ale na jednej maszynie. Nie jest dowodem gry na ośmiu telefonach. `docs/ROOM_PROTOCOL.md` opisuje protokół i integrację gry. Szczegóły odtwarzania budowy są w `BUILD_LOCAL.md`.

## Nowe w wersji 0.6: lobby i mecz 2–8

W oryginalnym menu otwórz **F10 → Połączenia → Pokój LAN**. Gospodarz wybiera Host, pozostali Join i wpisują jego adres IPv4. Wszystkie urządzenia muszą mieć ten sam silnik, skrypty i pakiet. Po dołączeniu każdy naciska **Gotowość**, a gospodarz **Start**. Można zacząć od dwóch graczy, także przy limicie ośmiu. Konto i dostęp do internetu nie są wymagane przy wspólnej sieci lokalnej. Sterowanie pierwszego gracza, w tym dotyk, jest mapowane na własny slot sieciowy. F1–F9 i kody odblokowujące w tym trybie nadaje gospodarz.

- Osobne procesy gry, różne ziarna startowe i różne wejścia: 2,3,4,5,6,7,8 uczestników po 120 klatek; identyczne końcowe skróty stanu.
- Pełna ścieżka lobby → oryginalny wybór postaci → mecz dla 2 i 8 graczy.
- Naprawiono błąd ośmiu graczy z postacią Random: pominięcie wyboru komputerów nie rozwiązywało losowych postaci przed rozpoczęciem walki.
- Synchronizacja kodu odblokowania postaci gospodarza na 2 i 8 procesach, także podczas oczekiwania na barierę.
- Pakiet LF4 Turbo: 2 i 8 osobnych procesów, po 120 klatek zgodnej symulacji.
- Wspólna tabela RNG; SHA-256 stanu symulacji przed następną klatką. Celowe uszkodzenie HP jednego klienta przerywa sesję.
- To prototyp lockstep bez rollbacku. Opóźnienie rośnie z czasem najwolniejszego uczestnika. Nie potwierdzono wydajności przez Wi-Fi, zgodności ARM/x64, wszystkich trybów kampanii ani działania ośmiu fizycznych urządzeń.

Wyniki i logi Linux: `validation/room-game/`; aktualne Windows: `validation/windows-native/room-game/`. Mod `tools/room-check/` automatyzuje tylko testy; normalne lobby nie uruchamia meczu bez decyzji graczy. Bluetooth, konta i APK nadal wymagają pracy; EXE Windows jest zbudowany lokalnie.

```sh
python tools/check_room_game.py --engine BUILD_DIR/polish-fighters --installer /sciezka/LF2_v2.0a.exe
python tools/check_room_game.py --engine BUILD_DIR/polish-fighters --installer /sciezka/LF2_v2.0a.exe --counts 2,8 --menu
python tools/check_room_game.py --engine BUILD_DIR/polish-fighters --installer /sciezka/LF2_v2.0a.exe --counts 2 --probe
```
