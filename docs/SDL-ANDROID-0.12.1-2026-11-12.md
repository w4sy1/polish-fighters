# Android 0.12.1 — usunięcie 27 błędów SDL, 2026-11-12

## Wynik

`lintDebug`: **0 błędów**, 39 ostrzeżeń. Kontroli Lint nie wyłączono,
nie dodano baseline ani adnotacji ukrywających zgłoszone błędy.
43 testy Androida PASS, w tym 16 przypadków poprawki na API 28/34.
Python: 55 testów — 54 PASS, 1 SKIP z powodu uprawnień Windows do symlinków.
Pełna kompilacja APK, kontrola danych, obu ABI, podpisu i wyrównania 16 KiB PASS.

## Naprawione problemy

1. 25 `MissingPermission`: operacje Bluetooth/GATT obsługują `SecurityException`.
   Odmowa lub cofnięcie uprawnienia zwraca wynik niepowodzenia zamiast przerywać
   aplikację. Dotyczy odczytu/zapisu, powiadomień, połączenia, MTU, wykrywania
   usług, metadanych urządzenia i zamykania połączenia. Zamknięcie jest wykonywane
   niezależnie od tego, czy poprzednie rozłączenie zostało odrzucone. Nieudane
   połączenie nie jest rejestrowane jako gotowy kontroler.
2. `NewApi`: rozpoznawanie pióra nie wywołuje `InputDevice.isExternal()` poniżej
   API 29. Przypadek API 28 jest sprawdzany testem.
3. `UnspecifiedRegisterReceiverFlag`: odbiornik USB używa zgodnej z API 21+
   rejestracji `ContextCompat` i `RECEIVER_NOT_EXPORTED`. Nie udostępnia aplikacjom
   zewnętrznym wewnętrznego odbiornika odpowiedzi na prośbę o dostęp USB.

Dodano AndroidX Core 1.16.0, zgodne z minSdk 21 i compileSdk 35. Jego manifest
wnosi techniczne uprawnienie o poziomie `signature` dla nieeksportowanego
odbiornika na starszym Androidzie. Nie jest to nowe uprawnienie wymagające
zgody użytkownika. ApplicationId, klucz podpisu i wymagane uprawnienia Bluetooth
pozostały niezmienione. Wersja APK: code 13 / 0.12.1-sdl.

## Trwałość poprawki i pliki

- `tools/patches/sdl3-3.4.14-android.patch` — niewielka poprawka trzech klas SDL.
- `tools/patches/SDLAndroidCompat.java` — obsługa odmowy uprawnień.
- `tools/apply_sdl_android_compat.py` — sprawdzane i powtarzalne nakładanie poprawki.
- `tools/prepare_android_studio.py` i `engine/dist/build-android.sh` — stosują
  tę samą poprawkę po rozpakowaniu źródeł SDL sprawdzonych SHA256.
- `engine/android/app/build.gradle` — zależność i numer wersji.
- `engine/android/app/src/test/java/org/libsdl/app/SDLAndroidCompatTest.java`
  oraz `tests/test_sdl_android_compat.py` — odmowa uprawnień, zachowanie po
  udzieleniu zgody, bezpieczne zamykanie, wersje API, ponowne nałożenie poprawki
  i odrzucanie nieznanego kontekstu źródeł.

Ponowne przygotowanie SDL i ponowne uruchomienie aplikatora PASS.
Składnia skryptu Linux/CI (`bash -n`) PASS. Nie wykonywano ponownego pełnego
cross-builda C++, ponieważ kod natywny nie został zmieniony. Obie biblioteki
sprawdzono względem bieżącego odcisku źródeł C++.

## Pozostałe ograniczenia

39 ostrzeżeń: 27 SetTextI18n, 5 StaticFieldLeak, 3 DiscouragedApi,
2 UnusedAttribute, 1 WifiManagerPotentialLeak, 1 AndroidGradlePluginVersion.
Nie przedstawiamy tego jako usunięcia wszystkich ostrzeżeń projektu.
Brak testu na fizycznym telefonie, kontrolerze BLE i urządzeniu USB;
nie potwierdzamy usunięcia wszystkich wcześniejszych zacięć gry.

Windows 0.12.0 i mechanika walki nie wymagają zmiany z powodu tej poprawki Java.
Dane gry oraz ich identyfikator w APK są takie same jak w 0.12.0; poprawka
nie wymaga ponownego pobierania i składania modów. Nie przywracano lokalnej
instalacji gry — do budowy odczytano zweryfikowane dane poprzedniego APK z Kosza.

Dokumentacja platformy:
- https://developer.android.com/reference/android/bluetooth/BluetoothGatt
- https://developer.android.com/develop/background-work/background-tasks/broadcasts
- https://developer.android.com/reference/android/view/InputDevice#isExternal()

## Publikacja i sprzątanie

Publiczne wydanie: https://github.com/w4sy1/polish-fighters/releases/tag/android-sdl-0.12.1-2026-11-12
Kod wydania: `3bdf1d728cd3e61b8441517f13c800da1001215f`.
APK: `PolishFighters-Android-0.12.1-SDL-2026-11-12.apk`, 544882567 bajtów.
SHA256: `44a51ad5563c6e0e46f347f62659d1502442fd8e876550d64118b64aeaed6d4d`.
Rozmiar i SHA256 w metadanych GitHuba zgodne z lokalnym APK; anonimowe pobieranie
potwierdzone HTTP 206 przy żądaniu zakresowym, bez ponownego transferu całej gry.
Certyfikat podpisu 0.12.1 jest taki sam jak 0.12.0. Zawartość DEX zawiera helper poprawki.

Po potwierdzeniu publikacji lokalny APK i katalogi generowane (3.13 GiB)
przeniesiono do Kosza. `engine/out` jest puste; źródła i prywatne ustawienia zachowano.
Kosza nie opróżniono. Stare raporty o 27 błędach SDL pozostają historycznym zapisem;
bieżący wynik 0.12.1 wynosi 0 błędów i 39 ostrzeżeń.
