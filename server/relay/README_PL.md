# Gra przez internet przez własny serwer (za darmo)

Gracze łączą się wyłącznie z Twoim serwerem. Nikt nie podaje adresu IP i nie
przekierowuje portów na routerze.

```
Gracz A ──┐                          ┌── Gracz B
          ├─► przekaźnik (Oracle) ◄──┤
          │   sprawdza bilety przez  │
          └─► API kont (Domenomania) ◄┘
```

- **API kont i pokoi** zostaje na Domenomanii (`/projekty/polish-fighters/api`).
  Wydaje jednorazowe bilety i podaje grze adres przekaźnika.
- **Przekaźnik meczu** działa na darmowym serwerze Oracle Cloud „Always Free”.
  Hosting z WordPressem nie utrzyma stałego połączenia przez cały mecz, dlatego
  przekaźnik musi stać osobno.
- **Gra** od wersji z protokołem 2 wysyła ruchy z kilkuklatkowym wyprzedzeniem
  (6 klatek przez internet, 2 w LAN), więc ping do około 200 ms nie spowalnia meczu.

## 1. Serwer Oracle (raz)

1. Załóż konto na https://www.oracle.com/cloud/free/ (wymaga weryfikacji kartą,
   konto „Always Free” nic nie pobiera).
2. Utwórz instancję *Compute*: obraz **Ubuntu**, kształt z oznaczeniem
   *Always Free-eligible*. Zapisz klucz SSH.
3. W sieci instancji (VCN → Security List → Ingress Rules) dodaj regułę:
   źródło `0.0.0.0/0`, protokół TCP, port docelowy `8766`.
4. Połącz się z serwerem (SSH albo Cloud Shell) i wklej:

```sh
curl -fsSL https://raw.githubusercontent.com/w4sy1/polish-fighters/main/server/relay/install-relay.sh | sudo bash -s -- https://www.projektocalenie.pl/projekty/polish-fighters/api
```

Skrypt instaluje przekaźnik jako usługę systemową, otwiera port w zaporze
serwera i wypisuje gotową zawartość pliku `relay_config.py`.

## 2. Hosting Domenomania (raz)

W menedżerze plików, w folderze aplikacji API (tam, gdzie `passenger_wsgi.py`):

1. Podmień `account_service.py` na wersję z `tools/account_service.py`.
2. Podmień `passenger_wsgi.py` na wersję z `server/passenger_wsgi.py`.
3. Utwórz `relay_config.py` z tekstem wypisanym przez skrypt z kroku 1.
4. Uruchom ponownie aplikację Python w panelu (albo dotknij `tmp/restart.txt`).

`relay_config.py` zawiera tajny klucz. Leży obok `passenger_wsgi.py`, więc nie
jest dostępny z przeglądarki. Nie publikuj go w repozytorium.

## 3. W grze

„Graj przez internet” ma już wpisany adres Twojego serwera. Gracz loguje się,
gospodarz klika **OPUBLIKUJ I HOSTUJ**, a pozostali wybierają pokój z listy.
Pokój przez serwer oznaczony jest tekstem „GRA PRZEZ SERWER”.

## Sprawdzenie

```sh
sudo systemctl status polish-fighters-relay
sudo journalctl -u polish-fighters-relay -n 50
```

Obie wersje gry muszą mieć protokół 2. Starsza wersja dostanie komunikat
„network protocol version mismatch; update the game on every device”.

## Ograniczenia

- Przekaźnik przesyła dane meczu bez szyfrowania (bilety są jednorazowe i ważne
  30 s; hasła i tokeny kont idą tylko przez HTTPS do API).
- Mecz bez przerw jest ograniczony pingiem: powyżej ~200 ms (np. Europa–Azja)
  gra będzie czekać na ruchy. Wtedy pomoże większe opóźnienie wejścia.
- Darmowy serwer Oracle obsłuży kilkadziesiąt równoczesnych meczów.
