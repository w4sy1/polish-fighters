# Android 0.12.2 — naprawa pierwszego startu i nowy ekran, 2026-11-12

## Przyczyna i naprawa

Komunikat „Brak indeksu paczki gry” wynikał z błędnej kolejności wpisów w ZIP.
Indeks `manifest.json` był na końcu archiwum, choć strumieniowy czytnik Androida
wymaga go jako pierwszego wpisu. Sam poprawny CRC i SHA256 nie wykrywał tego błędu.
Wcześniejsza aktualizacja SDL nie naprawiała tej kolejności.

Paczka została wygenerowana ponownie z indeksem na początku. Identyfikator danych
pozostał ten sam, więc istniejące poprawnie przygotowane dane nie wymagają ponownego
rozpakowania. Własne ustawienia są poza katalogiem rozpakowywanych danych.

Dodano niezależne zabezpieczenia:
- `verifyNativeGame` w Gradle zatrzymuje pakowanie przy indeksie poza początkiem ZIP
  lub niezgodnej sumie indeksu. Próba negatywna z błędną paczką została odrzucona;
  poprawna paczka została następnie przywrócona i zaakceptowana.
- Python sprawdza kolejność i położenie lokalnego nagłówka ZIP, sumę indeksu,
  ścieżki, kompletność i SHA256 wszystkich 7787 payloadów / 15389 ścieżek logicznych.
- Test Androida odtwarza dokładny błąd manifestu na końcu oraz poprawną instalację,
  zachowanie prywatnych ustawień i odrzucenie ścieżki wychodzącej poza katalog gry.
- Osobna próba czyta **gotowy dostarczany APK**, rozpakowuje go do pustego katalogu,
  sprawdza `.ready`, pliki LF2/skrypty/moduły i tworzy argumenty uruchomienia silnika.
  To ten sam kod przygotowania danych, którego używa Activity.

## Nowy ekran

Całkowicie przebudowano ekran przygotowania oraz główny ekran Androida:
ciemne tło, branding Polish Fighters, karta aktualnej gry, duży przycisk grania,
oddzielne wejścia do ustawień i gry ze znajomymi. Wi-Fi, Bluetooth PAN,
próbny Bluetooth radio i parowanie pozostają dostępne w menu połączeń.
Anulowanie połączenia pokazuje się dopiero po rozpoczęciu próby połączenia.

Ładowanie pokazuje postęp rozpakowywania i przygotowywania plików. Ekran błędu ma
czytelny opis, ponowienie i odnośnik aktualizacji. Nie pokazuje pustego paska 0%.
Domyślnie widoczny moduł jest zapisywany przed wejściem do silnika, aby pierwszy
start nie otwierał ponownie listy wszystkich modułów. Istniejące wybory zachowano.

Układy zostały wyrenderowane natywną grafiką Androida w Robolectric i obejrzane.
Podglądy nie są zdjęciami z fizycznego telefonu.

## Testy

- 52 unikalne przypadki Androida zaliczone w dwóch przebiegach: 51 PASS i jeden
  warunkowy test APK pominięty w przebiegu zwykłym; następnie ten test uruchomiono
  osobno z gotowym APK i uzyskano PASS, bez pominięcia.
- Python: 58 przypadków, 57 PASS / 1 SKIP (uprawnienia Windows do symlinków).
- Lint: 0 błędów / 35 ostrzeżeń. Poprawka SDL z 0.12.1 zachowana.
- Kompilacja APK, obie biblioteki ARM, CRC, podpis i wyrównanie 16 KiB: PASS.
- Wersja APK: versionCode 14 / 0.12.2-start. ApplicationId i klucz podpisu zachowane.
- Negatywny test Gradle: błędny ZIP z indeksem na końcu nie może przejść pakowania.

## Pliki i zakres

Android: `GameBootstrapActivity.java`, `BluetoothLobbyActivity.java`,
`GameLaunchArguments.java`, `AndroidManifest.xml`, `app/build.gradle` oraz nowe
zasoby w `app/src/main/res` (układy, kolory, tło, przyciski, pasek postępu i teksty).
Walidacja: `prepare_android_game.py`, `check_full_apk.py`,
`check_android_game_bundle.py`, `verify_game_bundle.py`.
Testy: `GameBootstrapTest.java`, `StartScreenTest.java`, `GamePackSettingsTest.java`,
`test_bundle_contract.py`.

Nie zmieniano kodu C++ ani mechaniki walki. Windows 0.12.0 pozostaje aktualny.
Nie wykonano fizycznej próby telefonu, walki, Bluetooth ani USB; ADB nie wykazało
urządzenia. Próba JVM potwierdza przygotowanie danych z APK i poprawne argumenty,
nie stanowi wykonania natywnego silnika ARM na telefonie.

Publikacja i sprzątanie: w toku.
