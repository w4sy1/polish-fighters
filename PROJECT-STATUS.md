## 2026-11-12 — Polish Little Fighters 0.13.0: klasyczne menu (testowe)

Przebudowano główne menu w stylu LF2, siedem trybów, przepływ moduł/gracze, PL/EN, kierunki pada i Android. Zachowano naprawę indeksu ZIP. Dalsze testy zatrzymano na prośbę użytkownika; końcowe poprawki tekstów tylko zbudowano/spakowano. Brak testu fizycznego telefonu i publicznego backendu. Szczegóły, granice dowodów i lista plików: [raport 0.13.0](docs/CLASSIC-MENU-0.13.0-2026-11-12.md).

# Android 0.12.2 — naprawa startu i nowy ekran, 2026-11-12

Naprawiono „Brak indeksu paczki gry”: manifest był na końcu ZIP zamiast na początku.
Paczka wygenerowana ponownie; walidacja sprawdza kolejność i wszystkie payloady.
Gotowy APK przeszedł rzeczywisty kod przygotowania gry na pustym katalogu w teście JVM.
Gradle odrzuca błędną kolejność indeksu. 52 przypadki Androida PASS, Python 57 PASS / 1 SKIP.
Lint 0 błędów / 35 ostrzeżeń. Nowe ekrany przygotowania i startu Androida wyrenderowane i sprawdzone.
APK code 14 / 0.12.2-start. Bez prób fizycznego telefonu; kod C++ i Windows bez zmian.
Raport: docs/START-ANDROID-0.12.2-2026-11-12.md. Wydanie publiczne: https://github.com/w4sy1/polish-fighters/releases/tag/android-start-0.12.2-2026-11-12
SHA256 i pobieranie bez logowania potwierdzone. Lokalny APK i jego kopie wyjsciowe
(1.01 GiB) przeniesiono do Kosza. Zweryfikowane dane budowy i biblioteki pozostaja
do kolejnego zamowionego etapu klasycznego menu; Kosza nie oprozniano.

---
# SDL Android — opublikowana 0.12.1, 2026-11-12

Usunięto 27 błędów Lint SDL: odmowa uprawnień Bluetooth, API pióra i odbiornik USB.
`lintDebug`: 0 błędów / 39 ostrzeżeń. 43 testy Androida PASS; Python 54 PASS / 1 SKIP.
APK code 13 / 0.12.1-sdl zbudowany, zawartość, podpis i wyrównanie PASS.
Poprawka jest nakładana po rozpakowaniu SDL w przygotowaniu lokalnym i Linux/CI.
Źródła C++ i dane gry niezmienione; Windows pozostaje 0.12.0.
Bez próby fizycznego Bluetooth/USB i bez potwierdzenia wszystkich zacięć telefonu.
Raport: docs/SDL-ANDROID-0.12.1-2026-11-12.md. Publiczny APK: https://github.com/w4sy1/polish-fighters/releases/tag/android-sdl-0.12.1-2026-11-12
Rozmiar i SHA256 GitHuba zgodne, pobieranie bez logowania potwierdzone.
Po publikacji lokalny APK i katalogi generowane (3.13 GiB) przeniesiono do Kosza.
Źródła i ustawienia pozostały, Kosza nie opróżniano.

---
# Poprawki sterowania i F4 — 0.12.0 opublikowana, 2026-11-12

Atak reaguje przy naciśnięciu w obu układach; F4 / POSTACIE podczas walki wraca
do wyboru postaci. Wybrany pojedynczy moduł Androida otwiera własne menu.
Usunięto stare znaczniki gotowości po ponownym wyborze. Bufor chroni krótkie ruchy i F4,
również podczas oczekiwania sieciowego. Testy Lua, Python,
natywne ruchu/ataku oraz 2/8 procesów sieciowych PASS; APK 12 / 0.12.0-controls
zbudowany i testy Androida PASS. Lint ma 27 wcześniejszych błędów SDL.
Nie odtworzono zgłoszonych lokalnych zacięć na telefonie; ADB bez urządzeń.
Całe zgłoszenie nie jest jeszcze potwierdzone jako rozwiązane.
Raport: docs/POPRAWKI-0.12-2026-11-12.md. Publiczne APK i pełny ZIP: https://github.com/w4sy1/polish-fighters/releases/tag/controls-back-0.12.0-2026-11-12
Rozmiary i SHA256 GitHuba oraz pobieranie bez logowania potwierdzone.
Lokalne wersje gry, paczki i wygenerowane katalogi Androida (9.33 GiB)
przeniesiono do Kosza; dwóch skrótów gry również już nie ma. Kosza nie opróżniono.
Źródła, zasoby i ustawienia zachowano; kopia ustawień: userdata/build-cleanup-20261112-0.12.

---
# Nazwy gałęzi i aktualna wersja — 2026-11-12

Najnowsza gałąź to `main`; jest też domyślną gałęzią GitHuba. Pozostałe gałęzie: `android-pack-selection-2026-11-11`, `bluetooth-mobile-test-2026-11-11`, `maps-build-2026-10-30`. Zmiana nazw zachowała wszystkie commity i lokalne stany gałęzi; dawne nazwy występują poniżej w historii prac. Zaktualizowano lokalne upstreamy i origin/HEAD.

Usunięto do Kosza również odnalezione stare paczki w delivery oraz generowane katalogi Android app/build, build i .gradle. Najnowsza pełna gra, ZIP, APK, zasoby źródłowe i prywatne ustawienia pozostały. ZIP jest skompresowaną dystrybucją; katalog projektu zawiera ponadto rozpakowaną grę, drugą kopię zasobów do budowania i narzędzia.

---
# Pelna paczka gry na Dysku Google — 2026-11-11

Przeslano pelny Windows z modulami/zasobami i APK Android, w 18 czesciach danych po maks. 90 MiB oraz z plikami laczenia i instrukcja. Folder Google ma obecnie dostep wlasciciela; publiczne udostepnienie wymaga zmiany przez wlasciciela w interfejsie Drive. Linki i sumy: `tools/distribution/GOOGLE-DOWNLOADS.md`. Metadane Google potwierdzaja przeslane rozmiary; lokalna rekonstrukcja w Windows PowerShell 5.1, SHA256 wynikow, CRC ZIP i uruchomienie samodzielnej paczki bez cache kompilacji PASS. Finalna plynnosc fizycznego Android–Windows i Bluetooth nadal wymagaja proby urzadzen.

Lokalnie pozostawiono najnowszy pelny folder Windows, ZIP, APK i aktualny silnik LAN powiazany z lokalna regula zapory. Do Kosza przeniesiono 13 starszych folderow buildow, 8 starszych paczek, nieudane czesci transferowe oraz wygenerowane `engine/build` i stare wyniki `validation`. Osiem raportow validation zapisanych w Git odtworzono; dane uzytkownika starych instalacji zachowano w ignorowanym userdata/build-cleanup-20261111. Oproznienie Kosza zwolni zajete przez te pliki miejsce. Dodano skrot pulpitu do najnowszej gry.

