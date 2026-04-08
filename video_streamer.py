#!/usr/bin/env python3
# Простой веб-сервер для стереовидео с двух USB-камер
# Запуск: sudo python3 video_streamer.py

import cv2
import time
import threading
from flask import Flask, Response

app = Flask(__name__)

class StereoCamera:
    def __init__(self, left_id=0, right_id=1, width=320, height=240):
        self.left_id = left_id
        self.right_id = right_id
        self.width = width
        self.height = height
        self.frame = None
        self.running = False
        self.thread = None

    def start(self):
        if self.thread is None:
            self.running = True
            self.thread = threading.Thread(target=self._capture)
            self.thread.start()
            # ждём первый кадр
            while self.frame is None:
                time.sleep(0.01)

    def _capture(self):
        cap_left = cv2.VideoCapture(self.left_id)
        cap_right = cv2.VideoCapture(self.right_id)

        if not cap_left.isOpened():
            print(f"Не удалось открыть камеру {self.left_id}")
            return
        if not cap_right.isOpened():
            print(f"Не удалось открыть камеру {self.right_id}")
            return

        # Настройка разрешения
        cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # MJPEG для производительности
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        cap_left.set(cv2.CAP_PROP_FOURCC, fourcc)
        cap_right.set(cv2.CAP_PROP_FOURCC, fourcc)

        time.sleep(2)

        while self.running:
            ret_l, img_l = cap_left.read()
            ret_r, img_r = cap_right.read()
            if ret_l and ret_r:
                # Горизонтальная склейка
                combined = cv2.hconcat([img_l, img_r])
                _, jpeg = cv2.imencode('.jpg', combined)
                self.frame = jpeg.tobytes()
            else:
                time.sleep(0.01)

        cap_left.release()
        cap_right.release()

    def get_frame(self):
        return self.frame

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

# Глобальный объект камеры
camera = StereoCamera(left_id=0, right_id=1)

@app.route('/video_feed')
def video_feed():
    def generate():
        camera.start()
        while True:
            frame = camera.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.05)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Стереокамера</title></head>
    <body style="background:black; text-align:center; color:white;">
        <h1>Видеопоток с двух камер</h1>
        <img src="/video_feed" style="max-width:95%; border:2px solid white;">
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
