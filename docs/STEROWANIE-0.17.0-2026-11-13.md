# Polish Fighters 0.17.0 — poprawki dotyku (wydanie testowe)

## Zmiany

- SDL zachowuje naciśnięcie palcem do następnej klatki skryptu. Krótki tap zakończony między odczytami nie znika już przed obsługą w Lua.
- Przycisk ATAK ma widoczny promień co najmniej 56 px, a strefa dotyku co najmniej 78 px. Zmiana obejmuje również starsze profile z mniejszym zapisanym przyciskiem; pozostałe rozmiary kontrolek i ustawienia pozostają zachowane.
- Przycisk komend w aktywnej walce jest większy i ma polską etykietę KOMENDY. Otwiera wybór ZA MNĄ / COME, ZOSTAŃ / STAY, ATAKUJ / ATTACK i BROŃ / DEFEND. Dotknięcie pozycji zamyka wybór i potwierdza komendę.
- Komendy nadal używają istniejących bitów wejścia gry, więc przechodzą przez symulację i istniejącą wymianę wejść multiplayer.
- Nie zmieniono joysticka ani klawiaturowych kombinacji Little Fighter.

## Weryfikacja

- Pełny zestaw Python: 70 testów zaliczonych, 1 pominięty z powodu uprawnień Windows do symlinków.
- Pełny zestaw Lua: 145 skryptów składniowych i wszystkie testy przepływów zaliczone, w tym wejście dotykowe, zwolnienie, AI komend drużyny i buforowanie w multiplayer.
- Pakiety APK i Windows są budowane w GitHub Actions; wynik oraz sumy kontrolne będą dopisane po pobraniu artefaktów.
- Nie podłączono fizycznego telefonu. Działanie na urządzeniu i odczucie przycisku wymagają testu sprzętowego; wydanie pozostaje testowe.

## Zakres ekranów

Komendy są kontrolką podczas aktywnej walki, a nie podczas wyboru postaci lub układania drabinki turniejowej. Na ekranie wyboru drużyny ATAK/OK służy do zatwierdzania zaznaczeń.
