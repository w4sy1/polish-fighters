# POLISH LITTLE FIGHTERS 0.13.0 — klasyczne menu (wydanie testowe)

## Zakres i wykonane funkcje

Zastąpiono główne menu nowoczesnego launchera klasycznym granatowym układem LF2: siedem pionowych prostokątnych przycisków, jasne obramowania, wyróżnienie aktywnej pozycji, własna czcionka pikselowa z polskimi znakami i selektor PL / EN. Zachowano istniejące tło LF2 i oryginalne dźwięki menu w silniku. Nie kopiowano grafiki z dostarczonego wzoru.

- BITWA, MODUŁY, GRA ONLINE, USTAWIENIA, JĘZYK, TWÓRCY, WYJŚCIE.
- Siedem rzeczywistych trybów oryginalnego silnika; delegacja do dotychczasowego flow. Battle Mode rozpoczyna się wyborem postaci przed konfiguracją bitwy.
- Tryb → moduł → konfiguracja graczy → istniejący wybór postaci/areny. Już wybrany pojedynczy moduł nie wymaga ponownego wyboru z całej biblioteki. Demo i odtwarzanie nie wymuszają zbędnych etapów.
- Powrót Escape / B i WSTECZ w podmenu; lokalny powrót z postaci do konfiguracji graczy. F4 w walce nadal wraca do wyboru postaci przez istniejące wejście synchronizowane.
- Wszystkie dziewięć dostępnych profili oraz wspólna pula zachowane. Włączanie/wyłączanie pakietów i ukrywanie duplikatów wykorzystują istniejący zapis i filtrowanie katalogu. Ekran zgodności prezentuje rzeczywisty audyt plików manifestów podczas budowy; brak plików blokuje uruchomienie profilu oznaczonego jako niekompletny w inwentarzu.
- Cztery indywidualne profile lokalne, klawiatura/mysz/pad, zapis, domyślne ustawienia i konflikty. Dodano zapisywane przypisania czterech kierunków pada, z kontrolą duplikatów. Dotychczasowe ustawienia wielkości, położenia, przezroczystości i układu dotyku pozostają dostępne. Nie zmieniano kombinacji specjalnych.
- Oryginalny ekran postaci LF2, portrety i kolory drużyn również w Polish Fighters i wspólnej puli. Nie zmieniano rekordów postaci ani ich mechaniki.
- Wspólne słowniki PL/EN oraz dane własnej czcionki w Lua; generator dostarcza identyczne dane Androidowi. Wybór języka jest zapisywany i działa od razu, także dla głównych ekranów Androida. Rozbudowano tłumaczenia istniejących paneli dodatków i sterowania.
- Android ma ten sam układ siedmiu pozycji; wąska kolumna dopasowuje się do dostępnej szerokości. Przygotowywanie danych pozostaje osobną czynnością i zachowuje naprawę indeksu ZIP z 0.12.2.
- Istniejące Wi-Fi/TCP, PAN i próbny most Bluetooth zachowane; ekran online oddziela LAN/własny serwer od niedostępnej publicznej usługi.

Warstwy menu korzystają z istniejącej nawigacji i zapisu. Dodano osobne pliki geometrii, lokalizacji, inwentarza modułów oraz generator czcionki/danych Androida. Nie przepisano silnika. Natywny EXE i biblioteki ARM pochodzą z wcześniej zweryfikowanego builda tej samej tożsamości źródeł C++; nowe funkcje są w Lua, Javie i zasobach. applicationId, podpisywanie i uprawnienia nie były zmieniane. APK: versionCode 15, versionName 0.13.0-classic-test.

## Funkcje niedostępne i ograniczenia

- Brak osobnego pakietu LF2 Turbo. Nie tworzono fikcyjnych postaci ani danych.
- Szybka gra i zaproszenia znajomych bez wdrożonej usługi są jawnie niedostępne. Lista pokoi wymaga własnego rzeczywistego serwera; nie jest publicznym matchmakingiem. Nie zmieniano DNS, hostingu ani nie wdrażano backendu.
- Obecność wszystkich zadeklarowanych zasobów nie oznacza pełnego odzyskania mechanik każdego moda. Zachowano wcześniejsze audyty niepełnych obiektów/kampanii i ograniczenie wspólnej puli do testów lokalnych.
- Dźwięki LF2 są zachowane w natywnym menu; ekran Androida przed SDL korzysta z obsługi kliknięć platformy.
- Pełnego przeglądu każdego dynamicznego komunikatu wszystkich starych dodatków w obu językach nie wykonano. Test odtwarzania nagrania dotyczył istniejących testów formatu i skierowania akcji z menu, nie ręcznego wyboru pliku nagrania w nowym wydaniu.

