import sqlite3, time, json
from datetime import datetime
from ring_event_sync import get_recent_ring_events

def reassess():
    conn = sqlite3.connect("devices.db")
    cursor = conn.cursor()

    # Get unconfirmed device entries
    cursor.execute("SELECT mac, timestamp FROM device_log WHERE friendly_name IS NULL")
    device_logs = cursor.fetchall()

    # Pull last 30 min of Ring events
    recent_events = get_recent_ring_events(minutes=30)

    for mac, ts in device_logs:
        for event in recent_events:
            if abs(event["timestamp"] - ts) < 120:  # within 2 min of motion
                cursor.execute("UPDATE device_log SET confidence = confidence + 1 WHERE mac = ?", (mac,))
                print(f"Boosted confidence for {mac}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    while True:
        reassess()
        print(f"AI reassessment ran at {datetime.now()}")
        time.sleep(1800)  # wait 30 mins
