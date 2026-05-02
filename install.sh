#!/usr/bin/env bash
# NextGenPresence installer — macOS (brew) and Raspberry Pi / Debian (apt-get)
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"

# ── Detect OS ──────────────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
    Darwin) PLATFORM="macos" ;;
    Linux)  PLATFORM="linux" ;;
    *)      echo "Unsupported OS: $OS"; exit 1 ;;
esac

SERVICE_USER="${SUDO_USER:-$(whoami)}"

echo "=== NextGenPresence Installer ==="
echo "Platform:     $PLATFORM"
echo "Repo:         $REPO_DIR"
echo "Install user: $SERVICE_USER"
echo ""

# ── 1. System packages ────────────────────────────────────────────────────────
echo "[1/6] Installing system packages..."

if [[ "$PLATFORM" == "macos" ]]; then
    if ! command -v brew &>/dev/null; then
        echo "  Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install python3 mosquitto libpcap git curl 2>/dev/null || true
    # Start Mosquitto via brew services
    brew services start mosquitto 2>/dev/null || true
    echo "  MQTT broker: mosquitto started via brew services"
else
    # Raspberry Pi / Debian
    apt-get update -qq
    apt-get install -y -qq \
        python3 python3-pip python3-venv \
        bluetooth bluez \
        libpcap-dev \
        mosquitto mosquitto-clients \
        git curl
    systemctl enable mosquitto
    systemctl start mosquitto
fi

# ── 2. Python virtual environment ─────────────────────────────────────────────
echo "[2/6] Setting up Python virtual environment at $VENV_DIR..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet \
    python-dotenv \
    ring_doorbell \
    "paho-mqtt<2" \
    scapy \
    flask
echo "  Python deps installed."

# ── 3. .env file ──────────────────────────────────────────────────────────────
echo "[3/6] Setting up .env..."
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo ""
    echo "  Created .env — edit it now before continuing:"
    echo "    nano $REPO_DIR/.env"
    echo ""
else
    echo "  .env already exists, skipping."
fi

# ── 4. Ring authentication ────────────────────────────────────────────────────
echo "[4/6] Ring API authentication..."
echo ""
echo "  Run this once to authenticate (handles 2FA):"
echo "    source $VENV_DIR/bin/activate"
echo "    python3 $REPO_DIR/presence_tracking_stack/ring_auth.py"
echo ""

# ── 5. Service setup ──────────────────────────────────────────────────────────
echo "[5/6] Setting up services..."

PYTHON="$VENV_DIR/bin/python3"

if [[ "$PLATFORM" == "macos" ]]; then
    # macOS: use start.sh (launchd not set up here — use start.sh for dev)
    echo "  macOS detected — using start.sh instead of systemd."
    echo "  Run './start.sh' to launch all services."
else
    # Linux / Raspberry Pi: install systemd units
    install_service() {
        local name="$1" script="$2" desc="$3"
        cat > "/etc/systemd/system/${name}.service" <<EOF
[Unit]
Description=${desc}
After=network.target mosquitto.service

[Service]
User=${SERVICE_USER}
WorkingDirectory=${REPO_DIR}
EnvironmentFile=${REPO_DIR}/.env
ExecStart=${PYTHON} ${script}
Restart=on-failure
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload
        systemctl enable "${name}.service"
        echo "  Installed: ${name}.service"
    }

    install_service nextgen-wifi    "$REPO_DIR/presence_tracking_stack/wifi_scanner.py"               "NextGen WiFi Presence Scanner"
    install_service nextgen-bt      "$REPO_DIR/presence_tracking_stack/bt_scanner.py"                 "NextGen Bluetooth Presence Scanner"
    install_service nextgen-ring    "$REPO_DIR/presence_tracking_stack/ring_logger.py"                "NextGen Ring Camera Logger"
    install_service nextgen-mqtt    "$REPO_DIR/presence_tracking_stack/presence_mqtt.py"              "NextGen MQTT Presence Publisher"
    install_service nextgen-reassess "$REPO_DIR/nextgen_ai_reassessment (1)/ai_reassessment.py"       "NextGen AI Reassessment Engine"
    install_service nextgen-ui      "$REPO_DIR/nextgen_ai_reassessment (1)/flask_ui.py"               "NextGen Device Tagger UI"
fi

# ── 6. Done ───────────────────────────────────────────────────────────────────
echo ""
echo "[6/6] Done!"
echo ""
if [[ "$PLATFORM" == "macos" ]]; then
    echo "Next steps:"
    echo "  1. Edit .env:      nano $REPO_DIR/.env"
    echo "  2. Auth Ring:      python3 $REPO_DIR/presence_tracking_stack/ring_auth.py"
    echo "  3. Start services: cd $REPO_DIR && ./start.sh"
    echo "  4. View logs:      ./start.sh logs"
    echo "  5. Tagger UI:      http://localhost:5001"
else
    echo "Next steps:"
    echo "  1. Edit .env:      nano $REPO_DIR/.env"
    echo "  2. Auth Ring:      python3 $REPO_DIR/presence_tracking_stack/ring_auth.py"
    echo "  3. Start services: sudo systemctl start nextgen-wifi nextgen-bt nextgen-ring nextgen-mqtt nextgen-reassess nextgen-ui"
    echo "  4. View logs:      journalctl -u nextgen-ui -f"
    echo "  5. Tagger UI:      http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo localhost):5001"
fi
echo ""
