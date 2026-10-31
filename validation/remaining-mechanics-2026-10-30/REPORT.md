# Zgodność DBZ / NTSD / One Piece i oględziny arkuszy — 2026-10-30

Własny Windows EXE: `engine/out/PolishFighters-remaining-2026-10-30/openlf2.exe`.

SHA256: `0c31efbe876e02fe28ef12cfa28c512ba5eec1bc940edc914e2d98f9e70be927`.

## Wyniki natywne

| Pakiet | Mapy | Starty etapów |
|---|---:|---:|
| bleach | 12/12 | 20/20 |
| kate | 11/11 | 33/33 |
| reinforced | 14/14 | 44/44 |
| lf4-turbo | 12/12 | 25/25 |
| ntsd | 17/17 | 25/25 |
| one-piece | 36/36 | 25/25 |
| lf2-classic | 13/13 | 25/25 |
| dbz | 14/14 | 62/62 |

Każdy przypadek: 120 klatek headless, odczyt i rysowanie zasobów, własny silnik, aktor QA Deep i autorscy przeciwnicy/sceny. Indeks: combined-native-results.json. Dodatkowo 50/50 wariantów DBZ. To nie są ukończone kampanie, testy wszystkich postaci, potwierdzenie zgodności obrazu ani pełnego odsłuchu.

## Zmienione elementy

- DBZ: klatki 0–998 i do 32 itr; bazowy profil zachowuje 400/16. Autorskie 14 scen i 50 wariantów, geometria, warstwy respond, opoint/arest, 62 powiązania etapów z bg/mode. Dane i źródłowe sumy: content-packs/dbz/scene-modes.json oraz stage-scenes.json.
- NTSD: 364 literały w 37 DAT przeliczone według własnego programu wywołującego zainstalowany x86 VC80 sscanf. To nie arbitralne przycinanie. Oryginały i nagłówki zachowano; ponowna kontrola CRT, wszystkich pól i sum: ntsd-normalization-verification.json.
- DBZ muzyka: [MU] obsłużono jako stop/unload na podstawie statycznego przepływu oryginalnego kodu (music-sentinel-proof.json). Brakujący standardowy bgm/stage4.wma otrzymał jawny zamiennik z przypiętego bazowego LF2 (inherited-base-music.json); to nie odzyskane nagranie DBZ.
- One Piece: dekoder FFmpeg wmalossless; wszystkie sześć oryginalnych plików ASF/WMA ma tag 0x0163. Audio nie transkodowano. Cztery dawne blokady startu usunięte.
- Obejrzano 11 arkuszy (Bleach6/Kate2/Reinforced3). Szczegóły: VISUAL-REVIEW.md. Nie odtworzono brakujących rysunków.

## Nierozwiązane — zakres nie jest ukończony

- Bleach284/action83 i151/action30: oba ID nieobecne w autorskim katalogu. Audyt wszystkich123 DAT wskazuje18/74 kandydatów z samym numerem akcji; to nie potwierdza tożsamości. weapon3.dat nie zawiera akcji30. Nie dodano zgadywanego celu. Dowód: content-packs/bleach/missing-object-audit.json.
- Starszy plik2.0 Final jest wymieniony na [stronie autora](https://bleachbankaibr.webnode.page/download/versoes-anteriores/), lecz wskazane 4shared/uploadmirrors nie dostarczyły archiwum. Nie odzyskano z nich danych.
- DBZ: nieprzeniesione pełna semantyka questów, selektory lustrzanych przeciwników8001–8008, zmiany scen między fazami i AI AngelScript. Start Mirror Match po naprawie muzyki nie dowodzi obecności właściwych lustrzanych przeciwników. Nadal brakuje common/kiball_pink.png, a autorskiego stage4.wma nie odzyskano.
- Android: zmiany wspólnego kodu są w źródłach; nie wykonano nowego natywnego buildu ARM ani testu na telefonie.

## Testy i pliki

Przegląd388 przypadków oraz pełne powtórzenie76 przypadków DBZ po zmianie obsługi muzyki. Python:48 testów,47 OK/1 pominięty (symlink Windows). LuaJIT:17 zestawów i składnia90 plików. MSVC:6 zestawów C++; TCP2–8 procesów, rozłączenie i timeout OK. Logi w tym katalogu. Oryginalnych EXE/DLL nie uruchamiano.

Zmiany kodu: engine/conanfile.py, engine/include/openlf2/resources/object_data.hpp, engine/src/resources/object_data.cpp, engine/src/app/application.cpp, content-packs/dbz/*.lua i package.manifest,37 lokalnych DAT NTSD oraz metadane i narzędzia testowe/odzyskiwania. Dokładny diff pozostaje w Git.

Kopia sprzed zmian: ../baseline-remaining-mechanics-2026-10-30/. Starsze paczki pozostają osobno. Nie wykonano commitu, push ani release w tym etapie.
