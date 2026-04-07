import sys, time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn
from ring_event_sync import get_recent_ring_events

INTERVAL = 1800  # 30 minutes
CORRELATION_WINDOW = 120  # seconds

def reassess():
    conn = get_conn()

    untagged = conn.execute(
        "SELECT mac, last_seen FROM device_log WHERE friendly_name IS NULL"
    ).fetchall()

    ring_events = get_recent_ring_events(minutes=30)

    boosted = 0
    for mac, last_seen_str in untagged:
        try:
            device_epoch = time.mktime(time.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S"))
        except (ValueError, TypeError):
            continue
        for event in ring_events:
            if abs(event["timestamp"] - device_epoch) < CORRELATION_WINDOW:
                conn.execute(
                    "UPDATE device_log SET confidence = confidence + 1 WHERE mac = ?",
                    (mac,),
                )
                boosted += 1
                break

    conn.commit()
    conn.close()
    print(f"[reassess] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: "
          f"checked {len(untagged)} untagged device(s), boosted {boosted}")

if __name__ == "__main__":
    print(f"AI reassessment running every {INTERVAL // 60} minutes")
    while True:
        try:
            reassess()
        except Exception as e:
            print(f"[reassess] error: {e}")
        time.sleep(INTERVAL)
