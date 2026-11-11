Archiwum planu z 31.10.2026. Opisuje owczesne braki; aktualny stan: PROJECT-STATUS.md.

# Polish Fighters — prompty do zwykłego ChatGPT

Stan sprawdzony 31.10.2026. To zestaw zadań do kontynuowania prac, nie informacja,
że wymienione niżej braki zostały już naprawione.

## Jak używać

1. Załącz do nowego czatu ZIP kodu wskazany poniżej i wklej PROMPT 0.
2. Następnie wysyłaj pojedynczo prompty 1–12 w kolejności. Dokończ jeden etap,
   zanim rozpoczniesz następny. Po etapie zachowaj ZIP zmian i raport.
3. Przy zmianie czatu dołącz aktualny kod oraz ostatni raport, ponownie wklej
   PROMPT 0. Pliki z wcześniejszego czatu nie przechodzą automatycznie do nowego.
4. Zwykły czat pracuje na plikach, które rzeczywiście otrzyma. Gdy ma środowisko
   do wykonywania kodu, może tworzyć i testować pliki w tym środowisku. Dostęp
   do dysku Windows, Android Studio, GitHuba i urządzeń trzeba potwierdzić osobno.
   Wynik bez tych narzędzi to kod do pobrania i polecenia do uruchomienia lokalnie.

Kod źródłowy ZIP:
https://github.com/w4sy1/polish-fighters/raw/refs/heads/codex/maps-build-2026-10-30/artifacts/PolishFighters-AndroidStudio-mixed-online-2026-10-31.zip

Repozytorium: https://github.com/w4sy1/polish-fighters
Branch: codex/maps-build-2026-10-30
Ostatni potwierdzony commit: dd5048e0430a25b45794ff833f6bd2397e03825d

ZIP nie zawiera importowanych danych LF2 i modów. Do pracy nad konkretną
postacią/mapą trzeba dołączyć odpowiednie lokalne dane, manifest i raport importu.
Nie przesyłaj userdata, baz kont, tokenów, plików .env ani kluczy podpisywania.

Lokalny projekt:
C:\Users\01dwa\Documents\Little-Fighter-Work\Polish-Fighters

Pełna lokalna instalacja:
C:\Users\01dwa\Documents\Little-Fighter-Work\Polish-Fighters\engine\out\LittleFighters-mixed-online-2026-10-31

## PROMPT 0 — wspólny kontekst i zasady, wklej na początek

