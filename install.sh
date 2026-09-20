#!/usr/bin/env bash
# Installs the redactor as a background service.
# Run with:  sudo bash install.sh
set -euo pipefail

PORT="${REDACTOR_PORT:-8765}"
DIR=/opt/redactor
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "== Redactor installer =="

if [[ $EUID -ne 0 ]]; then
  echo "STOP: run this with sudo, like:  sudo bash install.sh"; exit 1
fi
if [[ ! -f "$HERE/app.py" ]]; then
  echo "STOP: app.py is not in this folder ($HERE)."
  echo "Put app.py and install.sh in the same folder, then try again."; exit 1
fi
if command -v transactional-update >/dev/null 2>&1; then
  echo "STOP: this looks like an immutable system (MicroOS / Aeon / Leap Micro)."
  echo "Packages cannot be installed the normal way here. Use the Docker route instead."
  exit 1
fi
if ! command -v systemctl >/dev/null 2>&1; then
  echo "STOP: this machine does not use systemd, so the service step will not work."
  echo "You can still run it by hand. See step 9 of the instructions."; exit 1
fi

# --- 1. system packages -------------------------------------------------
echo "[1/6] Installing system packages..."
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq python3-venv python3-dev build-essential curl >/dev/null
elif command -v zypper >/dev/null 2>&1; then
  zypper --non-interactive --quiet install \
    python3-devel python3-pip gcc gcc-c++ make curl >/dev/null
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y python3-devel python3-pip gcc gcc-c++ make curl >/dev/null
else
  echo "STOP: could not find apt, zypper or dnf. Install Python 3 plus a compiler by hand."; exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "STOP: Python's venv tool is missing. Install it, then run this again."
  exit 1
fi

# --- 2. service user ----------------------------------------------------
echo "[2/6] Creating the service user..."
NOLOGIN=/usr/sbin/nologin
[[ -x "$NOLOGIN" ]] || NOLOGIN=/sbin/nologin
[[ -x "$NOLOGIN" ]] || NOLOGIN=/bin/false
id redactor &>/dev/null || useradd --system --no-create-home --shell "$NOLOGIN" redactor

# --- 3. python packages -------------------------------------------------
echo "[3/6] Installing Python packages. On a slow machine this takes 10-25 minutes..."
mkdir -p "$DIR"
install -m 644 "$HERE/app.py" "$DIR/app.py"
python3 -m venv "$DIR/venv"
"$DIR/venv/bin/pip" install -q --upgrade pip setuptools wheel
"$DIR/venv/bin/pip" install -q \
  flask waitress "spacy>=3.8,<3.9" presidio-analyzer presidio-anonymizer \
  python-docx pypdf reportlab pymupdf

# --- 4. language model --------------------------------------------------
RAM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
echo "[4/6] This machine has ${RAM_MB} MB of memory."
if [[ "$RAM_MB" -ge 3000 ]]; then
  MODEL=en_core_web_lg
  URL=https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl
else
  MODEL=en_core_web_sm
  URL=https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
fi
echo "      Installing the ${MODEL} language model..."
if ! "$DIR/venv/bin/pip" install -q "$URL"; then
  echo "      Download failed. Trying the smaller model instead..."
  MODEL=en_core_web_sm
  "$DIR/venv/bin/pip" install -q \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
fi
chown -R root:root "$DIR"

# --- 5. service ---------------------------------------------------------
echo "[5/6] Setting up the background service..."
cat > /etc/systemd/system/redactor.service <<EOF
[Unit]
Description=Redactor (keeps no logs)
After=network-online.target
Wants=network-online.target

[Service]
User=redactor
Group=redactor
Environment=REDACTOR_PORT=$PORT
Environment=REDACTOR_MODEL=$MODEL
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=TMPDIR=/tmp
ExecStart=$DIR/venv/bin/python $DIR/app.py
Restart=on-failure
TimeoutStartSec=180

# Nothing reaches the system log
StandardOutput=null
StandardError=null
SyslogLevel=emerg
LogLevelMax=0

# Read-only system; /tmp lives in memory
ProtectSystem=strict
ProtectHome=yes
TemporaryFileSystem=/tmp:mode=1777
PrivateDevices=yes
NoNewPrivileges=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now redactor.service

# --- 5b. firewall -------------------------------------------------------
if command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state >/dev/null 2>&1; then
  echo "      Opening port $PORT in firewalld..."
  firewall-cmd --permanent --add-port="$PORT/tcp" >/dev/null 2>&1 || true
  firewall-cmd --reload >/dev/null 2>&1 || true
elif command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
  echo "      Opening port $PORT in ufw..."
  ufw allow "$PORT/tcp" >/dev/null 2>&1 || true
fi

# --- 6. check -----------------------------------------------------------
echo "[6/6] Waiting for it to start..."
for _ in $(seq 1 30); do
  sleep 2
  if curl -fsS -o /dev/null --max-time 3 "http://127.0.0.1:$PORT/" 2>/dev/null; then
    echo
    echo "DONE. Open this on any device on your own network:"
    echo "   http://$(hostname -I 2>/dev/null | awk '{print $1}'):$PORT"
    echo "Language model in use: $MODEL"
    exit 0
  fi
done

echo
echo "It installed but did not answer on port $PORT."
echo "Run this to see why:   sudo systemctl status redactor --no-pager"
exit 1