---
# Sterowanie, LAN i płynność — test lokalny 2026-11-11

Gałąź robocza `codex/local-leumas-combo-guide-2026-11-11`. Zmiany źródeł i testów zapisano w commicie `16c5a11` i wypchnięto na roboczą gałąź GitHuba; nie utworzono release. F4/przycisk MENU wraca do modułów; wybór dotykowy 1/2 zachowuje się w ekranie walki i wyborze postaci. Wi‑Fi: host TCP 12345 lub klient po IPv4; Android i Windows wcześniej połączyły się fizycznie, ale końcowy APK nie został ponownie sprawdzony na telefonie. Bluetooth PAN/radio nadal niepotwierdzone.

Windowsowy profil zapisano jako WASD + Num7 atak / Num8 blok / Num9 skok, z kopią poprzedniego pliku ustawień poza repozytorium. Ładowanie offline przy rozgrzanym cache: mediana 5,55 → 1,25 s; mikrobenchmark oczekiwania 1 ms: 11,49 → 1,60 ms. Build Windows i Android Gradle PASS; 41 testów Lua, 53 Python (52 PASS/1 SKIP), 27 testów Android PASS. Lint nadal zgłasza 27 błędów/39 ostrzeżeń w generowanych plikach SDL. Końcowa poprawa płynności wymaga próby na prawdziwym telefonie i komputerze; użytkownik nie podłącza telefonu ponownie.

Raport: `docs/MULTIPLAYER-STEROWANIE-2026-11-11.md`; dostarczone APK/ZIP i raport testów są w katalogu wyników bieżącej rozmowy. Nie opublikowano release ani nie wdrożono serwera.

---
# Wydanie testowe 0.11 — opublikowane publicznie 2026-11-11

Użytkownik zatwierdził udostępnienie przygotowanych paczek 0.11.
Publikacja zakończona: 5/5 załączników dostępnych bez logowania; rozmiary
i SHA256 GitHuba zgodne z lokalnymi paczkami. Kod wydania: 81612a3.
Tag: guide-updates-test-2026-11-11. APK i pełny ZIP Windows mają te same
sumy kontrolne co lokalnie przetestowane pliki. Ograniczenia: brak próby
na fizycznym telefonie/Bluetooth; 27 istniejących błędów lint SDL.
Strona wydania: https://github.com/w4sy1/polish-fighters/releases/tag/guide-updates-test-2026-11-11

---

# Lokalna 0.11 — Leumas, poradnik i aktualizacje — 2026-11-11

Zmiany na branchu codex/local-leumas-combo-guide-2026-11-11. LeumasEX bez
przywoływania postaci; poradnik 42 kombosów pięciu bohaterów i mecha; Windows
i Android sprawdzają nowe wydania GitHuba przy starcie. Bez nowej publikacji: użytkownik
chciał najpierw pomysły. Bieżący raport: docs/LOKALNE-0.11-2026-11-11.md.
33 zestawy Lua, 128 plików składni, 51 Python + 1 SKIP, 21 Android PASS.
Kompilacja Windows i APK, próby natywne, zawartość i podpis paczek PASS.
Lokalne paczki 0.11 w engine/out i katalogu outputs bieżącej rozmowy; skrót
pulpitu wskazuje nowy EXE z zachowaniem starych ustawień. Lint: 27 istniejących błędów SDL.
Brak testu na fizycznym telefonie i radiu Bluetooth.

---

# Pięć poprawek z testów — 0.10.0, 2026-11-11

Kolejno: wybór modułów na Androidzie; ukrycie 50 powtórzeń podstawowych postaci
w pełnej puli; przejście własnych NPC przez wyjście kampanii; powrót do modułów
bez zamykania gry; ograniczenie samopowielania LeumasEX/Rudolfa do trzech żywych
kopii na przywołującego, bez potomków klonów. Bez usuwania rekordów i zasobów.
VersionCode 10 / 0.10.0-pack-selection-test, niezmienione applicationId i signing.
15 testów Androida, 30 zestawów Lua, 51 testów Python PASS (jeden SKIP).
Próby natywne: kampania 7/7, powrót do modułów 5/5, klony 4/4, katalog 4/4 PASS.
Przekaźnik lokalny i walka dwóch silników 120 klatek PASS. Fizyczny telefon i
radio Bluetooth wymagają prób użytkownika. Lint: 27 znanych błędów w klasach SDL.
APK: engine/out/PolishFighters-Android-moduly-2026-11-11.apk.
Windows: engine/out/PolishFighters-Modules-2026-11-11; skrót pulpitu zaktualizowany
z zachowaniem dotychczasowej ścieżki ustawień. Osobny ZIP zawiera aktualizację Lua
do poprzedniej pełnej paczki Windows. Historia wydań pozostawiona.
Raport: docs/POPRAWKI-0.10-2026-11-11.md; kolejka: docs/KOREKTY-2026-11-11.md.

---

# Bluetooth i ustawienia kodów Android — 2026-11-11

Wersja testowa 0.9.0-bluetooth-test, versionCode 9. Android: ekran startowy →
USTAWIENIA → Włącz kody → Zapisz; przy włączeniu okienko „lamus”. Zapis zachowuje
sterowanie i postęp; można wyłączyć kody lub anulować. PC: kod polishfighters zachowany.
Windows: engine/out/PolishFighters-Bluetooth-2026-11-11; APK:
engine/out/PolishFighters-Android-2026-11-11.apk. Podpis i applicationId bez zmian.
Build Windows/APK, 6 testów Androida, 27 zestawów Lua, 51 testów Python i natywne
próby postaci PASS (jeden test Python pominięty). Przekaźnik i dwa silniki: 120 klatek
na stronę, zgodny stan. APK: oba ABI, SHA256 danych, podpis i wyrównanie PASS.
Lint: 27 znanych błędów w generowanych klasach SDL, zero nowych błędów ustawień.
Nie potwierdzono radia Bluetooth ani uruchomienia na fizycznych telefonach.
Szczegóły, pliki i procedura testów: docs/TESTY-BLUETOOTH-2026-11-11.md.

---

# Aktualizacja postaci i APK bez Android Studio — 2026-11-07

Windows: `engine/out/LittleFighters-Heroes-2026-11-06` (nowy EXE z lokalnej kompilacji).
Android: `engine/out/PolishFighters-all-mods-Heroes-test.apk` (wersja 0.8.0, code 8).
Stały mech Remonoko, ogień i kombo; 600 HP i regeneracja; pełne klony SZ do drugiej
generacji; kontry Jasia; regeneracja Wasyla; trwałe toalety i nowy finisher Taty.
947 obiektów, 128 map, wszystkie 9 obecnych lokalnie pakietów, bez nowych głosów.
Wcześniejsze braki odzyskiwania modów pozostają.

