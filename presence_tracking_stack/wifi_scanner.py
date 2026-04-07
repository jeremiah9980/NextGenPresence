import sys, time
from pathlib import Path
from scapy.all import ARP, Ether, srp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn

SUBNET = __import__("os").getenv("WIFI_SUBNET", "172.16.207.0/24")

def scan(conn):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    arp = ARP(pdst=SUBNET)
    ans = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / arp, timeout=2, verbose=0)[0]
    for _, r in ans:
        mac, ip = r.hwsrc, r.psrc
        conn.execute(
            "INSERT INTO wifi_presence (timestamp, mac, ip) VALUES (?, ?, ?)",
            (now, mac, ip),
        )
        conn.execute(
            """INSERT INTO device_log (mac, first_seen, last_seen, source)
               VALUES (?, ?, ?, 'wifi')
               ON CONFLICT(mac) DO UPDATE SET last_seen=excluded.last_seen""",
            (mac, now, now),
        )
    conn.commit()
    print(f"[wifi] {now}: found {len(ans)} device(s)")

if __name__ == "__main__":
    conn = get_conn()
    print(f"WiFi scanner started (subnet: {SUBNET})")
    while True:
        try:
            scan(conn)
        except Exception as e:
            print(f"[wifi] error: {e}")
        time.sleep(60)