```text
Kontynuuj istniejący projekt Little Fighters / Polish Fighters z załączonego kodu.
Nie twórz nowej gry od zera. Najpierw sprawdź pliki i raporty, potem wprowadzaj
rzeczywiste, ograniczone zmiany. Odpowiadaj po polsku.

Źródło: github.com/w4sy1/polish-fighters, branch codex/maps-build-2026-10-30,
punkt odniesienia dd5048e0430a25b45794ff833f6bd2397e03825d z 31.10.2026.
Lokalna ścieżka użytkownika to:
C:\Users\01dwa\Documents\Little-Fighter-Work\Polish-Fighters
Nie zakładaj, że masz dostęp do tego dysku lub mojego GitHuba. Ustal, jakie
załączone pliki i narzędzia rzeczywiście widzisz. Jeśli czegoś brakuje, wskaż
konkretne niezbędne pliki, a w tym czasie wykonuj niezależną część zadania.

Przeczytaj PROJECT-STATUS.md, LITTLE_FIGHTERS_WINDOWS.md,
validation/mixed-2026-10-31/REPORT.md i instrukcje projektu. Pierwsza sekcja
statusu jest aktualna, starsze sekcje to historia. Repozytorium i ZIP źródeł
nie zawierają importowanych assets LF2/modów; nie udawaj ich obecności.

Stan bazowy:
- Jest natywny silnik C++/Lua, własna czwórka w polish-originals i osobne mody:
  LF4 Turbo, DBZ, One Piece, Kate, Reinforced, NTSD/Naruto, Bleach oraz baza LF2.
- Jest eksperymentalny mixed-all: 932 obiekty, nie 932 postacie, i 128 map.
  ID i część zależności są remapowane; wybór pakietów zmienia mieszaną pulę.
  Autorskie mechaniki, AI i kampanie mieszane nie są jeszcze kompletne.
- Są logowanie/rejestracja i katalog pokoi sprawdzone z lokalnym serwerem.
  Dwa procesy połączyły się przez katalog i rozegrały 120 klatek TCP zgodnie.
  Nie ma publicznego hostingu. Relay nie jest podłączony do nowego GUI.
  Bluetooth nie jest zaimplementowany. Android/APK nie jest potwierdzony.
- DBZ przełącza sceny między etapami. Mirror/questy pozostają niepełne.
- Bleach: nadal brakuje obiektów 284/action83 i 151/action30.
- Przegląd wymaga 11 uszkodzonych/niepełnych arkuszy: Bleach6, Kate2, Reinforced3.
- Krótkie próby renderowania wszystkich128 map przeszły. To nie są pełne testy.
  Wspomagana próba 48/56 kampanii zakończona; DBZ mirror ma brakujące selektory
  8002–8008, One Piece ma nierozpoznane122 we wspólnym pliku etapów,
  LF4 survival nie zakończył się w limicie20000 klatek, co nie dowodzi błędu.

Zasady:
1. Zachowaj oryginalne postacie, dane i zachowania LF2/modów. Nasze postacie:
   Wasyl, Szymonoko/SZ, Mega Ninja Jaś, boss Skibidi Sigma Tata. Modyfikacje
   zgodności rób w adapterach lub osobnych kopiach, z dowodami pochodzenia.
2. Domyślne sterowanie ma pozostać LF2; wygodny preset to WASD + NUM7 atak,
   NUM8 skok, NUM9 blok. Nie pomyl klawiatury numerycznej z cyframi nad literami.
   Zachowaj istniejące ustawienia użytkownika w userdata/common.
3. Nie usuwaj funkcji ani nie rób dużego refaktoru bez potrzeby. Jeśli jest Git,
   sprawdź branch/status/diff. Zachowaj punkt przywracania przed ryzykowną zmianą.
4. Nie uruchamiaj oryginalnych pobranych EXE/DLL do odzyskiwania danych.
   Brakujących zasobów nie zastępuj fikcyjnymi obiektami jako rzekomo odzyskanymi.
5. Nie zapisuj haseł/tokenów w kodzie, ustawieniach, logach i ZIP-ach.
6. Wykonuj pracę, nie kończ na planie. Kontynuuj do ukończenia konkretnego etapu
   lub rzeczywistej blokady. Nie obiecuj pracy po zakończeniu odpowiedzi.
7. Jeśli możesz edytować załączony projekt, oddaj ZIP zmienionych plików
   z zachowaną strukturą, listą zmian, podstawą wersji i poleceniami testów.
   Jeśli nie możesz utworzyć ZIP-a, oddaj dokładny patch lub pełne pliki.
8. Oddziel: zaimplementowane, przetestowane tutaj, do sprawdzenia na Windows,
   do sprawdzenia na telefonie i zablokowane brakiem danych/hostingu.
   Nie nazywaj testu wspomaganego naturalnym przejściem kampanii.
9. Na końcu etapu podaj zmienione pliki, wyniki testów, ograniczenia i następny
   krok. Aktualizuj status projektu, żeby kolejne etapy nie zaczynały od nowa.
10. Buildów, uploadów i testów urządzeń nie deklaruj bez wykonania. Nie publikuj
    release ani nie wdrażaj produkcji bez osobnej zgody. Przygotowanie patcha
    nie oznacza automatycznie jego zastosowania na moim laptopie.

Teraz wykonuj zadanie z mojego następnego promptu zgodnie z tym kontekstem.
```

## PROMPT 1 — audyt i uporządkowanie listy braków