## Weryfikacja i jej granice

Użytkownik polecił zatrzymać dalsze testy i przejął testowanie. Ostatnie korekty tłumaczeń Androida zakończono kompilacją oraz pakowaniem, bez ponawiania testów funkcjonalnych i lint. Nie należy przenosić poniższych wyników na twierdzenie o pełnym, fizycznym teście końcowej paczki.

Przed tą decyzją faktycznie zakończono:

- LuaJIT: składnia 137 plików PASS; 26 zestawów PASS, potem przebieg zatrzymało nieaktualne oczekiwanie 18 pozycji starego menu w pack_preferences_test.lua. Dostosowano to oczekiwanie do nowego menu siedmiu pozycji i ekranu przełączników; zgodnie z poleceniem użytkownika nie wykonano ponownego przebiegu ani pozostałych zestawów. Nowy zestaw bada tryby, moduły, zapis, powrót, PL/EN, granice przycisków, limit komend renderera i kierunki pada.
- Python: 61 przypadków, 60 PASS / 1 pominięty (uprawnienia symlinków Windows).
- Android: ostatni zakończony pełny przebieg 55 przypadków, 54 PASS / 1 warunkowo pominięty; ten warunkowy test rzeczywistego APK został następnie uruchomiony osobno i przeszedł. Lint: 0 błędów / 54 ostrzeżenia w tym przebiegu.
- Rzeczywisty wcześniejszy build APK 0.13.0: ekstrakcja pełnej paczki do pustego katalogu przez ten sam kod Java co aplikacja, utworzenie .ready i argumenty startowe; PASS. To wykonanie na Windows/Robolectric, nie uruchomienie ARM na telefonie.
- 18 scenariuszy rzeczywistego EXE: główne ekrany, wejście do postaci LF2 i LF4, Stage, oba Championship, Battle Mode, Escape, klawiatura i syntetyczny pad; PASS. Wykonano i obejrzano zrzuty renderera Windows oraz render Androida przez Robolectric.
- LF4 Turbo: 32/32 postaci porusza się i atakuje przy wejściu gracza. Przy ustalonym ziarnie 42: 32/32 botów porusza się; 31 wysłało zwykły atak, pozostały Julian wykonał animację ataku i zadał obrażenia. Moon atakował, lecz w tym scenariuszu nie potwierdzono trafienia. Nie jest to dowód zachowania AI we wszystkich arenach i sytuacjach.
- Dwa i osiem osobnych procesów EXE przez TCP: PASS, identyczne końcowe sumy stanu po co najmniej 120 klatkach. To nie test Internetu/NAT ani Bluetooth między telefonami.
- Wcześniejsza iteracja pełnego ZIP Windows: kontrola CRC i wszystkich SHA256, brak userdata, start EXE z lokalnymi względnymi ścieżkami; PASS. Końcowy ZIP ponownie spakowano po ostatniej zmianie słownika, bez dalszych testów na życzenie użytkownika.

Nie było podłączonego urządzenia ADB. Nie zweryfikowano instalacji i natywnego wykonania końcowego APK na fizycznym telefonie, sprzętowego pada, dotyku na urządzeniu, Bluetooth/PAN ani połączenia przez Internet. Nie wykonano ręcznie pełnego przejścia każdego trybu ze wszystkimi modułami. Końcowa paczka jest przeznaczona do testowania przez użytkownika.

## Dostawa i porządkowanie

Planowany tag plików testowych: `classic-menu-0.13.0-2026-11-12`. Windows: pełny ZIP z EXE, bibliotekami, danymi i `GRAJ.cmd`; Android: APK. Ustawienia prywatne są wyłączone z paczek. Publikacja obejmuje GitHub wskazany przez użytkownika, bez sklepu ani infrastruktury produkcyjnej. Wynik przesyłania i porządkowania należy dopisać po ich zakończeniu.

## Zmienione pliki

