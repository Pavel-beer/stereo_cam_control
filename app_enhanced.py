#!/usr/bin/env python3
# app_enhanced.py
# Веб-сервер для управления стереокамерой и сервоприводами
# Поддерживает: видеопоток, управление панорамой/наклоном, снимки,
# переключение режимов отображения (стерео/левый/правый) и смену разрешения

from flask import Flask, render_template, request, Response, jsonify, send_file
from camera_enhanced import StereoCameraEnhanced
from servo_enhanced import set_angle
import RPi.GPIO as GPIO
import os
import time
import cv2
import numpy as np

app = Flask(__name__)

# ====================== НАСТРОЙКИ ======================
PIN_PAN = 27          # GPIO для панорамы
PIN_TILT = 17         # GPIO для наклона
pan_angle = 90        # начальный угол панорамы
tilt_angle = 90       # начальный угол наклона

# Папка для снимков
SNAPSHOT_DIR = "snapshots_enhanced"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# ====================== ИНИЦИАЛИЗАЦИЯ ======================
# Настройка GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Камера (начальное разрешение)
camera = StereoCameraEnhanced(device_id=0, width=640, height=352)
camera.start()

# ====================== МАРШРУТЫ ======================
@app.route('/')
def index():
    """Главная страница"""
    return render_template('index_enhanced.html', pan=pan_angle, tilt=tilt_angle)

def gen():
    """Генератор видеопотока (MJPEG)"""
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.05)

@app.route('/video_feed')
def video_feed():
    """Маршрут для видеопотока"""
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    """Возвращает текущий статус (FPS, разрешение, углы)"""
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
    """Сохраняет текущий кадр и отдаёт его на скачивание"""
    frame = camera.get_frame()
    if frame:
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
    """Изменяет разрешение камеры (перезапускает захват)"""
    w = int(request.args.get('width', 640))
    h = int(request.args.get('height', 352))
    
    # Проверка, чтобы не тратить ресурсы на одинаковое разрешение
    if w == camera.width and h == camera.height:
        return jsonify({'status': 'ok', 'width': w, 'height': h})
    
    # Перезапуск камеры с новым разрешением
    camera.set_resolution(w, h)
    
    # Небольшая задержка, чтобы камера успела перестроиться
    time.sleep(0.5)
    
    return jsonify({'status': 'ok', 'width': w, 'height': h})

@app.route('/set_view_mode')
def set_view_mode():
    """Изменяет режим отображения (stereo/left/right)"""
    mode = request.args.get('mode', 'stereo')
    camera.set_view_mode(mode)
    return jsonify({'status': 'ok', 'mode': mode})

@app.route('/move_home')
def move_home():
    """Возвращает камеру в положение 90° (домой)"""
    global pan_angle, tilt_angle
    pan_angle = 90
    tilt_angle = 90
    set_angle(PIN_PAN, pan_angle)
    set_angle(PIN_TILT, tilt_angle)
    return jsonify({'pan': pan_angle, 'tilt': tilt_angle})

@app.route('/move_pan/<int:angle>')
def move_pan(angle):
    """Устанавливает угол панорамы (30–150°)"""
    global pan_angle
    pan_angle = max(30, min(150, angle))
    set_angle(PIN_PAN, pan_angle)
    return jsonify({'pan': pan_angle})

@app.route('/move_tilt/<int:angle>')
def move_tilt(angle):
    """Устанавливает угол наклона (30–150°)"""
    global tilt_angle
    tilt_angle = max(30, min(150, angle))
    set_angle(PIN_TILT, tilt_angle)
    return jsonify({'tilt': tilt_angle})

# ====================== ЗАПУСК ======================
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nЗавершение работы сервера...")
        camera.stop()
        GPIO.cleanup()