```text
Wykonaj audyt załączonej wersji według PROMPTU0. Nie przepisuj działających
modułów. Sprawdź dokumentację, katalog pakietów, UI, sterowanie, kampanie,
postacie, sieć, Android i narzędzia pakowania. Zestaw twierdzenia raportów
z faktycznie dostępnym kodem i dowodami.

Utwórz BACKLOG-CONTINUATION.md: ID zadania, stan, konkretne pliki, zależności,
priorytet, kryterium odbioru i brakujące dane. Wypisz wszystkie znane problemy,
bez dopisywania procentu ukończenia bez podstaw. Wyraźnie oddziel listę
obiektów od liczby grywalnych postaci. Sprawdź martwe przyciski, mylące napisy
i funkcje reklamowane w GUI, które nie mają implementacji.

Wykonaj od razu małe pewne poprawki wykryte podczas audytu i dostępne testy.
Oddaj plik backlogu oraz patch/ZIP zmian. Nie przedstawiaj samej listy planów
jako naprawienia gry. Ustal precyzyjną podstawę następnych etapów.
```

## PROMPT 2 — ładny, spójny interfejs całej gry

```text
Dopracuj istniejący interfejs Little Fighters / Polish Fighters w kodzie Lua,
bez zastępowania gry stroną WWW. Zachowaj obecne funkcje i routing ekranów.
Najpierw obejrzyj rzeczywiste ekrany, jeśli dostarczono obrazy lub renderer.

Kierunek: dopracowane menu gry 2D, granatowe półprzezroczyste panele, czerwone
akcenty Polish Fighters, czytelne polskie litery, oryginalne tło LF2 wyraźnie
widoczne, bez zalewania obrazu ciemną nakładką. Spójne odstępy, stany hover,
focus, aktywne/nieaktywne przyciski, komunikaty ładowania, błędów i braków danych.
Ekrany mają dobrze wyglądać w bazowym794×550 i przy skalowaniu16:9, bez
przycinania tekstów, elementów poza ekranem i nakładających się pól.

Ujednolić: menu główne, bibliotekę i wybór aktywnych modów, profil moda,
wybór postaci z dużymi ikonami twarzy, mapy, kampanie, sterowanie, ustawienia,
logowanie/pokoje, historię, odblokowania, pauzę i wyniki. Dla własnych postaci
zachować portrety120×120 i HUD40×45. Czytelnie pokazać aktualny pakiet i tryb
eksperymentalny. Zachować Little Fighters jako wspólny tytuł i Polish Fighters
jako nazwę własnego zestawu; spisać tę decyzję w jednym miejscu.

Menu ma zapewniać: wszystkie mody razem, Polish Fighters, LF2, LF4Turbo, DBZ,
OnePiece, Kate, Reinforced, NTSD/Naruto, Bleach, dobór pakietów, sterowanie,
ustawienia, grę lokalną, sieć, historię/odblokowania i wyjście. Zastosuj
czytelną nawigację i przewijanie tam, gdzie potrzeba; nie upychaj wszystkiego.

Wszystkie akcje mają działać myszą, klawiaturą i padem. Na Androidzie uwzględnij
dotyk i bezpieczne obszary ekranu. Brak hostingu nie może blokować gry lokalnej.
Używaj istniejących zasobów z dostarczonym pochodzeniem. Jeżeli tła nie ma
w załączniku, wskaż potrzebny plik; nie twierdź, że obejrzałeś nieobecny obraz.

Oddaj rzeczywiste zmiany UI i zrzuty renderera, jeśli możesz go uruchomić.
Makiety oznacz jako makiety. Zmiany sprawdź także przy najdłuższych napisach.
```

## PROMPT 3 — wspólna pula wszystkich modów i zgodność mechanik

