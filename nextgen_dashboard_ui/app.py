import sys, os
from pathlib import Path
from flask import Flask, render_template, jsonify
from datetime import datetime
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from db import get_conn

app = Flask(__name__)

HOME_PRESENT_MINUTES = int(os.getenv("HOME_PRESENT_MINUTES", "10"))
HOME_LAT  = float(os.getenv("HOME_LAT",  "44.9778"))
HOME_LON  = float(os.getenv("HOME_LON", "-93.2650"))
HOME_NAME = os.getenv("HOME_NAME", "Home")


def _since(ts_str):
    """Return elapsed seconds since a 'YYYY-MM-DD HH:MM:SS' timestamp."""
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - dt).total_seconds()
    except Exception:
        return None


def _fmt_duration(seconds):
    if seconds is None:
        return "unknown"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        h, m = divmod(seconds // 60, 60)
        return f"{h}h {m}m ago"
    return f"{seconds // 86400}d ago"


@app.route("/")
def dashboard():
    return render_template("dashboard.html",
                           home_lat=HOME_LAT,
                           home_lon=HOME_LON,
                           home_name=HOME_NAME)


@app.route("/api/presence")
def api_presence():
    conn = get_conn()
    rows = conn.execute(
        "SELECT mac, first_seen, last_seen, friendly_name, source, confidence "
        "FROM device_log ORDER BY last_seen DESC"
    ).fetchall()
    conn.close()

    devices = []
    for mac, first_seen, last_seen, name, source, confidence in rows:
        elapsed = _since(last_seen)
        home = elapsed is not None and elapsed < (HOME_PRESENT_MINUTES * 60)
        devices.append({
            "mac":        mac,
            "name":       name or mac,
            "tagged":     name is not None,
            "source":     source or "unknown",
            "confidence": confidence or 0,
            "last_seen":  last_seen,
            "first_seen": first_seen,
            "elapsed_s":  int(elapsed) if elapsed is not None else None,
            "duration":   _fmt_duration(elapsed),
            "home":       home,
            "status":     "home" if home else "away",
        })

    home_count = sum(1 for d in devices if d["home"])
    return jsonify({
        "devices": devices,
        "summary": {
            "total":   len(devices),
            "home":    home_count,
            "away":    len(devices) - home_count,
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    })


@app.route("/api/ring")
def api_ring():
    conn = get_conn()
    rows = conn.execute(
        "SELECT timestamp, kind, description, device "
        "FROM ring_events ORDER BY timestamp DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return jsonify({
        "events": [
            {"timestamp": ts, "kind": kind, "description": desc or "", "device": device}
            for ts, kind, desc, device in rows
        ]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