Przeszły natywne testy sterowania i umiejętności Windows, testy Lua/Python,
kontrola zachowania 7582 importowanych i 19 wcześniejszych własnych zasobów.
Android ma rzeczywiste biblioteki ARM64 i ARMv7 skompilowane bez Android Studio.
Próbny Bluetooth: ekran host/dołącz, sparowane urządzenia, RFCOMM przekazuje
protokół silnika przez lokalny przekaźnik; test przekaźnika na komputerze.
Nie potwierdzono instalacji, dotyku ani gry radiowej na fizycznych telefonach.
Lint Android zgłasza wcześniejsze problemy w generowanych źródłach SDL;
nie ukryto ich przez wyłączenie kontroli. Szczegóły i finalne wyniki:
`validation/hero-update-2026-11-06/REPORT.md`.
Starsze paczki i userdata zachowane. Bez commita, pushu, release i wdrożenia.

---

# Bieżący etap: mieszana pula i klient kont — 2026-10-31

Lokalna instalacja: `engine/out/LittleFighters-mixed-online-2026-10-31`.
`Graj-Wszystkie-Mody.cmd`: wspólne walki ośmiu źródeł; wybór aktywnych pakietów
zmienia pulę postaci. 932 obiekty i 128 map. Nowy wygląd menu/wyboru postaci.
Natywne konta i katalog pokoi sprawdzone z rzeczywistym lokalnym serwerem.
Użytkownik nie ma jeszcze hostingu; publicznego wdrożenia nie wykonano.
DBZ: przełączanie autorskich scen między etapami sprawdzone w natywnym silniku.

Testy: Windows Release OK; Lua120/23 zestawy; Python51 (50 OK/1skip);
C++6/TCP2–8; krótka walka8 źródeł i render128 map. Wspomagane przejścia:
48/56 zakończone, 7 blokad źródłowych (DBZ mirror, One Piece122), LF4 survival
bez końca w budżecie. To nie są naturalne pełne przejścia kampanii.

Pozostało: Bleach284/151, brakujące rysunki, pełne mechaniki/AI/questy modów,
pełne tłumaczenia, publiczne HTTPS/Internet/NAT, Bluetooth, Android i urządzenia.
Raport: `validation/mixed-2026-10-31/REPORT.md`; instrukcja serwera:
`server/README_PL.md`. Poniższe sekcje są historią wcześniejszych dostaw.

<!-- hub-controls:start -->
# Little Fighters — pierwsze menu i sterowanie, 2026-10-31

Nowa paczka: engine/out/LittleFighters-hub-2026-10-31/LittleFighters.exe. Wspolny tytul Little Fighters, osobny zestaw Polish Fighters. Pierwsze menu wybiera 9 profili bez osobnych procesow; 8 pakietow jest lokalnie. Dostepna konfiguracja klawiatury, przyciskow myszy i padow 1–4, zapisywana wspolnie w userdata/common. Stary panel nazw/sterowania i ustawienia nagran zachowane.

Naprawiono zwykly strzal SZ i gubienie krotkich tapniec. Proba natywna: 1 strzal, 22 obrazenia, 0 MP. Portrety 120×120 i HUD 40×45 jak LF2, poprawiona skala i pozycje animacji, wycinki efektow oraz pasek HP bossa. Animacje pozostaja eksperymentalne.

Oryginalne dane postaci i dodatkow zachowane; 7710 chronionych plikow bez zmian, 2 bazowe pliki UI zmienione celowo. Sprawdzono 7603 odwolania zasobow w 8 pakietach. Testy: 9 profili, konfiguracja i zapis przez GUI, 8×900 klatek walk, 28 kontrolowanych umiejetnosci; Lua19/skladnia106, Python48 (47OK/1skip), C++6/TCP2–8. Fizyczny pad/telefon/siec nowej czworki niepotwierdzone.

Nadal pozostaja wspolna pula wszystkich modow, dobieranie mieszanego zestawu, pobieranie/aktualizacje GitHub, finalne animacje/balans, pelne kampanie i Android. Raport: validation/hub-controls-2026-10-31/REPORT.md. Starsze paczki zachowane. Brak commita/pushu/release.
<!-- hub-controls:end -->

<!-- polish-originals:start -->
# Cztery własne postacie — 2026-10-31

Dodano Wasyla, Szymonoko/SZ, Mega Ninja Jasia i bossa Skibidi Sigma Tatę w osobnym pakiecie polish-originals. 7712/7712 dotychczasowych plików LF2 i dodatków zachowanych. Nowy Windows EXE, skala RGBA, animacje, klony, teleporty, miecze/śluz i umiejętności bossa.

Testy: 8 rzeczywistych prób wejść po 900 klatek; 4 kontrolowane próby po 7 umiejętności; SDL software 64 rysowania; Lua18/składnia99; Python48 (47OK/1skip); C++6/TCP2–8. Android, sieć nowej czwórki, replay i pełny balans nadal niepotwierdzone; grafika eksperymentalna z drobnymi artefaktami.

Uruchom engine/out/PolishFighters-originals-2026-10-31/Graj-Polish-Fighters.cmd. Raport: validation/polish-originals-2026-10-30/REPORT.md. Starsze paczki i opisane poniżej braki pozostałych dodatków zachowane.
<!-- polish-originals:end -->

<!-- remaining-mechanics:start -->
# Aktualizacja mechanik — 2026-10-30

129/129 map oraz 259/259 startów etapów przeszło test120 klatek na nowym Windows EXE. DBZ50/50 wariantów. NTSD25/25 i One Piece25/25 startów.

Bleach284/83 i151/30 pozostają nieodzyskane. DBZ: pełne questy, mirror/8001–8008, przejścia scen i AI nadal nieprzeniesione; stage4.wma to jawny zamiennik z bazowego LF2. 11 arkuszy obejrzano; brakujących rysunków nie odtworzono. Pełnej rozgrywki i Android ARM nie potwierdzono.

Raport: validation/remaining-mechanics-2026-10-30/REPORT.md. Nowy build: engine/out/PolishFighters-remaining-2026-10-30/. Testy Python48(47OK/1skip), Lua17/składnia90, C++6/TCP2–8.
<!-- remaining-mechanics:end -->

# Dostarczenie Windows / Android Studio — 2026-10-30

Nowy EXE zbudowany; pełna lokalna paczka i ZIP kodu Android Studio. Odzyskano Kate99/action390/392 (25 zasobów, oba opoint przetestowane). Pozostały2 cele Bleach. Bezpieczne przycinanie źródeł;58768 lookupów Lua bez wyjścia poza obraz.

