#!/usr/bin/env bash
# NextGenPresence – start all services locally (non-systemd, for dev/Pi direct use)
# Compatible with bash 3.2+ (macOS default)
# Usage:
#   ./start.sh          – start everything
#   ./start.sh status   – show running services
#   ./start.sh stop     – stop everything
#   ./start.sh logs     – tail all logs
#   ./start.sh restart  – stop then start

set -eu

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"
LOG_DIR="$REPO_DIR/logs"
PID_DIR="$REPO_DIR/.pids"
ENV_FILE="$REPO_DIR/.env"
PYTHON="$VENV_DIR/bin/python3"

# ── Colors ─────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}  v${RESET} $*"; }
warn() { echo -e "${YELLOW}  !${RESET} $*"; }
err()  { echo -e "${RED}  x${RESET} $*"; }
info() { echo -e "${CYAN}  ->${RESET} $*"; }

# ── Service definitions (bash 3.2 compatible — parallel arrays) ────────────────
SERVICE_NAMES=(wifi bluetooth ring mqtt reassess ui)
SERVICE_SCRIPTS=(
    "presence_tracking_stack/wifi_scanner.py"
    "presence_tracking_stack/bt_scanner.py"
    "presence_tracking_stack/ring_logger.py"
    "presence_tracking_stack/presence_mqtt.py"
    "nextgen_ai_reassessment (1)/ai_reassessment.py"
    "nextgen_ai_reassessment (1)/flask_ui.py"
)

script_for() {
    local name="$1"
    local i=0
    for n in "${SERVICE_NAMES[@]}"; do
        if [ "$n" = "$name" ]; then
            echo "${SERVICE_SCRIPTS[$i]}"
            return
        fi
        i=$((i + 1))
    done
}

# ── Helpers ────────────────────────────────────────────────────────────────────
pid_file() { echo "$PID_DIR/$1.pid"; }
log_file() { echo "$LOG_DIR/$1.log"; }

is_running() {
    local pid_f
    pid_f="$(pid_file "$1")"
    [ -f "$pid_f" ] && kill -0 "$(cat "$pid_f")" 2>/dev/null
}

start_service() {
    local name="$1"
    local script="$REPO_DIR/$(script_for "$name")"

    if is_running "$name"; then
        warn "$name already running (PID $(cat "$(pid_file "$name")"))"
        return
    fi

    if [ ! -f "$script" ]; then
        err "$name: script not found: $script"
        return 1
    fi

    mkdir -p "$LOG_DIR" "$PID_DIR"
    local log
    log="$(log_file "$name")"

    # WiFi scanner needs raw socket access
    if [ "$name" = "wifi" ] && [ "$(id -u)" -ne 0 ]; then
        warn "wifi scanner needs root for ARP — running with sudo"
        sudo -E env "PATH=$PATH" "$PYTHON" "$script" >> "$log" 2>&1 &
    else
        env $(grep -v '^#' "$ENV_FILE" | grep '=' | xargs) \
            "$PYTHON" "$script" >> "$log" 2>&1 &
    fi

    echo $! > "$(pid_file "$name")"
    ok "$name started (PID $!, log: logs/$name.log)"
}

stop_service() {
    local name="$1"
    local pid_f
    pid_f="$(pid_file "$name")"

    if ! is_running "$name"; then
        warn "$name is not running"
        rm -f "$pid_f"
        return
    fi

    local pid
    pid="$(cat "$pid_f")"
    kill "$pid" 2>/dev/null && ok "$name stopped (PID $pid)" || err "Failed to stop $name"
    rm -f "$pid_f"
}

# ── Preflight checks ───────────────────────────────────────────────────────────
preflight() {
    echo ""
    echo -e "${BOLD}NextGenPresence – Preflight Checks${RESET}"
    echo "─────────────────────────────────────"
    local all_ok=true

    if [ -x "$PYTHON" ]; then
        ok "Python venv: $VENV_DIR"
    else
        err "venv not found at $VENV_DIR"
        info "Run: python3 -m venv venv && source venv/bin/activate && pip install -r presence_tracking_stack/requirements.txt"
        all_ok=false
    fi

    if [ -f "$ENV_FILE" ]; then
        ok ".env found"
    else
        err ".env missing — copy .env.example to .env"
        all_ok=false
    fi

    if grep -q "your@email.com" "$ENV_FILE" 2>/dev/null; then
        warn "Ring credentials look like placeholders — edit .env"
    fi

    local token_file
    token_file="$(grep 'RING_TOKEN_FILE' "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")"
    token_file="${token_file:-$HOME/.nextgen_ring_token.json}"
    if [ -f "$token_file" ]; then
        ok "Ring token: $token_file"
    else
        warn "No Ring token — run: python3 presence_tracking_stack/ring_auth.py"
    fi

    if nc -z localhost 1883 2>/dev/null; then
        ok "MQTT broker :1883 reachable"
    else
        warn "MQTT broker not running on :1883"
        info "Start: brew services start mosquitto"
    fi

    echo "─────────────────────────────────────"
    $all_ok
}

# ── Commands ───────────────────────────────────────────────────────────────────
cmd_start() {
    echo -e "\n${BOLD}Starting NextGenPresence...${RESET}"
    preflight || { err "Fix the issues above, then retry."; exit 1; }
    echo ""
    for name in "${SERVICE_NAMES[@]}"; do
        start_service "$name"
    done
    echo ""
    info "All services launched. Run './start.sh status' to check."
    info "Tagger UI: http://localhost:5001"
    echo ""
}

cmd_stop() {
    echo -e "\n${BOLD}Stopping NextGenPresence...${RESET}"
    for name in "${SERVICE_NAMES[@]}"; do
        stop_service "$name"
    done
    echo ""
}

cmd_status() {
    echo ""
    echo -e "${BOLD}NextGenPresence Service Status${RESET}"
    echo "─────────────────────────────────────"
    printf "%-15s %-10s %-8s %s\n" "SERVICE" "STATUS" "PID" "LOG"
    echo "─────────────────────────────────────"
    for name in "${SERVICE_NAMES[@]}"; do
        if is_running "$name"; then
            local pid
            pid="$(cat "$(pid_file "$name")")"
            printf "%-15s ${GREEN}%-10s${RESET} %-8s %s\n" "$name" "running" "$pid" "logs/$name.log"
        else
            printf "%-15s ${RED}%-10s${RESET} %-8s\n" "$name" "stopped" "-"
        fi
    done
    echo "─────────────────────────────────────"
    echo ""
}

cmd_logs() {
    echo -e "\n${BOLD}Tailing all logs (Ctrl+C to stop)...${RESET}\n"
    mkdir -p "$LOG_DIR"
    for name in "${SERVICE_NAMES[@]}"; do
        touch "$LOG_DIR/$name.log"
    done
    tail -f "$LOG_DIR"/*.log
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

# ── Dispatch ───────────────────────────────────────────────────────────────────
case "${1:-start}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    status)  cmd_status ;;
    logs)    cmd_logs ;;
    restart) cmd_restart ;;
    *)
        echo "Usage: $0 {start|stop|status|logs|restart}"
        exit 1
        ;;
esac
