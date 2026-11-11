# Pobieranie pelnej gry Windows i Android

Dystrybucja obejmuje pelny ZIP Windows z modulami i zasobami oraz APK Android.
Czesci po 90 MiB wynikaja z ograniczenia transferu przez integracje Google Drive.

Pobierz wszystkie czesci Windows i Android oraz `manifest.json`, `Polacz.ps1`
i `POLACZ.cmd` do jednego katalogu. Uruchom `POLACZ.cmd` w Windows.
Skrypt sprawdza SHA256 kazdej czesci, laczy pliki i sprawdza SHA256 wyniku.
Nie nadpisuje istniejacego pliku o innej zawartosci.

Po polaczeniu rozpakuj caly `PolishFighters-Windows.zip` i uruchom `GRAJ.cmd`.
`PolishFighters-Android.apk` zainstaluj na telefonie. Do instalacji Androida
po polaczeniu plikow nie jest juz potrzebny komputer.

`manifest-2026-11-11.json` jest zrodlem manifestu tego testowego wydania.
W pobranym zestawie manifest ma nazwe `manifest.json`.

Windows: WASD / Num7 atak / Num8 blok / Num9 skok; F4 lub MENU/MODULY wraca do modulu.
APK i Windows maja zgodny kod natywny. Ostatnia poprawka plynnosci wymaga jeszcze
ponownej proby na prawdziwych urzadzeniach. Bluetooth PAN/radio niepotwierdzone.
Paczki nie zawieraja prywatnych zapisow graczy.