117/129 map i170/259 startów etapów OK (headless, stały aktor QA). DBZ/NTSD/część One Piece nadal eksperymentalne. Pełnych kampanii i obrazu nie potwierdzono.

Python46 (45OK/1skip),Lua14/składnia83,C++6 iTCP2–8 OK. Android: konfiguracja iJava OK; lint27 błędów SDL/9 ostrzeżeń,brak.so/APK/testu telefonu.

Aktualny raport: validation/maps-build-2026-10-30/REPORT.md; instrukcja Androida: ANDROID_STUDIO.md. Poniższe sekcje są historią wcześniejszych etapów.

# Aktualny stan Bleach / Kate / Reinforced — 2026-10-30

Usunięto blokady natywnego startu: setmetatable w historii oraz duże BMP Bleach
(bezstratny PNG, oryginały zachowane). Poprawiono odczyt8 upakowanych deklaracji
Bleach, pomijanie pustych źródeł i rysowanie obiektów daleko poza widokiem.
Kate: nienumerowany transform dostał wywnioskowany numer350; inferencja zapisana.

91/91 postaci przeszło natywną próbę300 klatek z kontrolą geometrii.
91/91 przeszło po2 powtarzalne próby ze sterowaniem do900 klatek lub naturalnego
zakończenia walki. W tych próbach nie zaobserwowano rysowania poza obrazami.
Kate30 odwiedziła350; w8 próbach Bleach obserwowano zmianę rekordu gracza.
To nie jest potwierdzenie wszystkich ataków, transformacji ani wyglądu.

130 dawnych alarmów:99 ma klatki mieszczące się w obrazie,20 ma całkowicie puste
źródła pomijane podczas rysowania,11 nadal ma częściowe przycięcia (6/2/3).
Pozostają4 nieistniejące cele opoint (Bleach284/151, Kate99 dwa razy), już nieobecne
w oryginalnych katalogach. Nie podstawiano zgadywanych obiektów ani rysunków.

Testy:44 Python (43OK,1pominięty),13 zestawów LuaJIT,składnia83 plików.
2162 fizyczne zasoby mają odświeżone SHA256 (w tym3 zachowane dodatkowe BMP).
Istniejący własny EXE bez zmian. Bez buildu EXE/APK, publikacji i wykonania
oryginalnych programów. Kampanie, pełna zgodność1.9c i Android niezweryfikowane.
Raport i wznowienie: validation/native-fixes-2026-10-29/REPORT.md.
Kopia przed zmianami: ../baseline-native-fixes-2026-10-29/.

## Historia poprzedniego etapu — poniższe blokady zostały już usunięte

# Zgodność Bleach / Kate / Reinforced — 2026-10-29

Sprawdzono130 alarmów siatek:91 ma komplet bezpośrednich pic w granicach obrazów,
39 ma odwołania poza obrazem (25Bleach/8Kate/6Reinforced). Dynamiczne przesunięcia,
osiągalność klatek i wygląd nie są tym potwierdzone. Dokładne prostokąty w raporcie.
Z5 alarmów spawn, oid0 Reinforced jest nieaktywne;4 aktywne brakujące cele istnieją
już w oryginalnych katalogach i pozostają nierozwiązane, bez zgadywania ID.

Sześć „brakujących nagrań” Bleach okazało się wyłączonymi #sound: w Kon.dat.
Poprawiono importer; ścisły import trzech pakietów kończy się bez aktywnych braków.
Bazy Kate/Reinforced uzupełniono współdzielonymi danymi Starterkitu zawierającego1.9c,
z zachowaniem plików dodatków. Wymiary285/268 bazowych obrazów są zgodne z1.9.
Dokładnej zgodności natywnej z1.9c nie potwierdzono.

Przeniesiono rozpoznany patch Bleach: transformacje8000–8999 ustawiają pic_offset0
zamiast140, przez izolowane rozszerzenie frame_rules.lua. Test rzeczywistego kodu
Lua potwierdza zmianę rekordu, granice zakresu oraz brak wpływu na klasyczny profil.
Kate/Reinforced mają .text/.rdata/.data identyczne zLF2v1.9.exe ze Starterkitu.

Testy:40Python (39OK,1pominięty),11LuaJIT,składnia79plików;2159hashy zasobów zgodnych.
Natywne próby na starym własnym EXE nie uruchomiły meczu: Bleach — limit pliku40MB;
Kate/Reinforced — wcześniejszy match_history.lua i niedostępny setmetatable.
Nie budowano EXE/APK. Nie wykonywano oryginalnych programów. Pozostałe problemy
nie są ukończone; raport: validation/pack-compatibility-2026-10-29/REPORT.md.
Kopie przed zmianami: ../baseline-pack-compatibility-2026-10-29/.

# Polish Fighters — stan lokalny, 2026-10-29

## Bleach, Kate i Reinforced — odzyskane i zaimportowane dane

| Pakiet | Postacie | Obiekty | Areny | Zasoby | Ograniczenia |
|---|---:|---:|---:|---:|---|
| Bleach BBR 2.0a | 34 | 100 | 12 | 753 | 6 brakujących nagrań, 43 rozbieżności arkuszy, 2 odwołania spawn poza katalogiem |
| Kate | 29 | 98 | 11 | 719 | 44 rozbieżności arkuszy, 2 odwołania spawn poza katalogiem, baza 1.9 zamiast dokładnej 1.9c |
| Reinforced | 28 | 100 | 14 | 687 | 43 rozbieżności arkuszy, 1 odwołanie spawn poza katalogiem, baza 1.9 zamiast dokładnej 1.9c |

Zakończono statyczne odzyskiwanie 356 plików danych Kate i 335 Reinforced;
nowy tools/clickteam_legacy.py czyta starą kompresję Clickteam i sprawdza rozmiary
oraz wspólny XOR sum rekordów. Wszystkie odzyskane pliki obu dodatków sprawdzono
ponownie po SHA256. Pominięto programy i skrót strony autora. Bleach odzyskano
statycznym demoleition 0.61: 1078 plików, log Molebox Pro v2.2534 i potwierdzenie
MD5 wejścia. Oryginalnych gier ani instalatorów nie wykonywano.

Kate/Reinforced wymagały brakujących danych bazowych. Z osobnego, statycznie
odczytanego LF2 1.9 skopiowano wyłącznie brakujące ścieżki: 395 dla Kate i 386
dla Reinforced. Nie nadpisano danych dodatków. Nie mają już braków w badanych
odwołaniach. Ogólna instrukcja LFE dopuszcza 1.9/1.9c, ale instrukcje tych
instalatorów wskazują 1.9c: dokładna zgodność tej bazy pozostaje niezweryfikowana.
Instalator 1.9c pobrano, lecz ekstraktor go nie odczytał; nie użyto jego danych.

