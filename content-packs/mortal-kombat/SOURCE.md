# Mortal Kombat LF2 — import eksperymentalny

Oryginalne źródło `MK-LF2 SETUP_LF2COMBO.exe` to instalator Indigo Rose "Setup Factory 8.0" —
nie dało się go statycznie rozpakować w tej sesji (7z/unrar/innoextract odmawiają, `sfextract`
zablokowany przez klasyfikator bezpieczeństwa). Użytkownik uruchomił instalator na swoim
Windows (działa poprawnie) i udostępnił już zainstalowany folder gry
(`C:\Program Files (x86)\Mortal Kombat LF2`).

Zaimportowano bezpośrednio z zainstalowanych plików: `bg`, `bgm`, `data`, `sprite` (pominięto
`mk-lf2.exe`, `Readme.txt`, `recording`, `Uninstall`). Import przeszedł bez żadnych napraw
źródła — zero błędów parsera przy pierwszej próbie.

Postacie: 55 obiektów, 11 teł, 447 zasobów. Brak brakujących zasobów (`missing_resources: []`).
43 arkusze sprite'ów nierozwiązane pod kątem dopasowania wymiarów — wymaga audytu przed pełnym
uznaniem za kompatybilne.

Status: eksperymentalny. Nie potwierdzono działania postaci, AI ani efektów — tylko statyczny
import danych.

Autorstwo i prawa do oryginalnych zasobów pozostają przy twórcach moda. Brak publicznej publikacji.
