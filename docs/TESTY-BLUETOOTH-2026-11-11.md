# Polish Fighters 0.9.0 — testy telefonu i Windows, 2026-11-11

## Pobranie i uruchomienie

Pliki: [wydanie testowe na GitHubie](https://github.com/w4sy1/polish-fighters/releases/tag/mobile-test-2026-11-11).

- Telefon: pobierz `PolishFighters-Android-2026-11-11.apk`, zainstaluj i poczekaj na przygotowanie danych przy pierwszym uruchomieniu. APK zawiera ARM64 i ARMv7 oraz dziewięć lokalnych pakietów gry. Wersja 0.9.0-bluetooth-test, versionCode 9, Android 5.0 lub nowszy. Przygotuj około 4 GB wolnego miejsca; system bez twardych dowiązań może potrzebować więcej.
- Windows: pobierz `PolishFighters-Windows-2026-11-11.zip`, rozpakuj cały ZIP i uruchom `PolishFighters-Windows/Graj-Wszystkie-Mody.cmd`. `LittleFighters.exe` jest właściwym EXE gry; potrzebuje sąsiednich DLL i folderów. `LF2_v2.0a.exe` jest źródłem danych, nie plikiem uruchamiającym tę wersję gry.
- Nie usuwaj starej aplikacji Android przed próbą aktualizacji: applicationId i dotychczasowy podpis debug zostały zachowane. W razie komunikatu o innym podpisie zachowaj poprzednie dane przed dalszymi działaniami.

## Kody na telefonie

Na ekranie startowym wybierz **USTAWIENIA**, zaznacz **Włącz kody — odblokuj ukryte postacie** i kliknij **Zapisz**. Przy zmianie z wyłączonych na włączone pojawi się okienko z dokładnym napisem **lamus**. Kodów nie trzeba wpisywać klawiaturą telefonu.

Odznaczenie pola i zapis wyłącza odblokowanie kodem. **Anuluj** zachowuje poprzedni stan. Ustawienie dotyczy ukrytych postaci dostępnego katalogu; nie instaluje brakujących modów ani nie usuwa postępu zdobytego w przygodzie. Przełącznik zapisuje istniejącą opcję silnika `options.unlock_characters` w `settings/config.json`, zachowując sterowanie, postęp i pozostałe ustawienia. Na komputerze nadal działa kod **polishfighters**.

## Bluetooth — następny test na dwóch telefonach

1. Na obu telefonach zainstaluj ten sam nowy APK, uruchom go i poczekaj na przygotowanie gry.
2. Sparuj telefony w ustawieniach Bluetooth Androida. Możesz przejść tam przyciskiem **PAROWANIE / USTAWIENIA BLUETOOTH**.
3. Na pierwszym wybierz **BLUETOOTH: ZAŁÓŻ GRĘ**. Na drugim **BLUETOOTH: DOŁĄCZ** i nazwę pierwszego telefonu. Zaakceptuj wymagane zgody; po systemowym włączeniu Bluetooth lub przyznaniu zgody ponów wybór trybu.
4. Sprawdź wspólny wybór postaci, kilka minut walki, reakcję na anulowanie i wyłączenie Bluetooth oraz ponowne połączenie. Każdy telefon steruje jednym graczem. Podczas pierwszej próby pozostaw oba ekrany włączone.
5. Przy problemie zapisz modele telefonów, wersje Androida, etap zatrzymania i tekst komunikatu. Szczególnie potrzebny jest test ARM32 ↔ ARM64.

Implementacja używa bezpiecznego RFCOMM oraz dwukierunkowego przekaźnika do protokołu pokoi silnika. Nie wymaga Internetu ani skanowania urządzeń przez grę. Wybiera wcześniej sparowany telefon i sprawdza zgodność profili przez protokół silnika.

## Wyniki sprawdzeń

- Windows: konfiguracja i build CMake/MSVC PASS, start pełnego katalogu z kodami wyłączonymi i włączonymi PASS. Natywne próby postaci, mecha, klonów, kontr, regeneracji, toalet i finishera PASS.
- Android: assembleDebug PASS. Zachowane applicationId `pl.prestigetech.polishfighters`, podpis i architektura aplikacji. Natywne biblioteki obu ABI pochodzą z poprzedniej zweryfikowanej kompilacji: obecna zmiana Java/ustawień nie wymaga zmiany C++. Sprawdzono ich obecność, zależności ELF i wyrównanie ARM64 do 16 KB w nowym APK.
- Sześć testów Androida w Robolectric PASS: włączanie/wyłączanie, zachowanie innych danych, uszkodzony JSON bez nadpisania, przerwany zapis, pełne kliknięcie okna ustawień i komunikat `lamus`, anulowanie bez zapisu. To testy na komputerze, nie fizyczny Android.
- Lua: 26 dotychczasowych zestawów oraz nowy test desktopowego kodu i współdzielonej opcji odblokowania PASS; składnia 125 plików PASS.
- Python: 51 PASS, jeden SKIP, łącznie 52 testy.
- Produkcyjny przekaźnik Java: trzy próby po 512 KiB, oba kierunki, rozłączenia i anulowanie PASS. Dwa nowe silniki przez ten przekaźnik: po 120 klatek walki we wspólnej puli, identyczny końcowy SHA256 stanu `e828b85bf1c107a2fce9a837585b2a2fe297e31d4c6643d2e547ef8efbab1b97`.
- APK: podpis v1/v2 PASS, zipalign/16 KB PASS, CRC PASS, obie architektury i klasy Bluetooth PASS. Potwierdzono rzeczywiste napisy `lamus` i poprawne polskie znaki w końcowym DEX. Komplet danych: 15399 plików logicznych i 7795 unikalnych zasobów, sprawdzonych SHA256.
- Windows ZIP: 15440 plików, CRC i brak powtórzonych wpisów PASS; bez wcześniejszego `userdata` i nagrań.
- Lint Android: nadal FAIL — 27 wcześniej istniejących błędów w wygenerowanych klasach SDL (25 MissingPermission, jeden NewApi i jeden UnspecifiedRegisterReceiverFlag). Nowe klasy ustawień nie mają błędów lint. Kontroli nie wyłączono i nie zmieniano zależności SDL poza zakresem zadania.

## Pliki i zakres zmian

Nowa funkcja: `BluetoothLobbyActivity.java`, `MobileCodeSettings.java`, dwa pliki testów Androida, `app/build.gradle` i `gradle.properties`; aktualizacja lokalnego skryptu budowy APK, testu kodu Lua i narzędzi weryfikacji paczek. Dokumentacja: ten plik, README, README_PL, ANDROID_STUDIO i centralny PROJECT-STATUS.

Publikowane źródła zawierają także wcześniej lokalne, przetestowane zmiany Heroes/Bluetooth wymagane do odtworzenia aktualnej gry. Nie cofnięto ich i nie nadpisano wcześniejszych paczek. Przed pracą zapisano kopię zmian i plików nieśledzonych w lokalnym katalogu walidacji. Utworzono osobny branch `codex/bluetooth-mobile-test-2026-11-11`. Nie zmieniano produkcyjnego podpisywania, Firebase, identyfikatora aplikacji ani historii Git.

Wzorce typowych sekretów sprawdzono w 526 plikach tekstowych, a nazwy plików prywatnych w 1925 wpisach istniejących śledzonych ZIP-ów — bez trafień. Publiczny klucz debug do testowych instalacji jest celowym, dotychczasowym elementem repozytorium. Lokalne dane użytkownika i konfiguracje środowiska są wyłączone przez `.gitignore`.

## Ograniczenia i ryzyka

Nie było podłączonych telefonów w ADB. Nie potwierdzono instalacji, szybkości pierwszego startu, dotyku, komunikatu na rzeczywistym telefonie ani radiowej gry Bluetooth. Test lokalnego przekaźnika nie potwierdza działania radia. To wydanie testowe przeznaczone właśnie do tych prób.

Pozostają wcześniejsze braki części importowanych modów, niepełna zgodność ich mechanik i niezweryfikowane pełne kampanie. Niczego z tego nie uznano za naprawione. Działające elementy i postęp zachowano. Zakres odpowiada przygotowaniu ustawień kodów, kontroli Bluetooth oraz paczek do testów na GitHubie; fizyczne testy pozostają do wykonania.
