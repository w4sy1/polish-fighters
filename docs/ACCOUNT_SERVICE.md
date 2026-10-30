# Konta i katalog pokoi — kod lokalny

Uruchomienie bez budowania gry, z katalogu projektu:

```powershell
python tools/account_service.py --database userdata/accounts.sqlite --port 8765
```

Usługa nasłuchuje wyłącznie na `127.0.0.1`. Nie wdrożono jej publicznie.
Przed udostępnieniem potrzebne są HTTPS, limity proxy, obsługa odzyskiwania kont,
retencja danych, administracja i testy obciążeniowe. Baza zawiera skróty scrypt
z osobnymi solami; przechowywane są skróty losowych tokenów sesji, nigdy jawne hasła.
Lokalną bazę chronią uprawnienia konta Windows. Gra nie wywołuje jeszcze tego API.

Każda operacja to POST JSON pod `/v1/<operation>`:

| Operacja | Dane |
|---|---|
| register, login | name, password; wynik: token ważny 24 h; rejestracja zwraca też kod odzyskiwania |
| recover | name, recovery_code, password (nowe); zużywa kod, wydaje nowy i unieważnia sesje oraz pokój |
| logout | pusty obiekt |
| publish-room | name, host (IP), port, profile, capacity (2–8) |
| list-rooms | pusty obiekt |
| delete-room | pusty obiekt; usuwa tylko pokój właściciela |
| relay-ticket | room, role (host/join); jednorazowy bilet ważny 30 s; rolę host otrzymuje tylko właściciel |
| heartbeat-room | room; właściciel odnawia ogłoszenie na 90 s |
| create-invite | room, opcjonalne expires_in (60–86400 s); właściciel otrzymuje losowy kod |
| resolve-invite | code; zwraca metadane istniejącego pokoju |
| revoke-invite | room, code; unieważnia zaproszenie należące do pokoju właściciela |

Poza register/login/recover wymagany nagłówek `Authorization: Bearer <token>`.
Kod odzyskiwania należy pokazać użytkownikowi raz i umożliwić bezpieczne zapisanie.
Nie ma wysyłania e-maili ani odzyskiwania bez kodu. Konta utworzone przed dodaniem
tej funkcji nie mają jeszcze kodu; potrzebują osobnego procesu jego ustanowienia.
Publikacja wygasa po 90 s; gospodarz odnawia ją przez publish-room.
Jedno konto ma jeden ogłaszany pokój. Katalog nie potwierdza dostępności,
liczby graczy ani zgodności zasobów. Nie przenosi pakietów meczu, nie zapewnia
przejścia NAT, relay ani zaproszeń. Pole IP jest ogłoszeniem użytkownika,
serwer nie wykonuje połączeń do wskazanego adresu.

## Przekaźnik istniejącego protokołu TCP

Opcja `--relay-port 8766` uruchamia obok API lokalny przekaźnik `room_relay.py`.
Obsługuje pary kanałów host/join, bilety jednorazowe, limit kanałów odpowiadający
pojemności pokoju, ograniczone bufory, timeout i zamykanie po rozłączeniu.
Nie parsuje ani nie zastępuje reguł `RoomHost`: przekazuje bajty protokołu gry.

`tools/relay_bridge.py` dostarcza most testowy dla istniejącej gry TCP. W trybie
host otwiera kanały wychodzące, po sparowaniu łączy je z pokojem na localhost.
W trybie join wystawia lokalny port TCP, do którego może dołączyć gra.
Token konta odczytuje z `PF_ACCOUNT_TOKEN`, nie z argumentów procesu.
Przykładowa pomoc: `python tools/relay_bridge.py --help`.

Poza literalnym loopback most wymaga HTTPS dla API i weryfikowanego TLS dla
przekaźnika. Lokalny serwer jest przygotowany do umieszczenia za proxy HTTPS/TLS;
nie został wdrożony i nie ma jeszcze konfiguracji konkretnej domeny/certyfikatu.
Most gospodarza odnawia ogłoszenie co 25 s przez heartbeat-room. Wygaśnięcie sesji
lub utrata prawa do pokoju zatrzymuje pracę mostu; nie odtwarza go automatycznie.
To kod i test lokalnego przesyłania danych, nie potwierdzona rozgrywka internetowa.
Menu gry i Android nie uruchamiają jeszcze mostu. Zaproszenia są dostępne w API.
Pokój publikuje się z `private: true`; wtedy inne konta nie widzą go w list-rooms
i muszą podać `invite` w żądaniu biletu join. Kod jest przechowywany jako SHA-256.
Most odczytuje go ze zmiennej `PF_ROOM_INVITE`, bez argumentów procesu i logowania.
Unieważnienie blokuje nowe bilety; już wydany bilet wygasa najpóźniej po 30 s.
Nie jest to funkcja wyrzucania uczestników z aktywnego meczu. Zaproszenie przestaje
działać po wygaśnięciu pokoju nawet wtedy, gdy jego własny termin jeszcze nie minął.
Zmiana schematu bazy dodaje kolumnę private bez kasowania istniejących pokoi.

## Android i zapora

Manifest deklaruje Bluetooth; `requestBluetoothPermissions()` w Activity obsługuje
żądanie systemowe odpowiednie dla wersji Androida. Brakuje jeszcze wywołania z menu,
obsługi odmowy w GUI, transportu oraz połączenia z natywnym protokołem meczu.
Nie należy utożsamiać uprawnień z działającym Bluetooth.

Regułę LAN można przejrzeć bez modyfikacji systemu:

```powershell
./tools/configure_firewall.ps1 -Executable ./engine/out/PolishFighters-Windows-x64-portable/openlf2.exe -WhatIf
```

Właściwe uruchomienie wymaga uprawnień administratora; gra nie podnosi ich sama.
Parametr `-Remove` usuwa tylko dokładnie wskazaną regułę. Skrypt ogranicza ruch
do TCP, wskazanego portu/pliku, profilu Private i LocalSubnet.
Nie otwiera połączeń internetowych ani nie konfiguruje routera.

Podstawy uprawnień: https://developer.android.com/develop/connectivity/bluetooth/bt-permissions
Reguły zapory: https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule
