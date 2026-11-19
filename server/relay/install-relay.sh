#!/usr/bin/env bash
# Installs the Polish Fighters match relay on a fresh Ubuntu server (e.g. Oracle Cloud
# Always Free). Run as root:
#   curl -fsSL https://raw.githubusercontent.com/w4sy1/polish-fighters/main/server/relay/install-relay.sh \
#     | sudo bash -s -- https://www.projektocalenie.pl/projekty/polish-fighters/api
# Re-running it updates the relay and keeps the existing key.
set -euo pipefail

API="${1:?Usage: install-relay.sh <account API URL> [port]}"
PORT="${2:-8766}"
SOURCE="${PF_RELAY_SOURCE:-https://raw.githubusercontent.com/w4sy1/polish-fighters/main/tools/room_relay.py}"
case "$API" in https://*) ;; *) echo "The account API must use https://" >&2; exit 1 ;; esac
case "$PORT" in ''|*[!0-9]*) echo "Port must be a number" >&2; exit 1 ;; esac

# On a first boot (cloud-init) unattended upgrades may still hold the package lock.
apt-get -o DPkg::Lock::Timeout=900 update -qq
DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=900 install -y -qq python3 curl ca-certificates iptables-persistent >/dev/null

id pfrelay >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin pfrelay
install -d -m 755 /opt/polish-fighters-relay
curl -fsSL "$SOURCE" -o /opt/polish-fighters-relay/room_relay.py.new
python3 -m py_compile /opt/polish-fighters-relay/room_relay.py.new
mv /opt/polish-fighters-relay/room_relay.py.new /opt/polish-fighters-relay/room_relay.py
rm -rf /opt/polish-fighters-relay/__pycache__

install -d -m 750 -o root -g pfrelay /etc/polish-fighters
# A key may be provided up front, e.g. by an Oracle "initialization script".
if [ -n "${PF_RELAY_KEY:-}" ]; then
  printf '%s
' "$PF_RELAY_KEY" > /etc/polish-fighters/relay.key
fi
if [ ! -s /etc/polish-fighters/relay.key ]; then
  python3 -c 'import secrets; print(secrets.token_urlsafe(36))' > /etc/polish-fighters/relay.key
fi
chown root:pfrelay /etc/polish-fighters/relay.key
chmod 640 /etc/polish-fighters/relay.key

cat > /etc/systemd/system/polish-fighters-relay.service <<UNIT
[Unit]
Description=Polish Fighters match relay
After=network-online.target
Wants=network-online.target

[Service]
User=pfrelay
ExecStart=/usr/bin/python3 /opt/polish-fighters-relay/room_relay.py --api ${API} --key-file /etc/polish-fighters/relay.key --port ${PORT}
Restart=always
RestartSec=3
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT

# Oracle Ubuntu images reject new inbound connections in iptables except SSH.
if ! iptables -C INPUT -p tcp --dport "$PORT" -m state --state NEW -j ACCEPT 2>/dev/null; then
  iptables -I INPUT 1 -p tcp --dport "$PORT" -m state --state NEW -j ACCEPT
  netfilter-persistent save >/dev/null
fi

systemctl daemon-reload
systemctl enable --now polish-fighters-relay >/dev/null
systemctl restart polish-fighters-relay
sleep 2
systemctl is-active --quiet polish-fighters-relay || { journalctl -u polish-fighters-relay -n 20 --no-pager; exit 1; }

PUBLIC_IP="$(curl -4 -fsS --max-time 10 https://api.ipify.org || echo 'PUBLICZNY_ADRES_IP')"
echo
echo "Przekaźnik działa na porcie ${PORT}."
echo "W konsoli Oracle otwórz jeszcze port TCP ${PORT} (Security List sieci VCN), jeśli tego nie zrobiłeś."
echo
echo "Zapisz ten plik jako relay_config.py obok passenger_wsgi.py na swoim hostingu:"
echo "----------------------------------------------------------------"
echo "RELAY_HOST = \"${PUBLIC_IP}\""
echo "RELAY_PORT = ${PORT}"
echo "RELAY_KEY = \"$(cat /etc/polish-fighters/relay.key)\""
echo "----------------------------------------------------------------"
echo "Klucz jest tajny: nie wklejaj go publicznie."
