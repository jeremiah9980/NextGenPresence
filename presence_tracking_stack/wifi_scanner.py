from scapy.all import ARP, Ether, srp
import sqlite3, time

conn = sqlite3.connect("event_sync.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS wifi_presence (id INTEGER PRIMARY KEY, timestamp TEXT, mac TEXT, ip TEXT)")
conn.commit()

def scan():
    arp = ARP(pdst="192.168.1.1/24")
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    ans = srp(ether/arp, timeout=2, verbose=0)[0]
    for s, r in ans:
        cursor.execute("INSERT INTO wifi_presence (timestamp, mac, ip) VALUES (?, ?, ?)",
                       (time.strftime('%Y-%m-%d %H:%M:%S'), r.hwsrc, r.psrc))
        conn.commit()

while True:
    scan()
    time.sleep(60)
