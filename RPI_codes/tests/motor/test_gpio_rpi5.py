#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple GPIO Motor Test - Raspberry Pi 5
Quick test to verify motor connections are working.
"""

import sys
import time

print("\n" + "=" * 50)
print("SIMPLE MOTOR CONNECTION TEST")
print("=" * 50 + "\n")

# Try to import GPIO library
try:
    import gpiod
    GPIO_BACKEND = 'gpiod'
    print("✅ Using gpiod (Raspberry Pi 5)")
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_BACKEND = 'RPi.GPIO'
        print("✅ Using RPi.GPIO (Raspberry Pi 4/3)")
    except ImportError:
        print("❌ No GPIO library found!")
        print("\nInstall with:")
        print("  sudo apt-get install python3-libgpiod")
        sys.exit(1)

# Motor pins
LEFT_PWM = 12
LEFT_DIR1 = 16
LEFT_DIR2 = 20
RIGHT_PWM = 13
RIGHT_DIR1 = 19
RIGHT_DIR2 = 26

print(f"\nPins: Left(12,16,20) Right(13,19,26)")
print("\nPress ENTER to start test...", end='')
input()

lines = {}

try:
    # Setup GPIO
    if GPIO_BACKEND == 'gpiod':
        # Simple gpiod setup
        for name, pin in [('l_pwm', LEFT_PWM), ('l_d1', LEFT_DIR1), ('l_d2', LEFT_DIR2),
                          ('r_pwm', RIGHT_PWM), ('r_d1', RIGHT_DIR1), ('r_d2', RIGHT_DIR2)]:
            line = gpiod.find_line(f"GPIO{pin}")
            if line is None:
                # Fallback: try direct chip access
                line = gpiod.Chip('gpiochip4').get_line(pin)
            line.request(consumer="test", type=gpiod.LINE_REQ_DIR_OUT)
            lines[name] = line
    else:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in [LEFT_PWM, LEFT_DIR1, LEFT_DIR2, RIGHT_PWM, RIGHT_DIR1, RIGHT_DIR2]:
            GPIO.setup(pin, GPIO.OUT)

    print("\n✅ GPIO ready\n")

    # Simple test sequence
    tests = [
        ("Left motor forward", 'l', 1, 0, 1),
        ("Left motor reverse", 'l', 0, 1, 1),
        ("Right motor forward", 'r', 1, 0, 1),
        ("Right motor reverse", 'r', 0, 1, 1),
        ("Both motors forward", 'b', 1, 0, 1),
    ]

    for name, motor, d1, d2, pwm in tests:
        print(f"→ {name}...", end=' ', flush=True)

        if GPIO_BACKEND == 'gpiod':
            if motor in ['l', 'b']:
                lines['l_d1'].set_value(d1)
                lines['l_d2'].set_value(d2)
                lines['l_pwm'].set_value(pwm)
            if motor in ['r', 'b']:
                lines['r_d1'].set_value(d1)
                lines['r_d2'].set_value(d2)
                lines['r_pwm'].set_value(pwm)
        else:
            if motor in ['l', 'b']:
                GPIO.output(LEFT_DIR1, d1)
                GPIO.output(LEFT_DIR2, d2)
                GPIO.output(LEFT_PWM, pwm)
            if motor in ['r', 'b']:
                GPIO.output(RIGHT_DIR1, d1)
                GPIO.output(RIGHT_DIR2, d2)
                GPIO.output(RIGHT_PWM, pwm)

        time.sleep(1.5)
        print("Done")

    # Stop all
    print("\n→ Stopping all motors...")
    if GPIO_BACKEND == 'gpiod':
        for line in lines.values():
            line.set_value(0)
    else:
        GPIO.output([LEFT_DIR1, LEFT_DIR2, LEFT_PWM, RIGHT_DIR1, RIGHT_DIR2, RIGHT_PWM], 0)

    print("\n" + "=" * 50)
    print("✅ TEST COMPLETE!")
    print("=" * 50)
    print("\nIf motors moved, connections are good!")
    print("Run: python3 ps3_motor_controller.py\n")

except KeyboardInterrupt:
    print("\n\n⚠️  Stopped by user")

except PermissionError:
    print("\n\n❌ Permission denied!")
    print("Run: sudo python3 test_gpio_rpi5.py")
    print("Or: sudo chmod 666 /dev/gpiochip4")

except Exception as e:
    print(f"\n\n❌ Error: {e}")

finally:
    # Cleanup
    print("\nCleaning up...", end=' ')
    if GPIO_BACKEND == 'gpiod' and lines:
        for line in lines.values():
            line.release()
    elif GPIO_BACKEND == 'RPi.GPIO':
        GPIO.cleanup()
    print("Done\n")
