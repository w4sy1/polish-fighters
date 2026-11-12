# POLISH LITTLE FIGHTERS — audyt i zakres przebudowy

Punkt wyjścia: `331130673a6e73cc00f30c0456133c17a13aa5d0`. Gałąź robocza `classic-menu-2026-11-12`; archiwum źródeł sprzed zmian zapisano poza repozytorium. Dwa nieśledzone archiwa mechaniki pozostają nietknięte.

## Stan potwierdzony w kodzie

- Silnik C++23, SDL3, LuaJIT; Windows i Android (Java przygotowuje dane, wybór pakietu i Bluetooth przed SDL).
- `base/ui/flow.lua` obsługuje VS, Stage, dwa Championship, Battle, Demo i Playback. Nowe menu ma delegować do tych samych ekranów i mechanik.
- `hub_launch.lua`, `hub_flow.lua` i `classic_shell.lua` rozszerzają istniejący launcher. `base/ui/navigation.lua` obsługuje klawiaturę, pad, mysz i dotyk w logicznej rozdzielczości 794×550.
- Cztery lokalne profile klawiatury/pada; ekran postaci i protokół pokoju obsługują do ośmiu uczestników. Boty, drużyny, portrety i arena są częścią istniejących ekranów gry.
- Rzeczywiste pakiety: Classic LF2 (przypięty instalator danych), Polish Fighters (6 postaci), LF4 Turbo (32), Reinforced (28), Naruto/NTSD (42), One Piece (61), Dragon Ball (56), Kate (29), Bleach (34). Wspólna pula jest generowana z istniejących zasobów. Osobnego LF2 Turbo nie znaleziono.
- Wszystkie pliki zadeklarowane w manifestach tych pakietów były obecne podczas audytu. Nie oznacza to pełnego odzyskania oryginalnych modów: zachowujemy istniejące raporty brakujących obiektów, ograniczeń kampanii i kompatybilności.
- TCP/LAN: istniejący protokół deterministyczny 2–8 urządzeń, sprawdzanie zgodności danych. Android: Wi-Fi/hotspot, PAN zależny od systemu, eksperymentalny most Bluetooth dwóch telefonów. Test lokalnych procesów nie dowodzi połączenia między telefonami ani działania przez Internet.
- Serwer kont/pokoi i klient mają kod, lecz publicznego wdrożenia nie potwierdzono. Szybka gra i zaproszenia znajomych nie są gotową usługą. Nie wdrażamy backendu.
- Istnieją zapis opcji, języków, masek modułów, układu dotyku, konfliktów sterowania i kombinacji specjalnych. Zachowujemy ich formaty oraz mechanikę.
- Naprawa 0.12.2: indeks `manifest.json` musi być pierwszym wpisem ZIP. Walidator, bramka Gradle i test rzeczywistego APK na pustym katalogu muszą pozostać.

## Plan realizacji

1. Osobne dane PL/EN i geometria menu, siedem klasycznych pozycji oraz podmenu istniejących trybów.
2. Nawigacja tryb → moduł → konfiguracja graczy → istniejący wybór postaci/areny; powrót i zachowanie ustawień. Wspólny format danych dla Androida i Lua.
3. Granat, jasne prostokątne obramowania, własna czcionka pikselowa z polskimi znakami, istniejące dźwięki menu. Usunięcie nowoczesnych kart ekranu startowego.
4. Testy przejść, zapisu, PL/EN, konfliktów, pakietów i istniejących mechanik; weryfikacja Windows oraz APK przed wydaniem testowych plików na GitHub.
5. Recykling starych wygenerowanych paczek dopiero po potwierdzeniu dostawy. Bez usuwania źródeł, zasobów, ustawień i nieopublikowanych archiwów.

## Granice weryfikacji

Nie podłączono telefonu do ADB. Render Androida przez Robolectric oraz ekstrakcja danych APK nie są testem wykonywania natywnego kodu ARM na telefonie. Wyniki końcowe i zakres pozostały do realizacji należy opisać po wykonaniu testów, bez przenoszenia wyników wcześniejszej wersji na nowy interfejs.