Bleach zachowuje oryginalny katalog; w kopii roboczej uzupełniono brakujące
dwukropki type w trzech rekordach (458,228,229). Braków audio nie zastąpiono
atrapami. SOURCE.md, import-report.json, sprite-edge-repairs.json i
asset-checksums.json opisują każdy pakiet i jego pochodzenie.

Weryfikacja: rzeczywisty katalog Lua wczytał wszystkie 91 postaci, 298 obiektów
i 37 aren z dysku. Audyty wykazały zero wartości poza int32; opisują odpowiednio
21/33/45 etapów i 64/179/131 faz (Bleach/Kate/Reinforced), bez potwierdzenia ich
przebiegu. Zweryfikowano SHA256 wszystkich 2159 zasobów trzech pakietów.
Testy: 36 Python (35 zaliczonych, 1 pominięty: uprawnienia symlinków),
10 zestawów LuaJIT, składnia 78 plików. Logi i audyty:
validation/bleach-kate-reinforced-2026-10-29/.

**Nie ukończono zgodności rozgrywki:** ruchów, własnych stanów i modyfikacji EXE,
AI, efektów, animacji i przebiegu kampanii. Nie uruchamiano natywnej symulacji C++
ani testów urządzeń dla tych pakietów. To importy eksperymentalne, bez nowego
EXE/APK i bez zmian w historycznej paczce Windows. Nie oznaczają trzech gotowych,
przetestowanych dodatków. Silnika tej tury nie zmieniano.

Projekt nie ma .git. Zachowano kopie źródeł i wcześniejsze niepełne importy w
../baseline-bleach-kate-reinforced-2026-10-29/; przegląd zmian w validation.

# Polish Fighters — stan lokalny, 2026-10-28

## Zakres 2, 3 i 5 — importy, kampanie i multiplayer

### 2. Pozostałe pakiety

Statycznie odzyskano 2879 plików danych DBZ z Enigma Virtual Box oraz osobno
osadzony data/stage.dat i 55 plików źródłowych AI AngelScript. Nie odtwarzano
ani nie wykonywano oryginalnego EXE/DLL. Zachowano oryginalne archiwa i katalogi.
Importer obsługuje teraz PNG, MP3/OGG i powtarzające się separatory; jawna opcja
aliasów BMP→istniejący PNG zachowuje kanał alfa. Braki nie są uzupełniane atrapami.

| Pakiet | Import eksperymentalny | Nadal blokuje pełną zgodność |
|---|---|---|
| DBZ | 56 postaci, 190 obiektów, 14 aren, 2119 zasobów | bgm/stage4.wma i common/kiball_pink.png; 149 rozbieżności arkuszy; 18 odwołań spawn poza katalogiem; autorskie rozszerzenia i AI nieprzeniesione |
| One Piece | 61 postaci, 130 obiektów, 36 aren, 1179 zasobów | cheat.bmp, cheatz.bmp, data/109.wav, nar/xit.bmp; 74 rozbieżności arkuszy; semantyka %, $, &, *, fileb nieprzeniesiona |
| Bleach | Zachowano oryginał i katalog; sprawdzono format PE/overlay | Bieżący statyczny ekstraktor nie czyta użytego opakowania; brak pełnych danych |
| Reinforced / Kate | Zachowano instalatory i instrukcje LF2 1.9c | Bieżący ekstraktor nie czyta tych instalatorów; nie uruchamiano instalacji |

Nowe katalogi: `content-packs/dbz`, `content-packs/one-piece`; SOURCE.md,
import-report.json i asset-checksums.json opisują pochodzenie i ograniczenia.
Nie są dołączone do starej paczki Windows. Limit loadera w **źródłach C++**
zwiększono do 4096 zasobów i 256 KiB manifestu; zmieniono test graniczny na
4096/4097. Nie kompilowano tego testu ani silnika. Dotychczasowy EXE ma stary limit.

### 3. Mapy i kampanie

Importer rozpoznaje katalog DBZ `<stage_information>`: 24 nazwane przygody i
wyzwania z osobnymi plikami etapów. Menu aktywnego pakietu przekazuje wybór do
rzeczywistego ekranu Stage. Zapisano osobną ścieżkę kampanii w opcjach meczu;
cache etapów jest rozdzielony według pliku, a brak kolejnego rozdziału kończy
samodzielną kampanię. Standardowy LF2 zachowuje dotychczasową ścieżkę danych.
Nagrody rozróżniają ID kampanii, zamiast mieszać rozdziały o tych samych numerach.

Cztery kampanie mają autorskie warunki hidden; GUI blokuje ich start, dopóki
nie zostanie przeniesiona ich semantyka. Pozostałe rozszerzenia DBZ (m.in. zmiany
aren w trakcie etapu, odwołania do plików i własne reguły) nadal wymagają audytu.
Początkową arenę indeksowano według ID katalogu; zgodność tej interpretacji z
oryginałem wymaga testu. Nie oznacza to ukończenia kampanii ani własnej historii
łączącej światy. One Piece zachowuje oryginalne etapy; ich przejścia niezweryfikowane.

### 5. Multiplayer

Usługa kont ma prywatne pokoje, zaproszenia z terminem, rozwiązywanie i odwoływanie
kodów, kontrolę właściciela oraz heartbeat. Prywatny pokój nie jest pokazywany
obcym kontom; uzyskanie biletu relay wymaga zaproszenia. Most gospodarza odnawia
pokój co 25 s. Rozdzielono limity prób logowania od pozostałych operacji API.
Migracja bazy zachowuje stare pokoje. Test HTTP→prywatne zaproszenie→relay→most
przesyła niezmienione bajty istniejącego protokołu.

**Nie ukończono:** integracji kont/relay z natywnym menu, transportu Bluetooth,
hostingu/TLS ani fizycznych testów internetu. Usługi nie wdrażano. Dalsza praca
jest potrzebna także w niezablokowanej integracji GUI; nie jest to zamknięcie
całego zleconego zakresu 2/3/5.

Weryfikacja: 30 testów Python (29 zaliczonych, 1 pominięty przez uprawnienia
symlinków), 10 zestawów LuaJIT i składnia 72 plików. Nowy C++ pozostaje
niezbudowany i niewykonany. Logi: `validation/packs-network-2026-10-28/`.
Nie tworzono EXE/APK, instalatora, wdrożenia ani reguł zapory. Kopie zmienianych
źródeł: `../baseline-packs-network-2026-10-28/`.

## Układy dotykowe i wpisywanie kodu na Androidzie — 2026-10-26

