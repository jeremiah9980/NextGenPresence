import time
def get_recent_ring_events(minutes=30):
    # MOCKED data – in real use, fetch from Ring API with timestamp conversion
    now = time.time()
    return [
        {"timestamp": now - 90, "type": "motion", "camera": "Front Door"},
        {"timestamp": now - 1400, "type": "motion", "camera": "Driveway"},
    ]
