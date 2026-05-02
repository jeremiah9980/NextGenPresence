"""
Run this once on initial setup to authenticate with Ring and save a token.
Handles 2FA automatically.

Usage:
    python3 ring_auth.py
"""
import sys, json, getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TOKEN_FILE = Path.home() / ".nextgen_ring_token.json"

def token_updated(token):
    TOKEN_FILE.write_text(json.dumps(token))

def authenticate():
    try:
        from ring_doorbell import Auth
        from ring_doorbell.exceptions import Requires2FAError
    except ImportError:
        print("Install ring_doorbell: pip install ring_doorbell")
        sys.exit(1)

    username = input("Ring account email: ").strip()
    password = getpass.getpass("Ring account password: ")

    auth = Auth("NextGenPresence/1.0", None, token_updated)
    try:
        auth.fetch_token(username, password)
    except Requires2FAError:
        otp = input("2FA code (check your email/phone): ").strip()
        auth.fetch_token(username, password, otp)

    # Verify by loading ring
    from ring_doorbell import Ring
    ring = Ring(auth)
    ring.update_data()

    cams = ring.video_devices()
    print(f"\nAuthenticated successfully. Token saved to {TOKEN_FILE}")
    print(f"Found {len(cams)} camera(s):")
    for cam in cams:
        print(f"  - {cam.name} ({cam.kind})")

if __name__ == "__main__":
    authenticate()
