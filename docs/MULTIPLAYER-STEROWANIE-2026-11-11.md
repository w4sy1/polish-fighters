# Multiplayer i sterowanie — lokalny test 2026-11-11

Repozytorium: `C:\Users\01dwa\Documents\Little-Fighter-Work\Polish-Fighters`.
Gałąź początkowa i końcowa: `codex/local-leumas-combo-guide-2026-11-11`.
Punkt początkowy: `8b7030f296771979489a516459c0545bddc64cb0`, zgodny ze zdalnym HEAD
w chwili rozpoczęcia. Brak zmian w śledzonych plikach przed zadaniem; dwa zastane ZIP-y
w `artifacts` zachowano. Po testach zapisano commit `16c5a11` i wypchnięto roboczą gałąź na GitHuba. Nie utworzono release ani wdrożenia.
Kopia początkowych plików śledzonych: `work/baseline/tracked-source.zip` w katalogu rozmowy.

## Ustalone przyczyny

- Metadane zachowanych buildów Windows i Androida wskazywały różne odciski kodu
  natywnego. Nowe EXE i oba ABI APK sprawdzane są względem tych samych źródeł;
  budowanie APK odrzuca nieaktualne biblioteki również przy `-SkipNative`.
- Główne połączenia prowadziły do panelu kont. LAN nie potrzebuje tej usługi.
- W rzeczywistej próbie Android–Windows start meczu przerywał fałszywy alarm
  `simulation desynchronized`. Zapis obu urządzeń wskazał różnicę lokalnego
  `match.held.filters.window`; pozostała część porównanego fragmentu była identyczna.
- Krótkie akcje mogły zginąć podczas oczekiwania sieciowego. Uczestnicy musieli
  też drugi raz dołączać do wyboru postaci, mimo obecności w pokoju.
- Część ekranów nie miała powrotu do modułów, a panel modułów ukrywał przyczynę
  rozłączenia. Naciśnięcie ze starej sesji mogło przejść do nowego menu.
- Start lokalny haszował wszystkie zasoby wyłącznie na potrzeby przyszłej gry
  sieciowej. Android czytał duży ZIP przez niebuforowany strumień zasobów.
- Sieć użytkownika miała średnio 61 ms i maksymalnie 118 ms RTT z komputera do
  telefonu. Dwa kolejne oczekiwania protokołu na klatkę wzmacniały ten koszt.

## Wprowadzone zmiany

1. Wspólny przycisk `MENU / MODUŁY (F4)` i obsługa F4 przed oczekiwaniem sieciowym.
   Opuszczenie aktywnego meczu wymaga potwierdzenia; powrót nie zamyka aplikacji.
   Po rozłączeniu stare naciśnięcie jest odrzucane, a następny dotyk działa.
2. Zachowano istniejący układ klasyczny jako opcję 1 i udostępniono istniejący
   joystick z celowaniem jako opcję 2. Wybór zapisuje się we wspólnych ustawieniach,
   również z początkowego panelu Androida. Nie przepisano działającego gamepada.
3. Ekran wyboru postaci pokazuje numer własnego gracza i rzeczywiście zapisane
   klawisze/pada. Android pokazuje numer układu, ruch, zatwierdzanie i cofanie.
4. Bezpośredni wybór Wi‑Fi/hotspot albo Bluetooth PAN, następnie utworzenie pokoju
   lub dołączenie. Host nasłuchuje na `0.0.0.0`; klient używa IPv4 gospodarza.
   Domyślny TCP 12345; Windows przyjmuje też `IP:port`. Są walidacja i wskazówki IP.
   Konta i wcześniejsze tryby pozostawiono dostępne.
5. Kontrola stanu pomija możliwości renderowania, ale nadal wykrywa rzeczywiste
   różnice HP i wejść. Każde urządzenie ma własny slot; podłączone urządzenia
   automatycznie trafiają do odrębnych miejsc wyboru postaci.
6. Wejście kolejnej klatki wysyłane jest bez osobnego oczekiwania na potwierdzenie
   poprzedniej sumy. Serwer przechowuje najwyżej jedno wejście i nadal sprawdza
   sumy przed wykonaniem następnej klatki. Nie zastąpiono tego pustymi wejściami.
