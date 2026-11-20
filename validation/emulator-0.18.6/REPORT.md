# Polish Fighters 0.18.6 — test na emulatorze (2026-11-20)

Emulator: AVD `PolishFighters_Mod_QA`, Android 15 (API 35), x86_64, APK x86_64 z workflow
„Polish Fighters builds” (run 44694972926, commit 1530ac5). Telefon nie był używany.

| Krok | Wynik | Zrzuty |
| --- | --- | --- |
| Start gry 0.18.6 | menu działa | 01 |
| Katalog modów → POLISH FIGHTERS - GITHUB → natywny ekran Mody | działa | 12–13 |
| Pobranie podpisanego katalogu (9 modów, podpis poprawny) | działa | 14 |
| Pobranie i instalacja LF4 Turbo (982 pliki, moduł wybrany) | działa | 15–17 |
| Powrót do gry, aktywny moduł LF4 Turbo, postać Deep z LF4 | działa | 18–23 |
| Klawiatura ekranowa w polu nicku (także po schowaniu Wstecz) | działa po poprawce | 07, 24–26 |
| GRAJ nickiem (EmuTest) | działa po poprawce CA | 27 (błąd przed), 29 |
| Pokój przez przekaźnik widoczny na serwerze | 1 pokój | 30 |
| Mecz online: 2 instancje emulatora (host + dołączający) | walka zsynchronizowana | 32–38 |

Nie sprawdzono: mecz Windows ↔ emulator (brak zgody na sterowanie oknem gry
Windows) oraz instalacji modu z GitHuba w grze Windows (kod zbudowany w CI,
nieuruchomiony). Narzędzie `tools/mod_manager.py github-install lf4-turbo`
na Windows pobrało i zainstalowało LF4 Turbo z GitHuba.
