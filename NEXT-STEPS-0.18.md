# Polish Fighters 0.18 — stan wydania testowego

## Potwierdzone

- Android Raptor_5G: bezpośredni start klasycznego menu LF2, wejście do modułów i powrót; układ z joystickiem po lewej, osobnymi kołami BLOK/SKOK/ATAK po prawej i rozwijanymi dymkami komend jest widoczny w walce.
- ATAK w walce: użytkownik potwierdził skuteczny cios.
- Nagranie z Raptora pokazuje jednoczesne podświetlenie BLOK i SKOK. Nie potwierdza równoczesnego ATAKU.
- Testy Lua układu, identyfikatorów palców, zwolnienia przycisków i komend oraz build Androida przeszły. Paczki APK i ZIP sprawdzono pod kątem integralności; ZIP zawiera zasoby offline i 9 paczek.
- Sterowania klawiaturą Windows nie zmieniano. Testy silnika Windows bez GUI przeszły.

## Do wykonania przed oznaczeniem wydania jako stabilne

1. Na fizycznym Raptor_5G w aktywnej walce sprawdzić osobno BLOK, SKOK i ATAK, następnie jednocześnie wszystkie trzy przyciski, ich niezależne zwolnienie i krótki tap. Zarejestrować ekran. Wcześniejsze nagranie nie objęło trzeciego przycisku.
2. W trybie treningowym sprawdzić faktyczne kombinacje LF2 (np. blok + kierunek + atak/skok) oraz ruch z jednoczesnymi akcjami. Użytkownik potwierdził cios, ale nie kombinacje.
3. Sprawdzić w grze efekt czterech komend drużyny: ZA MNĄ, ZOSTAŃ, BROŃ, ATAKUJ.
4. Uruchomić pełną paczkę Windows w widocznym oknie i sprawdzić płynność oraz walkę. Dotychczas wykonano testy silnika bez GUI; pełnego przebudowania natywnego EXE nie było z powodu brakującego lokalnego toolchainu Conan.
5. Po głównej naprawie przetestować pobieranie modów Naruto, Wrestler LF i Dragon Ball/Beerus z konkretnych źródeł. Nie potwierdzono pobrania tych archiwów.

Nie traktować testów Lua ani samego zbudowania paczek jako dowodu działania wszystkich gestów na telefonie.
