# Polish Fighters 0.10.0 — pięć poprawek z testów, 2026-11-11

[Pobierz APK i aktualizację Windows](https://github.com/w4sy1/polish-fighters/releases/tag/fixes-test-2026-11-11).

## Co zmieniono — w kolejności zgłoszeń

1. **Wybór modułów na telefonie.** Na ekranie startowym jest przycisk `MODUŁ: ...`. Pozwala uruchomić osobno Polish Fighters, Little Fighter 2, LF4 Turbo, Dragon Ball, One Piece, Kate, Reinforced, NTSD lub Bleach; można także wybrać wszystkie razem albo zaznaczyć własny zestaw. Wyboru nie zastępuje już stałe ładowanie dwóch pakietów w Activity. Ścieżka skryptów jest jawna, dzięki czemu silnik znajduje wspólne menu i pozostałe pakiety. Pustego zestawu nie można zapisać. Ustawienie startowe i skład własnej puli są zapamiętywane. Główne menu gry nadal pokazuje wszystkie osobne moduły, również wykluczone ze wspólnej puli.
2. **Ukrycie powtórzeń podstawowych postaci we wspólnej puli.** Dla powtarzających się nazw podstawowego katalogu LF2 domyślnie wybierany jest jeden dostępny przedstawiciel z aktywnych pakietów. Jeżeli LF2 jest wyłączone, pozostaje wersja z wybranego dodatku. Wyłączenie opcji przywraca warianty; osobne moduły zachowują swoje katalogi. To filtr wyboru i losowania, nie usuwanie rekordów, plików lub umiejętności. W pełnym odblokowanym katalogu: 308 → 258 pozycji, Deep 3 → 1; nadal 310 wpisów postaci i 947 rekordów obiektów. Pula tylko Polish Fighters ma pięć własnych postaci, tylko LF4 ma 32 pozycje.
3. **Przejście kampanii po pokonaniu przeciwników.** AI własnych postaci omijało wspólny rozkaz marszu do wyjścia i zatrzymywało się, gdy nie było celu walki. Bramka etapu czekała na całą drużynę. Dodano użycie istniejącego rozkazu przejścia przed własnym wyszukiwaniem przeciwnika. Przed poprawką kontrolna próba: Deep przechodzi, Wasyl zostaje w x≈150. Po poprawce Deep i wszystkie formy 410–415 samodzielnie przekraczają bramkę i przechodzą do następnego etapu. Nieruchome toalety, sterowanie człowieka i AI podczas walki pozostają zachowane.
4. **Powrót do wyboru modułów.** Przycisk `MODUŁY / MENU GŁÓWNE` jest w menu profilu, wyborze postaci, pauzie, wynikach i zakończeniu. W trakcie niedokończonej walki wymaga potwierdzenia jej opuszczenia; korzysta ze wspólnej obsługi zakończenia walki. Aplikacja pozostaje otwarta. Gotowe wyniki mogą zostać zapisane dotychczasowym mechanizmem, a przerwana kampania nie otrzymuje nagrody za ukończenie. Zakończona sesja sieciowa jest zamykana przy powrocie. W trwającej walce sieciowej zachowano istniejące zasady opuszczania połączenia.
5. **LeumasEX i Rudolf — lawina klonów.** Tworzenie postaci przez `opoint` miało nieograniczoną rekurencję. Dodano niezależne rodziny kopii: najwyżej trzy żywe kopie na przywołującego, a kopie nie przywołują kolejnych postaci. Mogą nadal walczyć i strzelać, a zabitą kopię można zastąpić. Zwykłe projektyle i oryginalne parametry podstawowego klona Rudolfa pozostają. Dotychczasowy osobny mechanizm klonów SZ zachowuje swoje dwa pokolenia. W kontrolowanej próbie na rzeczywistych rekordach: przed poprawką 20 potomków LeumasEX i 120 Rudolfa, po poprawce po trzy. Identyfikatory nie przechodzą między dodatkami: LeumasEX używa 55/1001, Rudolf 5/1019 w osobnym LF4/wspólnej puli. Źródłowych obrazów nie podmieniano.

Zachowano kody: na telefonie `USTAWIENIA → Włącz kody → Zapisz` i komunikat `lamus`; na PC kod `polishfighters`. Filtr powtórzeń jest w tych samych ustawieniach telefonu oraz w oknie dobierania pakietów w grze.

## Pliki i instalacja

- **Android:** `PolishFighters-Android-moduly-2026-11-11.apk`, versionCode 10, versionName `0.10.0-pack-selection-test`, ARM64 i ARMv7, Android 5.0+. Zainstaluj jako aktualizację poprzedniej paczki. Nie usuwaj aplikacji przed aktualizacją: zachowano applicationId `pl.prestigetech.polishfighters`, podpis i katalog ustawień. APK zawiera wszystkie dziewięć pakietów. Pierwsze przygotowanie lub aktualizacja danych wymaga oczekiwania na ekran postępu.
- **Windows:** `PolishFighters-Windows-poprawki-2026-11-11.zip` zawiera dziewięć poprawionych plików Lua do [poprzedniej pełnej paczki](https://github.com/w4sy1/polish-fighters/releases/tag/mobile-test-2026-11-11). Zamknij grę i rozpakuj ZIP w folderze nadrzędnym istniejącego `PolishFighters-Windows`, zgadzając się na zastąpienie wskazanych plików. Uruchom dotychczasowy `Graj-Wszystkie-Mody.cmd`. To aktualizacja skryptów; natywny EXE i biblioteki nie wymagały zmiany. Nie nadpisuje `userdata` ani danych dodatków.
- **Ten komputer:** przygotowano odrębny folder `engine/out/PolishFighters-Modules-2026-11-11`. Skrót `Polish Fighters` na pulpicie kieruje do tej wersji, przy zachowaniu dotychczasowej ścieżki ustawień i postępu. Poprzednie foldery i paczki pozostawiono.
- W Bluetooth obie strony powinny mieć ten sam nowy APK, moduły i ustawienia puli. Radio nie było testowane na urządzeniach.

## Zmienione pliki

- Android: `BluetoothLobbyActivity.java`, `OpenLF2Activity.java`, `MobileCodeSettings.java`, nowe `GamePackSettings.java` i `GameLaunchArguments.java`; `app/build.gradle`, `tools/build_android_local.ps1`, testy `GamePackSettingsTest.java` i `GamePackDialogTest.java`.
- Logika gry: `content-packs/mixed-all/catalog.lua`, `content-packs/polish-originals/ai.lua`, `engine/scripts/base/game/objects.lua`, `engine/scripts/base/ui/flow.lua`, `quit_dialog.lua`, `engine/scripts/polish-fighters/hub.lua`, `hub_flow.lua`, `hub_launch.lua`, `pack_preferences.lua`.
- Testy i diagnostyka: `mixed_duplicates_test.lua`, `campaign_exit_ai_test.lua`, `clone_spawn_test.lua`, `pack_preferences_test.lua`, `tools/probe_campaign_exit.py`, `probe_clone_families.py`, `probe_module_navigation.py`, `probe_roster_selection.py`.
- Dokumentacja: centralny `PROJECT-STATUS.md`, README, README_PL, ANDROID_STUDIO, kolejka `docs/KOREKTY-2026-11-11.md` i ten raport. Lokalnie zmieniono też skrót pulpitu; jego kopia sprzed zmiany jest w katalogu walidacji.

## Testy i wyniki

| Sprawdzenie | Wynik |
|---|---|
| Końcowy czysty build APK i testy Androida | PASS, 15 testów; wszystkie dziewięć pojedynczych modułów, własna pula, odrzucenie pustej puli, zachowanie ustawień i kodów |
| Lua | PASS, 30 zestawów; składnia 125 plików |
| Python | 51 PASS, jeden SKIP; razem 52 testy |
| Kampania: ruch od wyjścia do kolejnego etapu | PASS, siedem postaci/form, bez przesuwania NPC po rozpoczęciu próby |
| Powrót do głównego menu | PASS, pięć rzeczywistych scenariuszy kliknięć; obrazy menu i wyboru postaci sprawdzone wizualnie |
| Pełny katalog | PASS, cztery konfiguracje; Deep 3 → 1, warianty przywracane, sam LF4 oraz same własne postacie |
| Samopowielanie klonów | PASS, cztery próby natywne na plikach LF4 i wspólnej puli; przed/po zapisane osobno |
| Przekaźnik Bluetooth przez lokalne TCP | PASS, trzy testy strumienia oraz dwa silniki po 120 klatek, zgodny stan końcowy |
| APK: podpis, CRC, oba ABI, zależności ELF, wyrównanie ARM64 16 KB | PASS |
| Dane gry | PASS, 15399 ścieżek logicznych i 7795 unikalnych zasobów zweryfikowanych SHA256; 137 skryptów/manifestów odpowiada bieżącym źródłom |
| Windows ZIP | PASS, dziewięć plików Lua zgodnych ze źródłem, bez danych użytkownika |
| Android lint | FAIL, 27 wcześniejszych błędów w wygenerowanych klasach SDL; zero błędów w nowych klasach modułów |

Podczas kontroli wykryto pozostawione puste obszary w przyrostowo pakowanym APK. Skrypt budowy wykonuje teraz czyste pakowanie aplikacji, a końcowy plik przeszedł kontrolę rozmiaru i CRC. Natywne biblioteki Androida pozostają z istniejącego zweryfikowanego buildu: wszystkie poprawki silnika w tym etapie są w Lua, a zmiany Androida w Java.

## Czego nie potwierdzono i znane ryzyka

Nie było podłączonego telefonu w ADB. Obecnego APK nie uruchomiono automatycznie na fizycznym urządzeniu i nie przeprowadzono radiowego testu Bluetooth. Poprzedni APK użytkownik potwierdził jako uruchamiający się na telefonie; nie zastępuje to testu wersji 0.10.

Kontrolne próby kampanii sprawdzają ruch i przejście po pustym końcowym polu, a próby klonów wywołują rzeczywiste punkty tworzenia obiektów w kontrolowanych warunkach. Nie są pełnym naturalnym przejściem wszystkich kampanii ani dowodem naprawy wszystkich mechanik każdego dodatku. Wcześniejsze niezgodności importowanych kampanii i 27 błędów lint SDL pozostają. Kontroli nie wyłączono.

Zakres obejmuje wszystkie pięć zgłoszeń oraz ich paczki do dalszych testów. Nie usuwano postaci ani oryginalnych zasobów, nie zmieniano signing, uprawnień, Firebase czy identyfikatora aplikacji. Nie nadpisano historii Git i nie wdrażano produkcji. Poprzednie wydanie pozostaje dostępne.
