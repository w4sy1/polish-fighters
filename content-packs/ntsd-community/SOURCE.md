# NTSD Community Edition — import eksperymentalny

Źródło: plik dostarczony przez użytkownika `ntsdCE_setup.zip` → zawiera instalator Inno Setup `ntsdCE_setup.exe`.
Autorzy edycji: Tyci, Tobivv. Oryginalny zespół NTSD: zxcv11791 (leader/coder/sprites/stages), konkisuke (tła), nave, Zazz, Krele, kentaru-chou, Z, pimpen itachi, ZXO i inni (patrz `app/Credits.txt` w archiwum źródłowym). Silnik: "Neora Engine" (nie standardowy LF2 DLL — Alkarter/Drakken/Lord Silva/1477/Surik/Archer-Dante).

Instalator NIE był uruchamiany. Dane wydobyto statycznie przez `innoextract -s` (bez wykonania PE, bez rejestrów, bez skryptów instalacyjnych).

Napotkane i naprawione problemy przy imporcie (żadny nie wymagał modyfikacji treści postaci/grafik, tylko metadanych/duplikatów):
- **Duplikat ID obiektu 507** (`chars/weapon1.dat` "stone" vs `chars/air_creature_die.dat`) — druga linia w `data/data.txt` zakomentowana (`# DUPLICATE-ID-DISABLED-BY-IMPORT`), zachowano pierwszą (broń "stone"). To błąd autorski w źródle, nie importera.
- **30 plików PNG z uszkodzonym CRC chunka `iCCP`** (profil ICC, metadane koloru — nie dotyczy pikseli) — chunk usunięty, resztę pliku (nagłówek, IDAT, IEND) zweryfikowano bit-po-bicie jako nienaruszoną. Pillow (uzywany przez `repair_sprite_edges`) odmawia otwarcia PNG z błędnym CRC jakiegokolwiek chunka, w tym niekrytycznego.
- Specjalny fix dla `pack_id=='ntsd-community'` już istniejący w `tools/import_legacy.py` (błąd VC80 `sscanf` w `data/stage.dat`, `frame_limit=999` w `constants.lua`) — zadziałał automatycznie po użyciu dokładnie tego ID.

Wynik: 201 obiektów, 25 tła, 1560 zasobów, 2 kampanie (`Kazekage_Rescue`, `Madara_Uchiha`), `missing_resources: []`, 40 arkuszy sprite'ów nierozwiązanych pod kątem wymiarów (wymaga audytu).

Status: eksperymentalny — jak w innych paczkach, nie potwierdzono działania ciosów/AI/kampanii w silniku, tylko poprawność statycznego importu danych.
