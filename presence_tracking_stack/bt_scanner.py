import sys, time, subprocess, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn

_MAC_RE = re.compile(r"([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})")

def _bluetoothctl_scan(timeout=8):
    """Return list of (mac, name) discovered via bluetoothctl."""
    try:
        subprocess.run(["bluetoothctl", "power", "on"], capture_output=True, timeout=5)
        subprocess.run(["bluetoothctl", "scan", "on"], capture_output=True, timeout=2)
        time.sleep(timeout)
        out = subprocess.check_output(
            ["bluetoothctl", "devices"], text=True, timeout=5
        )
        subprocess.run(["bluetoothctl", "scan", "off"], capture_output=True, timeout=2)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    results = []
    for line in out.splitlines():
        # Format: "Device AA:BB:CC:DD:EE:FF DeviceName"
        m = _MAC_RE.search(line)
        if m:
            mac = m.group(1)
            name = line.split(mac, 1)[-1].strip() or "unknown"
            results.append((mac, name))
    return results

def scan(conn):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    devices = _bluetoothctl_scan()
    for mac, name in devices:
        conn.execute(
            "INSERT INTO bt_presence (timestamp, mac, name) VALUES (?, ?, ?)",
            (now, mac, name),
        )
        conn.execute(
            """INSERT INTO device_log (mac, first_seen, last_seen, source)
               VALUES (?, ?, ?, 'bluetooth')
               ON CONFLICT(mac) DO UPDATE SET last_seen=excluded.last_seen""",
            (mac, now, now),
        )
    conn.commit()
    print(f"[bt] {now}: found {len(devices)} device(s)")

if __name__ == "__main__":
    conn = get_conn()
    print("Bluetooth scanner started (using bluetoothctl)")
    while True:
        try:
            scan(conn)
        except Exception as e:
            print(f"[bt] error: {e}")
        time.sleep(90)
