# PC Remote

Control your PC from your phone's browser. No app to install, no accounts — just WiFi.

**Features:**
- touchpad with left/right click and scroll
- volume control, mute, media playback (play/pause, next, previous)
- keyboard — send text or individual special keys

---

## Install

```bash
pip install flask flask-socketio pynput pycaw comtypes
```

## Run

```bash
python server.py
```

The terminal will print the IP address, e.g. `http://192.168.1.42:5000`. Open it on your phone — both devices need to be on the same WiFi.

---

## Requirements

- Windows (pycaw handles volume control, Windows only)
- Python 3.8+
- phone and PC on the same local network

---

## Stack

`Flask` + `Flask-SocketIO` on the server, vanilla JS on the frontend. Mouse movement goes over WebSockets for low latency, everything else is plain HTTP.
