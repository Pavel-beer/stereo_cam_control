#!/usr/bin/env python3
# video_streamer_single.py
import cv2
import threading
import time
from flask import Flask, Response

app = Flask(__name__)

class StereoCamera:
    def __init__(self, device_id=0, width=1280, height=480):
        self.device_id = device_id
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
            while self.frame is None:
                time.sleep(0.01)

    def _capture(self):
        cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)
        if not cap.isOpened():
            print(f"Не удалось открыть камеру /dev/video{self.device_id}")
            self.running = False
            return

        # Принудительная установка разрешения (поддерживается камерой)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Пробуем включить MJPEG (если поддерживается)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        # Устанавливаем частоту кадров
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        time.sleep(2)

        while self.running:
            ret, img = cap.read()
            if ret:
                # Если разрешение 2560x720 — режем на два глаза
                if self.width == 2560 and self.height == 720:
                    half = self.width // 2
                    left = img[:, :half]
                    right = img[:, half:]
                    combined = cv2.hconcat([left, right])
                else:
                    combined = img
                
                # Масштабируем для удобного просмотра в браузере
                if combined.shape[1] > 1280:
                    scale = 1280 / combined.shape[1]
                    new_width = int(combined.shape[1] * scale)
                    new_height = int(combined.shape[0] * scale)
                    combined = cv2.resize(combined, (new_width, new_height))
                
                _, jpeg = cv2.imencode('.jpg', combined, [cv2.IMWRITE_JPEG_QUALITY, 80])
                self.frame = jpeg.tobytes()
            else:
                time.sleep(0.01)

        cap.release()

    def get_frame(self):
        return self.frame

# Инициализация камеры — выбираем режим
# Варианты:
# 1. 1280x480 @ 15fps (рекомендуемый баланс качества и скорости)
# 2. 2560x720 @ 5fps (максимальное качество, но медленно)
# 3. 640x352 @ 30fps (быстро, но низкое качество)

camera = StereoCamera(device_id=0, width=1280, height=480)  # <- можно менять

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Стереокамера</title>
        <style>
            body { background: black; text-align: center; color: white; font-family: Arial; }
            img { max-width: 95%; border: 2px solid white; margin-top: 20px; }
            .info { margin-top: 10px; font-size: 14px; }
        </style>
    </head>
    <body>
        <h1>Стереокамера (левый + правый глаз)</h1>
        <img src="/video_feed">
        <div class="info">Если изображение искажено — камера передаёт готовую стереопару</div>
    </body>
    </html>
    '''

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)
