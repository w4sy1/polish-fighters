# Wydanie testowe Android 0.9.0 — 2026-11-11

`tools/build_android_local.ps1` domyślnie buduje versionCode 9 / 0.9.0-bluetooth-test
i uruchamia sześć testów ustawień Androida w Robolectric. Wymaga JDK17.
Gotowy plik: `engine/out/PolishFighters-Android-2026-11-11.apk`.
`-VersionCode`, `-VersionName` i `-ApkName` pozwalają jawnie ustawić kolejną wersję.
Przy zmianach Java/Lua bez zmian C++ można użyć `-SkipNative`.
Przełącznik kodów: ekran startowy → USTAWIENIA; komunikat „lamus” po zapisaniu
włączenia. Pełne wyniki i ograniczenia: `docs/TESTY-BLUETOOTH-2026-11-11.md`.

---

# Budowa lokalna bez Android Studio — 2026-11-07

Gotowy skrypt: `powershell -ExecutionPolicy Bypass -File tools/build_android_local.ps1`.
Korzysta z istniejącego JDK17/Windows SDK oraz izolowanego WSL `PolishFighters-Build`
z Conan i NDK r28c. Buduje ARM64 + ARMv7 i dopiero potem pakuje uniwersalny APK.
Nie tworzy emulatora. `-SkipNative` ponownie pakuje istniejące biblioteki po zmianie
Lua/grafiki/Java. `-SkipBundle` zachowuje wcześniej przygotowany komplet zasobów.
`tools/prepare_android_game.py` deduplikuje wszystkie 9 lokalnych pakietów;
bootstrap weryfikuje SHA256 i instaluje zasoby do prywatnego katalogu aplikacji.
`tools/check_full_apk.py <apk>` sprawdza oba ABI, zależności ELF, 16 KB dla ARM64,
CRC i zgodność kompletnego pakietu gry. To nie zastępuje testu na telefonie.
Nie zmieniono applicationId ani konfiguracji podpisywania. Bluetooth jest próbny,
dla dwóch wcześniej sparowanych telefonów, przez ekran przed uruchomieniem gry.

---

# Polish Fighters w Android Studio

Otwórz folder `engine/android` przez **File → Open**. Gradle Wrapper8.13 i suma dystrybucji są dołączone. Wybierz **Gradle JDK17**; JDK25 z bieżącego Android Studio nie jest zgodne z Gradle8.13. Nie zmieniaj applicationId `pl.prestigetech.polishfighters`, konfiguracji signing ani namespace istniejącej Activity.

Przed pierwszą synchronizacją, z katalogu projektu:

```powershell
python tools/prepare_android_studio.py
```

Skrypt pobiera wyłącznie źródła SDL3.4.14 z kontrolą SHA256, przygotowuje jego rzeczywiste klasy Java, własne Lua i ikony. Android Studio wykryje SDK; lokalne `local.properties` nie jest częścią repozytorium. W ZIP AndroidStudio pliki przygotowania są już dołączone.

Sprawdzenie samego kodu Java i zasobów:

```powershell
cd engine/android
.\gradlew.bat :app:compileDebugJavaWithJavac
.\gradlew.bat :app:lintDebug
```

## Silnik natywny

To gra C++/SDL/Lua, więc do uruchomienia na telefonie potrzebne są także biblioteki ARM64. Nie są zastępowane pustą aplikacją Java. Lokalnie nie zbudowano jeszcze bibliotek Androida ani nie wykonano testu na telefonie; Windowsowe DLL nie działają na Androidzie.

Pełny, istniejący pipeline działa na Linuxie (albo GitHub Actions → **Polish Fighters builds → Run workflow**):

```sh
cd engine
bash dist/build-android.sh arm64-v8a
```

Wymagania tego pipeline: JDK17, Gradle8.13, SDK35, NDK28.2.13676358, Conan2.32.0, CMake, Ninja, kompilatory i narzędzia wymienione w `.github/workflows/build.yml`. Wynik to APK oraz artefakt `AndroidStudio-ARM64-native` zawierający katalogi `jniLibs`, `sdl-java`, `assets` i `res` do `engine/build/android/` w lokalnym projekcie.

Po dodaniu rzeczywistych `.so` można używać **Build → Make Project** lub `gradlew.bat assembleDebug`. Zadanie `verifyNativeGame` celowo przerywa pakowanie przy braku bibliotek: taki APK nie uruchomiłby gry.

Pliki LF2 i dodatków mają własnych autorów. Repozytorium i ZIP kodu nie zawierają cudzych instalatorów ani paczek graficznych. Lokalna pełna paczka Windows jest osobnym artefaktem. Uprawnienia Bluetooth w manifeście nie potwierdzają działającego połączenia Bluetooth.