Zaimplementowano wybór `Ustawienia → Układ dotykowy`: Klasyczny LF lub
Nowoczesny joystick. Dostępny także w `Dodatki → Sterowanie dotykowe`.
Klasyczny: cztery kierunki na krzyżaku i dokładnie trzy przyciski Skok/Blok/Atak.
Nowoczesny: joystick z dotychczasowym impulsem biegu, atak po puszczeniu palca,
przeciągnięcie wybiera kierunek, dodatkowe przyciski kombinacji pokazują się tylko,
gdy postać je obsługuje. Gest przekłada się na istniejące wejścia kierunku i ataku,
nie zmienia balistyki ani nie dodaje swobodnego celowania pociskiem pod dowolnym
kątem. Podgląd wskazuje ten sam jeden z czterech kierunków co rzeczywiste wejście.

Układ zapisuje się w istniejących opcjach; stare `digipad` jest migrowane.
Zmiany układu, rozmiaru, położenia i przezroczystości odświeżają nakładkę bez
restartu gry. Gesty są anulowane po pauzie, ukryciu lub zmianie geometrii okna;
palec trzymany przez pauzę nie staje się nowym atakiem po wznowieniu.
Zachowano normalne wejścia klawiatury/padów i protokół sieciowy.

Ekran odblokowania ma pole kodu, zatwierdzanie, obsługę tekstu z systemowej
klawiatury i błędnego kodu. Wywołuje istniejące `context.text_input`;
`polishfighters` oraz szybki przycisk pozostają dostępne. Klawiatura jest zamykana
po zatwierdzeniu/anulowaniu lub wybraniu innej czynności. Nie zweryfikowano jeszcze
wyglądu konkretnej klawiatury Androida ani jej współpracy z oknem na telefonie.

Weryfikacja: 9 zestawów LuaJIT, składnia 68 plików; testy przełącznika w rzeczywistym
skrypcie menu, migracji/zapisu, multitouch, próbkowania ataku co drugą klatkę,
anulowania gestów i wpisywania kodu. Podglądy poleceń renderera Lua (font podglądu
Arial, nie natywny bitmapowy): `preview/touch-classic.png`, `preview/touch-modern.png`.
Obejrzano oba podglądy. To nie zrzuty z uruchomionej gry.
Bez builda EXE/APK i bez zmian zapory. Kopie: `../baseline-touch-layouts-2026-10-26/`.

## Etap przy pozostałych 5%: postęp i nagrody za przygodę

Dodano `progression.lua` oraz `progression_network.lua`, zarejestrowano je w
manifeście i podłączono do istniejącej kroniki, zakończenia meczu i polityki rosteru.
Pierwsze ukończenie rozdziału lokalnego trybu Stage przez uczestniczącego gracza
odblokowuje kolejną ukrytą postać w kolejności katalogu danego pakietu.
Rozdział to grupa etapów 0–9, 10–19 itd.; zapisywany jest etap sprzed przejścia
silnika do następnej grupy. Jedna nagroda na rozdział i pakiet; ponowne przejście
nie służy do zdobywania kolejnych nagród. Brak nagród za porażki, demo, powtórki,
rozgrywkę bez człowieka oraz mecze sieciowe.

Postęp i historia zapisują się w jednym wywołaniu istniejącego magazynu ustawień.
Nieudany zapis nie daje odblokowania. Stan odblokowań jest pamiętany w cache
poza symulacją i odświeżany po udanym zapisie. Lokalne nagrody są zawieszone
w sesjach sieciowych, aby nie różnicować rosterów klientów. Jawne ograniczenia
`allowed_ids` i istniejące funkcje/kody pozostają zachowane.

Menu Odblokowanie postaci → Postęp przygody i nagrody pokazuje liczbę ukończonych
rozdziałów i następną nagrodę. Przyznana postać jest widoczna w szczegółach wpisu
kroniki. To odblokowanie istniejącej zawartości, nie deklaracja jej zgodności
ani implementacja nowej wieloświatowej kampanii. Przy braku kolejnych ukrytych
postaci rozdział nadal liczy się jako ukończony.

Weryfikacja: 7 zestawów LuaJIT zaliczonych; składnia 68 plików poprawna.
Testy obejmują przyznawanie i brak wielokrotnych nagród, rozdzielenie pakietów,
błędy zapisu, ograniczenia rosteru, zawieszenie sieciowe oraz rzeczywiste
wywołanie rozszerzenia zakończenia meczu z kontrolowanym stanem.
Log: `validation/content-work/progression-lua-tests.log`.
Nie budowano EXE/APK; nie zweryfikowano nowego meczu na fizycznym urządzeniu.
Kopie sprzed zmian: `../baseline-progression/`.

## Mały etap przy pozostałym limicie: kronika i kod postaci

Dodano `polish-fighters/chronicle.lua` i rozszerzenie `match_history.lua`,
zarejestrowane w manifeście pakietu. Zakończenie meczu dopisuje do ustawień
lokalnych maksymalnie 50 wpisów: kolejny numer, profil dodatku, tryb, flagę
sieci, arenę/etap, zwycięską drużynę, liczbę klatek, wybrane postacie i statystyki.
Pokazy, powtórki i niedokończone mecze nie są wpisywane. Nie zapisuje haseł,
adresów IP ani fikcyjnych dat; numer wpisu określa kolejność. Księgowanie jest
poza synchronizowanymi tabelami symulacji. Błędy zapisu są dostępne w menu historii.

Menu Dodatki ma ekrany Historia rozgrywek oraz Odblokowanie postaci. Na ekranie
odblokowania można wpisać `polishfighters` lub użyć przycisku dotykowego.
Kod ustawia istniejącą opcję `unlock_characters`, zapisuje ją i odblokowuje ukryte
postacie dostępnego rosteru. Zachowuje jawne ograniczenia `allowed_ids`, nie
instaluje dodatków, nie naprawia niezgodnych postaci i nie zmienia zasad sieci.
Dotychczasowy kod `lf2.net` pozostaje dostępny na dotychczasowych zasadach.

Testy: 6 zestawów LuaJIT oraz składnia 66 plików. Sprawdzono limit historii,
ochronę innych ustawień, błąd zapisu, jednokrotny wpis po zakończeniu,
pomijanie powtórek/pokazów, ekran pustej historii i kod odblokowania.
Nie zbudowano EXE/APK i nie wykonano nowego meczu na urządzeniu.
To pierwszy działający w testach element kroniki; nie obejmuje jeszcze
odblokowań za kampanie, wspólnej przygody, synchronizacji kont ani pełnych powtórek.
Kopie sprzed zmian: `../baseline-chronicle/`.

## Aktualny zakres użytkownika: źródła i zawartość, bez budowania

### Kontynuacja z wklejonego polecenia — 2026-10-25

Nie uruchamiano CMake, Gradle, kompilatora ani nowego builda gry. Nie zmieniano
zapory, nie publikowano ani nie uruchamiano obcych plików EXE. Do lokalnego
środowiska testowego pobrano gotowe koło `lupa 2.8`, używające LuaJIT 2.1.

