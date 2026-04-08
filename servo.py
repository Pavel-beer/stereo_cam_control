#!/usr/bin/env python3
# servo.py
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def set_angle(pin, angle):
    """angle от 30 до 150 градусов"""
    if not (30 <= angle <= 150):
        raise ValueError("Угол должен быть от 30 до 150")
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, 50)  # 50 Гц
    pwm.start(8)
    duty = angle / 18.0 + 3.0
    pwm.ChangeDutyCycle(duty)
    sleep(0.3)
    pwm.stop()
