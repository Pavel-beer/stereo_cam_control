#!/usr/bin/env python3
# app.py
from flask import Flask, render_template, request, Response
from camera import StereoCamera
from servo import set_angle
import RPi.GPIO as GPIO

app = Flask(__name__)

# Пины сервоприводов (BCM)
PIN_PAN = 27    # панорама
PIN_TILT = 17   # наклон

# Начальные углы
pan_angle = 90
tilt_angle = 90

# Настройка GPIO (один раз при старте)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Инициализация камеры (выберите разрешение под свою камеру)
# Варианты: (1280,480) - 15fps, (2560,720) - 5fps, (640,352) - 30fps
camera = StereoCamera(device_id=0, width=1280, height=480)

@app.route('/')
def index():
    return render_template('index.html', pan=pan_angle, tilt=tilt_angle)

def gen():
    camera.start()
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            import time
            time.sleep(0.05)

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/pan/<int:angle>')
def set_pan(angle):
    global pan_angle
    pan_angle = max(30, min(150, angle))
    set_angle(PIN_PAN, pan_angle)
    return '', 204

@app.route('/tilt/<int:angle>')
def set_tilt(angle):
    global tilt_angle
    tilt_angle = max(30, min(150, angle))
    set_angle(PIN_TILT, tilt_angle)
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