| Obszar | Zmiana źródeł / dowód | Pozostaje |
|---|---|---|
| Postacie | Audyt LF4 i NTSD obejmuje grafy klatek, kombinacje, stany i przywołania | Pełna implementacja/zgodność ruchów i przemian nieukończona |
| LF4 | 32 postacie, 12 aren, 26 deklaracji etapów; 58 odwołań opoint do ID poza katalogiem | Ustalić semantykę tych odwołań, nie podstawiać przypadkowych obiektów |
| NTSD | 42 postacie, 17 aren, 25 deklaracji etapów; 364 wartości poza int32 | Ustalić semantykę oryginalnego CRT i naprawy arkuszy |
| Przegląd pakietu | Menu czyta rzeczywiste postacie i etapy aktywnego profilu, ma strony i obsługę błędów; aktywny NTSD oznaczany poprawnie | Aktywacja innych profili, walidacja i mieszanie ID |
| Sterowanie | Wykrywanie powtórzeń przypisań w zestawie, odmowa nadpisania ustawień; edytor pozostaje otwarty po błędzie | Ostrzeżenia o współdzieleniu urządzeń, pełny edytor wszystkich parametrów |
| Dotyk | GUI: rozmiar, przesuwanie przycisków, przezroczystość i reset układu; zapis używany przez rysowanie | Ręczna ocena ergonomii i położenia na telefonie |
| Języki | Polski rozszerzony z 77 do 178 wpisów; audyt kluczy i parametrów, zero błędów formatowania | Wszystkie wymagane języki nadal nie są kompletne; sześć słowników jeszcze nie istnieje |
| Konta | Odzyskanie dostępu jednorazowym kodem, rotacja kodu i unieważnianie sesji/pokoju | Integracja z menu, ustanowienie kodów dla starszych kont |
| Relay | Bilety host/join, ograniczone kanały, transparentny TCP; most zachowuje istniejący protokół | Hosting/TLS, integracja natywna i GUI, zaproszenia, fizyczne testy internetu |
| Bluetooth | Bez zmian transportu w tej kontynuacji | Nadal niezaimplementowany; wcześniejsze deklaracje uprawnień to tylko przygotowanie |
| Pozostałe mody | Zachowane źródła i wcześniejsze raporty braków | Import/odtworzenie zasobów i obsługa modyfikacji EXE |

Dowody: `validation/content-work/`. Testy Python: 22 uruchomione, 21 zaliczonych,
1 pominięty (uprawnienia symlinków). Pięć zestawów LuaJIT i składnia 64 plików:
zaliczone. Testy obejmują rzeczywisty HTTP localhost, parowanie relay i przesyłanie
ponad 100 KiB przez most; nie uruchamiają meczu gry przez internet. Test menu
wykonuje skrypty z kontrolowanym wejściem i atrapą renderera, nie ocenia obrazu.

**Nie ma nowego potwierdzenia działania gry na urządzeniu.** Nowe źródła nie są
w historycznej paczce EXE. Zakres całości pozostaje otwarty, bez deklaracji, że
postacie, kampanie, Bluetooth lub wszystkie języki zostały ukończone.
Kopie zmienianych źródeł: `../baseline-source-continuation/`.

Użytkownik wstrzymał nowe buildy EXE/APK. Priorytet: kompletne postacie, areny,
kampanie i wygląd LF4, Naruto oraz pozostałych dodatków; pakiety, sterowanie,
języki, konta, Bluetooth i pokoje internetowe. Poniższy build Windows jest
historycznym wynikiem; nie zawiera zmian tego etapu.

W tym etapie dodano:

- `tools/audit_content.py`: odczyt manifestów, postaci i klatek, aren, kampanii,
  brakujących zasobów i wartości całkowitych poza zakresem. Raporty:
  `validation/content-work/ntsd.json` i `lf4-turbo.json`. Naruto: 42 postacie,
  364 wartości poza int32; LF4: 32 postacie, zero takich wartości. To audyt
  danych, nie potwierdzenie kompletności ruchów ani kampanii.
- `tools/account_service.py`: lokalna usługa rejestracji/logowania/wylogowania,
  hasła scrypt, wygasające tokeny, katalog pokoi z odnawianiem ogłoszeń,
  autoryzacja właściciela. Pięć testów, w tym HTTP na localhost, zaliczonych.
  Brak wdrożenia HTTPS, integracji GUI, relay/NAT, zaproszeń i synchronizacji.
- Android: deklaracje Bluetooth oraz metoda żądania uprawnień w Activity.
  Brak spięcia z menu i transportu. Nie wykonano kompilacji ani testu Androida.
- `tools/configure_firewall.ps1`: jawna konfiguracja/usuwanie reguły TCP LAN
  dla konkretnego EXE, Private/LocalSubnet. Sprawdzono tylko `-WhatIf`;
  zapora systemowa nie została zmieniona.
- Menu map: stronicowanie po osiem aren; zmiana kodu Lua bez nowego builda
  i bez potwierdzenia jej wykonania w silniku.

Dokumentacja API i ograniczeń: `docs/ACCOUNT_SERVICE.md`. Kopie sprzed zmian
manifestu, menu i statusu: `../baseline-content-work/`. Repozytorium nadal
nie ma Git; brak commitów i publikacji.

**Cały zamówiony zakres pozostaje nieukończony.** Nie dokończono postaci ani
kampanii LF4/Naruto, nie zaimportowano pozostałych modów i nie dodano pełnych
tłumaczeń/nowego sterowania. Następna praca zawartości: ustalenie interpretacji
364 wartości Naruto oraz naprawy arkuszy, potem zgodność stanów, ciosów,
przemian i kampanii. Nie zawijać/przycinać liczb bez dowodu zachowania.

## Gotowe lokalne wydanie testowe Windows x64

Folder: `engine/out/PolishFighters-Windows-x64-portable`.
Uruchom `Graj-LF2.cmd` albo `Graj-LF4-Turbo.cmd`. W paczce są własny silnik, biblioteki DLL, dane LF2 v2.0a, skrypty i izolowany pakiet LF4. Python nie jest potrzebny do grania. Ustawienia obu profili są rozdzielone. Nie tworzono instalatora systemowego ani publicznego release.

Budowa: MSVC 2022, C++23, CMake/Conan. Wszystkie zależności zbudowane/pobrane w lokalnym cache; poprawiono przepis LuaJIT, aby używał zgodnego CRT /MD. Końcowe linkowanie nie zgłasza konfliktu LNK4098. FreeType pobrano z mirrora z kontrolą oryginalnego SHA-256. Polecenia i granice: `BUILD_WINDOWS.md`.

## Weryfikacja Windows

