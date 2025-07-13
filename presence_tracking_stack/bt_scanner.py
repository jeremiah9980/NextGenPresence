import os, sqlite3, time

conn = sqlite3.connect("event_sync.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS bt_presence (id INTEGER PRIMARY KEY, timestamp TEXT, mac TEXT, name TEXT)")
conn.commit()

def scan():
    out = os.popen("hcitool scan").read().splitlines()[1:]
    for line in out:
        mac, name = line.strip().split("\t")
        cursor.execute("INSERT INTO bt_presence (timestamp, mac, name) VALUES (?, ?, ?)",
                       (time.strftime('%Y-%m-%d %H:%M:%S'), mac, name))
        conn.commit()

while True:
    scan()
    time.sleep(90)
