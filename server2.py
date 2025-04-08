import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet', ping_interval=25, ping_timeout=60)

# ✅ Serve the dashboard HTML
@app.route('/')
def index():
    return render_template('kok.html')  # Ensure this is in a "templates/" folder

# ✅ Handle connections (Browser or ESP32)
@socketio.on('connect')
def handle_connect():
    client_ip = request.remote_addr
    print(f"✅ Client connected: {client_ip}")

@socketio.on('disconnect')
def handle_disconnect():
    client_ip = request.remote_addr
    print(f"❌ Client disconnected: {client_ip}")

# ✅ Handle incoming data from ESP32
#@socketio.on('sensor_data')
#def handle_sensor_data(data):
   # client_ip = request.remote_addr
   # print(f"📨 Data from ESP32 [{client_ip}]: {data}")

    # Add device_id from IP if not already provided
   # if 'device_id' not in data:
   #     data['device_id'] = client_ip

    # Broadcast to dashboard/browser
   # socketio.emit('update_dashboard', data)
   # print(f"➡️ Emitted to browser: {data}")
@socketio.on('sensor_data')
def handle_sensor_data(data):
    print("⚠️ RAW data received:", data)

    # 🔄 Convert from JSON string if needed
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            print("❌ Invalid JSON from ESP32:", e)
            return

    if not isinstance(data, dict):
        print("❌ Parsed data is not a dictionary:", type(data))
        return

    # ✅ Add IP as device_id if not present
    client_ip = request.remote_addr
    if 'device_id' not in data:
        data['device_id'] = client_ip

    # 📡 Send to browser clients
    socketio.emit('update_dashboard', data)
    print(f"➡️ Emitted to browser: {data}")

if __name__ == '__main__':
    print("🔥 Flask-SocketIO Server running on 0.0.0.0:5000 using eventlet...")
    socketio.run(app, host='0.0.0.0', port=5000)
