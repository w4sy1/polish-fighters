# Test 0.18.12 — Windows i emulator Android (2026-11-20, Claude)

Środowisko: Windows 11 (instalacja testowa przez cichy instalator z CI), emulator `PolishFighters_Mod_QA` (API 35, x86_64, 320×640), serwer kont projektocalenie.pl. Telefonu Raptor nie używano: właściciel wycofał go z testów.

| # | Zrzut | Wynik |
|---|---|---|
| 01 | `01-android-moduly-lf4-bez-brak-danych.png` | LF4 Turbo (zainstalowany w `files/game/content-packs`) bez [BRAK DANYCH]. Pozostałe paczki mają znacznik, bo naprawdę ich brakuje. |
| 02 | `02-android-po-restarcie-modul-lf2.png` | LF2 wybrany w menu gry zostaje po force-stop i ponownym starcie. |
| 03 | `03-android-wstecz-z-konta-wraca-do-menu.png` | Wstecz na „Konto i pokoje” wraca do menu GRA ONLINE. W 0.18.10 zamykał grę. |
| 04 | `04-android-martwy-pokoj-relay-unavailable.png` | Pokój, którego gospodarz wyszedł przez POWRÓT (F4), zostaje na liście: „Relay channel unavailable”. Znany problem. |
| 05 | `05-android-0.18.12-rozlaczenie-z-windows.png` | Przed poprawką tożsamości: rozłączenie zaraz po wejściu do pokoju Windows. |
| 06 | `06-windows-0.18.10-powrot-konczy-gre.jpg` | 0.18.10: POWRÓT na ekranie konta kończy grę („OpenLF2 could not start”), przyczyna „duplicate frame flag”. |
| 07 | `07-android-0.18.10-menu-online.png` | Menu online 0.18.10 (stan wyjściowy). |
| 08–09 | `08-…`, `09-…` | Windows 0.18.9: LF4 Turbo pobrany z GitHuba w grze (982 pliki), moduł aktywny. |
| 10 | `10-windows-0.18.12-powrot-bez-bledu.jpg` | Windows 0.18.12: POWRÓT z aktywnym polem nicku wraca do menu. |
| 11 | `11-windows-0.18.10-logowanie-nickiem.jpg` | Windows 0.18.10: logowanie nickiem i lista pokojów. |
| 12 | `12-android-lan-…-przed-poprawka.png` | LAN Windows → emulator przed poprawką: „Niezgodny silnik, moduł lub dane gry”. Przyczyna: CRLF w skryptach Windows, escapowany w `bundle_source` jako `\013`. |
| 13 | `13-…`, `14-…` | Po poprawce: emulator wchodzi do pokoju LAN Windows, obie strony widzą dwóch graczy, start daje wspólny ekran „TY: GRACZ 1” / „TY: GRACZ 2”. |

Nie potwierdzone: po starcie wspólnego ekranu Windows ↔ emulator menu nie reagowało na wejście z żadnej strony (Enter, J, S na Windows; dotyk i Enter na emulatorze). Do sprawdzenia, czy to zatrzymanie symulacji, czy tylko sterowanie w menu sieciowym. Narzędzie testowe nie wysyła klawiszy numerycznych (atak to Num7).
