# Wspólna pula, interfejs, konta i kampanie — 2026-10-31

## Zmieniono

- Dodano generowany pakiet `content-packs/mixed-all`: 932 unikalne obiekty
  (postacie, pociski, efekty i przedmioty), 128 map, 7580 deklaracji zasobów.
  `tools/build_mixed_pack.py` przepisuje ID, odwołania `oid`, transformacje
  i ścieżki do oddzielnych kopii. Oryginalne pakiety pozostają osobno.
- Wybór aktywnych pakietów filtruje rzeczywistą mieszaną pulę postaci.
  Zależności efektów pozostają załadowane. Mieszany profil jest eksperymentalny,
  w GUI ograniczony do gry lokalnej; używa standardowych kampanii LF2.
- Menu, wybór postaci i ekrany dodatkowe mają wspólną stylistykę oraz oryginalne
  tło LF2. Zachowano oryginalne przypisania i gotowy WASD + Num7/8/9.
- Dodano asynchroniczny natywny klient kont, ekran rejestracji/logowania,
  publikowanie/listowanie/usuwanie pokoi, heartbeat i wybór gospodarza.
  Hasło i token są w pamięci; ustawienia przechowują wyłącznie adres serwera.
  HTTPS wymagany zdalnie; HTTP dopuszczony wyłącznie na loopback.
- DBZ przełącza autorskie sceny, geometrię i obiekty między etapami.
- `server/Start-LocalServer.ps1` i `server/README_PL.md` opisują lokalne
  uruchomienie i wymagania przyszłego hostowania. Publicznego serwera nie ma.

## Testy i granice dowodów

- Windows Release: kompilacja zakończona powodzeniem.
- Lua: składnia 120 plików, 23 zestawy testów OK.
- Python: 51 testów, 50 OK i 1 pominięty z powodu opcjonalnego lokalnego archiwum.
- C++: 6 zestawów OK, w tym limity zasobów mieszanej paczki; TCP 2–8 klientów
  i testy przerwania/timeoutów OK. Osobna regresja gry TCP: 2 i 4 procesy OK.
- `tools/probe_mixed_pack.py`: walka ośmiu źródeł przez 300 klatek, dwa przebiegi
  z tymi samymi warunkami prezentacji dają ten sam digest. Wszystkie 128 map
  narysowano przez SDL software po 4 klatki. To krótkie próby, nie pełna zgodność.
- `tools/probe_online_native.py`: rzeczywisty natywny klient i lokalny serwer
  HTTP — rejestracja, logowanie, lista/publikacja/usunięcie pokoju, wylogowanie
  OK. Zdalny zwykły HTTP odrzucony, dane uwierzytelniające nie zapisane.
- `tools/probe_online_room.py`: dwa osobne procesy gry utworzyły konta,
  opublikowały/odczytały pokój i połączyły się przez nowy klient katalogu.
  120 klatek rzeczywistej walki TCP dało identyczny digest obu stron.
  Użyto skryptowanych akcji i automatycznej gotowości w QA, lokalnego HTTP
  i loopback TCP; to nie jest dowód działania publicznego Internetu.
- `tools/probe_dbz_transition.py`: wymuszona zmiana etapu 0→1 rzeczywiście
  przełącza scenę 7→11 i obiekty. Nie jest to naturalne przejście kampanii.
- `tools/probe_mixed_delivery.py`: rzeczywiste przeładowanie mieszanego profilu
  przez menu i rysowanie ekranu dodatkowego OK; 15183 hashe zasobów w dostawie
  zgodne ze źródłami, 7582 pierwotne importowane zasoby zachowane bez zmian.
  Parser PowerShell zaakceptował skrypt startowy serwera; testy backendu
  i natywnego klienta sprawdzają usługę, nie publiczne wdrożenie.
- `tools/probe_campaign_traversal.py`: 56 prób rozdziałów/scenariuszy.
  Wspomagany test usuwa wpisy faz i przesuwa gracza; nie sprawdza trudności,
  naturalnych zwycięstw, pełnych ataków ani mechanik EXE/AngelScript.
  48 zakończono: DBZ 23, Bleach/Kate/Reinforced/LF4/NTSD po 5.
  DBZ Mirror Match zablokowany przez ID 8002–8008; sześć prób One Piece
  zablokowane przez ID 122 we wspólnym pliku etapów. LF4 survival odwiedził
  101 faz, bez zakończenia w budżecie 20000 klatek; to nie dowód błędu survivalu.

Surowe lokalne dowody: `validation/mixed-2026-10-31`, `online-native-2026-10-31`,
`dbz-transition-2026-10-31`, `campaign-traversal-2026-10-31` oraz
`mixed-delivery-2026-10-31`. Nie publikujemy testowych baz, konfiguracji
ani wygenerowanych prób zawierających jednorazowe dane testowych kont.

## Pozostało / ryzyka

Bleach 284/action83 i 151/action30 nadal nieodzyskane. Brakujące rysunki nie
zostały odtworzone. Pełne questy, mirror, hardkodowane mechaniki ID i autorskie
AI modów wymagają dalszego portu. Nie potwierdzono naturalnego przejścia całych
przygód, wszystkich umiejętności, końcowego balansu ani pełnego tłumaczenia.

Brak publicznego wdrożenia HTTPS, testów Internet/NAT i fizycznych urządzeń.
Nowy katalog pokoi używa bezpośredniego TCP/IPv4; istniejący relay nie jest
podłączony do tego GUI. Bluetooth niezaimplementowany. Android w tym etapie
nie był budowany ani uruchamiany; ZIP Android Studio zawiera źródła, nie APK.

## Dostarczenie

Pełna lokalna instalacja: `engine/out/LittleFighters-mixed-online-2026-10-31`.
`Graj-Wszystkie-Mody.cmd` uruchamia mieszaną pulę; `Graj-Little-Fighters.cmd`
otwiera menu. Stare instalacje i ich ustawienia zachowane.

Publiczne ZIP-y `artifacts/*-mixed-online-2026-10-31.zip` zawierają silnik albo
źródła. Nie zawierają importowanych danych LF2/modów ani danych użytkowników.
Publikacja kodu i tych archiwów jest częścią prośby; zakres całości pozostaje
częściowo wykonany, z powyższymi jawnymi brakami.
