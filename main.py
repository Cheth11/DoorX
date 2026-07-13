import cv2
import face_recognition
import pickle
import serial
import time
import numpy as np
import os
import json
from datetime import datetime

# 🔌 Arduino Setup
arduino = None
arduino_status = "NOT CONNECTED"

try:
    arduino = serial.Serial('COM7', 9600)
    time.sleep(2)
    arduino_status = "CONNECTED"
except:
    arduino_status = "NOT CONNECTED"

# 📁 Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODING_PATH = os.path.join(BASE_DIR, "encodings.pickle")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
STATUS_PATH = os.path.join(BASE_DIR, "status.json")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 🧠 Load encodings
with open(ENCODING_PATH, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]

# 🎥 Camera
cap = cv2.VideoCapture(0)

last_state = None
stable_name = None
stable_count = 0
confidence = 0.0

logs = []

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    logs.append(f"[{timestamp}] {msg}")
    if len(logs) > 6:
        logs.pop(0)

print("System started...")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    current_name = "Unknown"
    confidence = 0.0

    for face_encoding in face_encodings:
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)

        confidence = 1 - face_distances[best_match_index]

        if face_distances[best_match_index] < 0.45:
            current_name = known_names[best_match_index]
        else:
            current_name = "Unknown"

    # Stability logic
    if current_name == stable_name:
        stable_count += 1
    else:
        stable_name = current_name
        stable_count = 1

    status_text = "SCANNING..."

    if stable_count >= 3:
        if stable_name != "Unknown" and last_state != 1:
            status_text = "ACCESS GRANTED"
            add_log(f"{stable_name} → Granted")

            if arduino:
                try:
                    arduino.write(b'1')
                except:
                    pass

            last_state = 1

        elif stable_name == "Unknown" and last_state != 0:
            status_text = "ACCESS DENIED"

            # Screenshot
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filepath = os.path.join(SCREENSHOT_DIR, f"intruder_{timestamp}.jpg")
            cv2.imwrite(filepath, frame)

            add_log("⚠️ Unknown detected → Screenshot saved")

            if arduino:
                try:
                    arduino.write(b'0')
                except:
                    pass

            last_state = 0

    # 🌐 Write status for website
    status_data = {
        "user": stable_name,
        "status": status_text,
        "confidence": round(confidence, 2),
        "arduino": arduino_status,
        "time": datetime.now().strftime("%H:%M:%S")
    }

    with open(STATUS_PATH, "w") as f:
        json.dump(status_data, f)

    # Small delay for stability
    time.sleep(0.08)