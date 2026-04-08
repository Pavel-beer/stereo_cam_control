#!/usr/bin/env python3
# camera_enhanced.py
import cv2
import threading
import time

class StereoCameraEnhanced:
    def __init__(self, device_id=0, width=640, height=352):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.view_mode = 'stereo'  # stereo, left, right
        self.frame = None
        self.running = False
        self.thread = None
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()

    def start(self):
        if self.thread is None:
            self.running = True
            self.thread = threading.Thread(target=self._capture_loop)
            self.thread.start()
            while self.frame is None:
                time.sleep(0.01)

    def _capture_loop(self):
        self.cap = cv2.VideoCapture(self.device_id)
        if not self.cap.isOpened():
            print(f"Ошибка: не удалось открыть камеру {self.device_id}")
            self.running = False
            return
        self._apply_settings()
        time.sleep(2)

        while self.running:
            ret, img = self.cap.read()
            if ret:
                processed = self._process_frame(img)
                _, jpeg = cv2.imencode('.jpg', processed, [cv2.IMWRITE_JPEG_QUALITY, 80])
                self.frame = jpeg.tobytes()
                # Подсчёт FPS
                self.frame_count += 1
                now = time.time()
                if now - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.last_fps_time = now
            else:
                time.sleep(0.01)
        if self.cap:
            self.cap.release()

    def _process_frame(self, img):
        h, w = img.shape[:2]
        if self.view_mode == 'stereo':
            return img
        elif self.view_mode == 'left':
            half = w // 2
            return img[:, :half]
        elif self.view_mode == 'right':
            half = w // 2
            return img[:, half:]
        return img

    def _apply_settings(self):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def set_resolution(self, width, height):
        self.width = width
        self.height = height
        if self.cap:
            self._apply_settings()
            time.sleep(0.5)

    def set_view_mode(self, mode):
        if mode in ['stereo', 'left', 'right']:
            self.view_mode = mode

    def get_frame(self):
        return self.frame

    def get_fps(self):
        return self.fps

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
