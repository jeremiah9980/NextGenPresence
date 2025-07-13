
import paho.mqtt.client as mqtt
from flask import Flask, jsonify
from threading import Thread
import time

app = Flask(__name__)
latest_events = []

def on_connect(client, userdata, flags, rc):
    client.subscribe("presence/events")

def on_message(client, userdata, msg):
    event = msg.payload.decode()
    latest_events.append({"timestamp": time.time(), "event": event})
    if len(latest_events) > 100:
        latest_events.pop(0)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mqtt-broker", 1883, 60)
    client.loop_forever()

@app.route("/events")
def get_events():
    return jsonify(latest_events)

if __name__ == "__main__":
    Thread(target=start_mqtt).start()
    app.run(host="0.0.0.0", port=5001)
