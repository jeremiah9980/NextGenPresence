# NextGen AI Reassessment Platform

This project combines WiFi/Bluetooth presence detection, Ring camera sync, and AI-based reassessment of devices in a residential area, with a Flask UI for human tagging.

## Features
- Reassesses device presence every 30 minutes using AI logic
- Matches Ring motion events with nearby device presence
- Allows human-friendly naming/tagging of devices via Flask UI
- Outputs logs to aid in dashboarding with Grafana

## Getting Started
```bash
python db_init.py
python ai_reassessment.py
python ring_event_sync.py
python flask_ui.py
```

## Deployment
- Flask runs on port 5000
- Reassessment runs in background every 30 minutes
