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
        self.view_mode = 'stereo'
        self.frame = None
        self.running = False
        self.thread = None
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.lock = threading.Lock()  # для безопасного доступа к frame

    def start(self):
        """Запускает фоновый поток захвата, если он не запущен"""
        if self.thread is None:
            self.running = True
            self.thread = threading.Thread(target=self._capture_loop)
            self.thread.start()
            while self.frame is None:
                time.sleep(0.01)

    def _init_capture(self):
        """Создаёт новый объект VideoCapture с текущими настройками"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.cap = cv2.VideoCapture(self.device_id)
        if not self.cap.isOpened():
            print(f"Не удалось открыть камеру {self.device_id}")
            return False
        # Устанавливаем разрешение
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        # Не принуждаем MJPEG, чтобы избежать проблем
        time.sleep(0.5)  # даём время на применение
        return True

    def _capture_loop(self):
        """Основной цикл захвата кадров"""
        if not self._init_capture():
            self.running = False
            self.thread = None
            return

        while self.running:
            # Если камера закрылась или произошла ошибка – пересоздаём
            if self.cap is None or not self.cap.isOpened():
                if not self._init_capture():
                    time.sleep(1)
                    continue

            ret, img = self.cap.read()
            if ret:
                processed = self._process_frame(img)
                _, jpeg = cv2.imencode('.jpg', processed, [cv2.IMWRITE_JPEG_QUALITY, 80])
                with self.lock:
                    self.frame = jpeg.tobytes()
                # Подсчёт FPS
                self.frame_count += 1
                now = time.time()
                if now - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.last_fps_time = now
            else:
                # Если чтение не удалось – возможно, камера отвалилась
                time.sleep(0.05)
                # Пробуем пересоздать захват
                self._init_capture()

        if self.cap:
            self.cap.release()
            self.cap = None

    def _process_frame(self, img):
        """Обработка кадра в зависимости от режима отображения"""
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

    def set_resolution(self, width, height):
        """Изменяет разрешение камеры с пересозданием захвата"""
        with self.lock:
            self.width = width
            self.height = height
        # Перезапускаем поток захвата
        was_running = self.running
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        # Сбрасываем флаги
        self.frame = None
        self.running = was_running
        self.start()

    def set_view_mode(self, mode):
        """Безопасно меняет режим отображения (без перезапуска)"""
        if mode in ['stereo', 'left', 'right']:
            self.view_mode = mode

    def get_frame(self):
        """Возвращает текущий кадр (потокобезопасно)"""
        with self.lock:
            return self.frame

    def get_fps(self):
        return self.fps

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