7. Android uruchomiony przez panel LAN utrzymuje tryb Wi‑Fi o niskim opóźnieniu
   wyłącznie na pierwszym planie. Zwalnia go przy pauzie/zamknięciu. Dodano tylko
   potrzebne normalne uprawnienie `WAKE_LOCK`; applicationId, signing i wersji
   testowej 11 / `0.11.0-local` nie zmieniano. Zasady mechanizmu opisuje
   [dokumentacja Androida](https://developer.android.com/reference/android/net/wifi/WifiManager#WIFI_MODE_FULL_LOW_LATENCY).
8. Odcisk zasobów jest liczony przy pierwszym wejściu do multiplayera, nie przed
   menu lokalnym. Kontrola zasobów nie została usunięta. Android buforuje odczyt ZIP.
   Dodano pomiary etapów startu i prywatne logi `game/runtime.log` / `game/session.log`.

## Sprawdzenia

- Windows: pełna kompilacja Release; testy rzeczywistego EXE, pięć scenariuszy
  powrotu, 10 profili × 2 układy i zapis ustawień, powrót po zerwaniu połączenia,
  akceptacja zgodnych buildów i odrzucenie starego silnika/zmienionych zasobów.
- Multiplayer natywny: 2 i 8 procesów, 120 klatek ze zgodnym stanem; osobna próba
  przez menu; celowo zmienione HP nadal przerywa sesję. To próby lokalne na Windowsie.
- TCP: nowo skompilowany runner, 2–8 klientów × 30 klatek, wejścia wysłane przed
  pełnym potwierdzeniem sum, fragmentacja, błędy protokołu, duplikaty i zła kolejność
  wejść oczekujących, rozłączenie, brak odpowiedzi i komendy nieuprawnionego gracza.
- Lua: zestawy obejmują regresję Windows/Android `filters`, bufor krótkich wejść,
  niezależne sloty, podpowiedzi, widoczność błędów i wszystkie wcześniejsze testy.
- Python: 53 testy, 52 zaliczone / 1 pominięty (ograniczenie tworzenia symlinków).
- Android: oba ABI ARM64/ARMv7 zbudowane; Gradle `assembleDebug` i 27 testów PASS.
  Lint nadal ma 27 wcześniejszych błędów w wygenerowanych źródłach SDL; kontroli
  nie wyłączono. Dokładny końcowy stan zapisano w raporcie w `outputs` rozmowy.
- APK: odciski natywne, biblioteki i zależności, CRC, zgodność ZIP ze źródłami,
  15 402 ścieżki logiczne / 7 798 unikalnych payloadów, podpis i wyrównanie.

## Pomiary i granice

Windows, wspólna pula, trzy naprzemienne próby bez okna z rozgrzanym cache:
mediana startu 5,55 → 1,25 s. Pomiar etapów wskazał około 4,21 s na dotychczasowe
haszowanie sieciowe, około 1,15 s na pakiety, około 0,01 s na inicjalizację Lua.
Nie jest to pomiar pełnego startu z zimnego dysku ani działania wszystkich kampanii.

Po precyzyjnym timerze lokalny test 2 procesów / 120 klatek trwał 1,134 s; 8 procesów: 1,503 s.
Te czasy obejmują przygotowanie testu i nie oznaczają FPS telefonu ani testu radia.

Raptor 5G / Android 14 i Windows faktycznie połączyły się przez Wi‑Fi. Użytkownik
potwierdził wspólną walkę i niezależne sterowanie po usunięciu błędnego porównania
możliwości okna. Zgłoszone później spowolnienie uruchomiło poprawkę oczekiwań, Wi‑Fi
i precyzyjnego timera. Użytkownik nie podłącza ponownie telefonu. Końcowa poprawka
płynności i nowe podpowiedzi nie zostały zainstalowane ani sprawdzone fizycznie.

Poprzednie przygotowanie danych Androida po aktualizacji trwało około 85,9 s;
pełnego porównawczego pomiaru po buforowaniu nie wykonano. Pierwsze rozpakowanie dużej
paczki i późniejszy start z gotowymi danymi to różne etapy.

Bluetooth PAN i radio dwóch telefonów nie zostały potwierdzone fizycznie. PAN
wymaga konfiguracji parowania i udostępniania sieci w systemach. Wspólna pula
pozostaje eksperymentalna, z dotychczasowym ograniczeniem sieci w głównym menu.
Nie potwierdzono wielogodzinnej gry, wszystkich kampanii ani wszystkich par urządzeń.

Za osobną zgodą użytkownika dodano regułę zapory `PolishFighters-LAN-Test-20261111`:
tylko nowy testowy EXE, przychodzący TCP 12345, `LocalSubnet`. Nie zmieniono DNS,
hostingu ani kategorii sieci. Nie utworzono emulatorów i nie wdrożono serwera.

Zmiany odpowiadają pierwotnemu zakresowi oraz późniejszej prośbie o płynność
i podpowiedzi sterowania. Weryfikacja fizyczna końcowej poprawki płynności pozostaje
otwarta; nie jest to deklaracja ukończenia wszystkich testów urządzeń.