```text
Dokończ zgodność istniejącego mixed-all. Zacznij od tools/build_mixed_pack.py,
content-packs/mixed-all i adapterów silnika. Nie zmieniaj oryginalnych importów.

Zrób audyt wszystkich odwołań zależnych od starych ID: opoint/oid, transformacji,
efektów, broni, przywołań, klonów, specjalnych stanów i porównań w Lua/C++.
Sprawdź także specjalne zachowania silnika LF2 zakodowane pod oryginalnymi ID.
Samo przepisanie oid nie potwierdza zgodności. Zastosuj mapowanie pochodzenia
pakiet+stareID i adaptery, które nie zmieniają znaczenia mechanik innych modów.

Zachowaj unikalne ID i zależności efektów, również przy wyłączonym pakiecie.
Napraw odświeżanie wybranej puli, losowanie, ukryte postacie, puste wybory,
duplikaty, pełną listę map oraz bezpieczne raportowanie brakujących obiektów.
Braki źródła nie mogą prowadzić do losowego obiektu innego moda.

Zbadaj odtwarzalność generacji i weryfikację zgodności danych dwóch klientów.
Sieć mieszanego profilu odblokuj dopiero po testach wspólnego wyboru pakietów,
fingerprintu i deterministycznej symulacji. Zachowaj osobne oryginalne kampanie;
kampanii mieszanych nie reklamuj, dopóki nie mają własnej implementacji/testów.

Oddaj testy mechanik przedstawicieli każdego moda, raport braków i zmienione
pliki. Do testów wymagających brakujących assets poproś o konkretny pakiet.
```

## PROMPT 4 — cztery własne postacie, animacje, ataki, AI i balans

```text
Dopracuj polish-originals: Wasyl, Szymonoko/SZ, Mega Ninja Jaś i boss Skibidi
Sigma Tata. Odczytaj istniejące definicje i ustalone umiejętności. Nie wymyślaj
nowej tożsamości postaci ani nie zmieniaj oryginalnych bohaterów LF2/modów.

Sprawdź skalę względem LF2, linię stóp, kierunek, odbicie, portrety120×120,
HUD40×45 i kompletny zestaw animacji: stanie, chód, bieg, skok, lądowanie,
atak, blok, obrażenia, upadek, podniesienie, śmierć i umiejętności.
Usuń błędne wycinki, miganie, przenikanie i używanie jednej pozy do wszystkiego.
Jeżeli potrzebne są nowe rysunki, oddziel zadanie graficzne od naprawy kodu.

Dla każdego ataku sprawdź wejście, combo, czas, zasięg, hitbox/hurtbox, koszt,
obrażenia, efekt i dźwięk. SZ ma strzelać podstawowym atakiem bez many, również
po krótkim tapnięciu. Dopilnuj limitów klonów, teleportu w granicach mapy,
przywołań, mieczy, śluzu i faz bossa zgodnie z obecną specyfikacją.

Dodaj adekwatne AI: dystans, obrona, uniki, dobór umiejętności i cooldowny;
bez nieskończonego spamowania, leczenia, zasobów czy mnożenia klonów.
Przygotuj jawne tabele balansu i kontrolowane próby obrażeń/kontr.

Oddaj działające poprawki, tabelę ruchów i faktyczne wyniki dostępnych testów.
Grafiki koncepcyjne nie mogą zastępować gotowych arkuszy w raporcie.
```

## PROMPT 5 — Bleach i brakujące rysunki Kate/Reinforced

```text
Zajmij się brakującą zawartością z zachowaniem oryginałów i pochodzenia danych.
Bleach: szukamy obiektu284 z akcją83 oraz151 z akcją30. Prześledź wszystkie
odwołania, warianty katalogów, raporty odzysku i dostępne archiwa źródłowe.
Nie podstawiaj dowolnego pocisku pod brakujące ID. Jeśli źródła nie zawierają
obiektu, opisz dokładnie czego brakuje i jakie legalnie dostępne dane są potrzebne.

Sprawdź11 arkuszy: Bleach6, Kate2, Reinforced3. Znajdź dokładne listy w raportach
projektu. Zestaw rozmiary obrazów, siatkę, liczbę klatek i aktywne odwołania.
Obejrzyj rzeczywiste wycinki; clamp chroniący odczyt nie odtwarza rysunków.
Popraw pewne błędy indeksów; brakujące rysunki odzyskuj z potwierdzonego źródła
albo oznacz jako nowe autorskie odtworzenie, wymagające osobnej oceny.

Sprawdź transformacje Bleach, przełączanie rekordów i offsets po transformacji.
Sprawdź zgodność Kate/Reinforced z LF2 1.9c na podstawie konkretnych danych
wersji, a nie samej nazwy folderu. Zachowaj odzyskane dźwięki i wcześniejsze
naprawy Kate99/action390/392. Nie przywracaj starych braków już naprawionych.

Stosuj statyczne narzędzia odzysku; nie uruchamiaj obcych oryginalnych EXE/DLL.
Oddaj pliki, manifest pochodzenia i dowody, co odzyskano, a czego nadal brak.
```

