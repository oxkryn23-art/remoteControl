# PC Remote Server
# spustit: python server.py
# nutne: pip install flask flask-socketio pynput pycaw comtypes

import socket, ctypes, os
import comtypes
comtypes.CoInitialize()
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL

app      = Flask(__name__)
app.config['SECRET_KEY'] = 'pc-remote-2024'
socketio = SocketIO(app, cors_allowed_origins="*")
mouse    = MouseController()
keyboard = KeyboardController()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_vol():
    # inicializace COM pro aktualni vlakno, pak ziskame vychozi audio vystup
    comtypes.CoInitialize()
    speakers = AudioUtilities.GetDeviceEnumerator()
    default  = speakers.GetDefaultAudioEndpoint(0, 1)
    iface    = default.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return ctypes.cast(iface, ctypes.POINTER(IAudioEndpointVolume))

def get_local_ip():
    #  jak zjistit lokalni IP bez znalosti site
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    finally:
        s.close()

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'remote.html')

@app.route('/volume', methods=['GET'])
def get_volume():
    try:
        vol = get_vol()
        return jsonify({'volume': round(vol.GetMasterVolumeLevelScalar() * 100), 'muted': bool(vol.GetMute())})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/volume', methods=['POST'])
def set_volume():
    try:
        level = max(0, min(100, request.json.get('volume', 50)))
        get_vol().SetMasterVolumeLevelScalar(level / 100, None)
        return jsonify({'ok': True, 'volume': level})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/mute', methods=['POST'])
def toggle_mute():
    try:
        vol   = get_vol()
        muted = vol.GetMute()
        vol.SetMute(not muted, None)
        return jsonify({'muted': not bool(muted)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/devices', methods=['GET'])
def get_devices():
    try:
        devs = AudioUtilities.GetAllDevices()
        out  = [{'id': i, 'name': d.FriendlyName} for i, d in enumerate(devs) if d.FriendlyName]
        return jsonify({'devices': out})
    except Exception as e:
        return jsonify({'devices': [], 'error': str(e)})

@app.route('/media', methods=['POST'])
def media_control():
    action  = request.json.get('action')
    key_map = {
        'play_pause': Key.media_play_pause,
        'next':       Key.media_next,
        'prev':       Key.media_previous,
    }
    if action in key_map:
        keyboard.press(key_map[action])
        keyboard.release(key_map[action])
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400

@app.route('/keyboard', methods=['POST'])
def keyboard_input():
    data = request.json
    if 'text' in data:
        keyboard.type(data['text'])
        return jsonify({'ok': True})
    if 'key' in data:
        key_map = {
            'enter':     Key.enter,
            'backspace': Key.backspace,
            'escape':    Key.esc,
            'tab':       Key.tab,
            'space':     Key.space,
            'up':        Key.up,
            'down':      Key.down,
            'left':      Key.left,
            'right':     Key.right,
        }
        k = key_map.get(data['key'])
        if k:
            keyboard.press(k)
            keyboard.release(k)
            return jsonify({'ok': True})
    return jsonify({'ok': False}), 400

@socketio.on('mouse_move')
def on_move(data):
    mouse.move(data.get('dx', 0), data.get('dy', 0))

@socketio.on('mouse_click')
def on_click(data):
    mouse.click(Button.left if data.get('button') == 'left' else Button.right, 1)

@socketio.on('mouse_scroll')
def on_scroll(data):
    mouse.scroll(0, data.get('dy', 0))

if __name__ == '__main__':
    ip   = get_local_ip()
    port = 5000
    print("=" * 50)
    print("  PC Remote spusten!")
    print(f"  Otevri na mobilu: http://{ip}:{port}")
    print("  (mobil musi byt na stejne WiFi)")
    print("=" * 50)
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