- `PROJECT-STATUS.md`
- `docs/CLASSIC-MENU-0.13.0-2026-11-12.md`
- `docs/CLASSIC-MENU-AUDIT-2026-11-12.md`
- `engine/android/app/build.gradle`
- `engine/android/app/src/main/AndroidManifest.xml`
- `engine/android/app/src/main/assets/classic-menu.json`
- `engine/android/app/src/main/java/io/github/openlf2/openlf2/BluetoothLobbyActivity.java`
- `engine/android/app/src/main/java/io/github/openlf2/openlf2/ClassicButton.java`
- `engine/android/app/src/main/java/io/github/openlf2/openlf2/ClassicColumn.java`
- `engine/android/app/src/main/java/io/github/openlf2/openlf2/ClassicMenuData.java`
- `engine/android/app/src/main/java/io/github/openlf2/openlf2/GameBootstrapActivity.java`
- `engine/android/app/src/main/res/drawable/pf_background.xml`
- `engine/android/app/src/main/res/drawable/pf_button.xml`
- `engine/android/app/src/main/res/drawable/pf_card.xml`
- `engine/android/app/src/main/res/drawable/pf_primary.xml`
- `engine/android/app/src/main/res/drawable/pf_progress.xml`
- `engine/android/app/src/main/res/layout-land/activity_game_home.xml`
- `engine/android/app/src/main/res/layout/activity_game_home.xml`
- `engine/android/app/src/main/res/values-en/start.xml`
- `engine/android/app/src/main/res/values/start.xml`
- `engine/android/app/src/test/java/io/github/openlf2/openlf2/GamePackDialogTest.java`
- `engine/android/app/src/test/java/io/github/openlf2/openlf2/MobileSettingsDialogTest.java`
- `engine/android/app/src/test/java/io/github/openlf2/openlf2/StartScreenTest.java`
- `engine/scripts/base/ui/controls.lua`
- `engine/scripts/base/ui/flow.lua`
- `engine/scripts/polish-fighters/controls_hint.lua`
- `engine/scripts/polish-fighters/hub.lua`
- `engine/scripts/polish-fighters/hub_flow.lua`
- `engine/scripts/polish-fighters/hub_launch.lua`
- `engine/scripts/polish-fighters/input_settings.lua`
- `engine/scripts/polish-fighters/locales/android_en.lua`
- `engine/scripts/polish-fighters/locales/en.lua`
- `engine/scripts/polish-fighters/locales/pl.lua`
- `engine/scripts/polish-fighters/locales/ui_en.lua`
- `engine/scripts/polish-fighters/menu-font.png`
- `engine/scripts/polish-fighters/menu_font_index.lua`
- `engine/scripts/polish-fighters/menu_layout.lua`
- `engine/scripts/polish-fighters/menu_locale.lua`
- `engine/scripts/polish-fighters/module_inventory.lua`
- `engine/scripts/polish-fighters/package.manifest`
- `engine/scripts/polish-fighters/pixel_font.lua`
- `tests/classic_menu_test.lua`
- `tests/pack_preferences_test.lua`
- `tests/hub_input_test.lua`
- `tests/test_classic_menu_assets.py`
- `tools/generate_classic_menu_assets.py`
- `tools/generate_module_registry.py`
- `tools/movement-probe/flow.lua`

## Problemy rozwiązane podczas implementacji

Pierwsze kliknięcie po zmianie podmenu było przechwytywane przez automatyczne ustawienie fokusu; naprawiono priorytet rzeczywistego kliknięcia. Escape był przechwytywany przez globalne pytanie o zamknięcie gry; rozdzielono powrót z podmenu i wyjście z głównego ekranu. Rysowanie każdego piksela długiej listy modułów przekraczało limit poleceń silnika; zastąpiono je atlasem znaków z jednym poleceniem na znak. Battle Mode otwierał konfigurację bez stanu postaci; nowy przepływ najpierw tworzy ekran wyboru postaci.

## Kolejny etap

Testy użytkownika na telefonie i komputerze: pierwsza instalacja/aktualizacja, wybór pojedynczego modułu i puli, klawiatura/pad/dotyk, walka i F4, PL/EN oraz powrót. Następnie poprawki na podstawie rzeczywistych usterek, bez wdrażania publicznego serwera. Bieżąca implementacja odpowiada zakresowi klasycznego menu i integracji istniejących funkcji; nie stanowi ukończenia planowanych usług online ani pełnego audytu każdej mechaniki modów.
