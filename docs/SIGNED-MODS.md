# Podpisany moduł danych LF2

Do importu na Windows i Androidzie wybierz plik ZIP zawierający kolejno
`catalog.json`, `catalog.sig`, `manifest.json`, `manifest.sig` i `package.zip`.
Podpisy Ed25519 mają po 64 bajty. Podpisy obejmują dokładne bajty dokumentów JSON
kanonizowanych przez narzędzie `tools/verify_mod_package.py`. Wewnętrzny ZIP ma
hash i rozmiar z podpisanego manifestu. Indeks STABLE przypina manifest pod
kluczem `id@wersja`.

`package.zip` zawiera `module.json` z polami `source` i `stage` oraz pliki
`assets/a/<nazwa>.<format>`. Przykład deklaracji:
`{"source":"assets/a/data.txt","stage":"assets/a/stage.dat"}`.
Zasoby powinny być znormalizowane do postaci używanej przez silnik OpenLF2.
Instalator tworzy lokalnie `package.manifest` i adaptery Lua. Archiwum dostarcza
wyłącznie dane. Pierwsza wersja obsługuje moduły samodzielne bez dodatkowych
zależności, konfliktów, mapowania dźwięków i deklaracji dodatkowych kampanii.

Oba instalatory używają 32-bajtowego klucza publicznego Ed25519 w
`engine/android/app/src/main/assets/mods/catalog-ed25519.pub`. Dodanie
zatwierdzonego klucza jest wymagane do importu gotowych paczek. Klucz prywatny
pozostaje po stronie wydawcy. Testy generują własne klucze.

Na Windows użyj Tkinterowego menedżera albo
`python tools/mod_manager.py library install --archive <plik.zip>`.
W środowisku Pythona potrzebne są `cryptography==50.0.1` i
`jsonschema==4.25.1`, zgodnie z konfiguracją CI.
Na Androidzie wybierz ZIP w ekranie Mody. Build przeznaczony dla Google Play
musi być zbudowany z właściwością Gradle `-Popenlf2GooglePlay=true`, która
blokuje starszy import paczek z adapterami Lua. Wydania poza Google Play
zachowują dotychczasowy import paczek konwertera.

Instalacja używa istniejących katalogów staging i rejestru modułów. Windows
obsługuje aktualizację w bibliotece. Android zgłasza istniejącą instalację tego
samego ID i obsługuje tu pierwszą instalację. Katalog z sieci, zapamiętywanie
rewizji i automatyczne aktualizacje pozostają osobnymi etapami.
