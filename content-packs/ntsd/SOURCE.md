# Naruto: The Setting Dawn 2.4 — eksperymentalny import

Źródło: https://www.lf-empire.de/html/versions/NTSD.html
Archiwum: https://www.lf-empire.de/downloads/versions/NTSD_2.4_2.0a.zip
Autorzy moda: The NTSD Team. Oryginalny LF2: Marti Wong i Starsky Wong.
Kod silnika OpenLF2 i importera nie zmienia praw do zasobów gry i moda.

Import z wydania NTSD 2.4_2.0a zawiera 42 postacie, 137 obiektów, 17 aren i 1121 zasobów. Zachowano ID; przepisano przestrzeń nazw zasobów i skrócono opisowe etykiety klatek do limitu czytnika. Nie uruchamiano ani nie dołączono oryginalnych EXE/DLL.

**Profil nie jest gotowy do grania i nie jest dołączony do paczki Windows.** 13/42 postaci przeszło test 300 klatek. W pozostałych przypadkach głównym problemem są liczby poza zakresem 32-bitowym; jeden przypadek nie spełnił warunku obecności wybranej postaci w końcowym stanie. Nie przycinano ani nie zawijano tych wartości, ponieważ wymaga to ustalenia zachowania oryginalnego silnika. 31 arkuszy ma rozbieżności deklarowanych wymiarów; nie naprawiano ich automatycznie.

Raporty: `import-report.json`, `sprite-edge-repairs.json`, `asset-checksums.json` oraz `../../validation/windows-native/ntsd/`. Wyniki nie potwierdzają pełnej zgodności ciosów, przemian ani kampanii.
