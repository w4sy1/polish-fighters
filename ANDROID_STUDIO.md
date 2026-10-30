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
