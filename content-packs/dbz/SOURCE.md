# DBZ LF2 v0.6.9 hotfix — import eksperymentalny

Źródło: https://dbzlf2.itch.io/dbzlf2

Postacie: 56; obiekty: 190; areny: 14; zasoby: 2119.

Nie uruchamiano oryginalnego EXE ani bibliotek DLL. Dane zachowują oryginalne ID. Nie emulowano modyfikacji silnika autora. Ten import nie potwierdza działania postaci, AI, kampanii ani efektów. Nie jest dołączony do historycznej paczki Windows.

Braki danych: bgm/stage4.wma, common/kiball_pink.png.

Aktualizacja 2026-10-30: odzyskano autorskie definicje 14 scen / 50 wariantów z `data/bg_mode.dat` i `data/bg/*.dat`. Przeniesiono geometrię, wybór warstw `respond`, startowe globalne opoint i selektory `arest`; powiązania `bg`/`mode` etapów zachowano w `stage-scenes.json`. Izolowany profil czytnika DBZ obsługuje klatki 0–998 i do 32 pól itr (źródło zawiera maksymalnie 25). Inne profile zachowują limit 400 klatek / 16 itr.

W natywnych próbach przeszły 14/14 map i 50/50 wariantów. Dwie dodatkowe blokady muzyki usunięto: `[MU]` oznacza stop/unload, co potwierdza statyczny odczyt oryginalnych funkcji (music-sentinel-proof.json). Brakujący `bgm/stage4.wma` ma jawny zamiennik z przypiętego bazowego LF2 (inherited-base-music.json); nie jest to odzyskane nagranie autora DBZ. Aktualny wynik ponowionych testów etapów: validation/remaining-mechanics-2026-10-30/REPORT.md.

Nie emulowano jeszcze pełnej semantyki questów, lustrzanych przeciwników 8001–8008, zmian scen między fazami ani kodu AI AngelScript. Uruchomienie mapy/etapu nie dowodzi zgodności tych mechanik z oryginałem.

Statyczne odzyskanie danych: evbunpack 0.2.6 (https://github.com/HNIdesu/Enigma-Virtual-Box-Unpacker), bez odtwarzania PE. Osobno odzyskano wewnętrzne data/stagedata.dat oraz 55 plików źródłowych AI .as w ../games/DBZ-ai-source-2026-10-28. AI AngelScript nie zostało przeniesione do Lua. Użyto oryginalnego sprite/sys/jack_b.bmp z przypiętego instalatora LF2. Zastąpiono cztery brakujące nazwy BMP istniejącymi PNG o tej samej nazwie bazowej; lista w import-report.json. PNG/alpha zachowane. Katalog zawiera 24 przygody/wyzwania. Ich własne rozszerzenia reguł i warunki odblokowania wymagają audytu.

Autorstwo i prawa do oryginalnych zasobów pozostają przy twórcach. Sumy plików po imporcie: asset-checksums.json. Brak publicznej publikacji.