## PROMPT 6 — DBZ, NTSD, One Piece, LF4 Turbo i pełne kampanie

```text
Dokończ adaptery kampanii, zaczynając od faktycznych blokad obecnej wersji.
Nie kasuj problematycznych przeciwników i faz tylko po to, by test przeszedł.

DBZ: zachowaj istniejące przełączanie scen. Dokończ znaczenie dynamicznych
obiektów, selektorów mirror8001–8008, questów, autorskich warunków przejścia,
muzyki i rozszerzonych klatek. Bieżący MirrorMatch zgłasza brak8002–8008;
ustal ich rolę w oryginalnej semantyce, zamiast tworzyć przypadkowe postacie.
Rozdziel przeniesione mechaniki od zachowań oryginalnego EXE/AngelScript,
których obecny silnik jeszcze nie realizuje.

OnePiece: wyjaśnij nierozpoznaneID122 we wspólnym pliku etapów, które blokuje
obecny preflight sześciu prób rozdziałów. Sprawdź czy to obiekt, selektor,
błąd danych czy ograniczenie samego testu. Sprawdź muzykę i przejścia.
NTSD: regresja normalizacji liczb32-bit, odwołań do assets i etapów.
LF4Turbo: całość przygód, bossowie i survival; brak końca survivalu po20000
klatek sam w sobie nie jest błędem. Określ jego oryginalne warunki zakończenia.

Przejrzyj też przygody Bleach/Kate/Reinforced/LF2. Testy podziel na: parsowanie,
start etapu, render, wspomagane przejścia i naturalną pełną rozgrywkę.
Test usuwający przeciwników i teleportujący gracza nie dowodzi pełnego działania.
Zrób tabelę kampania→etap→warunek→wynik→blokada. Oddaj poprawki i scenariusze
do ręcznego przejścia tam, gdzie nie możesz wykonać naturalnej rozgrywki.
```

## PROMPT 7 — klawiatura, mysz, pad i dwa sterowania Android

```text
Dopracuj istniejące sterowanie i ekran przypisań, bez resetowania zapisów.
Domyślne ustawienia zachowaj zgodne z LF2. Preset dla mnie:
WASD + NUM7 atak / NUM8 skok / NUM9 blok, wyłącznie klawiatura numeryczna.

Sprawdź zmianę przypisań dla graczy1–4, konflikty, zapis/anulowanie/reset,
klawiaturę, klawiaturę+mysz, pady, D-pad, analog, podłączanie/odłączanie pada,
NumLock i krótkie tapnięcia. Nie przypisuj kliknięcia otwierającego pole jako
nowego przycisku. Zachowaj zwykłe LF2combo. Informacje o aktualnym sterowaniu
muszą zgadzać się z konfiguracją i być widoczne przed grą.

Android ma mieć dwa wybierane układy:
A. Nowoczesny inspirowany BrawlStars: lewy joystick ruchu, wygodny atak po prawej,
   obok skok i blok; opcjonalne umiejętności tylko gdy pasują do modelu walki.
B. Klasyczny LF: strzałki/D-pad i trzy przyciski atak, skok, blok.
Gra jest side-scrollerem: nie dodawaj pozornego celowania360°, którego silnik
nie obsługuje. Wyjaśnij, jak nowy układ wyraża istniejące kombinacje LF2.

Zapewnij multitouch, regulację rozmiaru/pozycji/przezroczystości, marginesy
bezpieczne, zwalnianie wejść po utracie focusu i brak blokowania gestów systemu.
Kod odblokowania na Androidzie wpisujemy przez wyraźny przycisk otwierający
pole tekstowe/klawiaturę ekranową, z zatwierdzeniem i wynikiem walidacji.
Zachowaj obecny kod POLISHFIGHTERS i zgodność istniejącego postępu.
Oddaj implementację oraz testy logiki; fizyczny pad/telefon oznacz osobno.
```

