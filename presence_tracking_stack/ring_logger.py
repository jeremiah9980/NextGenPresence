import sys, os, time, json
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from db import get_conn

TOKEN_FILE = Path(os.getenv("RING_TOKEN_FILE", str(Path.home() / ".nextgen_ring_token.json")))
POLL_INTERVAL = int(os.getenv("RING_POLL_SECONDS", "30"))

def token_updated(token):
    TOKEN_FILE.write_text(json.dumps(token))

def get_ring():
    from ring_doorbell import Auth, Ring
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"No Ring token at {TOKEN_FILE}. Run ring_auth.py first."
        )
    token = json.loads(TOKEN_FILE.read_text())
    auth = Auth("NextGenPresence/1.0", token, token_updated)
    ring = Ring(auth)
    ring.update_data()
    return ring

def log_events(ring, conn):
    inserted = 0
    for cam in ring.video_devices():
        for event in cam.history(limit=10):
            ts   = str(event.get("created_at", ""))
            kind = event.get("kind", "")
            desc = event.get("description", "")
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO ring_events
                       (timestamp, kind, description, device)
                       VALUES (?, ?, ?, ?)""",
                    (ts, kind, desc, cam.name),
                )
                inserted += conn.execute("SELECT changes()").fetchone()[0]
            except Exception:
                pass
    conn.commit()
    return inserted

if __name__ == "__main__":
    conn = get_conn()
    ring = get_ring()
    print(f"Ring logger started — polling every {POLL_INTERVAL}s")
    while True:
        try:
            n = log_events(ring, conn)
            print(f"[ring] {time.strftime('%Y-%m-%d %H:%M:%S')}: +{n} new event(s)")
        except Exception as e:
            print(f"[ring] error: {e}")
        time.sleep(POLL_INTERVAL)
