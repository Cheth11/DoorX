# DoorX — Python Backend
# Bridges the HTML frontend to Arduino via Serial

from flask import Flask, request, jsonify
from flask_cors import CORS
import serial
import serial.tools.list_ports
import time

app = Flask(__name__)
CORS(app)

# ─── FIND ARDUINO PORT ─────────────────────────────────────────────
def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if any(x in port.description.lower() for x in ['arduino', 'ch340', 'cp210', 'usb serial']):
            return port.device

    print("\nAvailable ports:")
    for p in ports:
        print(f"{p.device} — {p.description}")
    return None


# ─── CONNECT TO ARDUINO ────────────────────────────────────────────
ARDUINO_PORT = find_arduino_port()

if ARDUINO_PORT:
    print(f"Arduino found on: {ARDUINO_PORT}")
    try:
        arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=2)
        time.sleep(2)
        print("Arduino connected!")
        ARDUINO_CONNECTED = True
    except Exception as e:
        print(f"Connection failed: {e}")
        ARDUINO_CONNECTED = False
else:
    print("Arduino NOT found. Running in simulation mode.")
    ARDUINO_CONNECTED = False


# ─── SEND COMMAND ──────────────────────────────────────────────────
def send_to_arduino(command):
    if ARDUINO_CONNECTED:
        try:
            arduino.write((command + '\n').encode())
            time.sleep(0.1)
            return "SENT"
        except Exception as e:
            print("Serial error:", e)
            return "ERROR"
    else:
        print(f"[SIMULATION] {command}")
        return "SIMULATED"


# ─── ROUTES ────────────────────────────────────────────────────────
@app.route('/status')
def status():
    return jsonify({
        "server": "running",
        "arduino": "connected" if ARDUINO_CONNECTED else "simulation"
    })


@app.route('/access', methods=['POST'])
def access():
    data = request.get_json()

    name = data.get('name', 'Unknown')
    decision = data.get('decision', 'deny')

    print(f"\n[ACCESS] {name} → {decision.upper()}")

    if decision == 'grant':
        # 🔥 FIXED HERE
        response = send_to_arduino('OPEN')
        return jsonify({"status": "granted", "arduino": response})

    else:
        response = send_to_arduino('DENY')
        return jsonify({"status": "denied", "arduino": response})


@app.route('/test/grant')
def test_grant():
    return jsonify({"test": send_to_arduino('OPEN')})


@app.route('/test/deny')
def test_deny():
    return jsonify({"test": send_to_arduino('DENY')})


# ─── RUN ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n==============================")
    print(" DoorX Backend Running")
    print(" http://localhost:5000")
    print("==============================\n")

    app.run(host='0.0.0.0', port=5000)