# Protokół pokoju TCP v1

Stan wersji 0.6: `RoomHost` jest podłączony do lobby, wyboru postaci i symulacji gry. Przetestowano 2–8 osobnych procesów gry na jednym komputerze Linux. Oryginalny `NetworkTransport` zachowuje dotychczasowy tryb dwóch końców.

## Warstwa transportowa

Każdy komunikat to jeden obiekt JSON zakończony LF. Maksymalnie 4096 bajtów komunikatu, bufor odbioru 8192 bajty i 16 oczekujących/aktywnych połączeń transportowych. Pojemność przyjętych do pokoju uczestników: od 2 do 8 uczestników. Bufor wysyłki jest ograniczony do 64 KiB przez adapter TCP. Przy błędnym komunikacie serwer odsyła `error` i zamyka połączenie po krótkim czasie na opróżnienie kolejki.

TCP może dzielić lub łączyć zapisy, więc parser akumuluje bajty do pełnego LF. Wiadomości są przetwarzane w ograniczonych partiach. Odbiorca musi stale wywoływać `poll()`; klasa nie jest wielowątkowym serwerem z wewnętrzną pętlą.

## Przebieg

1. `{"op":"hello","protocol":1,"profile":"64 znaki SHA-256","name":"Gracz"}`. Profil musi odpowiadać profilowi pokoju. Serwer przydziela slot i odsyła `welcome`; tożsamość slotu wynika z połączenia, nie z pola nadanego przez klienta.
2. Serwer rozsyła `lobby` z listą uczestników, ich gotowością i pojemnością pokoju.
3. Klient ustawia gotowość przez `{"op":"ready","value":true}`.
4. Gospodarz wysyła `{"op":"start"}`. Wymaganych jest co najmniej dwóch uczestników i gotowość wszystkich. Przedwczesny start zwraca błąd bez usuwania gospodarza. Komunikat `start` zawiera wspólne ziarno i numer początkowej klatki.
5. Każdy uczestnik wysyła `{"op":"input","frame":0,"keys":"rc"}`. Dozwolone są niepowtarzające się litery `udlrcbf`. Po zebraniu wejść serwer rozsyła `frame` z tablicą ośmiu slotów.
6. Klienci wysyłają `{"op":"checksum","frame":0,"state":"64 znaki SHA-256"}`. Kolejna klatka jest blokowana do zgodnego raportu wszystkich. Serwer rozsyła `checked`.
7. `{"op":"ping"}` otrzymuje `pong`, aby utrzymać aktywność połączenia poza wysyłaniem wejść.

Serwer przerywa mecz komunikatem `abort` po rozłączeniu, przekroczeniu czasu lub rozbieżności stanu. Nie dopisuje po cichu pustych wejść nieobecnego gracza. Profil, sumy kontrolne i sloty nie zastępują kont ani logowania; to protokół lokalnej sesji gry, nie usługa uwierzytelniania.

## Czego protokół jeszcze nie dostarcza

- Zoptymalizowanego opóźnienia wejść, rollbacku, rekonfiguracji połączeń po zerwaniu, listy publicznych pokoi i zaproszeń.
- Bluetooth i testów na Androidzie/Windowsie oraz fizycznych urządzeniach.

W pliku `validation/network/tcp-results.json` znajdują się wyniki siedmiu testów po 30 klatek dla 2,3,4,5,6,7,8 klientów. Dodatkowo sprawdzono fragmentację powitania, cytowania/spacje w nazwach, niezgodny profil, przepełniony pokój, błędny JSON, za duży komunikat, próbę narzucenia innego slotu, rozbieżną sumę stanu, rozłączenie i zawieszonego uczestnika.

## Integracja gry 0.6

`polish-fighters/room_network.lua` rozszerza dotychczasowy interfejs sesji. Nowy tryb tworzy klienta TCP również dla gospodarza; `ResourceBridge` utrzymuje serwer na głównym wątku i odpytuje go przed gniazdem własnego klienta. Połączenie legacy pozostało osobną opcją. Jedno urządzenie wysyła tylko swój pierwszy zestaw sterowania; serwer ustala jego docelowy slot.

`start.seed` generuje wspólną tabelę 3000 bajtów, następnie zeruje sekwencję RNG. Lokalne ziarna/menu nie zmieniają początkowego RNG meczu. `input` może zawierać `functions` (cyfry F1–F9) i `unlock` (0–3). Tylko slot 0 może nadawać niepuste komendy globalne. Serwer rozsyła je w `frame`. Przed wysłaniem wejścia klatki N klient zgłasza wynik symulacji N-1 i czeka na `checked`.

`sync_state.lua` sortuje pola i wylicza SHA-256 z aktywnego ekranu, tabeli i indeksu RNG, listy losowań etapów, flag odblokowania oraz dynamicznego stanu meczu: obiektów, pozycji, klatek animacji, HP/MP, sterowania i liczników. Dane statyczne rekordów zastępuje ID i typ; są objęte profilem sesji. Wyłączono lokalny rendering, iskry, dźwięk i nagrywanie. To nie jest kompletny audyt deterministyczności wszystkich trybów i platform.

Testy `tools/check_room_game.py` uruchamiają prawdziwe procesy silnika, nie imitacje klientów. Przebieg menu używa oryginalnego wyboru postaci. Osobny test zmienia HP jednego procesu, sprawdzając przerwanie gry. Wyniki znajdują się w `validation/room-game/`. Testy transportowe w `validation/network/` nadal używają kontrolowanych sum.
