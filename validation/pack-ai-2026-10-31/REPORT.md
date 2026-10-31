# Pakiety, AI i polski interfejs — 2026-10-31

## Zakres wykonany

- Zapisywany wybór pakietów widocznych w menu: Wszystkie mody → Dobierz pakiety w menu.
  Zaznaczanie wszystkich, zapis, anulowanie i ochrona przed pustą listą; zachowanie innych ustawień.
  To filtr uruchamianych osobno profili, NIE wspólna pula postaci ani jednoczesna aktywacja modów.
- AI czterech własnych bohaterów wybiera specjalne ruchy zależnie od dystansu, linii walki,
  dostępnych klatek i MP. SZ używa strzałów z dystansu. Klony nie dostają specjalnych ruchów.
  Przy równym dystansie cel jest wybierany po numerze slotu, niezależnie od iteracji tabeli.
- Uzupełniono wszystkie klucze dwujęzycznych etykiet z istniejącego angielskiego słownika bitmap:
  polskie odpowiedniki oraz usunięcie dodatkowych chińskich wierszy, zgodnie z mechanizmem tłumaczeń.
  Dodano polskie komunikaty wybranych błędów pokoju. Nie jest to dowód kompletności wszystkich napisów w kodzie.
- Zachowano oryginalne dane LF2/modów oraz sterowanie LF2 i preset WASD + Num7/8/9 z poprzedniego etapu.

## Pliki

Nowy pack_preferences.lua i wpis manifestu; hub.lua, hub_launch.lua;
content-packs/polish-originals/runtime.lua oraz ai.lua; base/i18n/polish.lua;
tests/pack_preferences_test.lua, tests/polish_originals_test.lua, tests/ui_locale_test.lua;
tools/probe_pack_ai_delivery.py, check_room_game.py, room-check/flow.lua;
tools/package_delivery.py, LITTLE_FIGHTERS_WINDOWS.md, PROJECT-STATUS.md, .gitignore i artefakty ZIP.
Commit obejmuje także wcześniejsze, nieopublikowane etapy tego projektu; ich kod skompilowano i sprawdzono zestawami regresji.

## Sprawdzone

- 107 plików Lua: składnia PASS; 21 zestawów Lua: PASS.
- Python: 48 testów, 47 PASS, 1 SKIP.
- Windows Release: udany build z poprzedniego etapu UI; w bieżącym etapie zmiany wykonawcze są w Lua.
- 6 natywnych testów C++: PASS; TCP 2–8 klientów i przerwanie po rozłączeniu/timeout: PASS.
- Czterej bohaterowie: po dwa natywne przebiegi walki, wynik deterministyczny: PASS.
- Natywny zapis filtra pakietów i ponowne uruchomienie: PASS; zrzut obejrzany.
- Cztery osobne procesy gry z Wasylem, SZ, Jasiem i bossem: 120 klatek TCP,
  zgodny digest 2ff98254028d2351e4b55749bfd21281740a6cc15afd2915f5b9e497c74e6ce6.
- Publiczny ZIP silnika: CRC PASS; wypakowany LittleFighters.exe uruchomił menu
  z jawną ścieżką do lokalnego, przypiętego archiwum LF2.

## Nieukończone i niezweryfikowane

Całe zamówienie NIE jest ukończone. Do dalszej pracy pozostają:
pełne nowe animacje/rysunki i balans, wszystkie ataki/efekty, remapowanie wspólnej puli modów,
odzyskanie Bleach 284/action83 i 151/action30 (nadal brak wiarygodnego źródła),
pełne mechaniki i przejścia scen DBZ oraz przejście całych przygód.
Nie wdrożono publicznego serwera logowania/pokoi ani integracji klienta kont, Bluetooth i NAT traversal.
Test TCP wykonano na jednym komputerze; nie potwierdza działania przez internet ani między urządzeniami.
Android Studio ZIP jest źródłowym projektem, nie zbudowanym/przetestowanym APK.
Pełny redesign wszystkich ekranów oraz ręczny audyt wszystkich napisów nadal pozostają.

## Dostarczanie

Pełna wersja lokalna: engine/out/LittleFighters-pack-ai-2026-10-31/LittleFighters.exe.
Publiczny ZIP: artifacts/PolishFighters-Windows-core-pack-ai-2026-10-31.zip — silnik, biblioteki, skrypty,
bez danych gry i modów. Osobny ZIP Android Studio zawiera źródła. Sumy w artifacts/checksums.json.
Żadnego userdata, kont, tokenów ani oryginalnych EXE/DLL gier nie dołącza się do repozytorium.
Nie publikowano GitHub Release. Push obejmuje gałąź roboczą.
