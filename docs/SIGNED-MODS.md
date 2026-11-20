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
samego ID i obsługuje tu pierwszą instalację.

## Pełne paczki z GitHuba (`content-pack`)

Mody LF4 Turbo, DBZ, One Piece, Kate, Reinforced, NTSD, Bleach, Polish Fighters
i scalona paczka „Wszystkie razem” są udostępnione za zgodą autorów jako assety
wydania [`mods`](https://github.com/w4sy1/polish-fighters/releases/tag/mods).
Każdy asset `<id>-<wersja>.zip` to ta sama podpisana koperta, ale manifest ma
`package_type: content-pack` i `installation.method: content-pack-zip`
(entrypoint `package.manifest`). `package.zip` zawiera gotową paczkę silnika:
`package.manifest`, skrypty Lua, pliki JSON/MD i zasoby z manifestu. Kod Lua jest
zaufany wyłącznie dzięki podpisowi wydawcy. Pliki wykonywalne są odrzucane.
Paczka trafia do `content-packs/<id>` i zastępuje starszą kopię.

Repozytorium zawiera podpisany katalog `mods/catalog.json` i `mods/catalog.sig`
(format `polish-fighters-mods`). Każdy wpis ma `id`, `name`, `version`,
`profile`, `url`, `size_bytes`, `sha256` i `unpacked_size_bytes`. Klient:

1. pobiera `catalog.json` i `catalog.sig` z `raw.githubusercontent.com` i sprawdza
   podpis Ed25519 kluczem `catalog-ed25519.pub`;
2. pobiera kopertę z wydania (przekierowania tylko do serwerów GitHub), sprawdza
   rozmiar i SHA-256 z katalogu;
3. sprawdza podpisy, przypięcie manifestu i SHA-256 `package.zip` w kopercie,
   a potem rozpakowuje paczkę.

Klienci: Android — ekran Mody, źródło „Polish Fighters — GitHub”; Windows w grze —
katalog modów, przycisk „POLISH FIGHTERS - GITHUB” (moduł `github_mods.cpp`);
narzędzia — zakładka w `tools/mod_manager_gui.py`,
`python tools/mod_manager.py github-list` i `github-install <id>`.

Wydawca buduje koperty i podpisuje katalog poleceniem (klucz prywatny pozostaje
poza repozytorium):

```
python tools/build_mod_release.py --key <ścieżka>/catalog-ed25519-private.pem --engine 1.1.1
gh release upload mods delivery/mods-release/*.zip --clobber
```
