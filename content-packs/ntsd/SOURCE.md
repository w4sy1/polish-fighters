# Naruto: The Setting Dawn 2.4 — eksperymentalny import

Źródło: https://www.lf-empire.de/html/versions/NTSD.html
Archiwum: https://www.lf-empire.de/downloads/versions/NTSD_2.4_2.0a.zip
Autorzy moda: The NTSD Team. Oryginalny LF2: Marti Wong i Starsky Wong.
Kod silnika OpenLF2 i importera nie zmienia praw do zasobów gry i moda.

Import z wydania NTSD 2.4_2.0a zawiera 42 postacie, 137 obiektów, 17 aren i 1121 zasobów. Zachowano ID; przepisano przestrzeń nazw zasobów i skrócono opisowe etykiety klatek do limitu czytnika. Nie uruchamiano ani nie dołączono oryginalnych EXE/DLL.

Aktualizacja 2026-10-30: przeliczono 364 przepełnione literały w 37 DAT zgodnie z wynikiem `sscanf %d` z rzeczywistej x86 Microsoft VC80 8.0.50727.9680. Oryginalny NTSD importuje MSVCR80.dll. Uruchomiono wyłącznie własny program diagnostyczny i zainstalowaną bibliotekę Microsoft; nie uruchamiano kodu gry. Mapowania, sumy przed/po i numery linii: `vc80-integer-normalization.json`. Oryginały zachowano w `../../../baseline-remaining-mechanics-2026-10-30/`.

17/17 map i 25/25 startów etapów przeszło natywną próbę 120 klatek z aktorem QA Deep i autorskimi przeciwnikami. Pakiet znajduje się w nowym lokalnym wydaniu Windows. To nadal profil eksperymentalny: nie potwierdzono wszystkich 42 postaci, ruchów, rozbieżności arkuszy ani ukończenia kampanii. Wcześniejszy wynik 13/42 postaci pochodził sprzed naprawy liczb i nie jest aktualnym testem postaci.

Raporty: `import-report.json`, `sprite-edge-repairs.json`, `asset-checksums.json` oraz `../../validation/windows-native/ntsd/`. Wyniki nie potwierdzają pełnej zgodności ciosów, przemian ani kampanii.