- 5 natywnych testów C++: reguły pokoju, poprzedni transport TCP, parser Tigera, loader skryptów oraz limit zasobów 2048/2049.
- 3 zestawy testów Lua: roster, losowanie i model dodatków.
- Python: 9 zaliczonych, 1 pominięty z powodu braku uprawnienia Windows do tworzenia symlinków.
- TCP: 2–8 osobnych klientów po 30 klatek, przerwanie po rozłączeniu, timeout i niedozwolonym poleceniu klienta.
- 11 scenariuszy menu i klasycznej walki.
- LF4: 32/32 postacie po 300 klatek symulacji.
- Mecze 2–8 osobnych procesów gry po 120 klatek, zgodne końcowe skróty stanu.
- Lobby → wybór postaci → mecz: 2 i 8 procesów.
- LF4 w pokoju: 2 i 8 procesów; celowa desynchronizacja: sesja przerwana.
- Oba profile przeszły osobny test z danych gotowej paczki i obcego katalogu roboczego.
- 975/975 zasobów LF4 w paczce ma sumy zgodne z manifestem.

Logi i JSON: `validation/windows-native/`. Są to automatyczne testy bez okna, na jednym laptopie. Nie potwierdzają obrazu, sterowania, dźwięku z głośników, pełnych ciosów/kampanii ani ośmiu fizycznych urządzeń. Historyczne dowody Linux z Work zachowano w dotychczasowych katalogach.

## Dodatki

Archiwa w `../downloads/`; rozpakowane pliki w `../games/`. Dokładne źródła i sumy początkowych plików: `validation/windows-2026-10-25/downloads.json`; dodatkowe wydanie NTSD: `validation/windows-native/ntsd-download.json`.

| Dodatek | Stan |
|---|---|
| LF2 v2.0a | W lokalnej paczce; oficjalny instalator zgodny SHA-256; dane czytane bez instalowania go |
| LF4 Turbo | Działający profil testowy; 32/32 smoke, pełna zgodność ciosów i kampanii nadal niezweryfikowana |
| Naruto NTSD 2.4_2.0a | Zaimportowano 42 postacie, 137 obiektów, 17 aren i 1121 zasobów. Eksperymentalny: tylko 13/42 smoke zaliczonych. Główna przeszkoda: liczby poza zakresem 32-bitowym; 31 rozbieżności arkuszy. Nie jest w paczce do grania |
| NTSD 2.4 — pierwsze pobrane wydanie | 152 brakujące pliki katalogowe; zachowane osobno |
| R-LF2 / Kate | Archiwa poprawne; instalatory wymagają LF2 1.9c według instrukcji. Nie uruchamiano instalatorów |
| DBZ 0.6.9 hotfix | Archiwum poprawne; inspekcja wskazuje 204 brakujące pliki katalogowe; nie jest gotowym pakietem danych do importu |
| One Piece Legends of Sea 2.1X | Archiwum poprawne; katalog zawiera znaczniki %, $, &, * wymagające osobnego audytu. Nie usuwano ich automatycznie |
| Bleach Bankai Revolution 2.0a | Archiwum poprawne; zasoby nie są udostępnione jako pełny zwykły katalog. Nie uruchamiano EXE |

Pobranie i rozpakowanie oryginalnych modów nie oznacza potwierdzenia ich działania na Windowsie. Nie uruchamiano obcych EXE/DLL. Wykonano własny, skompilowany silnik projektu.

## Poprzedni plan — zastąpiony powyższym zakresem

1. Sprawdzić rzeczywiste okno gry Windows, obraz, sterowanie i audio; następnie pełne ciosy, przemiany i kampanię LF4.
2. Ustalić zachowanie liczb poza 32 bitami w oryginalnym NTSD; nie przycinać ani nie zawijać ich bez dowodu. Dokończyć zgodność i testy Naruto przed dołączeniem profilu.
3. Zbudować APK. Na dysku są JBR/SDK/android-35/CMake i NDK 29.x; obecny skrypt Androida jest dla Linuxa i wymaga NDK 28.2.13676358. APK ani testów telefonu jeszcze nie wykonano.
4. Testy fizycznego LAN/Wi-Fi/hotspot i zgodności ARM/x64; potem Bluetooth, pokoje online i zaproszenia.
5. Usługa kont/synchronizacji, wybór profilu w aplikacji, bezpieczne mapowanie ID do mieszania modów, rozbudowa sterowania i tłumaczeń.

## Zakres zmian i punkt przywracania

Odzyskana baza 0.6: czat „Little Fighter dodatki” (`6adcabde-96f0-83eb-a40d-e86a777d6d78`). Oryginalny ZIP pozostaje w Pobranych. Dodatkowe kopie zmienianych plików są w `../baseline-windows-build/`. Paczka źródłowa nie ma historii Git; użyto porównań `git diff --no-index` i porównania z oryginalnym archiwum.

Kontynuacja obejmuje pełny build Windows, testy lokalne, poprawkę CRT, rozszerzenie ograniczonego loadera do 2048 zasobów wraz z testem granicznym, eksperymentalny import Naruto oraz narzędzia i dokumentację. Nie usuwano istniejących funkcji. Brak commitów, pushów, publikacji i zmian w projekcie Prestige Tech. Cały projekt gry nadal nie jest ukończony.
<!-- ui-num789:start -->
## 2026-10-31 — polski interfejs i opcjonalny WASD + Num7/8/9

Nowy folder: `engine/out/LittleFighters-ui-num789-2026-10-31`.
Oryginalne klawisze LF2 pozostają domyślne; preset numeryczny wymaga wyboru i zapisu.
Polski domyślny dla nowych konfiguracji, uzupełnione etykiety wyboru postaci i poprawione menu.
Build Release, 20 testów Lua i natywne próby UI/zapisu: PASS.
Raport i granice weryfikacji: `validation/ui-num789-2026-10-31/REPORT.md`.
GitHub nie publikowano. Pełny redesign, kompletne tłumaczenia, Android i fizyczny pad pozostają do dalszej pracy.
<!-- ui-num789:end -->
<!-- pack-ai:start -->
## 2026-10-31 — wybór pakietów, AI i tłumaczenia

Wersja lokalna: `engine/out/LittleFighters-pack-ai-2026-10-31`.
Wykonano filtr pakietów w menu z zapisem, dobór ataków AI według dystansu/MP,
uzupełnienie etykiet bitmap PL oraz test czterech własnych bohaterów w 4 procesach TCP (120 klatek, zgodny digest).
Lua 21 zestawów PASS; Python 47 PASS/1 SKIP; C++ 6 PASS; TCP 2–8 PASS.
Pełny zakres użytkownika pozostaje częściowy: wspólna pula, finalne animacje/balans,
braki Bleach/DBZ, całe kampanie, logowanie w kliencie, publiczne pokoje i Bluetooth nieukończone.
Publiczny ZIP to rdzeń bez danych modów; raport: `validation/pack-ai-2026-10-31/REPORT.md`.
<!-- pack-ai:end -->
