import asyncio
import websockets
import json
import threading
from flask import Flask, render_template
from queue import Queue

# Flask app for serving dashboard.html
app = Flask(__name__)
data_queue = Queue()

@app.route('/')
def index():
    return render_template('dashboard.html')  # Make sure this is inside templates/

# Store WebSocket clients (browsers)
browser_clients = set()

# Handle incoming data from ESP32
async def esp32_handler(websocket, path):
    print("✅ ESP32 connected")
    try:
        async for message in websocket:
            print(f"📨 Data from ESP32: {message}")
            data_queue.put(message)  # Push data to be sent to browser
    except websockets.exceptions.ConnectionClosed:
        print("❌ ESP32 disconnected")

# Send data to browser clients via WebSockets
async def browser_sender(websocket, path):
    print("✅ Browser connected")
    browser_clients.add(websocket)
    try:
        while True:
            if not data_queue.empty():
                data = data_queue.get()
                await websocket.send(data)
    except websockets.exceptions.ConnectionClosed:
        print("❌ Browser disconnected")
    finally:
        browser_clients.remove(websocket)

# Combined handler to route based on path
async def handler(websocket, path):
    if path == "/esp32":
        await esp32_handler(websocket, path)
    elif path == "/browser":
        await browser_sender(websocket, path)

# Run WebSocket server
def start_websocket_server():
    print("🔥 WebSocket server running on ws://0.0.0.0:5000")
    asyncio.set_event_loop(asyncio.new_event_loop())
    start_server = websockets.serve(handler, "0.0.0.0", 5000)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

# Run Flask in a separate thread
def start_flask():
    print("🌐 Flask running on http://0.0.0.0:8000")
    app.run(host='0.0.0.0', port=8000)

if __name__ == "__main__":
    threading.Thread(target=start_flask).start()
    start_websocket_server()
