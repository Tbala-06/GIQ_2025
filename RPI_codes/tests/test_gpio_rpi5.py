#!/usr/bin/env python3
"""
GPIO Test Script for Raspberry Pi 5
Tests GPIO library availability and basic motor control without PS3 controller.
"""

import sys
import time

print("=" * 70)
print("GPIO Test Script - Raspberry Pi 5")
print("=" * 70)
print()

# Test GPIO library availability
print("1. Testing GPIO library availability...")
print("-" * 70)

GPIO_AVAILABLE = False
GPIO_BACKEND = None

try:
    import gpiod
    from gpiod.line import Direction, Value
    GPIO_AVAILABLE = True
    GPIO_BACKEND = 'gpiod'
    print("✅ gpiod is available (Raspberry Pi 5 native)")
except ImportError:
    print("❌ gpiod not found")
    try:
        import RPi.GPIO as GPIO
        GPIO_AVAILABLE = True
        GPIO_BACKEND = 'RPi.GPIO'
        print("✅ RPi.GPIO is available (Raspberry Pi 4/3)")
    except (ImportError, RuntimeError):
        print("❌ RPi.GPIO not found")
        GPIO_AVAILABLE = False
        GPIO_BACKEND = None

print()

if not GPIO_AVAILABLE:
    print("❌ ERROR: No GPIO library found!")
    print()
    print("To install on Raspberry Pi 5:")
    print("  sudo apt-get install python3-libgpiod")
    print()
    print("To install on Raspberry Pi 4/3:")
    print("  sudo apt-get install python3-rpi.gpio")
    sys.exit(1)

print(f"Selected backend: {GPIO_BACKEND}")
print()

# Motor GPIO Pins
MOTOR_LEFT_PWM = 12
MOTOR_LEFT_DIR1 = 16
MOTOR_LEFT_DIR2 = 20
MOTOR_RIGHT_PWM = 13
MOTOR_RIGHT_DIR1 = 19
MOTOR_RIGHT_DIR2 = 26

print("2. Testing GPIO pin configuration...")
print("-" * 70)
print(f"Left Motor:  PWM=GPIO{MOTOR_LEFT_PWM}, DIR1=GPIO{MOTOR_LEFT_DIR1}, DIR2=GPIO{MOTOR_LEFT_DIR2}")
print(f"Right Motor: PWM=GPIO{MOTOR_RIGHT_PWM}, DIR1=GPIO{MOTOR_RIGHT_DIR1}, DIR2=GPIO{MOTOR_RIGHT_DIR2}")
print()

# Initialize GPIO
print("3. Initializing GPIO...")
print("-" * 70)

chip = None
lines = {}

