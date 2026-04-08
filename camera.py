#!/usr/bin/env python3
# camera.py
import cv2
import threading
import time

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
            print(f"Ошибка: не удалось открыть /dev/video{self.device_id}")
            self.running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        # Пробуем MJPEG, но если не поддерживается – закомментировать
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FPS, 15)  # подберите под своё разрешение
        time.sleep(2)

        while self.running:
            ret, img = cap.read()
            if ret:
                # Если камера выдаёт склеенное стерео (2560x720) – режем на два глаза
                if self.width == 2560 and self.height == 720:
                    half = self.width // 2
                    left = img[:, :half]
                    right = img[:, half:]
                    combined = cv2.hconcat([left, right])
                else:
                    combined = img
                
                # Масштабируем для браузера (опционально)
                if combined.shape[1] > 1280:
                    scale = 1280 / combined.shape[1]
                    new_w = int(combined.shape[1] * scale)
                    new_h = int(combined.shape[0] * scale)
                    combined = cv2.resize(combined, (new_w, new_h))
                
                _, jpeg = cv2.imencode('.jpg', combined, [cv2.IMWRITE_JPEG_QUALITY, 80])
                self.frame = jpeg.tobytes()
            else:
                time.sleep(0.01)

        cap.release()

    def get_frame(self):
        return self.frame

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