## PROMPT 8 — konta, publiczne pokoje i rzeczywisty Internet

```text
Rozwiń istniejące online_client/online_screen/online_network/online_flow,
tools/account_service.py i room_relay.py. Nie zastępuj działającego klienta
logowania kolejnym pustym ekranem. Użytkownik nie ma serwera ani domeny.

Sprawdź rejestrację, logowanie, wylogowanie, odzyskiwanie konta, wygaśnięcie
sesji, błędy, anulowanie publikacji, heartbeat, usuwanie martwych pokoi,
paginację, prywatność i niezgodność wersji/profili/danych pakietów.
Publiczna lista pokoi nie oznacza automatycznie osiągalności gospodarza.
Obecnie gra używa bezpośredniego TCP/IPv4. Zintegruj istniejący relay z klientem
i GUI, jeśli jego protokół pasuje; inaczej przygotuj ograniczony adapter
z rzeczywistym przepływem bajtów, uwierzytelnieniem i limitami.

Dodaj czytelne stany łączenia, odmowy, rozłączenia, opóźnień i timeoutów.
Przetestuj deterministyczną rozgrywkę, nie tylko endpointy kont.
Nie zapisuj haseł/tokenów w ustawieniach/replayach/logach. Zachowaj HTTPS
zdalnie i izolację tokenu względem origin serwera. Nie obchodź walidacji TLS.

Przygotuj kompletny, przenośny pakiet uruchomienia usługi, konfigurację
reverseproxy/TLS, trwałą bazę, backup i diagnostykę. Nie wdrażaj usługi na
fikcyjnym adresie i nie zakładaj kont/płatnych usług. Jeżeli proponujesz
hosting, sprawdź aktualne warunki i oddziel darmowy wariant od kosztów.

Oddaj działające poprawki i testy lokalne end-to-end. Test prawdziwego Internetu
i NAT zostaje oddzielnym kryterium wymagającym dostępnej infrastruktury.
```

## PROMPT 9 — Bluetooth i uprawnienia Android/Windows

```text
Zaprojektuj i zaimplementuj rzeczywisty transport Bluetooth w istniejącej
architekturze sieci, jeśli dostępne narzędzia i platforma to umożliwiają.
Najpierw sprawdź moduły Android/JNI, port transportu i wymagany strumień danych.
Nie oznaczaj Bluetooth jako gotowego po dodaniu przycisku lub uprawnień.

Określ wspierane pary urządzeń Android–Android i Windows–Android/Windows,
role gospodarza, parowanie, discovery, wybór urządzenia, framing, limity,
timeouty, anulowanie, utratę połączenia i zgodność protokołu gry. Dobierz
transport do wymaganej komunikacji na podstawie faktycznej kompatybilności.

Android: dobierz wyłącznie uprawnienia potrzebne do zaimplementowanych funkcji,
z uwzględnieniem wersji systemu, runtime permissions, odmowy i cofnięcia zgody.
Nie dodawaj zbędnego dostępu do kontaktów, mikrofonu, zdjęć ani całego dysku.
Sprawdź Manifest oraz API na oficjalnej dokumentacji dla użytego targetSDK.

Windows: przygotuj opcjonalny, jawny skrypt reguły zapory wyłącznie dla naszego
EXE, rzeczywiście używanego portu i uzasadnionego profilu sieci. Dodaj możliwość
usunięcia tej reguły. Nie wyłączaj zapory i nie dodawaj szerokich wyjątków.
Nie uruchamiaj automatycznie operacji wymagających administratora.

Oddaj implementację i plan/testy połączenia. Jeśli brakuje sprzętu, określ
precyzyjnie co skompilowano, a czego nie sprawdzono fizycznie. Funkcja
częściowa ma być wyraźnie oznaczona w GUI i statusie.
```

