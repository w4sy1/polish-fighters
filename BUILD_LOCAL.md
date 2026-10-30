# Lokalna kompilacja Linux x86_64

W wersji 0.5 zbudowano pełny silnik projektu, w tym aplikację, renderer, odtwarzanie muzyki, LuaJIT, parser Tigera oraz backend pokoju TCP. Nie jest to kompilacja Androida ani Windows. Program korzysta z przygotowanych bibliotek współdzielonych; nie jest samodzielnym przenośnym wydaniem.

## Użyta metoda

Wykorzystano g++ 13.3, make, nagłówki odpowiednich bibliotek oraz pliki `.so` z uruchomionego wcześniej OpenLF2 v1.1.1 AppImage. LuaJIT zbudowano lokalnie statycznie. Nie instalowano pakietów globalnie.

Przygotowany katalog `DEPS` ma strukturę:

- `SDL`: źródła tagu release-3.4.14, nagłówki w include/SDL3.
- `SDL_ttf`: źródła tagu release-3.2.2, nagłówki w include/SDL3_ttf.
- `FFmpeg`: źródła tagu n7.1.5.
- `LuaJIT`: źródła v2.1 i zbudowany `src/libluajit.a`.

Dokładne rewizje Git są w `validation/native-build/build-manifest.json`. Używaj tych rewizji, a nie ruchomej końcówki gałęzi.

```sh
make -C DEPS/LuaJIT/src BUILDMODE=static XCFLAGS=-fPIC -j2
```

Katalog `RUNTIME_LIBS` musi zawierać zgodne biblioteki `libSDL3.so.0`, `libSDL3_ttf.so.0`, `libavformat.so.61`, `libavcodec.so.61`, `libavutil.so.59`, `libswresample.so.5`. Potrzebne są też systemowe nagłówki/biblioteki OpenSSL, curl i zlib oraz biblioteka bzip2. Nagłówek bzip2 1.0.8 `bzlib.h` umieść w `BUILD_DIR/generated/`.

```sh
python tools/manual_linux_build.py --deps DEPS --runtime-libs RUNTIME_LIBS --build-dir BUILD_DIR
BUILD_DIR/polish-fighters --help
python tools/smoke_lf4.py --engine BUILD_DIR/polish-fighters --installer /sciezka/LF2_v2.0a.exe
```

Skrypt używa ścisłych ostrzeżeń (`-Werror`) dla kodu projektu, nagłówków zewnętrznych jako systemowych i pamięci podręcznej obiektów zależnej od źródeł, nagłówków oraz flag. Generuje odcisk natywnego kodu niezależny od ścieżki i zakończeń CRLF. Generator CMake został osobno uruchomiony przez CMake 3.31.6; otrzymano ten sam odcisk.

## Testy transportu pokoju bez SDL/FFmpeg

```sh
g++ -std=c++23 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -pthread -I engine/include tests/room_host_runner.cpp engine/src/engine/room_host.cpp engine/src/engine/room.cpp engine/src/core/json.cpp engine/src/adapters/network/transport.cpp -o room-host-runner
python tests/test_room_tcp.py --runner ./room-host-runner
```

Runner służy testom i nasłuchuje na localhost z automatycznie przydzielanym portem. Nie jest to gotowy klient gry. `RoomHost` jest wspólnym serwerem protokołu; nowy pokój LAN jest podłączony do gry, a poprzednie połączenie dwupunktowe pozostaje osobną opcją.

## Test zgodności połączenia gry

```sh
python tools/check_native_network.py --engine BUILD_DIR/polish-fighters --old-engine /sciezka/do/starego/AppRun --installer /sciezka/LF2_v2.0a.exe
```

Sprawdza dwa zgodne procesy gry, odrzucenie starszego silnika i odrzucenie różniących się plików zasobów przy takich samych deklaracjach pakietu.

Nie dołączono tutaj SDK/NDK Androida, MSVC ani zewnętrznych plików `.so`. Przepisy budowania Androida i Windows pozostają w `.github/workflows/build.yml` oraz `engine/dist/`; nie były uruchomione na tych platformach.
