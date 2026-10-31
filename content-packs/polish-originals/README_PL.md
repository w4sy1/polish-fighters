# Cztery postacie Polish Fighters

Pakiet dodaje Wasyla (410), Szymonoko/SZ (411), Mega Ninja Jasia (412) i bossa Skibidi Sigma Tatę (413). Oryginalne rekordy LF2 są przed nowymi; ich dane, numery, mapy i zasady odblokowania pozostają zachowane. Nowa czwórka jest dostępna od razu, na końcu listy wyboru. Pozostałe dodatki pozostają osobnymi pakietami.

Aktualna paczka: uruchom `LittleFighters.exe` w `engine/out/LittleFighters-hub-2026-10-31`, następnie wybierz **Polish Fighters**. Nowe menu ma bezpośredni dostęp do ustawień klawiatury, myszy i pada. Starszy katalog `PolishFighters-originals-2026-10-31` zachowuje poprzednią wersję. Nie uruchamiaj instalatora ani oryginalnych EXE dodatków. Plik LF2_v2.0a.exe jest czytany przez nasz silnik jako archiwum danych.

SZ strzela również zwykłym atakiem — nie wymaga to kombinacji ani many. Portrety wyboru mają 120×120, ikony HUD 40×45, zgodnie z bazowym LF2. Poprawiono skalę sylwetek, widoczną linię stóp, przypisania pozycji umiejętności i wycinki efektów. Pełna płynność animacji nadal wymaga dopracowania.

W tabeli **D** oznacza akcję blok, **A** atak, **J** skok. To nazwy akcji LF, nie narzucone klawisze klawiatury. Użyj klawiszy/przycisków przypisanych w ustawieniach. Strzałka → oznacza kierunek patrzenia postaci.

| Kombinacja | Wasyl | SZ | Mega Ninja Jaś | Sigma Tata |
|---|---|---|---|---|
| D → A | Seria niebieskich fal | Seria pocisków | Osiem mieczy | Kule ognia |
| D ↑ A | Jeden klon | Jeden klon | Śluz | Tupnięcie obszarowe |
| D ↓ A | Teleport | Teleport i strzał | Teleport | Fala ognia |
| D → J | Obrotowe kopnięcie | Seria pocisków | Surfowanie na mieczu | Robak |
| D ↑ J | Duża seria fal | Ogień własny i klona | Huragan ośmiu mieczy | Trzech pomocników |
| D ↓ J | Duża seria fal | Teleport i salwa | Śluz | Deszcz dziewięciu kul |
| D J A | Atak kończący | Atak kończący | Huragan mieczy | Salwa królewska |

Klon Wasyla/SZ ma połowę maksymalnego HP rodzica. Nie wygasa czasowo; następnego można przywołać dopiero po pokonaniu poprzedniego. Klon walczy podstawowymi atakami i nie tworzy kolejnych klonów. Wasyl odzyskuje do 1/4 ostatniej utraty HP, maksymalnie 8 punktów na krok; umiejętność nie wskrzesza. Śluz zadaje okresowe obrażenia i spowalnia ruch przeciwnika do 60% na ograniczony czas. Boss ma 1500 HP i drugą fazę poniżej połowy HP. W danych Jasia zachowano siłę 2 i trudność 2,5. Klasyczny font wyświetla `Mega Ninja Jas`; pełna nazwa pozostaje w metadanych.

Grafika: cztery wygenerowane atlasowe PNG, zachowane bez przetwarzania pikseli. `layout.lua` wybiera i skaluje rzeczywiste wycinki; część pozycji powtarza rysunki, więc 256 adresów nie oznacza 256 unikalnych animacji. Widoczne mogą być drobne obwódki i fragmenty sąsiadujących efektów. Autorskie sprites nie korzystają jeszcze z opcjonalnego cieniowania postaci. To grywalna wersja eksperymentalna, wymagająca dalszego sprawdzenia płynności i balansu.

Testy obejmują natywne próby Windows i renderer SDL software. Android/ARM, dotyk w rzeczywistej grze, synchronizacja nowej czwórki przez sieć, odtwarzanie nagrań i pełne kampanie nie zostały potwierdzone w tym etapie.

Odtworzenie lokalnych DAT: po umieszczeniu przypiętego LF2 w `../downloads/LF2_v2.0a.exe` uruchom `.build-venv/Scripts/python.exe tools/build_polish_originals.py` z katalogu projektu. Wygenerowane PNG są w `art/`; zasoby zależne od LF2 w `assets/` pozostają lokalne.
