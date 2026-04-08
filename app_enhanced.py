#!/usr/bin/env python3
# app_enhanced.py
from flask import Flask, render_template, request, Response, jsonify, send_file
from camera_enhanced import StereoCameraEnhanced
from servo_enhanced import set_angle
import RPi.GPIO as GPIO
import os
import time
import cv2
import numpy as np
from io import BytesIO

app = Flask(__name__)

# Пины серво
PIN_PAN = 27
PIN_TILT = 17
pan_angle = 90
tilt_angle = 90

# Настройка GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Инициализация камеры (разрешение по умолчанию)
camera = StereoCameraEnhanced(device_id=0, width=640, height=352)
camera.start()

# Папка для снимков
SNAPSHOT_DIR = "snapshots_enhanced"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index_enhanced.html', pan=pan_angle, tilt=tilt_angle)

def gen():
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.05)

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify({
        'fps': camera.get_fps(),
        'width': camera.width,
        'height': camera.height,
        'view_mode': camera.view_mode,
        'pan': pan_angle,
        'tilt': tilt_angle
    })

@app.route('/snapshot')
def snapshot():
    frame = camera.get_frame()
    if frame:
        # Конвертируем байты в массив numpy для сохранения
        nparr = np.frombuffer(frame, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        timestamp = int(time.time())
        filename = f"snapshot_{timestamp}.jpg"
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        cv2.imwrite(filepath, img)
        return send_file(filepath, as_attachment=True)
    return "No frame", 404

@app.route('/set_resolution')
def set_resolution():
    w = int(request.args.get('width', 640))
    h = int(request.args.get('height', 352))
    camera.set_resolution(w, h)
    return jsonify({'status': 'ok', 'width': w, 'height': h})

@app.route('/set_view_mode')
def set_view_mode():
    mode = request.args.get('mode', 'stereo')
    camera.set_view_mode(mode)
    return jsonify({'status': 'ok', 'mode': mode})

@app.route('/move_home')
def move_home():
    global pan_angle, tilt_angle
    pan_angle = 90
    tilt_angle = 90
    set_angle(PIN_PAN, pan_angle)
    set_angle(PIN_TILT, tilt_angle)
    return jsonify({'pan': pan_angle, 'tilt': tilt_angle})

@app.route('/move_pan/<int:angle>')
def move_pan(angle):
    global pan_angle
    pan_angle = max(30, min(150, angle))
    set_angle(PIN_PAN, pan_angle)
    return jsonify({'pan': pan_angle})

@app.route('/move_tilt/<int:angle>')
def move_tilt(angle):
    global tilt_angle
    tilt_angle = max(30, min(150, angle))
    set_angle(PIN_TILT, tilt_angle)
    return jsonify({'tilt': tilt_angle})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