## PROMPT 10 — historia, odblokowania i własny tryb przygód

```text
Rozwiń istniejące chronicle/progression, historię gier i odblokowania zamiast
tworzyć drugie konkurencyjne systemy. Najpierw sprawdź ich obecny zapis i testy.

Historia: profil i aktywne pakiety, mapa/kampania, uczestnicy, tryb, wynik,
czas gry i ewentualne nagranie, jeśli silnik ma te dane. Dodaj filtrowanie,
szczegóły, limit rozmiaru i bezpieczną migrację. Nie zapisuj danych konta
ani tokenów w historii. Wynik ma pochodzić z faktycznego zakończenia gry.

Odblokowania: jasne warunki, widoczny postęp, nagrody bez wielokrotnego farmienia
tego samego zakończenia, zapis odporny na błąd, oddzielne zasady lokalne i sieciowe.
Zachowaj kod POLISHFIGHTERS do odblokowania całej lokalnej puli i przycisk
wpisania kodu na Androidzie. Przywrócenie ustawień sterowania nie może kasować
odblokowań. W sieci wynik/sesja mają zachowywać wspólne reguły.

Opracuj autorski tryb przygód Polish Fighters, który korzysta z istniejącego
silnika: wybór misji, rozgałęzienia, cele inne niż wyłącznie zabicie wszystkich,
bossowie, nagrody i kooperacja tam, gdzie rzeczywiście działa. Zapisz specyfikację
i dostarcz jedną kompletną, grywalną misję pokazującą pomysł. Nie nazywaj jej
unikalną na świecie bez dowodów. Pozostałe misje oznacz jako plan, nie gotowce.
Nie zmieniaj przy tym oryginalnych przygód LF2 i modów.
```

## PROMPT 11 — pełne tłumaczenia i dostępność

```text
Przejrzyj wszystkie widoczne napisy w Lua/C++/Android i konfiguracji menu.
Ujednolić terminologię: atak, skok, blok, gospodarz, dołącz, pokój, pakiet,
postać, kampania, historia i odblokowania. Popraw polskie znaki, literówki,
teksty bez ogonków i błędne tłumaczenia. Zachowaj nazwy własne oryginalnych modów.

Wykorzystaj istniejący system i18n; nie twórz równoległego słownika.
Usuń mieszanie polskiego i angielskiego w ekranach, które są lokalizowane.
Dla innych planowanych języków określ faktyczne pokrycie i fallback; nie
deklaruj pełnego tłumaczenia po skopiowaniu polskiego/angielskiego do innych locale.

Sprawdź kontrast, czytelność, długie napisy, skalowanie, fokus pada/klawiatury,
komunikaty błędów i zrozumiałość funkcji niedostępnych. Pokaż brak hostingu,
brak danych i tryb eksperymentalny tak, żeby użytkownik wiedział co zrobić.
Ekran logowania ma umożliwiać wygodną grę lokalną bez konta.

Oddaj poprawione pliki, raport pokrycia tłumaczeń, sprawdzenie kluczy i zrzuty
tam, gdzie dostępny jest renderer. Nie przedstawiaj samych liczników kluczy
jako ręcznej kontroli jakości wszystkich tekstów.
```

## PROMPT 12 — menedżer modów, aktualizacje, Windows EXE i Android Studio

