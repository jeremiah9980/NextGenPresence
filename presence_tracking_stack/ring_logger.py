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

def _is_auth_error(exc):
    """Best-effort detection of an expired/invalid Ring auth token."""
    try:
        from ring_doorbell.exceptions import AuthenticationError
        if isinstance(exc, AuthenticationError):
            return True
    except ImportError:
        pass
    msg = str(exc).lower()
    return "401" in msg or "unauthorized" in msg or "auth" in msg and "token" in msg

def refresh_or_exit(auth, exc):
    """Try to refresh the Ring auth token; if that's not possible, exit with
    a clear, actionable message instead of crashing with a raw traceback."""
    print(f"[ring] warning: auth token appears to be expired/invalid ({exc})")
    refresh_token = getattr(auth, "refresh_token", None)
    if callable(refresh_token):
        try:
            refresh_token()
            print("[ring] token refreshed successfully, resuming polling")
            return True
        except Exception as refresh_exc:
            print(f"[ring] warning: token refresh failed ({refresh_exc})")
    print(
        "[ring] Ring authentication has expired and could not be refreshed.\n"
        "       Re-run the auth flow to fix this:\n"
        f"           python3 {Path(__file__).resolve().parent / 'ring_auth.py'}\n"
        "       Exiting so the failure isn't silent."
    )
    sys.exit(1)

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
            if _is_auth_error(e):
                refresh_or_exit(ring.auth, e)
                # If we get here, the token was refreshed — re-fetch ring data
                # before the next poll so we use the new credentials.
                try:
                    ring.update_data()
                except Exception as refresh_update_exc:
                    print(f"[ring] error: still failing after refresh: {refresh_update_exc}")
            else:
                print(f"[ring] error: {e}")
        time.sleep(POLL_INTERVAL)
