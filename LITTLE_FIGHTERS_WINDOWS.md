# Little Fighters — menu i sterowanie, 2026-10-31

Uruchom **Graj-Little-Fighters.cmd** z katalogu `engine/out/LittleFighters-mixed-online-2026-10-31`. **Graj-Wszystkie-Mody.cmd** uruchamia od razu mieszaną pulę. Program znajduje dane LF2 w katalogu gry; nie uruchamiaj instalatora LF2_v2.0a.exe. Zachowaj obok programu biblioteki DLL, `scripts`, `content-packs` i `licenses`.

Publiczny ZIP `artifacts/PolishFighters-Windows-core-mixed-online-2026-10-31.zip` zawiera silnik, skrypty i biblioteki. Nie zawiera danych LF2 ani dodatków z pełnej lokalnej paczki. To nie jest pełna paczka modów. Repozytorium zawiera kod i pochodzenie importów; własne grafiki postaci są w `content-packs/polish-originals/art`.

W **Wszystkie mody / wspólna pula → Dobierz aktywne pakiety** wybierz zestawy i zapisz wybór. **Wszystkie razem — tryb testowy** przeładowuje wspólny katalog postaci zaznaczonych pakietów. Działa lokalna walka postaci z różnych dodatków. Zależności efektów pozostają załadowane niezależnie od wyboru.

Pierwszy ekran to **Little Fighters**. **Polish Fighters** oznacza osobny zestaw naszych czterech postaci razem z zachowanym katalogiem LF2. Pozostałe wybory: LF2, LF4 Turbo, Dragon Ball, One Piece, Kate, Reinforced, NTSD/Naruto i Bleach. Wybranie innego zestawu przeładowuje dane w tym samym programie, a następnie pokazuje wybór walki, kampanii, bitwy, turnieju i map. Pakiety są już lokalnie w pełnej paczce.

Mieszana pula jest eksperymentalna: 932 obiekty i 128 map, standardowe etapy LF2. Autorskie mechaniki EXE/AngelScript, wyspecjalizowane AI i mieszane kampanie pozostają niepełne. Oryginalne przygody wybieraj w osobnych profilach. Automatyczne pobieranie/aktualizowanie modów z GitHuba nadal nie jest dostępne.

**Konta / pokoje / LAN** otwiera ekran logowania i katalog pokoi. Bez serwera nadal działa gra lokalna i LAN. Uruchomienie lokalnego serwera oraz wymagania przyszłego hostowania opisano w `server/README_PL.md`; nie ma jeszcze publicznej usługi ani Bluetooth. Mieszany profil ma w GUI wyłączoną sieć do czasu dalszych testów.

## Sterowanie

Menu obsługuje mysz, strzałki/Enter oraz D-pad/A. Wybierz **Ustawienia sterowania**, potem gracza 1–4.

- Klikaj **Urządzenie**, aby przechodzić przez klawiaturę, klawiaturę z myszą i pady 1–4. Pad musi być podłączony, aby przypisać jego przycisk. Kierunki pada obsługuje D-pad lub lewy analog.
- Kliknij akcję i naciśnij nowy klawisz/przycisk. Kliknięcie otwierające przypisanie jest ignorowane do zwolnienia. Escape anuluje przypisywanie.
- Gotowe układy: **WASD + Num7/8/9** (atak/skok/blok), **WASD + J/K/L**, **strzałki + Num1/2/3**, **WASD + mysz + spacja**. W ostatnim układzie LPM atakuje/strzela, spacja skacze, PPM blokuje. Nie jest to jeszcze celowanie kursorem.
- Jeśli układ koliduje z innymi graczami, użyj **Usuń kolizje z innymi**. To usuwa wspólne przypisania pozostałych graczy z edytowanego zestawu. Dopiero **Zapisz** zmienia plik; **Anuluj** porzuca edycję.
- Ustawienia są wspólne dla pakietów w `userdata/common/config.json`. Nie kasuj tego katalogu przy aktualizacji. Starsze foldery gry i ich ustawienia pozostały zachowane osobno.

Bez własnych zapisanych ustawień pozostają oryginalne przypisania LF2: gracz 1 używa Num8/2/4/6, Num5 — atak, Num0 — skok, Num+ — blok. Aktualne przypisania gracza 1 są pokazane przy wyborze postaci oraz w menu zestawu. Na laptopie wygodniej wybrać jeden z gotowych układów.

## Cztery postacie

Wasyl, SZ, Mega Ninja Jaś i Skibidi Sigma Tata znajdują się na końcu listy postaci. Portrety wyboru mają rozmiar LF2 **120×120**, a ikony HUD **40×45**. Rozmiar sylwetek i położenie stóp poprawiono względem poprzedniej paczki. SZ strzela zwykłym atakiem, bez many; pojedyncze krótkie kliknięcie jest buforowane do najbliższej próbki sterowania. Specjalne kombinacje opisano w `content-packs/polish-originals/README_PL.md`.

Przypisano właściwsze pozy do skoków, bloków i umiejętności; poprawiono wycinki pocisków i ich położenie. Nie jest to jeszcze finalny zestaw płynnych animacji ani ukończony balans. Boss ma 1500 HP; jego pasek jest skalowany do dostępnej szerokości HUD.

## Co pozostaje

- Pełna zgodność autorskich mechanik we wspólnej puli i mieszane kampanie.
- Pobieranie pakietów, sprawdzanie aktualizacji i naprawa instalacji z GitHuba.
- Dopracowanie unikalnych klatek animacji, wszystkich ataków, AI i balansu.
- Wcześniejsze braki zawartości Bleach i mechanik DBZ oraz pełne przejścia kampanii.
- Android/APK, rzeczywisty telefon, fizyczny pad oraz testy sieci nowej czwórki. Bluetooth nadal niezaimplementowany.

Pełny raport bieżącego etapu: `validation/mixed-2026-10-31/REPORT.md`. Uruchomienia testowe i obrazy z SDL nie zastępują testu fizycznego pada ani pełnego ręcznego przejścia gry.
