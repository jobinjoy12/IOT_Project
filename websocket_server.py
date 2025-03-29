import asyncio
import websockets
import json
import threading
from flask import Flask, render_template
from asyncio import Queue

# Flask app for serving dashboard.html
app = Flask(__name__)
data_queue = Queue()

@app.route('/')
def index():
    return render_template('dashboardnsw.html')  # Ensure this is in /templates

# Track all browser connections
browser_clients = set()

# Handle incoming data from ESP32
async def esp32_handler(websocket, path):
    print("✅ ESP32 connected")
    try:
        async for message in websocket:
            print(f"📨 Data from ESP32: {message}")
            await data_queue.put(message)  # ✅ async-safe
    except websockets.exceptions.ConnectionClosed:
        print("❌ ESP32 disconnected")

# Handle sending data to browser
async def browser_sender(websocket, path):
    print(f"✅ Browser connected from {websocket.remote_address}")
    browser_clients.add(websocket)
    try:
        while True:
            data = await data_queue.get()  # ✅ non-blocking
            print(f"➡️ Sending to browser: {data}")
            await websocket.send(data)
    except websockets.exceptions.ConnectionClosed:
        print("❌ Browser disconnected")
    finally:
        browser_clients.remove(websocket)

# Start WebSocket server
def start_websocket_server():
    async def handler(websocket):
        path = websocket.request.path
        if path == "/esp32":
            await esp32_handler(websocket, path)
        elif path == "/browser":
            await browser_sender(websocket, path)
        else:
            print(f"❌ Unknown WebSocket path: {path}")
            await websocket.close()

    async def run_ws():
        async with websockets.serve(handler, "0.0.0.0", 5000):
            print("🔥 WebSocket server running on ws://0.0.0.0:5000")
            await asyncio.Future()  # Keep alive forever

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_ws())

# Run Flask in a separate thread
def start_flask():
    print("🌐 Flask running on http://0.0.0.0:8000")
    app.run(host='0.0.0.0', port=8000)

# Entry point
if __name__ == "__main__":
    threading.Thread(target=start_flask).start()
    start_websocket_server()
