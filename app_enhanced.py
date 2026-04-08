#!/usr/bin/env python3
# servo_enhanced.py
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def set_angle(pin, angle):
    angle = max(30, min(150, angle))
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, 50)
    pwm.start(8)
    duty = angle / 18.0 + 3.0
    pwm.ChangeDutyCycle(duty)
    sleep(0.3)
    pwm.stop()
