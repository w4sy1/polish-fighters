# Test 0.18.13 — Windows i emulator Android (2026-11-20, Claude)

Środowisko: Windows 11 (instalacja testowa aktualizowana cichym instalatorem z CI), emulator `PolishFighters_Mod_QA` (API 35, x86_64), serwer kont projektocalenie.pl z przekaźnikiem. Telefonu nie używano.

| # | Zrzut | Wynik |
|---|---|---|
| 01 | `01-windows-0.18.12-lan-pojedynek-z-komputerami.png` | LAN, Windows gospodarz, emulator dołącza przez 10.0.2.2. Po starcie wspólnego ekranu S/Num7 na Windows i ATAK na emulatorze działają, wybór postaci i mecz z komputerami są zsynchronizowane. W 0.18.12 symulacja nie stała: testowano Enter/J, a atak to Num7. |
| 02 | `02-android-0.18.12-lan-dymek-otwarty.png` | Dymek komend otwiera się na Androidzie i na Windows w meczu sieciowym. |
| 03 | `03-android-lista-pokojow-nick-gospodarza.png` | 0.18.13: lista pokojów pokazuje „winpc: Pokój Polish Fighters / lf2-classic”. |
| 04–05 | `04-windows-przekaznik-mecz-ruch-3s.png`, `05-android-przekaznik-ten-sam-stan.png` | Przekaźnik, Windows gospodarz, emulator gracz 2: 3 s ruchu w prawo ≈ 420 px (≈ 4,7 px/klatkę przy 30 kl./s), bez zatrzymań; ten sam stan na obu ekranach. Ruch joystickiem z emulatora widoczny na Windows. |
| 06–07 | `06-android-po-wyjsciu-gospodarza-0-pokojow.png`, `07-windows-usunieto-ogloszenie-po-powrot.png` | Gospodarz wychodzi przez POWRÓT (F4): Windows pokazuje „Usunięto ogłoszenie pokoju.”, emulator po odświeżeniu: 0 pokojów. |
| 08–09 | `08-windows-gracz2-w-pokoju-androida-przez-przekaznik.png`, `09-android-gospodarz-tytul-bez-sterowania-dotykiem.png` | Odwrotnie: emulator gospodarzem, Windows dołącza przez przekaźnik i steruje menu. Android na wspólnym menu tytułowym nie miał joysticka ani przycisków — poprawione w `3dacc6d`. |
| 10–11 | `10-android-gospodarz-tytul-z-joystickiem.png`, `11-windows-menu-przesuniete-joystickiem-androida.png` | Build `4a64a87`: Android gospodarzem przez przekaźnik ma joystick i przyciski na wspólnym menu. Ruch joystickiem przesuwa wybór także na Windows. |
| 12–13 | `12-windows-dymek-przez-przekaznik.png`, `13-windows-come-sojusznik-podszedl.png` | Pojedynek (łatwy), Henry (komputer, Team 1) jako sojusznik. COME z Windows (gracz 2): Henry podchodzi do Firena. |
| 14–15 | `14-android-dymek-come.png`, `15-windows-come-z-androida-sojusznik-u-gracza-1.png` | COME z Androida (gracz 1): Henry przechodzi do Deepa. Dymki działają przez przekaźnik w obie strony. |

Wydanie: [v0.18.13](https://github.com/w4sy1/polish-fighters/releases/tag/v0.18.13), build CI 44789423744 (Windows, Android arm64-v8a, x86_64), tag na `4a64a87`.

Uwaga: tapnięcia w czasie pierwszych ok. 25 s startu na emulatorze (czarny ekran) wywołują systemowe „nie odpowiada”. Po starcie gra działa normalnie.

Instalator: aktualizacja instalacji 0.18.12 do 0.18.13 usunęła `scripts/base/ui/hud_editor.lua`, `touch_gamepad.lua` i `base/attack-pl.wav`; `userdata/` i `content-packs/` zostały.

Nie sprawdzono:
- TCP_NODELAY w przekaźniku działa dopiero po ponownej instalacji przekaźnika na serwerze (`install-relay.sh` pobiera `tools/room_relay.py` z main). Testy przez przekaźnik szły na starej wersji przekaźnika.
- Dymek bez sojusznika komputerowego w drużynie gracza nie ma widocznego skutku (komenda dotyczy tylko komputerów z tej samej drużyny). Gracze „Bez drużyny” nie mają sojuszników.
- Telefon fizyczny i iPhone/inne urządzenia.