try:
    if GPIO_BACKEND == 'gpiod':
        # RPi 5 - gpiod
        chip = gpiod.Chip('/dev/gpiochip4')
        print(f"✅ Opened GPIO chip: {chip.name()}")

        pin_config = {
            'left_pwm': MOTOR_LEFT_PWM,
            'left_dir1': MOTOR_LEFT_DIR1,
            'left_dir2': MOTOR_LEFT_DIR2,
            'right_pwm': MOTOR_RIGHT_PWM,
            'right_dir1': MOTOR_RIGHT_DIR1,
            'right_dir2': MOTOR_RIGHT_DIR2,
        }

        for name, pin in pin_config.items():
            line = chip.get_line(pin)
            line.request(consumer="gpio_test", type=gpiod.LINE_REQ_DIR_OUT)
            lines[name] = line
            print(f"  ✅ Configured {name} (GPIO {pin})")

    elif GPIO_BACKEND == 'RPi.GPIO':
        # RPi 4/3 - RPi.GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(MOTOR_LEFT_PWM, GPIO.OUT)
        GPIO.setup(MOTOR_LEFT_DIR1, GPIO.OUT)
        GPIO.setup(MOTOR_LEFT_DIR2, GPIO.OUT)
        GPIO.setup(MOTOR_RIGHT_PWM, GPIO.OUT)
        GPIO.setup(MOTOR_RIGHT_DIR1, GPIO.OUT)
        GPIO.setup(MOTOR_RIGHT_DIR2, GPIO.OUT)

        print("✅ All GPIO pins configured")

    print()
    print("4. Running motor test sequence...")
    print("-" * 70)
    print("This will test each motor direction for 2 seconds each.")
    print("Motors should be connected to see results.")
    print()

    input("Press ENTER to start test (or Ctrl+C to exit)...")
    print()

    def set_motor_gpiod(name_prefix, dir_val1, dir_val2, pwm_val):
        """Set motor with gpiod"""
        lines[f'{name_prefix}_dir1'].set_value(dir_val1)
        lines[f'{name_prefix}_dir2'].set_value(dir_val2)
        lines[f'{name_prefix}_pwm'].set_value(pwm_val)

    def set_motor_rpi_gpio(pwm_pin, dir1_pin, dir2_pin, dir_val1, dir_val2, pwm_val):
        """Set motor with RPi.GPIO"""
        GPIO.output(dir1_pin, GPIO.HIGH if dir_val1 else GPIO.LOW)
        GPIO.output(dir2_pin, GPIO.HIGH if dir_val2 else GPIO.LOW)
        GPIO.output(pwm_pin, GPIO.HIGH if pwm_val else GPIO.LOW)

    tests = [
        ("Left motor FORWARD", 'left', 1, 0, 1),
        ("Left motor REVERSE", 'left', 0, 1, 1),
        ("Left motor STOP", 'left', 0, 0, 0),
        ("Right motor FORWARD", 'right', 1, 0, 1),
        ("Right motor REVERSE", 'right', 0, 1, 1),
        ("Right motor STOP", 'right', 0, 0, 0),
        ("Both motors FORWARD", 'both', 1, 0, 1),
        ("Both motors STOP", 'both', 0, 0, 0),
    ]

    for test_name, motor, dir1, dir2, pwm in tests:
        print(f"  → {test_name}...", end=" ", flush=True)

        if GPIO_BACKEND == 'gpiod':
            if motor in ['left', 'both']:
                set_motor_gpiod('left', dir1, dir2, pwm)
            if motor in ['right', 'both']:
                set_motor_gpiod('right', dir1, dir2, pwm)

        elif GPIO_BACKEND == 'RPi.GPIO':
            if motor in ['left', 'both']:
                set_motor_rpi_gpio(MOTOR_LEFT_PWM, MOTOR_LEFT_DIR1, MOTOR_LEFT_DIR2, dir1, dir2, pwm)
            if motor in ['right', 'both']:
                set_motor_rpi_gpio(MOTOR_RIGHT_PWM, MOTOR_RIGHT_DIR1, MOTOR_RIGHT_DIR2, dir1, dir2, pwm)

        time.sleep(2)
        print("✅")

    print()
    print("=" * 70)
    print("✅ All tests completed successfully!")
    print("=" * 70)
    print()
    print("If motors moved as expected, your GPIO setup is working correctly!")
    print("You can now run: python3 ps3_motor_controller.py")
    print()

except KeyboardInterrupt:
    print("\n\n⚠️  Test interrupted by user")

except PermissionError:
    print("\n❌ ERROR: Permission denied!")
    print()
    print("Try one of these solutions:")
    print("  1. Run with sudo: sudo python3 test_gpio_rpi5.py")
    print("  2. Add user to gpio group: sudo usermod -a -G gpio $USER")
    print("  3. On RPi 5: sudo chmod 666 /dev/gpiochip4")
    print()

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Cleanup
    print("\nCleaning up GPIO...")

    if GPIO_BACKEND == 'gpiod' and lines:
        for line in lines.values():
            line.release()
        if chip:
            chip.close()
    elif GPIO_BACKEND == 'RPi.GPIO':
        GPIO.cleanup()

    print("✅ Cleanup complete\n")