```text
Przygotuj końcowe dostarczenie aktualnej wersji, zachowując istniejące narzędzia
pakowania. Najpierw zamknij niezbędne zależności wcześniejszych etapów.

Menedżer pakietów: zainstalowane/dostępne/aktywne mody, pobieranie, postęp,
anulowanie, weryfikacja SHA256, wersje i zgodność silnika, bezpieczne rozpakowanie,
atomowa instalacja, kopia poprzedniej wersji i przywrócenie po błędzie.
Aktualizacja nie może nadpisywać userdata. Manifest aktualizacji ma wskazywać
rzeczywiste istniejące pliki, bez fikcyjnych URL-i i obiecywania danych, których
nie opublikowano. Zachowaj zasady dystrybucji i pochodzenie zasobów.

Windows: zbuduj własny silnik tylko jeśli masz właściwe narzędzia i platformę.
Przygotuj portable z DLL/scripts/licenses, launcherem i instrukcją. Osobno
zdefiniuj publiczny core bez importowanych danych i pełną lokalną instalację.
Zweryfikuj uruchomienie po rozpakowaniu, konfigurację, wybór pakietu, walkę,
brakujące assets i zachowanie zapisów. Sam EXE bez DLL nie jest pełną paczką.

Android: sprawdź istniejący Gradle/CMake/JNI, natywne biblioteki, ABI,
Manifest, runtime permissions, wersje, dotyk, lifecycle i ścieżki zasobów.
Nie zmieniaj przypadkowo applicationId, signing, Firebase ani produkcyjnych
konfiguracji. Uruchom odpowiedni Gradle build/test/lint, jeśli środowisko pozwala.
Oddaj projekt Android Studio i instrukcję importu. APK deklaruj dopiero po
rzeczywistym buildzie; działanie na telefonie dopiero po teście urządzenia.

Uruchom dostępne testy Python/Lua/C++/sieci i istotne próby gry. Sprawdź diff,
nieśledzone pliki, sekrety, bazy, userdata, ZIP CRC i SHA256. Uaktualnij
PROJECT-STATUS.md, instrukcję i raport ograniczeń. Nie mów, że wszystko gotowe,
jeżeli pozostały istotne braki kampanii, grafiki, Bluetooth albo testów urządzeń.

Jeśli nie masz dostępu do mojego lokalnego repozytorium/GitHuba, oddaj gotowy
ZIP/patch i dokładne komendy do przejrzenia, zastosowania, testów i zwykłego
commita/pushu. Nie udawaj wykonania uploadu. Publikacja release i wdrożenie
produkcji wymagają osobnej decyzji. Dołącz końcowy prompt kontynuacji z listą
faktycznie zmienionych plików i niezamkniętych problemów.
```

## PROMPT KONTYNUACJI — kiedy odpowiedź się urwie

```text
Kontynuuj ten sam etap od ostatniego faktycznie ukończonego pliku. Nie zaczynaj
od nowa i nie powtarzaj całego planu. Uwzględnij dotychczasowe poprawki.
Najpierw sprawdź, które pliki i wyniki nadal masz dostępne. Pracuj dalej do
konkretnego wyniku; na końcu oddaj aktualny ZIP/patch, raport testów oraz listę
rzeczy zablokowanych. Jeśli nie możesz wykonać operacji w tym środowisku,
powiedz wprost i przygotuj dokładne pliki oraz polecenia do uruchomienia lokalnie.
```

## Gdy czat poprosi o lokalne testy

W katalogu projektu, po świadomym zastosowaniu otrzymanego patcha:

```powershell
git status --short
git branch --show-current
git diff --check
git diff --stat
& ./.build-venv/Scripts/python.exe tools/test_lua_scripts.py
& ./.build-venv/Scripts/python.exe -m unittest discover -s tests -p 'test_*.py'
```

Istniejące próby natywne wymagają zbudowanego własnego EXE, odpowiednich DLL
i lokalnych danych gry. Polecenia są punktami odniesienia dla wersji bazowej:

```powershell
& ./.build-venv/Scripts/python.exe -X utf8 tools/probe_mixed_pack.py
& ./.build-venv/Scripts/python.exe -X utf8 tools/probe_online_native.py
& ./.build-venv/Scripts/python.exe -X utf8 tools/probe_online_room.py
& ./.build-venv/Scripts/python.exe -X utf8 tools/probe_dbz_transition.py
```

Nie uruchamiaj automatycznie nieprzejrzanych skryptów otrzymanych w czacie.
Nie zastępuj całego projektu starszym ZIP-em: zmiany stosuj do właściwej wersji,
z zachowaniem własnych plików i userdata.
