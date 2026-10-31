# Konta i katalog pokoi

Nie potrzebujesz serwera do gry lokalnej ani LAN. Nowy klient kont jest sprawdzony
z serwerem lokalnym. Publiczna usługa nie została wdrożona.

## Uruchomienie lokalne na Windows

Z katalogu projektu, z zainstalowanym Pythonem 3.11 lub nowszym:

```powershell
& ./server/Start-LocalServer.ps1
```

W środowisku deweloperskim projektu można wskazać istniejący interpreter:

```powershell
& ./server/Start-LocalServer.ps1 -Python ./.build-venv/Scripts/python.exe
```

W grze wybierz konta/pokoje i adres `http://127.0.0.1:8765`. Utwórz konto.
Zachowaj wyświetlony kod odzyskiwania. Hasło i token sesji nie trafiają do
ustawień gry. SQLite w `userdata/server/accounts.sqlite` zawiera konta i skróty
danych uwierzytelniających: zachowaj bazę przy aktualizacji, nie publikuj jej.
Ctrl+C zatrzymuje proces; ponowne uruchomienie używa tej samej bazy.

## Późniejsze hostowanie

Pakiet kodu Android Studio zawiera również cały kod serwera Python bez dodatkowych
zależności pip. Na wybranym serwerze można uruchomić:

```sh
python3 tools/account_service.py --database /var/lib/polish-fighters/accounts.sqlite --port 8765
```

Folder bazy trzeba wcześniej utworzyć i nadać zapis użytkownikowi usługi.
Serwer nasłuchuje wyłącznie na loopback. Publiczny dostęp wymaga domeny,
certyfikatu HTTPS i reverse proxy do `127.0.0.1:8765`, z limitami żądań,
timeoutami, kopią bazy i nadzorem procesu. Klient przyjmuje zdalnie tylko HTTPS.
Nie ma tu skonfigurowanego dostawcy hostingu ani automatycznego wdrożenia.

Katalog pokoi publikuje adres gospodarza; sama publikacja nie otwiera portu
na routerze. Gra łączy się obecnie bezpośrednio po TCP/IPv4, więc gospodarz musi
być osiągalny dla drugiego komputera. Istniejący eksperymentalny relay
`tools/room_relay.py` ma osobne testy, ale nie jest podłączony do nowego GUI gry.
Nie deklarujemy jeszcze działania przez NAT, publiczny Internet ani Bluetooth.
Mieszana pula modów jest na razie ograniczona w GUI do gry lokalnej.
