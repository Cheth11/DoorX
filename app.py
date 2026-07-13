from flask import Flask, render_template, Response, jsonify
import cv2
import face_recognition
import pickle
import numpy as np
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder="../screenshots")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODING_PATH = os.path.join(BASE_DIR, "../encodings.pickle")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "../screenshots")
STATUS_PATH = os.path.join(BASE_DIR, "../status.json")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Load encodings
with open(ENCODING_PATH, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]

camera = cv2.VideoCapture(0)

last_state = None
stable_name = None
stable_count = 0

def generate_frames():
    global last_state, stable_name, stable_count

    while True:
        success, frame = camera.read()
        if not success:
            continue

        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        current_name = "Unknown"
        confidence = 0.0

        for face_encoding in face_encodings:
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            best = np.argmin(distances)

            confidence = 1 - distances[best]

            if distances[best] < 0.45:
                current_name = known_names[best]

        # Stability logic
        if current_name == stable_name:
            stable_count += 1
        else:
            stable_name = current_name
            stable_count = 1

        status_text = "SCANNING..."

        if stable_count >= 3:
            if stable_name != "Unknown":
                status_text = "ACCESS GRANTED"
                last_state = 1
            else:
                status_text = "ACCESS DENIED"

                # 📸 Save intruder
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filepath = os.path.join(SCREENSHOT_DIR, f"intruder_{timestamp}.jpg")
                cv2.imwrite(filepath, frame)

                last_state = 0

        # Write status JSON
        status_data = {
            "user": stable_name,
            "status": status_text,
            "confidence": round(confidence, 2),
            "arduino": "SIMULATED",
            "time": datetime.now().strftime("%H:%M:%S")
        }

        with open(STATUS_PATH, "w") as f:
            json.dump(status_data, f)

        # Stream frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/status')
def status():
    if os.path.exists(STATUS_PATH):
        with open(STATUS_PATH) as f:
            return jsonify(json.load(f))
    return jsonify({"status": "No Data"})


@app.route('/intruder')
def intruder():
    files = os.listdir(SCREENSHOT_DIR)
    if not files:
        return ""

    latest = sorted(files)[-1]
    return f"/static/{latest}"


if __name__ == "__main__":
    app.run(debug=True)