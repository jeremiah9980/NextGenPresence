import sys, time, json, os
from pathlib import Path
import paho.mqtt.client as mqtt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import get_conn

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

client = mqtt.Client()
client.connect(MQTT_HOST, MQTT_PORT)

def push_latest(conn, table, topic):
    cur = conn.execute(f"SELECT * FROM {table} ORDER BY timestamp DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        cols = [d[0] for d in cur.description]
        payload = json.dumps(dict(zip(cols, row)))
        client.publish(f"presence/{topic}", payload)

if __name__ == "__main__":
    conn = get_conn()
    print(f"MQTT publisher started → {MQTT_HOST}:{MQTT_PORT}")
    while True:
        try:
            push_latest(conn, "wifi_presence", "wifi")
            push_latest(conn, "bt_presence", "bluetooth")
            push_latest(conn, "ring_events", "ring")
        except Exception as e:
            print(f"[mqtt] error: {e}")
        time.sleep(30)
