# Oględziny 11 arkuszy — 2026-10-30

Obejrzano trzy plansze kontaktowe i fragmenty krawędzi oryginalnych plików.
Narzędzie: `tools/inspect_partial_sheets.py`; rozmiary, SHA256 i odwołania:
`visual/sheets.json`. Nie zmieniono pikseli ani numerów klatek.

| Pakiet / plik | Widoczna zawartość i ustalenie |
|---|---|
| Bleach 000212.bmp | Jeden turkusowy pocisk 155×53. Deklaracja 199×199 i następne komórki nie odpowiadają fizycznemu arkuszowi. |
| Bleach 000210.bmp | Jeden turkusowy pocisk 123×71. Zadeklarowany pionowy układ 53×155 wychodzi poza obraz; brak podstaw do dopisania kolejnych póz. |
| Bleach 000175.bmp | Osiem póz wojownika z mieczem i niebieskimi smugami w układzie 4×2. Wiele odwołań wskazuje kolejne, nieistniejące rzędy/kolumny. |
| Bleach 000570.bmp | Postać w czarnym płaszczu w układzie 5×4. Ostatni rząd jest fizycznie krótszy od zadeklarowanej siatki 319+1; brakujących dolnych pikseli nie odzyskano. |
| Bleach 000278.png | Poziomy pas tekstury na dużym czarnym tle; rzeczywista szerokość 4000 zamiast deklarowanych 5000. Nie rozciągano tekstury. |
| Bleach 000133.bmp | Sześć małych głów/masek na czarnym tle. Odwołania do dalszego rzędu nie mają kompletnych odpowiedników w źródle. |
| Kate 000538.bmp | Cztery rzędy póz wojownika i efekty ognia; plik kończy się na wysokości 350. Klatki 95/96 żądają niepełnego lub całkowicie nieistniejącego dalszego rzędu. |
| Kate 000203.bmp | Kolejne fazy pionowego fioletowego promienia, zanikające w prawo. Ostatnia zadeklarowana komórka wychodzi poza prawą krawędź; brakujących pikseli nie odtworzono. |
| Reinforced 000520.bmp | Ten sam widoczny układ bazowego wojownika i ognia co Kate 000538; takie same odwołania 95/96 poza siatką. |
| Reinforced 000525.bmp | Sylwetki nietoperza i efekty ognia w czterech rzędach. Klatki 95/96 wskazują poza istniejące pełne rzędy. |
| Reinforced 000511.bmp | Trzy rzędy postaci z fioletowymi efektami. Odwołania 95/96 są całkowicie poza plikiem; 97/98 częściowo poza dolną krawędzią. |

Dwa BMP Reinforced są RLE8. Pillow odrzuca ich bezpośredni odczyt pikseli;
do planszy użyto ograniczonego dekodera diagnostycznego z kontrolą współrzędnych,
palety i znacznika końca strumienia. Nie oznacza to uzupełnienia grafiki.

**Wniosek:** oględziny wykonane; nadal nie ma źródła brakujących rysunków ani
podstaw do wskazania autorskich klatek zastępczych. Dotychczasowe zabezpieczenie
odczytu pozostaje. Nie potwierdzono zgodności wyglądu podczas pełnej walki.
