import os, time, sqlite3
from ring_doorbell import Ring
from dotenv import load_dotenv

load_dotenv()
conn = sqlite3.connect("event_sync.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS ring_events (id INTEGER PRIMARY KEY, timestamp TEXT, kind TEXT, description TEXT, device TEXT)")
conn.commit()

ring = Ring(username=os.getenv("RING_USERNAME"), password=os.getenv("RING_PASSWORD"))
devices = ring.devices()

def log_events():
    for cam in devices['doorbots']:
        for e in cam.history(limit=5):
            ts, kind, desc = e['created_at'], e['kind'], e['description']
            cursor.execute("SELECT 1 FROM ring_events WHERE timestamp=? AND kind=?", (ts, kind))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO ring_events (timestamp, kind, description, device) VALUES (?, ?, ?, ?)",
                               (ts, kind, desc, cam.name))
                conn.commit()

while True:
    log_events()
    time.sleep(30)
