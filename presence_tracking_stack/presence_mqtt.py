import sqlite3, time, json
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("localhost", 1883)

def push(table):
    conn = sqlite3.connect("event_sync.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        payload = json.dumps(dict(zip([c[0] for c in cursor.description], row)))
        client.publish(f"presence/{table}", payload)

while True:
    push("wifi_presence")
    push("bt_presence")
    time.sleep(30)
