#!/usr/bin/env python3
# camera.py
import cv2
import threading
import time

class StereoCamera:
    def __init__(self, left_id=0, right_id=1, width=320, height=240, horizontal=True):
        self.left_id = left_id
        self.right_id = right_id
        self.width = width
        self.height = height
        self.horizontal = horizontal  # True: горизонтальная склейка, False: вертикальная

        self.frame = None  # объединённый кадр
        self.running = False
        self.thread = None
        self.last_access = 0

    def start(self):
        if self.thread is None:
            self.running = True
            self.thread = threading.Thread(target=self._capture)
            self.thread.start()
            while self.frame is None:
                time.sleep(0.01)

    def get_frame(self):
        self.last_access = time.time()
        self.start()
        return self.frame

    def _capture(self):
        cap_left = cv2.VideoCapture(self.left_id)
        cap_right = cv2.VideoCapture(self.right_id)

        if not cap_left.isOpened():
            print(f"Ошибка: не удалось открыть левую камеру {self.left_id}")
            self.running = False
            return
        if not cap_right.isOpened():
            print(f"Ошибка: не удалось открыть правую камеру {self.right_id}")
            self.running = False
            return

        # Устанавливаем разрешение
        cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Включаем MJPEG (если поддерживается)
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        cap_left.set(cv2.CAP_PROP_FOURCC, fourcc)
        cap_right.set(cv2.CAP_PROP_FOURCC, fourcc)

        time.sleep(2)  # прогрев

        while self.running:
            ret_l, img_l = cap_left.read()
            ret_r, img_r = cap_right.read()
            if ret_l and ret_r:
                # Приводим к целевому размеру
                if img_l.shape[:2] != (self.height, self.width):
                    img_l = cv2.resize(img_l, (self.width, self.height))
                if img_r.shape[:2] != (self.height, self.width):
                    img_r = cv2.resize(img_r, (self.width, self.height))

                if self.horizontal:
                    combined = cv2.hconcat([img_l, img_r])
                else:
                    combined = cv2.vconcat([img_l, img_r])

                # Кодируем в JPEG
                _, jpeg = cv2.imencode('.jpg', combined)
                self.frame = jpeg.tobytes()
            else:
                time.sleep(0.01)

            # Останавливаем поток, если нет запросов 10 секунд
            if time.time() - self.last_access > 10:
                break

        cap_left.release()
        cap_right.release()
        self.running = False
        self.thread = None
