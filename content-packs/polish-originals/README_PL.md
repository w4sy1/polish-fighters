# Własne postacie — aktualizacja 2026-11-07

Windows: `engine/out/LittleFighters-Heroes-2026-11-06/Graj-Wszystkie-Mody.cmd`.
Android: `engine/out/PolishFighters-all-mods-Heroes-test.apk`, ARM64 i ARMv7,
bez Android Studio. Wszystkie 9 lokalnych pakietów, wspólna pula 947 obiektów i 128 map.
To dotychczas zaimportowana zawartość; nie oznacza pełnego odzyskania każdego oryginalnego moda.
Nie dodano nowych nagrań głosowych. Starsze paczki i userdata pozostają zachowane.

D = blok, A = atak, J = skok; są to akcje z ustawień gry. Strzałka → oznacza
kierunek patrzenia. Kombinacje wciskaj kolejno.

## Remonoko / Remek (414) i Kamienny Mech (415)

600 HP, prędkość zwykłej formy: chód 6,8, bieg 13,2. Regeneracja 4 HP co
15 kroków gry oraz odzyskanie 35% otrzymanej straty, do 20 HP na zdarzenie.
Nie wskrzesza i nie przekracza maksymalnego HP. Regeneracja działa też w mechu.

| Akcja | Zwykła forma | Mech |
|---|---|---|
| A | Strzał i podstawowe ciosy | Cios łapą i ogień z dłoni |
| D → A | Metalowe BUM, 55 MP | Doskok, początek kombo, 55 MP |
| potem A, potem A | — | Podbicie 30 MP, ognisty finisz 65 MP |
| D ↑ A | Mega Strzał 100 MP | Dwie potężne fale ognia |
| D ↓ A | Metalowy Kop 35 MP | Uderzenie obszarowe i pierścień |
| D → J | Seria ognia 90 MP | Wachlarz płomieni z rąk |
| D ↑ J | Teleport 65 MP | Ognisty krąg |
| D ↓ J | Pułapka 70 MP | Pułapka |
| D J A | Transformacja 200 MP | Odwołanie formy, 0 MP |
| J w powietrzu | Dwa dodatkowe skoki | Dwa dodatkowe skoki |

Mech pozostaje bez limitu czasu aż do śmierci lub odwołania. Ma oddzielne pozy
chodu, biegu, ciosów, ognia, obrony, trafienia, skoku i upadku. Nie jest osobnym
wyborem w menu. Ogień łączy pomarańczowe płomienie z turkusowymi brzegami.
To własny efekt inspirowany charakterem ognistych ataków LF2; nie kopia Firena.

## Szymonoko (411), Mega Ninja Jaś (412), Wasyl (410)

Szymonoko: D ↑ A tworzy pełnego klona z 500 HP i 500 MP, AI i umiejętnościami.
Oryginał może mieć jednego żywego bezpośredniego klona. Ten klon może mieć jednego
klona drugiej generacji; dalej łańcuch się kończy. Maksymalnie trzy żywe postacie
w rodzinie, bez wzajemnych obrażeń, także przy drużynie niezależnej.
Po śmierci dziecka można je ponownie przywołać, z zachowaniem limitu rodziny.

Jaś: co trzecie otrzymane trafienie naprzemiennie uruchamia unik z teleportacją
lub kontrę błyskawicą; co najmniej 35 kroków między kontrami. Działa na rzeczywistą
utratę HP, nie na sam kontakt z obroną; nie wskrzesza i nie wyrywa z chwytu.

Wasyl odzyskuje 60% utraconego HP, do 40 HP na zdarzenie, oraz 2 HP co 12 kroków
przez 120 kroków po trafieniu. Nie wskrzesza. Jego dotychczasowy pojedynczy klon
pozostaje osobną, słabszą mechaniką; nie dotyczy go nowy łańcuch Szymonoko.

## Skibidi Sigma Tata (413)

1500 HP i zachowana druga faza poniżej połowy HP. Nowy motyw: ciemne kule,
pierścienie i trwałe ogniste toalety zamiast zwykłych ludzkich pomocników.

| Kombinacja | Moc |
|---|---|
| D → A | Trzy kule zaćmienia |
| D ↑ A | Obszarowa fala uderzeniowa |
| D ↓ A | Wachlarz ognia |
| D → J | Seria ognistych pocisków |
| D ↑ J | Do trzech ognistych toalet |
| D ↓ J | Deszcz ciemnych kul |
| D J A | Ładowany finisher: obszarowy wybuch i osiem kul |

Toalety mają po 180 HP, stoją w miejscu, samodzielnie celują i strzelają do
przeciwników co 40 kroków. Nie wygasają czasowo; znikają po zniszczeniu. Ponowne
przywołanie uzupełnia brakujące do trzech. Nie ranią właściciela ani swoich toalet.
Finisher ładuje się 45 kroków, może zostać przerwany trafieniem lub chwytem,
ma 240 kroków odnowienia. Wybuch zadaje 120 obrażeń przed pozostałymi efektami.

## Android i Bluetooth

APK jest testowy i podpisany kluczem debug. Pierwszy start rozpakowuje wspólne
zasoby i sprawdza ich sumy SHA256; zostaw około 4 GB wolnego miejsca.
Ekran startowy umożliwia grę lokalną albo próbne połączenie Bluetooth dwóch telefonów.
Sparuj telefony w ustawieniach Androida. Na pierwszym wybierz ZAŁÓŻ GRĘ, na drugim
DOŁĄCZ i nazwę pierwszego telefonu. Na obu użyj identycznego APK. Na Androidzie 12+
zaakceptuj dostęp do urządzeń w pobliżu. Nie jest wymagany internet ani skanowanie GPS.
Przy problemie anuluj połączenie i ponów. Gra przez radio i sterowanie na fizycznym
telefonie nie zostały jeszcze zweryfikowane. Test przekaźnika bajtów nie jest dowodem
rozgrywki Bluetooth na urządzeniach.

## Odtworzenie i ograniczenia

`.build-venv/Scripts/python.exe tools/build_polish_originals.py` odtwarza DAT z
przypiętego LF2 i zachowanych PNG, bez zmiany importowanych zasobów.
`tools/build_windows_portable.ps1` buduje EXE, a `tools/build_android_local.ps1`
buduje biblioteki w izolowanym WSL i pakuje APK bez Android Studio.
Szczegóły testów: `validation/hero-update-2026-11-06/REPORT.md`.
Balans i płynność na telefonach pozostają eksperymentalne. Pełne kampanie,
międzyplatformowa synchronizacja i nagrania nie są potwierdzone w tym etapie.
