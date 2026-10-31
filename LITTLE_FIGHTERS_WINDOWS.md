# Little Fighters — menu i sterowanie, 2026-10-31

Uruchom **LittleFighters.exe** z katalogu `engine/out/LittleFighters-pack-ai-2026-10-31`. Program znajduje dane LF2 obok siebie; nie uruchamiaj instalatora LF2_v2.0a.exe. Zachowaj obok programu biblioteki DLL, `scripts`, `content-packs` i `licenses`.

Publiczny ZIP `artifacts/PolishFighters-Windows-core-pack-ai-2026-10-31.zip` zawiera silnik, skrypty i biblioteki. Nie zawiera danych LF2 ani ośmiu dodatków z pełnej lokalnej paczki. To nie jest pełna paczka modów. Repozytorium zawiera kod i pochodzenie importów; własne grafiki postaci są w `content-packs/polish-originals/art`.

W **Wszystkie mody — katalog → Dobierz pakiety w menu** można ukryć wybrane zestawy i zapisać wybór. To filtr menu, a nie łączenie postaci różnych modów w jednej walce. Zawsze można wrócić do panelu i zaznaczyć wszystkie.

Pierwszy ekran to **Little Fighters**. **Polish Fighters** oznacza osobny zestaw naszych czterech postaci razem z zachowanym katalogiem LF2. Pozostałe wybory: LF2, LF4 Turbo, Dragon Ball, One Piece, Kate, Reinforced, NTSD/Naruto i Bleach. Wybranie innego zestawu przeładowuje dane w tym samym programie, a następnie pokazuje wybór walki, kampanii, bitwy, turnieju i map. Pakiety są już lokalnie w pełnej paczce.

**Wszystkie mody — katalog** pozwala wybrać pojedynczy pakiet. Nie oznacza jeszcze wspólnej puli postaci. Łączenie modów, własne mieszane zestawy i automatyczne pobieranie/aktualizowanie z GitHuba nie są w tej wersji dostępne.

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

- Wspólna pula wszystkich modów i dobieranie mieszanego zestawu.
- Pobieranie pakietów, sprawdzanie aktualizacji i naprawa instalacji z GitHuba.
- Dopracowanie unikalnych klatek animacji, wszystkich ataków, AI i balansu.
- Wcześniejsze braki zawartości Bleach i mechanik DBZ oraz pełne przejścia kampanii.
- Android/APK, rzeczywisty telefon, fizyczny pad oraz testy sieci nowej czwórki. Bluetooth nadal niezaimplementowany.

Pełny raport bieżącego etapu: `validation/hub-controls-2026-10-31/REPORT.md` lub `RAPORT-HUB-STEROWANIE.md` w paczce. Uruchomienia testowe i obrazy z SDL nie zastępują testu fizycznego pada ani pełnego ręcznego przejścia gry.
