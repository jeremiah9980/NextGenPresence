import os, sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

DB_PATH = os.getenv("NEXTGEN_DB", str(Path.home() / "nextgen.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS wifi_presence (
    id        INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    mac       TEXT NOT NULL,
    ip        TEXT
);

CREATE TABLE IF NOT EXISTS bt_presence (
    id        INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    mac       TEXT NOT NULL,
    name      TEXT
);

CREATE TABLE IF NOT EXISTS ring_events (
    id          INTEGER PRIMARY KEY,
    timestamp   TEXT NOT NULL,
    kind        TEXT,
    description TEXT,
    device      TEXT,
    UNIQUE(timestamp, device, kind)
);

CREATE TABLE IF NOT EXISTS device_log (
    id            INTEGER PRIMARY KEY,
    mac           TEXT NOT NULL UNIQUE,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    friendly_name TEXT,
    source        TEXT,
    confidence    INTEGER DEFAULT 0
);
"""

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(_SCHEMA)
    return conn
