# One Piece: Legends of Sea 2.1X — import eksperymentalny

Plik dostarczony przez użytkownika: `OPLoS2.1X.rar` (folder "OPLoS2.1X", exe `OPLoS2.1X.exe`, dodatkowo
`LoSCheat.exe` i `ddraw.dll` — pominięte, nie uruchamiano).

Import z RAR-a przez `unrar` (7z/p7zip zgłaszał "Unsupported Method" na ~1464 wpisach przy próbie przez
`7z x`; `unrar` rozpakował wszystko bez błędów).

Dwie naprawy zastosowane na źródłowym `data/data.txt` przed importem:
1. 4 pojedyncze śmieciowe linie (`%`, `$`, `&`, `*`) między sekcją `<object>` a dalszym ciągiem listy
   postaci — zakomentowane jako `# JUNK-LINE-DISABLED-BY-IMPORT`, najwyraźniej artefakt błędnej edycji
   pliku przez autora moda (parser silnika nie rozpoznawał tych linii).
2. literówka `fileb:` zamiast `file:` przy wpisie `id: 231 ... data\ace_b.dat` — poprawiona.

Postacie: 130 obiektów, 36 teł, 1179 zasobów. 4 brakujące zasoby, wszystkie kosmetyczne/pomocnicze
(`cheat.bmp`, `cheatz.bmp`, `data/109.wav`, `nar/xit.bmp` — ekrany/dźwięk cheatów, nie wpływają na
rozgrywkę postaci). 74 arkusze sprite'ów nierozwiązane pod kątem dopasowania wymiarów — wymaga audytu
przed pełnym uznaniem za kompatybilne.

Status: eksperymentalny. Nie potwierdzono działania postaci, AI ani efektów — tylko statyczny import
danych.

Autorstwo i prawa do oryginalnych zasobów pozostają przy twórcach moda. Brak publicznej publikacji.
