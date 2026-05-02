"""
Reads real Ring events from the unified DB.
Returns events as dicts with a float 'timestamp' (epoch seconds).
"""
import sys, time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn

def get_recent_ring_events(minutes=30):
    conn = get_conn()
    cutoff = time.time() - (minutes * 60)
    rows = conn.execute(
        "SELECT timestamp, kind, device FROM ring_events ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()

    events = []
    for ts_str, kind, device in rows:
        try:
            # Handle both ISO strings and numeric timestamps
            if isinstance(ts_str, (int, float)):
                epoch = float(ts_str)
            else:
                dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                epoch = dt.timestamp()
            if epoch >= cutoff:
                events.append({"timestamp": epoch, "kind": kind, "camera": device})
        except (ValueError, TypeError):
            continue
    return events
