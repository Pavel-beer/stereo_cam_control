#!/usr/bin/env python3
# video_streamer_single.py
import cv2
import threading
import time
from flask import Flask, Response

app = Flask(__name__)

class SingleCamera:
    def __init__(self, device_id=0, width=640, height=480):
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
        cap = cv2.VideoCapture(self.device_id)
        if not cap.isOpened():
            print(f"Не удалось открыть камеру /dev/video{self.device_id}")
            self.running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        # Включение MJPEG для ускорения
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        time.sleep(2)

        while self.running:
            ret, img = cap.read()
            if ret:
                _, jpeg = cv2.imencode('.jpg', img)
                self.frame = jpeg.tobytes()
            else:
                time.sleep(0.01)

        cap.release()

    def get_frame(self):
        return self.frame

camera = SingleCamera(device_id=0, width=640, height=480)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Стереокамера</title></head>
    <body style="background:black; text-align:center; color:white;">
        <h1>Видеопоток с камеры</h1>
        <img src="/video_feed" style="max-width:95%; border:2px solid white;">
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
