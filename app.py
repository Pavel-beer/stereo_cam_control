#!/usr/bin/env python3
# app.py
import time
from flask import Flask, render_template, Response, request
from camera import StereoCamera
from servos import set_servo_angle, cleanup_gpio
import atexit

app = Flask(__name__)

# Пины для сервоприводов (BCM)
PAN_PIN = 27
TILT_PIN = 17

# Начальные углы
pan_angle = 90
tilt_angle = 90

# Инициализация камеры (индексы устройств могут отличаться)
# Обычно первая камера /dev/video0, вторая /dev/video2
# Но у вас стереокамера может давать video0 и video1 – проверьте
camera = StereoCamera(left_id=0, right_id=1, width=320, height=240, horizontal=True)

@app.route('/')
def index():
    return render_template('index.html', pan=pan_angle, tilt=tilt_angle)

def generate_frames():
    """Генератор кадров для видеопотока"""
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.05)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/move/<axis>/<int:angle>')
def move(axis, angle):
    global pan_angle, tilt_angle
    if axis == 'pan':
        pan_angle = angle
        set_servo_angle(PAN_PIN, angle)
    elif axis == 'tilt':
        tilt_angle = angle
        set_servo_angle(TILT_PIN, angle)
    return '', 204  # успешно, без содержимого

# При завершении очищаем GPIO
atexit.register(cleanup_gpio)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
