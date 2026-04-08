#!/usr/bin/env python3
# servos.py
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def set_servo_angle(pin, angle):
    """
    Устанавливает угол сервопривода (30-150 градусов).
    pin: номер GPIO (BCM)
    angle: угол от 30 до 150
    """
    if angle < 30:
        angle = 30
    if angle > 150:
        angle = 150

    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, 50)  # 50 Гц
    pwm.start(8)
    duty_cycle = angle / 18.0 + 3.0
    pwm.ChangeDutyCycle(duty_cycle)
    sleep(0.3)
    pwm.stop()

def cleanup_gpio():
    GPIO.cleanup()
